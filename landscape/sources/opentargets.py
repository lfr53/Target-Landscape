"""Open Targets Platform (GraphQL v4).

Supplies three things nothing else does for free:
  * a resolved target identity (Ensembl gene ID) to key everything else on,
  * tractability buckets — whether the target is antibody- or small-molecule-
    accessible at all, which bounds what a competitor can even attempt,
  * target–disease associations with a genetic-evidence component, which is
    what turns "no drugs here" into "no drugs here *and* the biology says
    there should be" — i.e. whitespace rather than absence of interest.

Licence: Open Targets data is CC0. Attribution is still emitted in the memo.

The Platform schema changes between releases. Field-level failures are
downgraded to warnings rather than aborting the run, because a memo missing
its tractability section is far more useful than no memo.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .. import normalize
from ..config import MAX_ASSOCIATIONS, MAX_KNOWN_DRUGS, OPENTARGETS_GRAPHQL
from ..http import HTTPError, post_json
from ..models import Asset, DiseaseAssociation, Provenance, Target

PLATFORM_URL = "https://platform.opentargets.org"

_SEARCH_QUERY = """
query Search($q: String!) {
  search(queryString: $q, entityNames: ["target"], page: {index: 0, size: 10}) {
    hits {
      id
      entity
      object { ... on Target { id approvedSymbol approvedName biotype } }
    }
  }
}
"""

_TARGET_QUERY = """
query TargetCore($id: String!) {
  target(ensemblId: $id) {
    id
    approvedSymbol
    approvedName
    biotype
    synonyms { label source }
    functionDescriptions
    tractability { label modality value }
  }
}
"""

# Platform 26.x replaced `knownDrugs` with `drugAndClinicalCandidates`, which
# is one row per DRUG rather than per (drug, disease, phase) triple, reports
# phase as a string enum, and nests the trial records that used to be a flat
# list of NCT ids. It also now carries the sponsor's stop reason directly —
# see ClinicalReport.trialWhyStopped.
_CANDIDATES_QUERY = """
query Candidates($id: String!) {
  target(ensemblId: $id) {
    drugAndClinicalCandidates {
      count
      rows {
        id
        maxClinicalStage
        drug {
          id
          name
          drugType
          maximumClinicalStage
          mechanismsOfAction { rows { mechanismOfAction actionType } }
        }
        diseases { diseaseFromSource disease { id name } }
        clinicalReports {
          id
          source
          trialPhase
          trialOverallStatus
          trialWhyStopped
        }
      }
    }
  }
}
"""

# The pre-26 query, kept so an older deployment still works.
_KNOWN_DRUGS_QUERY = """
query KnownDrugs($id: String!, $size: Int!) {
  target(ensemblId: $id) {
    knownDrugs(size: $size) {
      count
      rows {
        drugId
        prefName
        drugType
        mechanismOfAction
        phase
        status
        ctIds
        disease { id name }
      }
    }
  }
}
"""

# Where the protein sits and what family it belongs to. Kept in a *separate*
# query, fetched with its own try/except, for one reason: a field rename in
# either of these would otherwise 400 the core target query and take the whole
# analysis down with it. The 26.x schema break taught that lesson once already.
# Everything downstream of this treats an empty result as "unknown", never as
# "not on the surface".
_BIOLOGY_QUERY = """
query TargetBiology($id: String!) {
  target(ensemblId: $id) {
    id
    subcellularLocations { location labelSL source }
    targetClass { label level }
  }
}
"""

_ASSOCIATIONS_QUERY = """
query Assoc($id: String!, $size: Int!) {
  target(ensemblId: $id) {
    associatedDiseases(page: {index: 0, size: $size}) {
      count
      rows {
        score
        datatypeScores { id score }
        disease { id name }
      }
    }
  }
}
"""


def _query(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    resp = post_json(OPENTARGETS_GRAPHQL, {"query": query, "variables": variables})
    if isinstance(resp, dict) and resp.get("errors"):
        messages = "; ".join(e.get("message", "?") for e in resp["errors"])
        raise HTTPError(f"Open Targets GraphQL error: {messages}")
    return (resp or {}).get("data") or {}


def resolve_target(symbol_or_id: str) -> Optional[str]:
    """Return an Ensembl gene ID for a gene symbol, or pass one through."""
    if symbol_or_id.upper().startswith("ENSG"):
        return symbol_or_id.upper()
    data = _query(_SEARCH_QUERY, {"q": symbol_or_id})
    hits = ((data.get("search") or {}).get("hits")) or []
    # Prefer an exact symbol match; the search endpoint is fuzzy and will
    # happily return paralogues for a three-letter gene name.
    for hit in hits:
        obj = hit.get("object") or {}
        if (obj.get("approvedSymbol") or "").upper() == symbol_or_id.upper():
            return obj.get("id")
    for hit in hits:
        obj = hit.get("object") or {}
        if obj.get("id"):
            return obj["id"]
    return None


def search_targets(query: str, size: int = 8) -> list[dict[str, str]]:
    """Autocomplete over target names. Used by the web interface only."""
    data = _query(_SEARCH_QUERY, {"q": query})
    hits = ((data.get("search") or {}).get("hits")) or []
    out: list[dict[str, str]] = []
    for hit in hits[:size]:
        obj = hit.get("object") or {}
        if not obj.get("approvedSymbol"):
            continue
        out.append(
            {
                "symbol": obj["approvedSymbol"],
                "name": obj.get("approvedName", ""),
                "ensembl_id": obj.get("id", ""),
            }
        )
    return out


def fetch_target(ensembl_id: str) -> Target:
    data = _query(_TARGET_QUERY, {"id": ensembl_id})
    node = data.get("target") or {}
    if not node:
        raise HTTPError(f"Open Targets returned no target for {ensembl_id}")

    tractability: dict[str, list[str]] = {}
    for entry in node.get("tractability") or []:
        # Only the buckets the target actually falls into are informative.
        if entry.get("value"):
            # 'id' until Platform 25.x, 'label' from 26.x. Read either so the
            # adapter survives whichever release a user is pointed at.
            bucket = entry.get("label") or entry.get("id") or "?"
            tractability.setdefault(entry.get("modality", "?"), []).append(bucket)

    functions = node.get("functionDescriptions") or []
    return Target(
        ensembl_id=node.get("id", ensembl_id),
        symbol=node.get("approvedSymbol", ""),
        name=node.get("approvedName", ""),
        biotype=node.get("biotype", ""),
        function=functions[0] if functions else "",
        synonyms=sorted({s.get("label", "") for s in (node.get("synonyms") or []) if s.get("label")}),
        tractability=tractability,
        provenance=[
            Provenance(
                source="opentargets",
                identifier=ensembl_id,
                url=f"{PLATFORM_URL}/target/{ensembl_id}",
            )
        ],
    )


def fetch_biology(ensembl_id: str) -> dict[str, list[str]]:
    """Subcellular location and protein family, or empty on any failure.

    Called separately from ``fetch_target`` so that a schema change here costs
    the modality-fit section and nothing else.
    """
    try:
        data = _query(_BIOLOGY_QUERY, {"id": ensembl_id})
    except HTTPError:
        return {"locations": [], "target_class": []}
    node = data.get("target") or {}
    locations, topology = normalize.split_locations(sorted({
        (entry.get("location") or entry.get("labelSL") or "").strip()
        for entry in node.get("subcellularLocations") or []
        if entry.get("location") or entry.get("labelSL")
    }))
    classes = sorted({
        (entry.get("label") or "").strip()
        for entry in node.get("targetClass") or []
        if entry.get("label")
    })
    return {"locations": locations, "topology": topology, "target_class": classes}


# Phase arrives as a number pre-26 and as a string enum from 26.x
# (PHASE_3, PRECLINICAL, EARLY_PHASE1). Both are folded to the same integer
# scale the rest of the tool uses.
_PHASE_WORDS = {
    "PRECLINICAL": 0,
    "EARLY_PHASE1": 1,
    "EARLYPHASE1": 1,
    "APPROVED": 4,
    "PHASE4": 4,
    "PHASE3": 3,
    "PHASE2": 2,
    "PHASE1": 1,
}


def _phase_to_int(phase: Any) -> int:
    if phase is None:
        return -1
    if isinstance(phase, (int, float)):
        value = int(phase)
        return value if -1 <= value <= 4 else -1
    text = str(phase).strip().upper().replace("_", "").replace(" ", "")
    if not text:
        return -1
    if text in _PHASE_WORDS:
        return _PHASE_WORDS[text]
    # "PHASE1/2" and similar: take the highest number present.
    digits = [int(d) for d in re.findall(r"[0-4]", text)]
    if digits:
        return max(digits)
    try:
        return int(float(text))
    except ValueError:
        return -1


_NCT_RE = re.compile(r"\bNCT\d{8}\b")


def _nct_ids(reports: list[dict[str, Any]]) -> list[str]:
    """Pull registry identifiers out of the nested clinical reports.

    Reports come from several sources (registries, labels, literature), and
    only the registry ones carry an NCT id — so the id is matched by shape
    rather than trusted by position.
    """
    out: list[str] = []
    for report in reports or []:
        for value in (report.get("id"), report.get("url")):
            match = _NCT_RE.search(str(value or ""))
            if match and match.group(0) not in out:
                out.append(match.group(0))
    return out


def _assets_from_candidates(rows: list[dict[str, Any]]) -> tuple[list[Asset], list[str]]:
    """Parse the Platform 26.x drugAndClinicalCandidates shape."""
    assets: list[Asset] = []
    all_ncts: set[str] = set()

    for row in rows:
        drug = row.get("drug") or {}
        drug_id = drug.get("id") or row.get("id") or ""
        name = (drug.get("name") or drug_id or "").strip()
        if not name:
            continue

        mechanisms = ((drug.get("mechanismsOfAction") or {}).get("rows")) or []
        mechanism_text = ""
        action_type = ""
        if mechanisms:
            mechanism_text = mechanisms[0].get("mechanismOfAction") or ""
            action_type = (mechanisms[0].get("actionType") or "").upper()

        indications: list[str] = []
        for entry in row.get("diseases") or []:
            disease = (entry.get("disease") or {}).get("name") or entry.get("diseaseFromSource")
            if disease and disease not in indications:
                indications.append(disease)

        reports = row.get("clinicalReports") or []
        ncts = _nct_ids(reports)
        all_ncts.update(ncts)

        phase = max(
            [
                _phase_to_int(row.get("maxClinicalStage")),
                _phase_to_int(drug.get("maximumClinicalStage")),
            ]
            + [_phase_to_int(r.get("trialPhase")) for r in reports]
        )

        asset = Asset(
            name=name,
            drug_id=drug_id,
            chembl_id=drug_id if str(drug_id).startswith("CHEMBL") else "",
            mechanism_text=mechanism_text,
            action_type=action_type,
            max_phase=phase,
            indications=indications,
            trials=ncts,
            provenance=[
                Provenance(
                    source="opentargets",
                    identifier=drug_id,
                    url=f"{PLATFORM_URL}/drug/{drug_id}" if drug_id else None,
                )
            ],
        )
        asset.modality = drug.get("drugType") or "Other / unclassified"
        assets.append(asset)

    return assets, sorted(all_ncts)


def _assets_from_known_drugs(rows: list[dict[str, Any]]) -> tuple[list[Asset], list[str]]:
    """Parse the pre-26 knownDrugs shape: one row per (drug, disease, phase)."""
    by_drug: dict[str, Asset] = {}
    all_ncts: set[str] = set()
    for row in rows:
        drug_id = row.get("drugId") or row.get("prefName") or ""
        if not drug_id:
            continue
        name = (row.get("prefName") or drug_id).strip()
        asset = by_drug.get(drug_id)
        if asset is None:
            asset = Asset(
                name=name,
                drug_id=drug_id,
                chembl_id=drug_id if drug_id.startswith("CHEMBL") else "",
                mechanism_text=row.get("mechanismOfAction") or "",
                provenance=[
                    Provenance(
                        source="opentargets",
                        identifier=drug_id,
                        url=f"{PLATFORM_URL}/drug/{drug_id}",
                    )
                ],
            )
            asset.modality = row.get("drugType") or "Other / unclassified"
            by_drug[drug_id] = asset

        asset.max_phase = max(asset.max_phase, _phase_to_int(row.get("phase")))
        disease = (row.get("disease") or {}).get("name")
        if disease and disease not in asset.indications:
            asset.indications.append(disease)
        for nct in row.get("ctIds") or []:
            all_ncts.add(nct)
            if nct not in asset.trials:
                asset.trials.append(nct)

    return list(by_drug.values()), sorted(all_ncts)


def fetch_known_drugs(ensembl_id: str) -> tuple[list[Asset], list[str]]:
    """Assets against the target, plus every registry id linked to them.

    Tries the Platform 26.x field first and falls back to the pre-26 one, so
    the same code works whichever release the configured endpoint serves.
    """
    try:
        data = _query(_CANDIDATES_QUERY, {"id": ensembl_id})
        node = ((data.get("target") or {}).get("drugAndClinicalCandidates")) or {}
        return _assets_from_candidates(node.get("rows") or [])
    except HTTPError as exc:
        if "drugAndClinicalCandidates" not in str(exc):
            raise
    data = _query(_KNOWN_DRUGS_QUERY, {"id": ensembl_id, "size": MAX_KNOWN_DRUGS})
    rows = (((data.get("target") or {}).get("knownDrugs") or {}).get("rows")) or []
    return _assets_from_known_drugs(rows)


def fetch_associations(ensembl_id: str) -> list[DiseaseAssociation]:
    data = _query(_ASSOCIATIONS_QUERY, {"id": ensembl_id, "size": MAX_ASSOCIATIONS})
    rows = (((data.get("target") or {}).get("associatedDiseases") or {}).get("rows")) or []
    out: list[DiseaseAssociation] = []
    for row in rows:
        disease = row.get("disease") or {}
        genetic = 0.0
        for score in row.get("datatypeScores") or []:
            if score.get("id") == "genetic_association":
                genetic = float(score.get("score") or 0.0)
        out.append(
            DiseaseAssociation(
                disease_id=disease.get("id", ""),
                name=disease.get("name", ""),
                score=float(row.get("score") or 0.0),
                genetic_score=genetic,
            )
        )
    return out
