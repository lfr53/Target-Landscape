"""Command line entry point.

    python -m landscape doctor                       # check the APIs first
    python -m landscape TNFRSF13C
    python -m landscape TNFRSF13C IL23A TL1A --out out/
    python -m landscape --fixture fixtures/TNFRSF13C.json
    python -m landscape TNFRSF13C --save-fixture fixtures/TNFRSF13C.json
    python -m landscape --calibrate                  # run the reference set
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Optional

from . import pipeline, render
from .models import Deal, Landscape

CALIBRATION_SET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calibration", "targets.txt"
)


def load_deals(path: Optional[str]) -> list[Deal]:
    if not path:
        return []
    if not os.path.exists(path):
        print(f"warning: deals file not found: {path}", file=sys.stderr)
        return []
    out: list[Deal] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            def num(key: str) -> Optional[float]:
                value = (row.get(key) or "").strip()
                try:
                    return float(value) if value else None
                except ValueError:
                    return None

            out.append(
                Deal(
                    date=(row.get("date") or "").strip(),
                    acquirer=(row.get("acquirer") or "").strip(),
                    target_company=(row.get("target_company") or "").strip(),
                    asset=(row.get("asset") or "").strip(),
                    mechanism=(row.get("mechanism") or "").strip(),
                    stage_at_deal=(row.get("stage_at_deal") or "").strip(),
                    upfront_usd_m=num("upfront_usd_m"),
                    total_usd_m=num("total_usd_m"),
                    territory=(row.get("territory") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                )
            )
    return out


def load_calibration_targets(path: str) -> list[str]:
    if not os.path.exists(path):
        print(f"error: calibration set not found: {path}", file=sys.stderr)
        return []
    targets: list[str] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                targets.append(line)
    return targets


def write_outputs(landscape: Landscape, out_dir: str, formats: set[str]) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    stem = landscape.target.symbol or "landscape"
    written: dict[str, str] = {}
    if "html" in formats:
        path = os.path.join(out_dir, f"{stem}_landscape.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render.to_html(landscape))
        written["html"] = path
    if "md" in formats:
        path = os.path.join(out_dir, f"{stem}_landscape.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render.to_markdown(landscape))
        written["md"] = path
    if "json" in formats:
        path = os.path.join(out_dir, f"{stem}_landscape.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(landscape.to_dict(), fh, indent=2, ensure_ascii=False)
        written["json"] = path
    return written


def summarise(landscape: Landscape) -> str:
    c = landscape.crowding
    return (
        f"{landscape.target.symbol:<12} "
        f"{str(c.get('weighted_score', 0)):>6}  {c.get('verdict', '?'):<10} "
        f"{c.get('n_active', 0):>3} active  lead {c.get('lead_phase', '?')}"
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="landscape",
        description="Build competitive landscape memos for drug targets from public data.",
        epilog="Run 'python -m landscape doctor' first if a live run behaves oddly — "
               "it reports which API field moved.",
    )
    parser.add_argument("targets", nargs="*",
                        help="gene symbols or Ensembl IDs; or the single word 'doctor'")
    parser.add_argument("--fixture", help="build from a saved JSON fixture instead of the network")
    parser.add_argument("--save-fixture", help="write the raw records to JSON for offline reuse")
    parser.add_argument("--out", default="out", help="output directory (default: out)")
    parser.add_argument("--format", default="html,md,json", help="comma-separated: html, md, json")
    parser.add_argument("--deals", help="CSV of hand-curated deal comparables")
    parser.add_argument("--index", action="store_true",
                        help="also write index.html comparing the targets (default when >1)")
    parser.add_argument("--calibrate", action="store_true",
                        help="run the reference target set in calibration/targets.txt")
    parser.add_argument("--no-llm", action="store_true", help="rules only, no model calls")
    parser.add_argument("--llm", action="store_true", help="force the model pass on")
    args = parser.parse_args(argv)

    # doctor is a subcommand in positional clothing — it needs no other flags.
    if len(args.targets) == 1 and args.targets[0].lower() == "doctor":
        from . import doctor

        return doctor.run()

    targets = list(args.targets)
    if args.calibrate:
        targets = load_calibration_targets(CALIBRATION_SET) or targets
        if not targets:
            return 1
        args.index = True

    if not targets and not args.fixture:
        parser.error("give one or more target symbols, --fixture, --calibrate, or 'doctor'")

    use_llm: Optional[bool] = None
    if args.no_llm:
        use_llm = False
    elif args.llm:
        use_llm = True

    formats = {f.strip().lower() for f in args.format.split(",") if f.strip()}
    deals = load_deals(args.deals)
    built: list[tuple[Landscape, str]] = []
    failures: list[str] = []

    if args.fixture:
        landscape = pipeline.load_fixture(args.fixture)
        if deals:
            landscape.deals = deals
        if args.save_fixture:
            os.makedirs(os.path.dirname(args.save_fixture) or ".", exist_ok=True)
            pipeline.save_fixture(landscape, args.save_fixture)
            print(f"fixture → {args.save_fixture}")
        written = write_outputs(landscape, args.out, formats)
        built.append((landscape, os.path.basename(written.get("html", ""))))
        for kind, path in written.items():
            print(f"{kind} → {path}")
    else:
        for i, symbol in enumerate(targets, 1):
            prefix = f"[{i}/{len(targets)}] " if len(targets) > 1 else ""
            print(f"{prefix}{symbol} …", flush=True)
            try:
                from . import store as store_mod
                landscape = pipeline.build(
                    symbol,
                    use_llm=use_llm,
                    deals=deals or store_mod.load_deals(symbol),
                )
            except Exception as exc:  # noqa: BLE001 - one bad target must not stop a batch
                failures.append(f"{symbol}: {exc}")
                print(f"    failed: {exc}", file=sys.stderr)
                continue
            if args.save_fixture and len(targets) == 1:
                os.makedirs(os.path.dirname(args.save_fixture) or ".", exist_ok=True)
                pipeline.save_fixture(landscape, args.save_fixture)
                print(f"    fixture → {args.save_fixture}")
            written = write_outputs(landscape, args.out, formats)
            built.append((landscape, os.path.basename(written.get("html", ""))))
            if len(targets) == 1:
                for kind, path in written.items():
                    print(f"{kind} → {path}")
            else:
                print("    " + summarise(landscape))

    if not built:
        print("nothing built.", file=sys.stderr)
        return 1

    if (args.index or len(built) > 1) and "html" in formats:
        index_path = os.path.join(args.out, "index.html")
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(render.to_index(built))
        print(f"index → {index_path}")

    print()
    if len(built) > 1:
        print("target        score  verdict     assets")
        for landscape, _ in sorted(
            built, key=lambda e: -(e[0].crowding.get("weighted_score") or 0)
        ):
            print("  " + summarise(landscape))
    else:
        print(summarise(built[0][0]))

    seen: set[str] = set()
    for landscape, _ in built:
        for warning in landscape.warnings:
            if warning not in seen:
                seen.add(warning)
                print(f"  warning: {warning}", file=sys.stderr)
    for failure in failures:
        print(f"  failed: {failure}", file=sys.stderr)
    return 1 if failures and not built else 0


if __name__ == "__main__":
    raise SystemExit(main())
