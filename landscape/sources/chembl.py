"""ChEMBL REST API.

Open Targets already surfaces ChEMBL drugs, but it flattens away two fields
that carry real signal:

  * ``action_type`` — INHIBITOR vs ANTAGONIST vs AGONIST. For a receptor like
    BAFF-R the difference between blocking the ligand and depleting the cell
    is the entire competitive argument, and it lives here.
  * ``molecule_type`` and ``withdrawn_flag`` on the molecule record, which fix
    modality and catch assets that reached the market and were pulled.

So ChEMBL is queried directly and merged over the Open Targets rows.

Licence: ChEMBL is CC BY-SA 3.0 — attribution is emitted in the memo.
"""

from __future__ import annotations

from typing import Any, Optional

from ..config import CHEMBL_BASE
from ..http import HTTPError, get_json
from ..models import Provenance

CHEMBL_WEB = "https://www.ebi.ac.uk/chembl"


def _paged(path: str, params: dict[str, Any], collection: str, limit: int = 1000) -> list[dict]:
    """Walk ChEMBL's page_meta.next links."""
    params = dict(params, format="json", limit=min(limit, 1000))
    out: list[dict] = []
    url = f"{CHEMBL_BASE}/{path}"
    first = True
    while url and len(out) < limit:
        payload = get_json(url, params if first else None)
        first = False
        out.extend(payload.get(collection) or [])
        nxt = (payload.get("page_meta") or {}).get("next")
        url = f"https://www.ebi.ac.uk{nxt}" if nxt else None
    return out[:limit]


def find_target_ids(gene_symbol: str, organism: str = "Homo sapiens") -> list[str]:
    """Resolve a gene symbol to ChEMBL target IDs.

    Restricted to single-protein human targets: protein-family and complex
    entries would drag in every drug against every member of the family and
    silently inflate the competitive count.
    """
    try:
        payload = get_json(
            f"{CHEMBL_BASE}/target/search",
            {"q": gene_symbol, "format": "json", "limit": 25},
        )
    except HTTPError:
        return []

    ids: list[str] = []
    for target in payload.get("targets") or []:
        if target.get("organism") != organism:
            continue
        if target.get("target_type") != "SINGLE PROTEIN":
            continue
        # Confirm the gene symbol really is one of this entry's synonyms,
        # because /target/search is a full-text match over descriptions.
        synonyms = {
            (c.get("component_synonym") or "").upper()
            for comp in target.get("target_components") or []
            for c in comp.get("target_component_synonyms") or []
        }
        pref = (target.get("pref_name") or "").upper()
        if gene_symbol.upper() in synonyms or gene_symbol.upper() in pref:
            ids.append(target["target_chembl_id"])
    return ids


def fetch_mechanisms(target_chembl_ids: list[str]) -> dict[str, dict[str, Any]]:
    """molecule_chembl_id -> {action_type, mechanism_of_action, …}."""
    out: dict[str, dict[str, Any]] = {}
    for tid in target_chembl_ids:
        for row in _paged("mechanism", {"target_chembl_id": tid}, "mechanisms"):
            mol = row.get("molecule_chembl_id")
            if not mol:
                continue
            out[mol] = {
                "action_type": row.get("action_type") or "",
                "mechanism_of_action": row.get("mechanism_of_action") or "",
                "target_chembl_id": tid,
                "max_phase": row.get("max_phase"),
            }
    return out


def fetch_molecules(molecule_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Batch-fetch molecule records. ChEMBL accepts __in filters.

    Requests that failed are left on ``fetch_molecules.last_errors`` so the
    pipeline can say the enrichment was partial instead of publishing a table
    whose synonym lists are quietly empty.
    """
    out: dict[str, dict[str, Any]] = {}
    failed: list[str] = []
    for i in range(0, len(molecule_ids), 40):
        chunk = molecule_ids[i : i + 40]
        try:
            rows = _paged(
                "molecule",
                {"molecule_chembl_id__in": ",".join(chunk)},
                "molecules",
                limit=len(chunk),
            )
        except HTTPError as exc:
            # A molecule fetch that fails costs the synonym list, and without
            # synonyms the same drug enters the table two or three times under
            # its code and its brand name. Reported rather than skipped.
            failed.append(str(exc))
            continue
        for row in rows:
            mid = row.get("molecule_chembl_id")
            if not mid:
                continue
            out[mid] = {
                "pref_name": row.get("pref_name") or "",
                "molecule_type": row.get("molecule_type") or "",
                "max_phase": row.get("max_phase"),
                "first_approval": row.get("first_approval"),
                "withdrawn_flag": bool(row.get("withdrawn_flag")),
                "synonyms": sorted(
                    {
                        s.get("molecule_synonym", "")
                        for s in row.get("molecule_synonyms") or []
                        if s.get("molecule_synonym")
                    }
                ),
            }
    fetch_molecules.last_errors = failed
    return out

def provenance_for(molecule_id: str) -> Provenance:
    return Provenance(
        source="chembl",
        identifier=molecule_id,
        url=f"{CHEMBL_WEB}/compound_report_card/{molecule_id}/",
    )


def phase_to_int(max_phase: Any) -> int:
    """ChEMBL max_phase is a float where 4.0 = approved, and may be None."""
    if max_phase is None:
        return -1
    try:
        return int(float(max_phase))
    except (TypeError, ValueError):
        return -1
