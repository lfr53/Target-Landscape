#!/usr/bin/env python3
"""Seed the curated tier.

    python scripts/precompute.py TNFRSF13C TNFSF13B PDCD1
    python scripts/precompute.py --set calibration/targets.txt
    python scripts/precompute.py --from-fixture fixtures/TNFRSF13C.json

Curated records are committed to the repository. They are what makes the site
open instantly and what makes a demo safe: serving them touches no external
API, so a Space with a curated library still works on a morning when Open
Targets is down.

Records are stored fully computed — analysis included — rather than as raw
source data, because the web layer should never do analysis on the request
path. Recomputing after a rule change means re-running this script, which is
the right trade: rule changes are rare, page loads are not.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import pipeline, store  # noqa: E402


def _progress(stage: str, label: str, index: int, total: int) -> None:
    print(f"    [{index + 1}/{total}] {label}…", flush=True)


def read_set(path: str) -> list[str]:
    out: list[str] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                out.append(line)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Precompute curated target landscapes.")
    parser.add_argument("targets", nargs="*", help="gene symbols")
    parser.add_argument("--set", dest="set_file", help="file of symbols, one per line")
    parser.add_argument("--from-fixture", help="promote a saved fixture into the curated tier")
    parser.add_argument("--no-llm", action="store_true", help="rules only")
    parser.add_argument("--skip-existing", action="store_true",
                        help="leave targets already in the curated tier alone")
    args = parser.parse_args(argv)

    if args.from_fixture:
        landscape = pipeline.load_fixture(args.from_fixture)
        path = store.save_curated(landscape)
        print(f"curated ← {args.from_fixture} → {path}")
        return 0

    targets = list(args.targets)
    if args.set_file:
        targets += read_set(args.set_file)
    if not targets:
        parser.error("give some symbols, --set, or --from-fixture")

    existing = set(store.curated_symbols())
    done, failed = 0, []
    for i, symbol in enumerate(targets, 1):
        if args.skip_existing and symbol.upper() in existing:
            print(f"[{i}/{len(targets)}] {symbol} — already curated, skipping")
            continue
        print(f"[{i}/{len(targets)}] {symbol}")
        started = time.time()
        try:
            landscape = pipeline.build(
                symbol,
                use_llm=False if args.no_llm else None,
                deals=store.load_deals(symbol),
                on_progress=_progress,
            )
        except Exception as exc:  # noqa: BLE001 - one bad target must not stop the batch
            print(f"    failed: {exc}", file=sys.stderr)
            failed.append(f"{symbol}: {exc}")
            continue
        path = store.save_curated(landscape)
        crowding = landscape.crowding
        print(f"    {crowding.get('n_active')} active · {crowding.get('verdict')} "
              f"({crowding.get('weighted_score')}) · {time.time() - started:.0f}s → {path}")
        done += 1

    print(f"\ncurated {done} target(s) into {store.CURATED_DIR}")
    for failure in failed:
        print(f"  failed: {failure}", file=sys.stderr)
    if failed:
        print("\nRe-run for the failures once the APIs recover, or check "
              "'python -m landscape doctor'.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
