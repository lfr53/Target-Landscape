"""What a trial can prove, and when it will say so.

Every target database counts trials. Counting is the least informative thing
you can do with them, because trials are not interchangeable units. Fourteen
Phase 2s on a target sounds like a crowded, well-validated mechanism. If
eleven of them are single-arm, open-label studies whose primary endpoint is
receptor occupancy, then the mechanism has not been tested at all — a great
deal of money is being spent and none of it will settle the question. That
distinction is knowable *before* any of them read out, because the design and
the primary endpoint are registered in advance, and it is the difference
between an early investor who understands what they are buying and one who is
counting logos on a slide.

Two judgements are made here, from registered fields only:

**What is the primary endpoint measuring?** A hard clinical outcome, a
surrogate regulators have accepted in that setting, a pharmacodynamic marker,
or safety. Classification is by keyword against a vocabulary held in this
file, which is crude and occasionally wrong on an unusual measure — so the
matched phrase is reported with the verdict, and the raw endpoint text is
always shown alongside it.

**What could a positive result support?** Design decides this, not hope.
Randomisation gives you a comparison; blinding protects a subjective endpoint;
enrollment decides whether an effect could be distinguished from noise. A
trial that is missing all three can generate a hypothesis and nothing more.

The output is deliberately phrased as what the trial *can* show. It never
predicts whether the trial will succeed — no public field carries that.
"""

from __future__ import annotations

from ..normalize import plural

import re
from datetime import date
from typing import Any, Optional

from ..config import ACTIVE_STATUSES
from ..models import PHASE_LABELS, Trial

# ---------------------------------------------------------------------------
# Endpoint vocabulary
# ---------------------------------------------------------------------------
#
# Ordered most-specific first: "progression free survival" must be caught as a
# surrogate before the bare word "survival" claims it as a hard outcome.

ENDPOINT_CLASSES = {
    "hard": "Hard clinical outcome",
    "surrogate": "Accepted surrogate",
    "scale": "Validated clinical scale",
    "biomarker": "Biomarker / pharmacodynamics",
    "pk": "Pharmacokinetics",
    "safety": "Safety / tolerability",
    "feasibility": "Feasibility / operational",
    "other": "Unclassified",
}

# Each entry: (class, regex, human label for the matched concept).
_ENDPOINT_RULES: list[tuple[str, str, str]] = [
    # ── Surrogates that contain a hard-outcome word, so they must match first
    ("surrogate", r"progression[- ]free survival|\bpfs\b", "progression-free survival"),
    ("surrogate", r"event[- ]free survival|\befs\b", "event-free survival"),
    ("surrogate", r"disease[- ]free survival|\bdfs\b", "disease-free survival"),
    ("surrogate", r"relapse[- ]free survival|\brfs\b", "relapse-free survival"),
    ("surrogate", r"metastasis[- ]free survival|\bmfs\b", "metastasis-free survival"),
    # ── Hard clinical outcomes
    ("hard", r"overall survival|\bos\b(?! ?score)", "overall survival"),
    ("hard", r"\bmortality\b|\bdeath\b|survival rate|survival time", "mortality"),
    ("hard", r"major adverse cardiac|\bmace\b|cardiovascular death", "MACE"),
    ("hard", r"\bhospitali[sz]ation\b|\bre-?admission\b", "hospitalisation"),
    ("hard", r"\bstroke\b|myocardial infarction", "cardiovascular event"),
    ("hard", r"\bfracture\b", "fracture"),
    ("hard", r"end[- ]stage renal|\bdialysis\b|kidney failure|\btransplant(ation)?\b", "organ failure"),
    ("hard", r"time to (first )?(exacerbation|event|relapse|flare)", "time to event"),
    # ── Accepted surrogates
    ("surrogate", r"objective response rate|overall response rate|\borr\b", "objective response rate"),
    ("surrogate", r"complete (response|remission) rate|\bcr rate\b|\bmrd\b", "complete response"),
    ("surrogate", r"pathologic(al)? complete response|\bpcr rate\b", "pathological complete response"),
    ("surrogate", r"duration of response|\bdor\b", "duration of response"),
    ("surrogate", r"\bhba1c\b|glycated haemoglobin|glycated hemoglobin", "HbA1c"),
    ("surrogate", r"\bldl\b|low[- ]density lipoprotein", "LDL-C"),
    ("surrogate", r"\bfev1?\b|forced expiratory", "FEV1"),
    ("surrogate", r"\begfr\b slope|estimated glomerular|\bproteinuria\b|\buacr\b", "renal function"),
    ("surrogate", r"annuali[sz]ed relapse rate|\barr\b", "annualised relapse rate"),
    ("surrogate", r"seizure frequency", "seizure frequency"),
    ("surrogate", r"viral load|\bsvr\b|undetectable", "viral load"),
    ("surrogate", r"blood pressure|systolic|diastolic", "blood pressure"),
    ("surrogate", r"exacerbation rate", "exacerbation rate"),
    # ── Validated clinical scales / responder definitions
    ("scale", r"\backr?\s?-?\s?(20|50|70)\b", "ACR response"),
    ("scale", r"\bpasi\s?-?\s?(50|75|90|100)\b|\bpasi\b", "PASI"),
    ("scale", r"\beasi\s?-?\s?(50|75|90)\b|\beasi\b", "EASI"),
    ("scale", r"\biga\b|investigator'?s? global assessment", "IGA"),
    ("scale", r"\bdas28\b|disease activity score", "DAS28"),
    ("scale", r"\bsledai\b|\bbiclas?\b|\bsri-?4\b", "lupus responder index"),
    ("scale", r"\bmayo score\b|\bcdai\b|endoscopic (remission|improvement)|clinical remission",
     "clinical remission"),
    ("scale", r"\badas-?cog\b|\bcdr-?sb\b|\bmmse\b", "cognitive scale"),
    ("scale", r"\bmadrs\b|\bham-?d\b|\bphq-?9\b|\bpanss\b", "psychiatric scale"),
    ("scale", r"\bupdrs\b|\balsfrs\b|\bedss\b|\bhaq\b", "functional scale"),
    ("scale", r"six[- ]minute walk|6[- ]?mwd|walking distance", "6-minute walk"),
    ("scale", r"\bnrs\b|\bvas\b|pain (score|intensity)|itch", "symptom score"),
    ("scale", r"quality of life|\bsf-?36\b|\bpro\b|patient[- ]reported", "quality of life"),
    ("scale", r"\bbest corrected visual acuity\b|\bbcva\b|\betdrs\b", "visual acuity"),
    # ── Pharmacodynamics / biomarkers
    ("biomarker", r"receptor occupancy|target engagement", "target engagement"),
    ("biomarker", r"\bb[- ]?cell (count|deplet)|\bcd19\+? count|lymphocyte count", "cell count"),
    ("biomarker", r"cytokine|\bil-?\d+\b|\btnf\b levels?|\bcrp\b|c[- ]reactive", "soluble marker"),
    ("biomarker", r"\bbiomarker\b|\bpharmacodynamic\b|\bpd\b marker", "pharmacodynamic marker"),
    ("biomarker", r"gene expression|transcriptom|\brna\b levels?|protein (level|expression)",
     "expression marker"),
    ("biomarker", r"\bamyloid\b|\btau\b|\bsuvr\b|\bneurofilament\b|\bnfl\b", "imaging or fluid marker"),
    ("biomarker", r"\bimmunogenicity\b|anti[- ]drug antibod", "immunogenicity"),
    # ── PK
    ("pk", r"\bpharmacokinetic|\bcmax\b|\bauc\b|half[- ]life|\btmax\b|serum concentration",
     "pharmacokinetics"),
    ("pk", r"\bbioavailability\b|\bbioequivalence\b", "bioequivalence"),
    # ── Safety
    ("safety", r"dose[- ]limiting toxicit|\bdlt\b", "dose-limiting toxicity"),
    ("safety", r"maximum tolerated dose|\bmtd\b|recommended phase ?2 dose|\brp2d\b",
     "maximum tolerated dose"),
    ("safety", r"adverse event|\bteae\b|\bsae\b|\btoxicit|\btolerabilit|\bsafety\b",
     "adverse events"),
    # ── Feasibility
    ("feasibility", r"\bfeasibilit|\brecruitment\b|\benrol(l)?ment\b|\badherence\b|\bcomplianc",
     "feasibility"),
    ("feasibility", r"\bnumber of participants who complete|\bwithdrawal rate", "completion"),
    # ── Last resort, and only after everything above has declined.
    #
    # Every disease area has its own instrument and no vocabulary will hold
    # them all — ESSDAI, PGA-F, LEI, SNOT-22. What they share is their shape:
    # a change in a named score, index or scale. Matching on that shape rather
    # than on the instrument's name is what keeps this from calling a
    # perfectly ordinary registrational endpoint "unclassified", which is the
    # worst outcome here because it silently downgrades a good trial.
    #
    # Placed last so that a biomarker or safety measure that happens to
    # contain the word "score" has already been claimed by its own rule.
    ("scale", r"\b(score|index|scale|questionnaire|rating|assessment)\b", "clinical instrument"),
    ("surrogate", r"\bresponse rate\b|\bremission\b|\bclearance\b|\bcure\b", "response"),
]

_COMPILED = [(cls, re.compile(pattern, re.I), label) for cls, pattern, label in _ENDPOINT_RULES]

# Endpoint classes that could, in principle, support an efficacy claim.
EFFICACY_CLASSES = {"hard", "surrogate", "scale"}


def classify_endpoint(measure: str) -> dict[str, str]:
    """Classify one primary outcome measure.

    Returns the class, the concept that matched, and the verbatim text — the
    last of which matters most. Keyword matching over free-text endpoint
    descriptions is imperfect by construction, so a reader must always be able
    to see the string that was classified and disagree with the verdict.
    """
    text = (measure or "").strip()
    if not text:
        return {"class": "other", "label": ENDPOINT_CLASSES["other"], "matched": "", "measure": ""}
    for cls, pattern, label in _COMPILED:
        hit = pattern.search(text)
        if hit:
            return {
                "class": cls,
                "label": ENDPOINT_CLASSES[cls],
                "matched": label,
                "measure": text,
            }
    return {"class": "other", "label": ENDPOINT_CLASSES["other"], "matched": "", "measure": text}


def trial_endpoints(trial: Trial) -> list[dict[str, str]]:
    return [classify_endpoint(m) for m in (trial.primary_outcomes or [])]


def _dominant_class(endpoints: list[dict[str, str]]) -> str:
    """The strongest claim any primary endpoint could support.

    A trial with a co-primary of OS and adverse events is an efficacy trial;
    taking the first endpoint, or the most common one, would call it a safety
    study. Precedence runs from the strongest evidence downward.
    """
    order = ["hard", "surrogate", "scale", "biomarker", "pk", "safety", "feasibility", "other"]
    present = {e["class"] for e in endpoints}
    for cls in order:
        if cls in present:
            return cls
    return "other"


# ---------------------------------------------------------------------------
# What the design could support
# ---------------------------------------------------------------------------

EVIDENCE_LEVELS = {
    "confirmatory": "Confirmatory",
    "controlled": "Controlled",
    "signal": "Signal-generating",
    "dose": "Dose and safety",
    "mechanistic": "Mechanistic",
    "unclear": "Design not stated",
}

# Below this, a difference between arms is unlikely to be distinguishable from
# noise on anything but a very large effect. It is a rough line and it is
# printed as one.
SMALL_TRIAL = 60


def _is_randomised(trial: Trial) -> bool:
    return trial.allocation == "RANDOMIZED"


def _is_blinded(trial: Trial) -> bool:
    return trial.masking in {"DOUBLE", "TRIPLE", "QUADRUPLE"}


def grade_trial(trial: Trial) -> dict[str, Any]:
    """What could this trial establish, if it succeeds?

    Phrased around the design rather than the sponsor's ambition, because the
    design is the binding constraint. The note is written to be read by
    someone deciding whether an upcoming readout will change their mind.
    """
    endpoints = trial_endpoints(trial)
    cls = _dominant_class(endpoints)
    randomised = _is_randomised(trial)
    blinded = _is_blinded(trial)
    n = trial.enrollment or 0
    single_arm = trial.intervention_model == "SINGLE_GROUP" or (
        trial.allocation == "NA" and not randomised
    )

    reasons: list[str] = []
    if trial.allocation:
        reasons.append("randomised" if randomised else "not randomised")
    if trial.masking:
        reasons.append(
            {"NONE": "open-label", "SINGLE": "single-blind"}.get(
                trial.masking, trial.masking.lower() + "-blind"
            )
        )
    if n:
        reasons.append(f"n={n}")
    if endpoints:
        reasons.append(f"primary endpoint: {endpoints[0]['label'].lower()}")

    if cls in {"safety", "feasibility"} and trial.phase <= 1:
        level, note = "dose", (
            "A first-in-human safety and dose study. It establishes tolerability and a "
            "dose to take forward; it is not designed to say anything about efficacy, "
            "and a clean result is not evidence the mechanism works."
        )
    elif cls in {"biomarker", "pk"}:
        level, note = "mechanistic", (
            "The primary endpoint measures what the drug does to the body, not what it "
            "does to the disease. A positive result confirms the molecule reaches and "
            "engages the target — necessary, and routinely mistaken for proof of "
            "concept. It cannot support an efficacy claim."
        )
    elif cls in {"safety", "feasibility"}:
        level, note = "dose", (
            f"Registered at {PHASE_LABELS.get(trial.phase, 'unknown phase')} with a safety or "
            "operational primary endpoint. Whatever else this study collects, its "
            "registered question is not whether the drug works."
        )
    elif cls in EFFICACY_CLASSES and randomised and blinded and n >= SMALL_TRIAL:
        level, note = "confirmatory", (
            "Randomised, blinded, and large enough for a difference between arms to mean "
            "something. If this reads out positive on its primary endpoint, it is the "
            "kind of result that supports a registration or a licensing conversation."
        )
    elif cls in EFFICACY_CLASSES and randomised:
        gap = "small" if n and n < SMALL_TRIAL else "open-label"
        level, note = "controlled", (
            f"Randomised against a comparator, so the result carries a control — but it is "
            f"{gap}, which limits how far a positive result travels. Read it as strong "
            "supporting evidence rather than as a settled question."
        )
    elif cls in EFFICACY_CLASSES and single_arm:
        level, note = "signal", (
            "Single-arm with an efficacy endpoint. There is no comparator, so the result "
            "cannot separate the drug from patient selection or the natural history of "
            "the disease. In oncology a single-arm response rate can still support "
            "accelerated approval; everywhere else, treat it as a hypothesis."
        )
    elif cls in EFFICACY_CLASSES:
        level, note = "signal", (
            "An efficacy endpoint without a stated randomisation. A positive result is a "
            "signal to follow, not a controlled comparison."
        )
    else:
        level, note = "unclear", (
            "The registry entry does not carry enough design detail to say what a result "
            "here would establish."
        )

    return {
        "level": level,
        "level_label": EVIDENCE_LEVELS[level],
        "note": note,
        "reasons": reasons,
        "endpoint_class": cls,
        "endpoint_label": ENDPOINT_CLASSES[cls],
        "endpoints": endpoints,
        "randomised": randomised,
        "blinded": blinded,
        "enrollment": trial.enrollment,
    }


def annotate(trials: list[Trial]) -> None:
    """Write the grade back onto each trial, in place."""
    for trial in trials:
        grade = grade_trial(trial)
        trial.endpoint_class = grade["endpoint_class"]
        trial.evidence_level = grade["level"]
        trial.evidence_note = grade["note"]


# ---------------------------------------------------------------------------
# Catalysts
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$")


def parse_date(text: str) -> Optional[date]:
    """ClinicalTrials.gov dates are 'YYYY-MM' or 'YYYY-MM-DD'."""
    match = _DATE_RE.match((text or "").strip())
    if not match:
        return None
    year, month, day = match.group(1), match.group(2), match.group(3)
    try:
        return date(int(year), int(month or 1), int(day or 1))
    except ValueError:
        return None


def next_catalysts(
    trials: list[Trial], today: Optional[date] = None, limit: Optional[int] = 8
) -> list[dict[str, Any]]:
    """Upcoming primary completions, soonest first.

    This is the question an early-stage investor asks before anything else:
    what is the next event that could change the value of this mechanism, when
    is it, and will it be interpretable when it lands. All three come out of
    fields the sponsor registered years in advance.

    Only trials that are still running are included — a terminated study has
    no readout — and the estimated dates are flagged as estimates, because
    sponsors move them and a diligence timeline built on them will slip.
    """
    today = today or date.today()
    rows: list[dict[str, Any]] = []
    for trial in trials:
        if trial.status not in ACTIVE_STATUSES:
            continue
        when = parse_date(trial.completion_date)
        if when is None or when < today:
            continue
        grade = grade_trial(trial)
        rows.append({
            "nct_id": trial.nct_id,
            "title": trial.title,
            "sponsor": trial.sponsor,
            "phase": trial.phase,
            "phase_label": PHASE_LABELS.get(trial.phase, "Unknown"),
            "date": trial.completion_date,
            "date_iso": when.isoformat(),
            "estimated": trial.completion_date_type != "ACTUAL",
            "months_away": max(0, (when.year - today.year) * 12 + (when.month - today.month)),
            "conditions": trial.conditions[:3],
            "level": grade["level"],
            "level_label": grade["level_label"],
            "note": grade["note"],
            "endpoints": [e["measure"] for e in grade["endpoints"]][:3],
            "endpoint_label": grade["endpoint_label"],
            "url": trial.url,
        })
    rows.sort(key=lambda r: r["date_iso"])
    return rows if limit is None else rows[:limit]


def headline_catalyst(catalysts: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The one readout worth putting on the front page.

    Not simply the soonest. A Phase 1 safety readout six months from now is
    nearer than a Phase 3 efficacy readout in two years and tells you far
    less — leading with it would be accurate and useless. So the soonest
    *interpretable* readout wins, and the soonest of any kind is the fallback
    when nothing controlled is scheduled at all.
    """
    if not catalysts:
        return None
    interpretable = [c for c in catalysts if c["level"] in {"confirmatory", "controlled"}]
    if interpretable:
        chosen = dict(interpretable[0])
        chosen["is_interpretable"] = True
        # How much sooner the nearest readout of any kind is. Without this the
        # page silently skips past everything in between; with it the reader
        # can see that something lands earlier and go look at it.
        soonest = catalysts[0]
        if soonest["nct_id"] != chosen["nct_id"]:
            chosen["soonest_other"] = {
                "nct_id": soonest["nct_id"],
                "date": soonest["date"],
                "level_label": soonest["level_label"],
            }
        return chosen
    chosen = dict(catalysts[0])
    chosen["is_interpretable"] = False
    return chosen


# ---------------------------------------------------------------------------
# Target-level summary
# ---------------------------------------------------------------------------


def summarise(trials: list[Trial], today: Optional[date] = None) -> dict[str, Any]:
    """How much of the activity on this target could actually settle anything.

    The headline number every other source reports is the trial count. The
    number that decides whether a mechanism is about to be de-risked is how
    many of those trials are built to answer the efficacy question — and on
    most targets those two numbers are nothing alike.
    """
    today = today or date.today()
    active = [t for t in trials if t.status in ACTIVE_STATUSES]
    grades = [(t, grade_trial(t)) for t in active]

    by_level: dict[str, int] = {}
    for _, grade in grades:
        by_level[grade["level"]] = by_level.get(grade["level"], 0) + 1

    confirmatory = [t for t, g in grades if g["level"] == "confirmatory"]
    controlled = [t for t, g in grades if g["level"] in {"confirmatory", "controlled"}]
    # Two lists, on purpose. The tab shows the soonest eight, because a reader
    # scanning upcoming dates does not want 165 rows. The headline is chosen
    # from *every* upcoming readout, because on a busy target the soonest
    # eight are all small studies and the Phase 3 that would actually settle
    # something sits at position forty. Picking the headline out of the
    # truncated list is how PD-1 came to lead with an eight-patient academic
    # study of sexual function.
    catalysts = next_catalysts(trials, today=today)
    all_catalysts = next_catalysts(trials, today=today, limit=None)

    n_active = len(active)
    n_controlled = len(controlled)
    # A trial with no registered design is not an uncontrolled trial. Counting
    # it as one turns a gap in the registry into a finding about the target,
    # which is the same class of error as reading a missing termination reason
    # as "stopped for no reason".
    n_undescribed = sum(1 for t in active if not t.allocation and not t.primary_outcomes)

    if not n_active:
        verdict = "No trial is currently running on this target."
    elif n_undescribed == n_active:
        verdict = (
            f"{plural(n_active, 'trial')} running, none of which registered a design or a primary "
            "endpoint in the fields this tool reads. That is a gap in the record, not a "
            "judgement about the trials — rebuild this target to pick up the design "
            "fields, or open the studies on ClinicalTrials.gov."
        )
    elif not n_controlled:
        verdict = (
            f"{plural(len(trials), 'trial')} on record, {n_active} still running, none of them "
            "randomised against a comparator with "
            "an efficacy endpoint. Whatever is spent here, the mechanism will not be "
            "settled by the current wave — every readout will be a signal that needs a "
            "controlled trial behind it."
        )
    elif n_controlled == n_active:
        verdict = (
            f"{plural(len(trials), 'trial')} on record, {n_active} still running, and all of "
            "those are controlled efficacy studies. The mechanism is being tested "
            "properly and the answer is coming."
        )
    else:
        # The tab beside this sentence is badged with the total, so the
        # sentence says which number it is talking about. "45 of 168 running
        # trials" under a tab reading "Trials 243" reads as two figures that
        # disagree.
        verdict = (
            f"{plural(len(trials), 'trial')} on record, {n_active} still running. "
            f"{n_controlled} of those are controlled efficacy studies; the other "
            f"{n_active - n_controlled} cannot settle whether the drug works. "
            "Weight the readout calendar accordingly — activity and evidence are not the "
            "same quantity."
        )

    return {
        "n_trials": len(trials),
        "n_active": n_active,
        "n_controlled": n_controlled,
        "n_confirmatory": len(confirmatory),
        "n_undescribed": n_undescribed,
        "by_level": by_level,
        "level_labels": EVIDENCE_LEVELS,
        "verdict": verdict,
        "catalysts": catalysts,
        "next_catalyst": headline_catalyst(all_catalysts),
    }
