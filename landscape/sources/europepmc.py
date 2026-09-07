"""Europe PMC: the reading list.

A scientist looking at an unfamiliar target wants two things before anything
else: the review that will bring them up to speed, and the papers that
established the mechanism. Both are a search away, and both take twenty
minutes to find well, because a naive PubMed query on a gene symbol returns
several thousand papers ordered by date, most of which use the target
incidentally.

Two queries fix most of that:

  * **Reviews, by citation count.** The most-cited review on a target is
    close to a definition of the field's own consensus summary. It is a far
    better first read than the newest one.
  * **Recent primary work, by citation count within a window.** Restricting
    to the last few years and *then* sorting by citations finds what the
    field has actually taken up, rather than what happened to be published
    last week. Citation counts are age-biased, so the window has to come
    first — sorting the whole corpus by citations returns 1998 every time.

Europe PMC is used rather than PubMed because it has no key requirement, an
honest REST interface, a citation count in the default record, and open-access
status per record so the interface can say which papers a reader can actually
open.

Licence: Europe PMC metadata is available for reuse; abstracts remain under
their publishers' terms, so only titles, journals, years and identifiers are
stored — never abstract text.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

from ..http import HTTPError, get_json

EUROPEPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
EUROPEPMC_WEB = "https://europepmc.org/article"

# Journals whose reviews are, in practice, where a field's consensus lands.
# Used only to break ties in the ranking — never to exclude anything.
_PREFERRED_REVIEW_JOURNALS = (
    "nature reviews", "annual review", "trends in", "immunity", "cell",
    "nature", "science", "lancet", "new england journal", "pharmacological reviews",
)


def _record(item: dict[str, Any]) -> dict[str, Any]:
    """Title, journal, year, identifiers, citations — and nothing else.

    Deliberately excludes the abstract: abstracts are under publisher terms,
    and a tool that stores them for redistribution has a licensing problem it
    does not need.
    """
    journal = (item.get("journalTitle") or "").strip()
    pmid = (item.get("pmid") or "").strip()
    doi = (item.get("doi") or "").strip()
    source, ext_id = item.get("source") or "MED", item.get("id") or ""
    return {
        "title": (item.get("title") or "").strip().rstrip("."),
        "authors": (item.get("authorString") or "").strip(),
        "journal": journal,
        "year": (item.get("pubYear") or "").strip(),
        "pmid": pmid,
        "doi": doi,
        "citations": int(item.get("citedByCount") or 0),
        "open_access": (item.get("isOpenAccess") or "N") == "Y",
        "url": f"{EUROPEPMC_WEB}/{source}/{ext_id}" if ext_id else (
            f"https://doi.org/{doi}" if doi else ""
        ),
    }


def _search(query: str, page_size: int = 25, sort: str = "CITED desc") -> list[dict[str, Any]]:
    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "lite",
        "sort": sort,
    }
    payload = get_json(f"{EUROPEPMC_BASE}/search", params)
    results = ((payload or {}).get("resultList") or {}).get("result") or []
    return [_record(item) for item in results]


def _terms(symbol: str, aliases: Optional[list[str]] = None) -> str:
    """A title/abstract query over the symbol and its best-known aliases.

    Restricted to TITLE_ABS rather than full text: a gene mentioned only in a
    methods section is not what anyone means by "papers about this target".
    """
    names = [symbol] + [a for a in (aliases or []) if 2 < len(a) < 20][:4]
    clauses = " OR ".join(f'TITLE_ABS:"{n}"' for n in dict.fromkeys(names))
    return f"({clauses})"


def reviews(symbol: str, aliases: Optional[list[str]] = None, limit: int = 5) -> list[dict[str, Any]]:
    """The most-cited reviews on this target."""
    query = f'{_terms(symbol, aliases)} AND PUB_TYPE:"review" AND SRC:MED'
    try:
        rows = _search(query, page_size=30)
    except HTTPError:
        return []
    rows.sort(
        key=lambda r: (
            -r["citations"],
            0 if any(j in r["journal"].lower() for j in _PREFERRED_REVIEW_JOURNALS) else 1,
        )
    )
    return rows[:limit]


def mechanism_papers(
    symbol: str, aliases: Optional[list[str]] = None, limit: int = 5, years: int = 5
) -> list[dict[str, Any]]:
    """Recent primary work on the mechanism, most-cited within the window.

    The window is the whole point. Sorting the target's entire literature by
    citations returns the same handful of foundational papers for every gene
    and tells a reader nothing about where the field is now.
    """
    cutoff = _dt.date.today().year - years
    query = (
        f"{_terms(symbol, aliases)} AND "
        '(TITLE_ABS:"mechanism" OR TITLE_ABS:"signaling" OR TITLE_ABS:"signalling" '
        'OR TITLE_ABS:"structure" OR TITLE_ABS:"inhibitor" OR TITLE_ABS:"agonist" '
        'OR TITLE_ABS:"antibody" OR TITLE_ABS:"pathway") '
        f"AND (FIRST_PDATE:[{cutoff} TO {_dt.date.today().year}]) AND SRC:MED"
    )
    try:
        rows = _search(query, page_size=30)
    except HTTPError:
        return []
    return rows[:limit]


def fetch(symbol: str, aliases: Optional[list[str]] = None) -> dict[str, Any]:
    """Both lists, plus the query links so a reader can go further themselves.

    The "search it yourself" links matter more than they look. This tool is
    not trying to be a literature database, and pointing a scientist at the
    live query is more useful — and more honest — than freezing twenty rows
    into a cache.
    """
    terms = _terms(symbol, aliases)
    return {
        "reviews": reviews(symbol, aliases),
        "mechanism": mechanism_papers(symbol, aliases),
        "search_url": f"https://europepmc.org/search?query={terms.replace(' ', '%20')}",
        "note": (
            "Reviews ranked by citation count; mechanism papers restricted to the last "
            "five years first, then ranked, so the list reflects current work rather "
            "than the field's founding papers."
        ),
    }
