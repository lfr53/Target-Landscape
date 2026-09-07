"""Pre-flight check for the three public APIs.

    python -m landscape doctor

Why this exists: the retrieval layer depends on three APIs that change field
names between releases, and nothing warns you. Without a check like this the
first symptom of drift is a memo that renders perfectly and says nothing —
empty asset table, no warnings, plausible-looking prose. That failure is much
worse than a crash, because it is quiet.

So the doctor probes each source with the exact queries the pipeline uses, on
a target known to have data, and reports which specific field moved rather
than raising a stack trace. Every check names the file and symbol to fix.
"""

from __future__ import annotations

import contextlib
import sys
from typing import Any, Callable, Iterator, Optional

from . import http as http_mod
from .config import CHEMBL_BASE, CTGOV_BASE, OPENTARGETS_GRAPHQL
from .http import HTTPError, get_json, post_json
from .sources import chembl as chembl_src
from .sources import ctgov as ctgov_src
from .sources import europepmc as pmc_src
from .sources import opentargets as ot_src

# A target with data in all three sources, used as the probe.
PROBE_SYMBOL = "TNFRSF13C"
PROBE_ENSEMBL = "ENSG00000159958"

OK, WARN, FAIL = "ok", "warn", "fail"

_MARK = {OK: "  ok  ", WARN: " warn ", FAIL: " FAIL "}


class Check:
    def __init__(self, name: str, fix: str):
        self.name = name
        self.fix = fix
        self.status = OK
        self.detail = ""

    def report(self) -> str:
        line = f"[{_MARK[self.status]}] {self.name}"
        if self.detail:
            line += f"\n            {self.detail}"
        if self.status != OK:
            line += f"\n            → {self.fix}"
        return line


@contextlib.contextmanager
def fail_fast(timeout: int = 12) -> Iterator[None]:
    """No retries, short timeout.

    A health check that takes four minutes to tell you the network is down is
    not a health check. The pipeline's patient retry behaviour is right for a
    real run and wrong here.
    """
    old_retries, old_timeout = http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT
    http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT = 1, timeout
    try:
        yield
    finally:
        http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT = old_retries, old_timeout


def _run(name: str, fix: str, probe: Callable[[], Optional[str]]) -> Check:
    """Run one probe. Returning a string means a warning; raising means failure."""
    check = Check(name, fix)
    try:
        detail = probe()
        if detail:
            check.status = WARN
            check.detail = detail
    except HTTPError as exc:
        check.status = FAIL
        detail = str(exc)[:200]
        if "400" in detail or "GraphQL error" in detail:
            detail += "  (schema drift, not an outage — the query needs updating)"
        check.detail = detail
    except Exception as exc:  # noqa: BLE001
        check.status = FAIL
        check.detail = f"{type(exc).__name__}: {exc}"[:200]
    return check


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def _probe_ot_reachable() -> Optional[str]:
    data = post_json(
        OPENTARGETS_GRAPHQL, {"query": "{ meta { apiVersion { x y z } } }"}, cache_ttl=None
    )
    if data.get("errors"):
        return f"reachable, but the meta query failed: {data['errors'][0].get('message')}"
    version = ((data.get("data") or {}).get("meta") or {}).get("apiVersion") or {}
    if version:
        return None if version else "no version reported"
    return "reachable, but no apiVersion in the response"


def _probe_ot_resolve() -> Optional[str]:
    resolved = ot_src.resolve_target(PROBE_SYMBOL)
    if resolved is None:
        raise HTTPError(f"search returned no target for {PROBE_SYMBOL}")
    if resolved != PROBE_ENSEMBL:
        return f"resolved to {resolved}, expected {PROBE_ENSEMBL} — check the exact-symbol preference"
    return None


def _probe_ot_target() -> Optional[str]:
    target = ot_src.fetch_target(PROBE_ENSEMBL)
    missing = [
        field
        for field, value in [
            ("approvedSymbol", target.symbol),
            ("approvedName", target.name),
            ("functionDescriptions", target.function),
            ("synonyms", target.synonyms),
            ("tractability", target.tractability),
        ]
        if not value
    ]
    if missing:
        return "empty fields: " + ", ".join(missing)
    return None


def _probe_ot_known_drugs() -> Optional[str]:
    assets, ncts = ot_src.fetch_known_drugs(PROBE_ENSEMBL)
    if not assets:
        raise HTTPError("knownDrugs returned no rows for a target that has approved-phase assets")
    notes = []
    if not any(a.max_phase >= 0 for a in assets):
        notes.append("no asset has a usable phase — the 'phase' field may have changed type")
    if not ncts:
        notes.append("no ctIds returned — trial linkage will fall back to the text sweep")
    if not any(a.indications for a in assets):
        notes.append("no disease names returned")
    return "; ".join(notes) or None


def _probe_ot_associations() -> Optional[str]:
    associations = ot_src.fetch_associations(PROBE_ENSEMBL)
    if not associations:
        raise HTTPError("associatedDiseases returned no rows")
    if not any(a.genetic_score > 0 for a in associations):
        return (
            "no genetic_association datatype score found — the whitespace screen "
            "requires it and will return nothing"
        )
    return None


def _probe_chembl_reachable() -> Optional[str]:
    get_json(f"{CHEMBL_BASE}/status", {"format": "json"}, cache_ttl=None)
    return None


def _probe_chembl_target() -> Optional[str]:
    ids = chembl_src.find_target_ids(PROBE_SYMBOL)
    if not ids:
        return (
            "no single-protein human target matched; mechanism detail will rest on "
            "Open Targets alone (see find_target_ids in sources/chembl.py)"
        )
    return None


def _probe_chembl_mechanism() -> Optional[str]:
    ids = chembl_src.find_target_ids(PROBE_SYMBOL)
    if not ids:
        return "skipped — no ChEMBL target id"
    mechanisms = chembl_src.fetch_mechanisms(ids[:1])
    if not mechanisms:
        return "no mechanism rows; action types will be blank"
    if not any(m.get("action_type") for m in mechanisms.values()):
        return "mechanism rows carry no action_type — check the field name"
    molecule_id = next(iter(mechanisms))
    molecules = chembl_src.fetch_molecules([molecule_id])
    if not molecules:
        return "molecule lookup returned nothing — check the molecule_chembl_id__in filter"
    if not molecules[molecule_id].get("molecule_type"):
        return "molecule records carry no molecule_type — modality falls back to heuristics"
    return None


def _probe_ctgov_reachable() -> Optional[str]:
    get_json(f"{CTGOV_BASE}/version", cache_ttl=None)
    return None


def _probe_ctgov_fields() -> Optional[str]:
    """The field selector is the fragile part: a renamed path returns nothing."""
    payload = get_json(
        f"{CTGOV_BASE}/studies",
        {
            "query.intr": '"ianalumab"',
            "pageSize": 5,
            "format": "json",
            "fields": "|".join(ctgov_src._FIELDS),
        },
        cache_ttl=None,
    )
    studies = payload.get("studies") or []
    if not studies:
        raise HTTPError("no studies returned for a term that has them — check query.intr syntax")
    parsed = [t for t in (ctgov_src._parse_study(s) for s in studies) if t]
    if not parsed:
        raise HTTPError("studies returned but none parsed — protocolSection layout has changed")
    notes = []
    if not any(t.phase >= 0 for t in parsed):
        notes.append("no phases parsed (designModule.phases)")
    if not any(t.sponsor for t in parsed):
        notes.append("no sponsors parsed (sponsorCollaboratorsModule.leadSponsor.name)")
    if not any(t.interventions for t in parsed):
        notes.append("no interventions parsed (armsInterventionsModule.interventions)")
    if not any(t.conditions for t in parsed):
        notes.append("no conditions parsed (conditionsModule.conditions)")
    return "; ".join(notes) or None


def _probe_ctgov_why_stopped() -> Optional[str]:
    """whyStopped drives the whole termination analysis, so check it directly."""
    payload = get_json(
        f"{CTGOV_BASE}/studies",
        {
            "query.term": "AREA[OverallStatus]TERMINATED",
            "pageSize": 20,
            "format": "json",
            "fields": "protocolSection.identificationModule.nctId|"
            "protocolSection.statusModule.overallStatus|"
            "protocolSection.statusModule.whyStopped",
        },
        cache_ttl=None,
    )
    studies = payload.get("studies") or []
    if not studies:
        return "could not retrieve terminated studies to check whyStopped"
    with_reason = sum(
        1
        for s in studies
        if ((s.get("protocolSection") or {}).get("statusModule") or {}).get("whyStopped")
    )
    if with_reason == 0:
        raise HTTPError(
            "no terminated study returned a whyStopped value — the termination "
            "analysis is the core of this tool and would be empty"
        )
    return None



def _probe_ctgov_design() -> Optional[str]:
    """The design fields decide what a trial can prove, so check them directly.

    They are new to the field selector, and a rename here would silently turn
    every trial into "design not stated" — a page full of shrugs that still
    looks like it is working.
    """
    payload = get_json(
        f"{CTGOV_BASE}/studies",
        {
            "query.term": "AREA[DesignAllocation]RANDOMIZED",
            "pageSize": 10,
            "format": "json",
            "fields": "|".join(ctgov_src._FIELDS),
        },
        cache_ttl=None,
    )
    parsed = [t for t in (ctgov_src._parse_study(s) for s in payload.get("studies") or []) if t]
    if not parsed:
        return "could not retrieve randomised studies to check the design fields"
    notes = []
    if not any(t.allocation for t in parsed):
        notes.append("no allocation parsed (designModule.designInfo.allocation)")
    if not any(t.primary_outcomes for t in parsed):
        notes.append("no primary endpoints parsed (outcomesModule.primaryOutcomes.measure)")
    if not any(t.masking for t in parsed):
        notes.append("no masking parsed (designModule.designInfo.maskingInfo.masking)")
    return "; ".join(notes) or None


def _probe_ot_biology() -> Optional[str]:
    """Subcellular location and protein family, which drive the modality read."""
    biology = ot_src.fetch_biology(PROBE_ENSEMBL)
    if not biology["locations"] and not biology["target_class"]:
        return (
            "no location or protein family returned — the modality-fit read will "
            "report 'cannot tell' for every target"
        )
    return None


def _probe_europepmc() -> Optional[str]:
    """The reading list. Never fatal — a memo without references is still a memo."""
    rows = pmc_src.reviews(PROBE_SYMBOL, limit=3)
    if not rows:
        return "no reviews returned for a target that has them"
    if not any(r["url"] for r in rows):
        return "records returned with no resolvable link (source/id fields)"
    return None


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

_CHECKS: list[tuple[str, str, str, Callable[[], Optional[str]]]] = [
    ("Open Targets", "reachable", "check network/proxy, or set OPENTARGETS_GRAPHQL",
     _probe_ot_reachable),
    ("Open Targets", "resolves a gene symbol",
     "see resolve_target in sources/opentargets.py", _probe_ot_resolve),
    ("Open Targets", "target core fields",
     "update _TARGET_QUERY in sources/opentargets.py", _probe_ot_target),
    ("Open Targets", "known drugs",
     "update _KNOWN_DRUGS_QUERY in sources/opentargets.py", _probe_ot_known_drugs),
    ("Open Targets", "disease associations",
     "update _ASSOCIATIONS_QUERY in sources/opentargets.py", _probe_ot_associations),
    ("Open Targets", "location and protein family",
     "update _BIOLOGY_QUERY in sources/opentargets.py; without this the "
     "modality-fit read is blank", _probe_ot_biology),
    ("ChEMBL", "reachable", "check network/proxy, or set CHEMBL_BASE",
     _probe_chembl_reachable),
    ("ChEMBL", "target resolution",
     "see find_target_ids in sources/chembl.py", _probe_chembl_target),
    ("ChEMBL", "mechanism and molecule records",
     "see fetch_mechanisms / fetch_molecules in sources/chembl.py",
     _probe_chembl_mechanism),
    ("ClinicalTrials.gov", "reachable", "check network/proxy, or set CTGOV_BASE",
     _probe_ctgov_reachable),
    ("ClinicalTrials.gov", "field selector and parsing",
     "update _FIELDS / _parse_study in sources/ctgov.py", _probe_ctgov_fields),
    ("ClinicalTrials.gov", "whyStopped is populated",
     "update _FIELDS in sources/ctgov.py; without this the termination "
     "analysis is empty", _probe_ctgov_why_stopped),
    ("ClinicalTrials.gov", "design and endpoint fields",
     "update _FIELDS / _parse_study in sources/ctgov.py; without these every "
     "trial reads as 'design not stated'", _probe_ctgov_design),
    ("Europe PMC", "reading list", "see sources/europepmc.py — not fatal, the "
     "analysis does not depend on it", _probe_europepmc),
]


def run(verbose: bool = True) -> int:
    """Run every check. Returns a process exit code."""
    results: list[tuple[str, Check]] = []
    current_source: Optional[str] = None
    unreachable: set[str] = set()

    if verbose:
        print(f"Probing three public APIs with {PROBE_SYMBOL}.\n")

    with fail_fast():
        for source, name, fix, probe in _CHECKS:
            if source != current_source:
                current_source = source
                if verbose:
                    print(f"{source}")

            # No point spending a timeout per check on a host that is down.
            if source in unreachable:
                check = Check(name, fix)
                check.status = WARN
                check.detail = "skipped — source unreachable"
                check.fix = "fix the connection above first"
            else:
                check = _run(name, fix, probe)
                if check.status == FAIL and name == "reachable":
                    unreachable.add(source)

            results.append((source, check))
            if verbose:
                print("  " + check.report().replace("\n", "\n  "))
        if verbose:
            print()

    failed = [c for _, c in results if c.status == FAIL]
    warned = [c for _, c in results if c.status == WARN]

    if failed:
        print(f"{len(failed)} check(s) failed, {len(warned)} warning(s).")
        if unreachable:
            print(f"Unreachable: {', '.join(sorted(unreachable))}. If you are behind a "
                  "corporate proxy or VPN, that is the first thing to check.")
        print("The pipeline will still run — every source degrades rather than "
              "aborting — but the memo will be missing whatever these cover, and "
              "will say so in its own warnings block.")
        return 1
    if warned:
        print(f"All sources reachable. {len(warned)} warning(s) — see above. "
              "Warnings mean a section of the memo will be thin, not that the run "
              "will fail.")
        return 0
    print("All checks passed. The pipeline has everything it expects.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
