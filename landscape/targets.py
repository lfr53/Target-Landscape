"""The target index: what you can search for.

Autocomplete against a remote API has two problems for this tool. It is a
round trip per keystroke to a service the analysis also depends on, and it
only matches what that service indexes — which, for gene search, means
approved symbols and whatever aliases the source happens to carry. Nobody
types ``TNFRSF13C``. They type BAFF-R, HER2, PD-1, TL1A.

So search runs against a local index instead: instant, offline, and matched on
the names people actually use. The index ships seeded with the targets that
come up in drug development (``scripts/seed_target_index.py``) and expands to
the full HGNC gene set when someone runs ``scripts/build_target_index.py``.

Ranking matters more than matching here. A query of "MET" must return MET
before MC4R, METTL3 and every gene whose description contains the word. The
order is: exact symbol, exact alias, symbol prefix, alias prefix, symbol
substring, then name substring — with shorter symbols first inside each band,
because a short symbol matching a short query is almost always the intended one.
"""

from __future__ import annotations

import functools
import json
import os
import re
from typing import Any, Optional

INDEX_PATH = os.environ.get(
    "LANDSCAPE_TARGET_INDEX",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "target_index.json"
    ),
)

_NORM = re.compile(r"[^a-z0-9]")

# HGNC carries entries that are not single approved gene symbols: readthrough
# fusions (APOBEC3A_B), cluster placeholders (PCDHA@), duplicated-region
# records (C4A_2). They resolve to nothing in Open Targets, so a user who
# picks one from the dropdown gets a build that cannot start. They are dropped
# at load rather than filtered per query, so every path sees the same index.
_APPROVED_SYMBOL = re.compile(r"^[A-Z][A-Z0-9-]{1,14}$")


def _word_match(needle: str, haystack: str) -> bool:
    try:
        return re.search(r"\b" + re.escape(needle), haystack) is not None
    except re.error:
        return needle in haystack


def normalise(text: str) -> str:
    """Fold to a comparison key: 'BAFF-R', 'baff r' and 'BAFFR' all match."""
    return _NORM.sub("", (text or "").lower())


@functools.lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    """Load and index the file once per process."""
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {"records": [], "by_symbol": {}, "by_key": {}, "areas": {}}

    records = [
        r for r in (raw.get("records") or [])
        if _APPROVED_SYMBOL.match((r.get("symbol") or "").upper())
    ]
    by_symbol: dict[str, dict[str, Any]] = {}
    by_key: dict[str, list[dict[str, Any]]] = {}
    areas: dict[str, int] = {}

    for record in records:
        symbol = (record.get("symbol") or "").upper()
        by_symbol[symbol] = record
        for name in [symbol] + list(record.get("aliases") or []):
            key = normalise(name)
            if key:
                by_key.setdefault(key, []).append(record)
        for area in record.get("areas") or []:
            areas[area] = areas.get(area, 0) + 1

    return {"records": records, "by_symbol": by_symbol, "by_key": by_key, "areas": areas}


def reload_index() -> None:
    """Drop the cache — used after regenerating the file."""
    _load.cache_clear()


def size() -> int:
    return len(_load()["records"])


def areas() -> list[dict[str, Any]]:
    counts = _load()["areas"]
    return [{"area": a, "n": n} for a, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def get(symbol: str) -> Optional[dict[str, Any]]:
    return _load()["by_symbol"].get((symbol or "").upper())


def resolve_alias(query: str) -> Optional[str]:
    """Return the approved symbol for an alias, if the index knows one.

    This is what lets someone search "HER2" and get an ERBB2 landscape rather
    than a failed lookup — the pipeline only speaks approved symbols.
    """
    hits = _load()["by_key"].get(normalise(query)) or []
    if not hits:
        return None
    key = normalise(query)
    return min(hits, key=lambda r: _alias_rank(r, key, (query or "").strip().lower()))["symbol"]


def _alias_rank(record: dict[str, Any], key: str, spelling: str) -> tuple:
    """Tie-break order when several genes answer to one nickname.

    Vernacular names are not unique in HGNC and shortest-symbol-wins gets the
    common ones wrong: ``PD1`` is an alias of PDCD1, of SNCA (Parkinson
    disease 1) and of SPATA2, and the shortest of those is alpha-synuclein.
    Serving that for "PD-1" is not a near miss — it is a different field of
    medicine, and on a drug-target tool it is the answer nobody meant.

    So three signals come before symbol length:

      * **The spelling the user typed.** ``PD-1`` is curated as an alias on
        PDCD1 and only ``PD1`` on SNCA. A curator writing the hyphenated
        vernacular on a gene is evidence about which gene owns the nickname.
      * **How many spellings of it that gene carries.** PDCD1 lists both
        ``PD-1`` and ``PD1``; SNCA lists ``PD1`` alone, as a relic of the
        Parkinson disease 1 locus. A gene whose curators recorded the nickname
        more than one way is the gene the nickname belongs to.
      * **Whether the gene is a hand-checked drug target.** The seeded records
        are the targets that come up in drug development. On a genuine
        ambiguity, this tool exists to answer about those.

    None of this makes the search omniscient, and it is not meant to: the
    dropdown still lists every gene that answers to the query, in this order,
    so a reader who wanted alpha-synuclein can see it and click it.
    """
    aliases = [a.strip() for a in record.get("aliases") or []]
    lowered = {a.lower() for a in aliases}
    spellings = sum(1 for a in aliases if normalise(a) == key)
    return (
        0 if normalise(record["symbol"]) == key else 1,
        0 if spelling in lowered else 1,
        -spellings,
        0 if "seed" in (record.get("source") or "") else 1,
        len(record["symbol"]),
        record["symbol"],
    )


def search(query: str, limit: int = 12) -> list[dict[str, Any]]:
    """Ranked search over symbols, aliases and names."""
    raw = (query or "").strip()
    if len(raw) < 1:
        return []
    key = normalise(raw)
    lowered = raw.lower()
    if not key:
        return []

    index = _load()
    scored: list[tuple[tuple, dict[str, Any]]] = []

    for record in index["records"]:
        symbol = record["symbol"]
        symbol_key = normalise(symbol)
        alias_keys = [normalise(a) for a in record.get("aliases") or []]
        name = (record.get("name") or "").lower()

        rank: Optional[int] = None
        matched_on = symbol

        if symbol_key == key:
            rank = 0
        elif key in alias_keys:
            rank = 1
            # Show the alias the user actually typed where it exists, so
            # "HER2" is not echoed back as "HER-2".
            aliases = record.get("aliases") or []
            matched_on = next(
                (a for a in aliases if a.lower() == lowered),
                next((a for a in aliases if normalise(a) == key), symbol),
            )
        elif symbol_key.startswith(key):
            rank = 2
        elif any(a.startswith(key) for a in alias_keys):
            rank = 3
            matched_on = next(
                (a for a in record.get("aliases") or [] if normalise(a).startswith(key)), symbol
            )
        elif key in symbol_key:
            rank = 4
        elif len(lowered) >= 3 and _word_match(lowered, name):
            # Word-boundary only: a bare substring makes "MET" match
            # "methyltransferase" and "methylglutaryl", burying the real gene.
            rank = 5
        elif len(key) >= 3 and any(key in a for a in alias_keys):
            rank = 5
            matched_on = next(
                (a for a in record.get("aliases") or [] if key in normalise(a)), symbol
            )

        if rank is None:
            continue
        # Inside a band, the same tie-break resolve_alias uses — a dropdown
        # that puts SNCA above PDCD1 for "PD-1" is wrong in the one place the
        # reader has no way to correct it. The band still leads: an exact
        # symbol match never loses to a better-nicknamed alias hit.
        scored.append((
            (rank, *_alias_rank(record, key, lowered)[1:]),
            {**record, "matched_on": matched_on},
        ))

    scored.sort(key=lambda pair: pair[0])
    return [record for _, record in scored[:limit]]


def browse(area: Optional[str] = None, limit: int = 500) -> list[dict[str, Any]]:
    """Records for browsing, with the drug targets first.

    After the HGNC merge the index holds ~28,000 genes, the vast majority of
    which are not drug targets. Sorting the whole thing alphabetically puts
    A1BG, A1BG-AS1 and A1CF on the landing page, which tells a visitor nothing
    about what the tool is for. The hand-checked seed — the targets that
    actually come up in drug development — leads instead, and the rest of the
    genome follows behind it.
    """
    records = _load()["records"]
    if area:
        records = [r for r in records if area in (r.get("areas") or [])]
    # A therapeutic-area tag only exists on seeded records, so it doubles as
    # the "this is a real drug target" flag.
    return sorted(
        records,
        key=lambda r: (0 if (r.get("areas") or r.get("source") in {"seed", "hgnc+seed"}) else 1,
                       r["symbol"]),
    )[:limit]


def seeded_count() -> int:
    return sum(
        1
        for r in _load()["records"]
        if r.get("areas") or r.get("source") in {"seed", "hgnc+seed"}
    )
