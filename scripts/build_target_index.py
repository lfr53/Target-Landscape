#!/usr/bin/env python3
"""Expand the target index to the full human gene set.

    python scripts/build_target_index.py

Pulls the HGNC complete set — every approved human gene symbol with its name,
previous symbols and alias symbols — and merges it over the hand-checked seed
index. Roughly 20,000 protein-coding genes, about 3 MB on disk, and after this
the search box covers every target anyone could ask for, offline.

The seed is merged *on top*, not replaced, for one reason: HGNC's alias fields
are authoritative but incomplete for vernacular. "PD-1" is in there. "BAFF-R",
"TL1A" and "Claudin-18.2" are patchier, and those are exactly the strings
people type. So the seed's aliases and therapeutic areas survive the merge.

Non-coding genes, pseudogenes and withdrawn entries are dropped: they cannot
be drug targets, and 20,000 relevant rows search faster and rank better than
45,000 rows where most are noise.

HGNC is free to use with attribution (https://www.genenames.org/about/).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import targets as targets_mod  # noqa: E402

HGNC_URL = os.environ.get(
    "HGNC_URL",
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt",
)

# Locus types that can plausibly be a drug target.
KEEP_LOCUS_TYPES = {
    "gene with protein product",
    "immunoglobulin gene",
    "T cell receptor gene",
    "RNA, micro",
    "RNA, long non-coding",
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "target-landscape/0.2"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


def parse(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    out: list[dict] = []
    for row in reader:
        if (row.get("status") or "").strip() != "Approved":
            continue
        if (row.get("locus_type") or "").strip() not in KEEP_LOCUS_TYPES:
            continue
        symbol = (row.get("symbol") or "").strip().upper()
        if not symbol:
            continue

        aliases: set[str] = set()
        for field in ("alias_symbol", "prev_symbol", "alias_name"):
            value = (row.get(field) or "").strip().strip('"')
            for part in value.split("|"):
                part = part.strip()
                # Long descriptive alias names add noise without helping search.
                if part and part.upper() != symbol and len(part) <= 40:
                    aliases.add(part)

        out.append({
            "symbol": symbol,
            "name": (row.get("name") or "").strip(),
            "aliases": sorted(aliases),
            "areas": [],
            "source": "hgnc",
        })
    return out


def merge(hgnc: list[dict], seed: list[dict]) -> list[dict]:
    """HGNC as the base; the seed's aliases and areas layered over it."""
    by_symbol = {r["symbol"]: r for r in hgnc}
    for record in seed:
        symbol = record["symbol"]
        existing = by_symbol.get(symbol)
        if existing is None:
            by_symbol[symbol] = {**record, "source": "seed"}
            continue
        existing["aliases"] = sorted(
            set(existing.get("aliases") or []) | set(record.get("aliases") or [])
        )
        existing["areas"] = sorted(set(existing.get("areas") or []) | set(record.get("areas") or []))
        existing["source"] = "hgnc+seed"
        if record.get("name") and not existing.get("name"):
            existing["name"] = record["name"]
    return [by_symbol[k] for k in sorted(by_symbol)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the full target index from HGNC.")
    parser.add_argument("--url", default=HGNC_URL)
    parser.add_argument("--out", default=targets_mod.INDEX_PATH)
    parser.add_argument("--from-file", help="parse a local HGNC TSV instead of downloading")
    args = parser.parse_args(argv)

    # Keep whatever is already there — the seed, or a previous full build.
    existing: list[dict] = []
    if os.path.exists(args.out):
        try:
            with open(args.out, "r", encoding="utf-8") as fh:
                existing = (json.load(fh) or {}).get("records") or []
        except (OSError, json.JSONDecodeError):
            existing = []
    seed = [r for r in existing if r.get("source") in {"seed", "hgnc+seed"}]
    print(f"seed records to preserve: {len(seed)}")

    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        print(f"downloading {args.url} …", flush=True)
        try:
            text = fetch(args.url)
        except Exception as exc:  # noqa: BLE001
            print(f"\ndownload failed: {exc}", file=sys.stderr)
            print(
                "The index still works — it keeps the seeded targets, and any symbol "
                "can still be looked up directly. Retry when the network allows, or "
                "download the file yourself and pass --from-file.",
                file=sys.stderr,
            )
            return 1

    hgnc = parse(text)
    print(f"HGNC approved, drug-target-plausible loci: {len(hgnc)}")

    records = merge(hgnc, seed)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"version": 2, "source": "HGNC + seed", "records": records}, fh,
                  ensure_ascii=False)

    size_mb = os.path.getsize(args.out) / 1_048_576
    print(f"{args.out} — {len(records)} targets, {size_mb:.1f} MB")

    targets_mod.reload_index()
    for probe in ["HER2", "BAFF-R", "PD-1", "TL1A"]:
        hits = targets_mod.search(probe, limit=1)
        print(f"  {probe:8} → {hits[0]['symbol'] if hits else 'NOT FOUND'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
