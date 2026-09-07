#!/usr/bin/env python3
"""Re-run the analysis layer over every curated target. No network.

    python scripts/recompute_curated.py
    python scripts/recompute_curated.py PDCD1 EGFR      # only these

Curated files are stored **fully computed** — the crowding verdict, the six
questions, the tier text, the header facts are all written into the file, so
that serving a target touches no external API and cannot fail on a strange
network. The cost of that trade is this script: when a rule changes, every
file built before the change still carries the old output.

Nothing here calls an API. `pipeline.load_fixture(recompute=True)` re-runs the
whole analysis layer over the raw records already in the file — the same
records, the current rules — so it takes about a second per target instead of
the twenty to forty seconds a rebuild costs, and it works with no connection
at all. The two layers that genuinely are network results, the reading list
and the curated UniProt annotation, are carried across untouched.

Rebuild with `precompute.py` instead when you want *newer data*; recompute
with this when you want *the current rules over the data you already have*.
"""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import consistency, pipeline, relevance, store  # noqa: E402
from landscape.store import CURATED_DIR, _path  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        symbols = store.curated_symbols()
    except Exception as exc:
        print(f"Could not read the curated library: {exc}")
        return 1

    if argv:
        wanted = {s.upper() for s in argv}
        missing = sorted(wanted - {s.upper() for s in symbols})
        if missing:
            print(f"Not in the curated library: {', '.join(missing)}")
        symbols = [s for s in symbols if s.upper() in wanted]

    if not symbols:
        print("Nothing to recompute.")
        return 0

    print(f"Recomputing {len(symbols)} target(s) with the current rules. No network.")
    failed: list[str] = []
    unverifiable: list[tuple[str, int]] = []
    inconsistent: list[tuple[str, list[str]]] = []
    for index, symbol in enumerate(symbols, 1):
        path = _path(CURATED_DIR, symbol)
        try:
            landscape = pipeline.load_fixture(path, recompute=True)
            # Which stored trials cannot be shown to be about this target?
            # This pass cannot decide them: the registry matched on a summary
            # the older builds never stored, so a genuine TL1A antibody trial
            # and a hypertension trial look identical from here. Counted and
            # reported, not deleted -- a rebuild is what settles them.
            terms = relevance.terms_for(landscape.target, landscape.assets)
            _, unclear = relevance.filter_trials(landscape.trials, terms)
            store.save_curated(landscape)
            if unclear:
                unverifiable.append((symbol, len(unclear)))
            note = f" - {len(unclear)} trial(s) unverified" if unclear else ""
            # Every figure the page shows, checked against the data behind it.
            # Counts are derived by different modules from one asset table, so
            # they can drift apart silently; this is where that surfaces.
            problems = consistency.check(landscape)
            if problems:
                inconsistent.append((symbol, problems))
                note += f" - {len(problems)} figure(s) disagree"
            print(f"  [{index}/{len(symbols)}] {symbol}{note}")
        except Exception:
            # One bad file must not stop the pass — the other twenty are fine,
            # and the traceback is what says which rule broke on which target.
            failed.append(symbol)
            print(f"  [{index}/{len(symbols)}] {symbol} — FAILED")
            traceback.print_exc()

    if inconsistent:
        print()
        print("Figures that do not agree with each other:")
        for symbol, problems in inconsistent:
            print(f"  {symbol}")
            for problem in problems:
                print(f"      {problem}")

    if unverifiable:
        print()
        print("Trials whose own text names neither the target nor any drug known to")
        print("act on it. They are counted as trials and contribute no asset, so this")
        print("is a note about the record rather than something to fix:")
        for symbol, n in unverifiable:
            print(f"  {symbol}: {n}")

    if failed:
        print(f"\n{len(failed)} failed: {', '.join(failed)}")
        print("Those targets still hold their previous, older output.")
        return 1
    print("\nDone. Every curated target now reflects the current rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
