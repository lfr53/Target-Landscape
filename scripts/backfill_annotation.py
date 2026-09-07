"""Fill the curated landscapes with UniProt annotation, without rebuilding them.

A curated landscape is precomputed and committed, so it carries whatever the
pipeline produced on the day it ran. Adding a source afterwards leaves those
files one block short: the header falls back to the Open Targets function line
and says so, which is honest but thin, and rebuilding fifteen landscapes to
add one paragraph means fifteen more full sweeps of three APIs.

This does the small version. It reads each stored landscape, fetches the
UniProt record for its symbol, writes the annotation block back, and leaves
everything else in the file untouched.

    python scripts/backfill_annotation.py              # every curated file
    python scripts/backfill_annotation.py TNFRSF13C    # one of them
    python scripts/backfill_annotation.py --show PDCD1 # print, write nothing

``--show`` is the one to run first. It prints the paragraph a target would
get, so the parser can be checked against the live API by reading its output
rather than by trusting it.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape.sources import uniprot as uniprot_src  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED = os.path.join(ROOT, "data", "curated")
FIXTURES = os.path.join(ROOT, "fixtures")


def _stored_landscape(symbol: str):
    """The curated or fixture landscape for this symbol, if one is stored.

    Only used to preview the derived half of the header. Returns None rather
    than raising: a symbol with no stored landscape is normal, and the preview
    says so instead of failing.
    """
    from landscape import pipeline

    for directory in (CURATED, FIXTURES):
        path = os.path.join(directory, f"{symbol.upper()}.json")
        if os.path.exists(path):
            try:
                return pipeline.load_fixture(path, recompute=True)
            except Exception:  # noqa: BLE001 - a preview is never worth failing for
                return None
    return None


def show(symbol: str) -> int:
    try:
        record = uniprot_src.fetch_brief(symbol)
    except Exception as exc:  # noqa: BLE001 - this is the diagnostic path
        # Saying "no reviewed entry" here would state something about the
        # protein that this run has no evidence for. The request failed; say
        # that, and print enough to fix it.
        print(f"{symbol}: the UniProt request FAILED — this is not a statement")
        print("about the gene. The query never got an answer.")
        print()
        print(f"  error: {exc}")
        print(f"  url:   {uniprot_src.UNIPROT_API}")
        print(f"  query: gene:{symbol} AND organism_id:9606 AND reviewed:true")
        print(f"  fields:{uniprot_src.FIELDS}")
        print()
        print("Most likely a blocked network, or a field name UniProt has renamed.")
        return 2
    if not record:
        print(f"{symbol}: the query succeeded and matched no reviewed human entry.")
        return 1

    brief = record.get("brief") or {}
    print(f"{symbol}  —  {record.get('protein_name', '')}")
    print(f"{record.get('accession', '')}  ·  {record.get('url', '')}")
    print()
    if not brief.get("segments"):
        print("No FUNCTION comment, so no curated header. The page will fall back")
        print("to the Open Targets function line and say where it came from.")
        return 1

    # The curated text is only half the header. The other half - what the
    # target is actually being drugged for - is derived from the asset table,
    # so previewing the curated half alone shows something mostly about a
    # germline disease and misrepresents what the page will render.
    from landscape.analysis import brief as brief_mod

    landscape = _stored_landscape(symbol)
    # Composed either way. With no stored landscape the composer withholds
    # both the development row and the germline-disease row, rather than
    # printing a header whose only disease is the one nobody is treating.
    shown = brief_mod.compose(landscape, record)
    if not shown:
        print("The composer returned nothing for this record.")
        return 1

    # compose() returns separable fact rows and a mechanism note. It used to
    # return one paragraph under a "text" key, and this preview still read that
    # key long after the paragraph was replaced -- so every run ended in a
    # KeyError after the build had already succeeded.
    for row in shown.get("facts") or []:
        print(f"  {row['label']}")
        print(f"      {row['value']}")
        if row.get("note"):
            print(f"      ({row['note']})")
        if row.get("pmids"):
            print(f"      PMID {', '.join(row['pmids'])}")
        print()

    mechanism = shown.get("mechanism") or {}
    if mechanism.get("text"):
        words = len([w for w in mechanism["text"].split() if w])
        print(f"  Mechanisms tab [{words} words]")
        print(f"      {mechanism['text'][:300]}{'...' if len(mechanism['text']) > 300 else ''}")
        if mechanism.get("pmids"):
            print(f"      PMID {', '.join(mechanism['pmids'])}")
        print()

    domains = ", ".join(f"{d['name']} x{d['count']}" for d in record.get("domains", []))
    print(f"  domains   {domains or 'none annotated'}")
    for disease in record.get("disease", []):
        print(f"  disease   {disease['name']} ({disease.get('acronym') or '-'})")
    if shown.get("development_unknown"):
        print()
        print(f"  NOTE: no landscape is stored for {symbol}, so this preview cannot")
        print("  show what the target is being developed for - and the germline")
        print("  disease row is withheld with it, because on its own a reader")
        print("  takes it for the indication. Build the landscape to see the full")
        print("  header:")
        print(f"      python scripts\\precompute.py {symbol}")
    return 0


def backfill(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    symbol = (payload.get("target") or {}).get("symbol") or ""
    if not symbol:
        return f"{os.path.basename(path)}: no symbol, skipped"

    try:
        record = uniprot_src.fetch_brief(symbol)
    except Exception as exc:  # noqa: BLE001
        return f"{symbol}: REQUEST FAILED ({exc}) — file left as it was"
    if not record:
        return f"{symbol}: no reviewed UniProt entry — left as it was"

    payload["annotation"] = record
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    brief = record.get("brief") or {}
    if not brief.get("text"):
        return f"{symbol}: record stored, but no FUNCTION comment — no brief"
    return f"{symbol}: {brief['words']} words, {record['accession']}"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--show":
        if len(argv) < 2:
            print("usage: backfill_annotation.py --show SYMBOL")
            return 2
        return show(argv[1])

    wanted = {a.upper() for a in argv}
    paths = []
    for directory in (CURATED, FIXTURES):
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            if wanted and name[:-5].upper() not in wanted:
                continue
            paths.append(os.path.join(directory, name))

    if not paths:
        print("Nothing to do.")
        return 1
    for path in paths:
        print(backfill(path), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
