"""ClinicalTrials.gov API v2.

This is the only free source that carries ``whyStopped`` — the sponsor's own
one-line account of why a trial was terminated. It is the single highest-value
free field in competitive intelligence and it is almost never used, because
it is unstructured text sitting behind a paginated API.

Two retrieval modes:
  * ``fetch_by_nct`` — the trials Open Targets already linked to a drug.
  * ``search_trials`` — a free-text sweep over the target's names and its
    known drug names, which catches assets that never made it into ChEMBL:
    academic INDs, Chinese and Japanese sponsors, cell therapies. On most
    targets this is where a third of the real landscape lives.

Licence: ClinicalTrials.gov records are US Government public domain.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from ..config import CTGOV_BASE, MAX_TRIALS
from ..http import HTTPError, get_json
from .. import normalize
from ..models import Trial

_PHASE_MAP = {
    "EARLY_PHASE1": 1,
    "PHASE1": 1,
    "PHASE2": 2,
    "PHASE3": 3,
    "PHASE4": 4,
    "NA": -1,
}

_DRUG_INTERVENTION_TYPES = {
    "DRUG",
    "BIOLOGICAL",
    "GENETIC",
    "COMBINATION_PRODUCT",
}

# Enough of the summary to carry the drug and target names, which a sponsor
# puts in the first sentence or not at all.
SUMMARY_CHARS = 400

# How many quoted terms go into one intervention query. The registry answers
# 400 Bad Request once the URL grows past roughly four thousand characters,
# and a well-drugged target easily supplies two hundred terms.
_TERMS_PER_QUERY = 20

_FIELDS = [
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.descriptionModule.briefSummary",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.whyStopped",
    "protocolSection.statusModule.startDateStruct.date",
    "protocolSection.statusModule.primaryCompletionDateStruct.date",
    "protocolSection.statusModule.primaryCompletionDateStruct.type",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor.class",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.enrollmentInfo.count",
    # Design and endpoints. Registered before the trial reads out, which is
    # what makes them useful: they say in advance whether the result will be
    # interpretable.
    "protocolSection.designModule.designInfo.allocation",
    "protocolSection.designModule.designInfo.interventionModel",
    "protocolSection.designModule.designInfo.primaryPurpose",
    "protocolSection.designModule.designInfo.maskingInfo.masking",
    "protocolSection.outcomesModule.primaryOutcomes.measure",
    "protocolSection.conditionsModule.conditions",
    "protocolSection.armsInterventionsModule.interventions.name",
    "protocolSection.armsInterventionsModule.interventions.type",
    "protocolSection.armsInterventionsModule.interventions.otherNames",
    "protocolSection.contactsLocationsModule.locations.country",
]


def _phases_to_int(phases: Optional[list[str]]) -> int:
    if not phases:
        return -1
    return max((_PHASE_MAP.get(p, -1) for p in phases), default=-1)


def _parse_study(study: dict[str, Any]) -> Optional[Trial]:
    section = study.get("protocolSection") or {}
    ident = section.get("identificationModule") or {}
    nct = ident.get("nctId")
    if not nct:
        return None
    status = section.get("statusModule") or {}
    sponsors = section.get("sponsorCollaboratorsModule") or {}
    lead = sponsors.get("leadSponsor") or {}
    design = section.get("designModule") or {}
    design_info = design.get("designInfo") or {}
    arms = section.get("armsInterventionsModule") or {}
    outcomes = section.get("outcomesModule") or {}
    locations = (section.get("contactsLocationsModule") or {}).get("locations") or []
    primary_completion = status.get("primaryCompletionDateStruct") or {}

    # Only drug-like interventions. Keeping "Procedure" or "Behavioral" arms
    # would let placebo-controlled surgical comparators enter the asset table.
    interventions: list[str] = []
    for iv in arms.get("interventions") or []:
        if (iv.get("type") or "").upper() not in _DRUG_INTERVENTION_TYPES:
            continue
        name = iv.get("name")
        if name:
            interventions.append(name)
        interventions.extend(iv.get("otherNames") or [])

    trial = Trial(
        nct_id=nct,
        title=ident.get("briefTitle", ""),
        brief_summary=((section.get("descriptionModule") or {})
                       .get("briefSummary") or "")[:SUMMARY_CHARS],
        status=status.get("overallStatus", ""),
        why_stopped=(status.get("whyStopped") or "").strip(),
        phase=_phases_to_int(design.get("phases")),
        sponsor=lead.get("name", ""),
        sponsor_class=lead.get("class", ""),
        conditions=section.get("conditionsModule", {}).get("conditions", []) or [],
        interventions=sorted(set(interventions)),
        countries=sorted({loc.get("country", "") for loc in locations if loc.get("country")}),
        enrollment=(design.get("enrollmentInfo") or {}).get("count"),
        start_date=(status.get("startDateStruct") or {}).get("date", ""),
        completion_date=primary_completion.get("date", ""),
        completion_date_type=(primary_completion.get("type") or "").upper(),
        allocation=(design_info.get("allocation") or "").upper(),
        masking=((design_info.get("maskingInfo") or {}).get("masking") or "").upper(),
        intervention_model=(design_info.get("interventionModel") or "").upper(),
        primary_purpose=(design_info.get("primaryPurpose") or "").upper(),
        primary_outcomes=[
            (o.get("measure") or "").strip()
            for o in (outcomes.get("primaryOutcomes") or [])
            if (o.get("measure") or "").strip()
        ],
    )
    # Registry free text carries the occasional broken character; it is
    # dropped here rather than rendered as a black diamond on the page.
    normalize.clean_trial_text(trial)
    return trial


def _fetch_page(params: dict[str, Any]) -> tuple[list[Trial], Optional[str]]:
    payload = get_json(f"{CTGOV_BASE}/studies", params)
    trials = [t for t in (_parse_study(s) for s in payload.get("studies") or []) if t]
    return trials, payload.get("nextPageToken")


def _short_error(message: str) -> str:
    """The status and the endpoint, without the query string."""
    text = str(message or "").strip()
    cut = text.find("?")
    if cut != -1:
        text = text[:cut] + " (query omitted)"
    return text[:160]


class SweepIncomplete(Exception):
    """The registry refused part of the sweep.

    Carries whatever did come back, so the caller can use it and still say the
    picture is partial. Silence here is what let a failed sweep be published as
    "no trials on this target".
    """

    def __init__(self, trials: list, errors: list[str]):
        # The registry echoes the whole request back in its error, and a
        # well-drugged target's query runs to four thousand characters. Printed
        # in full it filled the terminal and the page's warning box with a URL
        # nobody can read. The status line is the part that says what happened.
        super().__init__("; ".join(_short_error(e) for e in errors[:2]))
        self.trials = trials
        self.errors = errors


def search_trials(terms: Iterable[str], limit: int = MAX_TRIALS) -> list[Trial]:
    """Search by intervention terms, in batches.

    One OR-ed query per call was the original design: one round trip, and the
    API does the deduplication. It works until a target has enough known drugs
    to overflow a URL. ERBB2 has 45, each contributing a name and up to three
    synonyms, and the query came to roughly 180 quoted terms and four thousand
    characters. ClinicalTrials.gov answered 400 Bad Request, every time -- so
    the sweep did not fail intermittently on ERBB2, it could never succeed, and
    the page was published with 45 assets and no trials at all.

    So the terms go out in batches and the results are unioned here. More round
    trips on a well-drugged target, and it returns an answer instead of an
    error.
    """
    quoted = [f'"{t}"' for t in terms if t and len(t) > 2]
    if not quoted:
        return []

    found: dict[str, Trial] = {}
    failures: list[str] = []
    for start in range(0, len(quoted), _TERMS_PER_QUERY):
        if len(found) >= limit:
            break
        expression = " OR ".join(quoted[start : start + _TERMS_PER_QUERY])
        token: Optional[str] = None
        while len(found) < limit:
            params: dict[str, Any] = {
                "query.intr": expression,
                "pageSize": 100,
                "format": "json",
                "fields": "|".join(_FIELDS),
            }
            if token:
                params["pageToken"] = token
            try:
                trials, token = _fetch_page(params)
            except HTTPError as exc:
                # An empty result and a refused request are the same empty list
                # to the caller, and that is how a 400 became a finding.
                failures.append(str(exc))
                break
            for trial in trials:
                found.setdefault(trial.nct_id, trial)
            if not token:
                break
    if failures:
        raise SweepIncomplete(list(found.values())[:limit], failures)
    return list(found.values())[:limit]


def fetch_by_nct(nct_ids: list[str]) -> list[Trial]:
    """Fetch specific studies. The API takes an OR list of ids in query.id."""
    out: dict[str, Trial] = {}
    for i in range(0, len(nct_ids), 50):
        chunk = nct_ids[i : i + 50]
        params = {
            "query.id": " OR ".join(chunk),
            "pageSize": 100,
            "format": "json",
            "fields": "|".join(_FIELDS),
        }
        try:
            trials, _ = _fetch_page(params)
        except HTTPError:
            continue
        for trial in trials:
            out.setdefault(trial.nct_id, trial)
    return list(out.values())


_TOKEN_RE = re.compile(r"[^a-z0-9]+")


def normalise_drug_name(name: str) -> str:
    """Loose key for matching an intervention string to a known drug name."""
    return _TOKEN_RE.sub("", (name or "").lower())
