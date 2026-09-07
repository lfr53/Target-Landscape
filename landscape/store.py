"""Where landscapes live between requests.

Two tiers, and the distinction is visible to the user rather than hidden:

**Curated** — targets precomputed by a maintainer and committed to the repo.
These load in milliseconds and cannot fail, because serving them touches no
external API. They are what a demo runs on, and what a first-time visitor
lands in.

**Cached** — targets someone looked up live. Written to a cache directory,
served from there until they age out. On Hugging Face Spaces this directory is
ephemeral (it resets when the Space restarts), which is fine: the curated tier
is the durable one, and a cache miss just means a rebuild.

Every record carries the tier and the time it was built, because a competitive
landscape from four months ago is a different claim from one built this
morning, and the interface has to say which it is showing.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re
import threading
from typing import Any, Optional

from . import pipeline
from .models import Landscape

# Committed to the repo; seeded by scripts/precompute.py.
CURATED_DIR = os.environ.get(
    "LANDSCAPE_CURATED",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "curated"),
)
# Ephemeral. On Spaces, /data is writable when persistent storage is enabled,
# otherwise this falls back to a temp dir the container owns.
CACHE_DIR = os.environ.get(
    "LANDSCAPE_STORE_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "target-landscape", "store")
)
CACHE_MAX_AGE_DAYS = int(os.environ.get("LANDSCAPE_CACHE_DAYS", "14"))

DEALS_DIR = os.environ.get(
    "LANDSCAPE_DEALS",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "deals"),
)

# Programmes a person entered by hand, because the rules would not take them
# from the record. The discovery rules only admit a drug when the trial's own
# words tie it to the target, and that is deliberate -- it is what keeps
# posaconazole off CARD9 and hydrochlorothiazide off MAP3K14. It also costs
# real programmes: NCT07431281 mentions Claudin18.2 three times and all three
# are "-positive" and "Expressing", the patient-selection criterion. The rule
# cannot tell that record from a chemotherapy trial in the same population,
# and it should not guess. A person can, with a source.
ASSETS_DIR = os.environ.get(
    "LANDSCAPE_ASSETS",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "assets"),
)

_SYMBOL_RE = re.compile(r"^[A-Za-z0-9\-]{1,32}$")
_lock = threading.Lock()


class UnknownTarget(ValueError):
    pass


def normalise_symbol(symbol: str) -> str:
    """Uppercase and validate. Also the path-traversal guard.

    Symbols become filenames, so anything that is not a plain gene symbol or
    Ensembl id is rejected here rather than being sanitised into something
    surprising.
    """
    cleaned = (symbol or "").strip().upper()
    if not _SYMBOL_RE.match(cleaned):
        raise UnknownTarget(f"not a valid target symbol: {symbol!r}")
    return cleaned


def _path(directory: str, symbol: str) -> str:
    return os.path.join(directory, f"{symbol}.json")


def _age_days(path: str) -> float:
    return (_dt.datetime.now().timestamp() - os.path.getmtime(path)) / 86400.0


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


_PHASE_FROM_TEXT = {
    "preclinical": 0, "0": 0,
    "phase 1": 1, "phase1": 1, "1": 1, "i": 1, "phase i": 1,
    "phase 1/2": 2, "phase 2": 2, "phase2": 2, "2": 2, "ii": 2, "phase ii": 2,
    "phase 2/3": 3, "phase 3": 3, "phase3": 3, "3": 3, "iii": 3, "phase iii": 3,
    "approved": 4, "phase 4": 4, "4": 4, "iv": 4, "marketed": 4,
}


def parse_phase(value: str) -> int:
    """"Phase 3", "3" and "III" all mean 3. Anything else means unknown, which
    the page prints as Unknown rather than guessing a number."""
    return _PHASE_FROM_TEXT.get((value or "").strip().lower(), -1)


def load_manual_assets(symbol: str) -> list["Asset"]:
    """Hand-entered programmes for one target, from data/assets/<SYMBOL>.csv.

    Every row carries a source URL, and the page shows it: a row a reader
    cannot check is worse than a missing row, because the rest of the table is
    checkable and this one would borrow that credibility.

    The rows are merged before the analysis layer runs, not attached at read
    time like the deal file. A programme changes the asset count, the phase
    histogram, the crowding band and the mechanism clusters; attaching it later
    would put a row on the page that none of the figures above it knew about,
    which is the arithmetic that had to be fixed once already.
    """
    from .models import Asset, Provenance

    symbol = normalise_symbol(symbol)
    path = os.path.join(ASSETS_DIR, f"{symbol}.csv")
    if not os.path.exists(path):
        return []

    def split(value: str) -> list[str]:
        return [p.strip() for p in (value or "").split(";") if p.strip()]

    out: list[Asset] = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                name = (row.get("name") or "").strip()
                url = (row.get("source_url") or "").strip()
                # No source, no row. The file is only worth having if this
                # holds, so it is enforced here rather than asked for in a
                # README.
                if not name or not url:
                    continue
                out.append(Asset(
                    name=name,
                    sponsor=(row.get("sponsor") or "").strip(),
                    modality=(row.get("modality") or "").strip() or "Other / unclassified",
                    mechanism_text=(row.get("mechanism") or "").strip(),
                    max_phase=parse_phase(row.get("max_phase", "")),
                    indications=split(row.get("indications", "")),
                    trials=split(row.get("trials", "")),
                    synonyms=split(row.get("synonyms", "")),
                    # Optional, and the reason it exists is ERBB2. ChEMBL's
                    # record for ado-trastuzumab emtansine lists "Trastuzumab",
                    # "Herceptin" and every trastuzumab biosimilar among its
                    # synonyms, so the parent antibody was folded into the ADC
                    # and the table showed no trastuzumab at all. Two different
                    # ChEMBL ids are ChEMBL saying these are two molecules, and
                    # the merge respects that.
                    chembl_id=(row.get("chembl_id") or "").strip(),
                    provenance=[Provenance(
                        source="manual",
                        identifier=(row.get("note") or "").strip() or "entered by hand",
                        url=url,
                    )],
                ))
    except OSError:
        return []
    return out


def load_pathway(symbol: str) -> dict:
    """The hand-written pathway row for one target, or nothing.

    One CSV for the whole library rather than one file per target: the rows
    are three sentences each and a file per target would be fifteen files of
    three lines. Every row carries a source_url, on the same rule as the deal
    and asset files -- a sentence about biology that a reader cannot check is
    worse than no sentence, because the rest of the page is checkable.
    """
    path = os.path.join(os.path.dirname(ASSETS_DIR), "pathways.csv")
    if not os.path.exists(path):
        return {}
    symbol = normalise_symbol(symbol)
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if (row.get("symbol") or "").strip().upper() != symbol.upper():
                    continue
                if not (row.get("source_url") or "").strip():
                    return {}
                return {
                    "pathway": (row.get("pathway") or "").strip(),
                    "does": (row.get("pathway_does") or "").strip(),
                    "role": (row.get("role") or "").strip(),
                    "neighbours": [n.strip() for n in
                                   (row.get("drugged_neighbours") or "").split(";")
                                   if n.strip()],
                    "source_url": (row.get("source_url") or "").strip(),
                    "note": (row.get("note") or "").strip(),
                }
    except OSError:
        return {}
    return {}


def load_deals(symbol: str) -> list["Deal"]:
    """Hand-curated deal comparables for one target.

    A CSV per target under data/deals/. There is no free deal database, so
    this is the honest shape: a file a maintainer edits, with a source URL on
    every row, rather than a section that quietly stays empty.
    """
    from .models import Deal

    symbol = normalise_symbol(symbol)
    path = os.path.join(DEALS_DIR, f"{symbol}.csv")
    if not os.path.exists(path):
        return []

    def num(value: str) -> Optional[float]:
        value = (value or "").strip()
        try:
            return float(value) if value else None
        except ValueError:
            return None

    out: list[Deal] = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if not (row.get("asset") or "").strip():
                    continue
                out.append(Deal(
                    date=(row.get("date") or "").strip(),
                    acquirer=(row.get("acquirer") or "").strip(),
                    target_company=(row.get("target_company") or "").strip(),
                    asset=(row.get("asset") or "").strip(),
                    mechanism=(row.get("mechanism") or "").strip(),
                    # Absent column means licence: the common case, and the
                    # one that belongs in a median. A file written before this
                    # column existed keeps working.
                    deal_type=((row.get("deal_type") or "").strip().lower() or "licence"),
                    stage_at_deal=(row.get("stage_at_deal") or "").strip(),
                    upfront_usd_m=num(row.get("upfront_usd_m", "")),
                    total_usd_m=num(row.get("total_usd_m", "")),
                    territory=(row.get("territory") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                ))
    except OSError:
        return []
    return out


def curated_symbols() -> list[str]:
    if not os.path.isdir(CURATED_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(CURATED_DIR) if f.endswith(".json") and not f.startswith("_")
    )


def index() -> list[dict[str, Any]]:
    """Summary rows for the landing page, without loading every full record."""
    rows: list[dict[str, Any]] = []
    for symbol in curated_symbols():
        try:
            with open(_path(CURATED_DIR, symbol), "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        crowding = raw.get("crowding") or {}
        target = raw.get("target") or {}
        rows.append(
            {
                "symbol": target.get("symbol") or symbol,
                "name": target.get("name", ""),
                "verdict": crowding.get("verdict"),
                "weighted_score": crowding.get("weighted_score"),
                "n_active": crowding.get("n_active"),
                "lead_phase": crowding.get("lead_phase"),
                "n_mechanism_classes": crowding.get("n_mechanism_classes"),
                "generated": raw.get("generated", ""),
                "tier": "curated",
            }
        )
    return sorted(rows, key=lambda r: -(r.get("weighted_score") or 0))


def _attach_deals(landscape: Landscape, symbol: str) -> None:
    """Re-apply the curated deal file on read.

    Deals are edited by hand long after a target was precomputed, so they are
    matched at read time rather than baked into the stored record. Editing a
    CSV should show up on the next page load, not require a re-run.
    """
    from .analysis import feasibility as feasibility_mod
    from .analysis import licensing as licensing_mod

    deals = load_deals(symbol)
    if not deals:
        return
    landscape.deals = deals
    if landscape.licensing:
        landscape.licensing["deals"] = licensing_mod.match_deals(deals, landscape.assets)
        landscape.narrative["licensing"] = licensing_mod.narrative(landscape.licensing)
        # The six questions are stored, and one of them counts deals. Attaching
        # the file without re-running them left ERBB2 reading "No deal on file"
        # three lines above a panel listing four of them.
        landscape.feasibility = feasibility_mod.read(landscape, landscape.modalities)


def _attach_pathway(landscape: Landscape, symbol: str) -> None:
    """Attach the pathway row, and answer the one question it cannot: which of
    the neighbours this site already holds a page for, and which modalities
    have actually reached approval on this target.

    Both are computed here rather than written into the CSV, because both
    change when the library or the asset table changes and a hand-written
    answer would go stale without anyone noticing.
    """
    row = load_pathway(symbol)
    if not row:
        return
    try:
        in_library = {s.upper() for s in curated_symbols()}
    except Exception:  # noqa: BLE001 - a missing library is not a page failure
        in_library = set()
    row["neighbours"] = [
        {"symbol": name, "in_library": name.upper() in in_library}
        for name in row.get("neighbours") or []
    ]
    # Named classes only. "Antibody — mechanism unresolved" is the record
    # failing to say what a molecule does, and listing it beside ADC and TKI
    # as a fourth thing that has worked here would be reading a gap as a fact.
    approved = [a for a in landscape.assets if a.max_phase >= 4]
    named = sorted({
        a.mechanism_class for a in approved
        if a.mechanism_class and "unresolved" not in a.mechanism_class.lower()
        and a.mechanism_class != "Unclassified"
    })
    row["approved_here"] = named
    row["approved_unclassified"] = len(approved) - sum(
        1 for a in approved if a.mechanism_class in named)
    landscape.pathway = row


def load(symbol: str) -> Optional[tuple[Landscape, dict[str, Any]]]:
    """Return (landscape, meta) from the curated tier, then the cache."""
    symbol = normalise_symbol(symbol)

    # recompute=False, and this is the load-bearing word in the file. The
    # curated record is stored with its analysis already in it; re-deriving
    # that analysis here meant every page view re-clustered 203 assets and
    # rebuilt an 1814-row indication matrix, which cost 4.3 seconds on PDCD1
    # against 0.05 for the read. Only the date-dependent layers are refreshed.
    path = _path(CURATED_DIR, symbol)
    if os.path.exists(path):
        landscape = pipeline.refresh_dated(pipeline.load_fixture(path, recompute=False))
        _attach_deals(landscape, symbol)
        _attach_pathway(landscape, symbol)
        return landscape, {"tier": "curated", "age_days": round(_age_days(path), 1)}

    path = _path(CACHE_DIR, symbol)
    if os.path.exists(path):
        age = _age_days(path)
        if age <= CACHE_MAX_AGE_DAYS:
            landscape = pipeline.refresh_dated(pipeline.load_fixture(path, recompute=False))
            _attach_deals(landscape, symbol)
            _attach_pathway(landscape, symbol)
            return landscape, {"tier": "cached", "age_days": round(age, 1)}
    return None


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def save_cached(landscape: Landscape) -> None:
    symbol = normalise_symbol(landscape.target.symbol)
    with _lock:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = _path(CACHE_DIR, symbol) + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(landscape.to_dict(), fh, ensure_ascii=False)
            os.replace(tmp, _path(CACHE_DIR, symbol))
        except OSError:
            # A read-only filesystem is a normal deployment state, not an
            # error: the request still succeeds, it just will not be cached.
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass


def save_curated(landscape: Landscape) -> str:
    symbol = normalise_symbol(landscape.target.symbol)
    os.makedirs(CURATED_DIR, exist_ok=True)
    path = _path(CURATED_DIR, symbol)
    record = landscape.to_dict()
    # Which version of the asset-discovery rules wrote this file. The loader
    # re-derives the swept half of the asset table when the marker is missing
    # or older, so a library built last week heals by being opened -- and
    # skips that work, which is a second per busy target, once the file on
    # disk already reflects the current rules.
    record["rules_version"] = pipeline.RULES_VERSION
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    return path
