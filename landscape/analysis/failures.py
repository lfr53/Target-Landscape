"""Mining terminated and withdrawn trials.

The premise of this module is a question every BD and search-and-evaluation
conversation reaches within ten minutes: *who has died on this target, and
did they die of the science or of the business?*

A raw termination count cannot answer it. Of the trials that stop, a large
share stop for reasons that say nothing about the target — the sponsor ran
out of money, the programme was deprioritised after a merger, recruitment
failed in a rare indication, COVID-19 closed the sites. Counting those as
evidence against the biology is the most expensive mistake a landscape
analysis can make, because it walks a team away from a target that never
actually failed.

So terminations are classified into a taxonomy that separates:
  * **science** — efficacy, safety, PK/PD. These are evidence about the target.
  * **operational** — recruitment and site problems. Weak evidence, mostly
    about the indication and the protocol.
  * **business** — funding, strategy, portfolio. No evidence about the target
    at all, and often a licensing opportunity rather than a warning.

Classification is keyword-first. ``whyStopped`` is short, formulaic and
written by people with strong house styles, so rules cover most of it; the
LLM pass handles only what the rules miss and is asked to justify itself
against the verbatim text.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..config import STOPPED_STATUSES
from ..models import (BUSINESS_CLASSES, CMC_CLASSES, FAILURE_CLASSES,
                      SCIENCE_CLASSES, Trial)

# The third bucket. Recruitment, site problems, a sponsor who ran out of
# sites -- real reasons, and not evidence about the target either way. Named
# here so the four counts on the page partition the stopped trials.
OPERATIONAL_CLASSES = {"recruitment", "operational", "regulatory", "covid"}

# Ordered: the first pattern that matches wins, so specific beats generic.
_RULES: list[tuple[str, re.Pattern]] = [
    (
        "covid",
        re.compile(r"covid|coronavirus|sars-cov-2|pandemic", re.I),
    ),
    (
        "safety",
        re.compile(
            r"\bsafety\b|adverse event|\bae\b|toxicit|tolerabilit|\bdlt\b|"
            r"\bsae\b|dose[- ]limiting|clinical hold|risk[- ]benefit|"
            r"unacceptable.{0,20}(risk|toxic)",
            re.I,
        ),
    ),
    (
        "efficacy",
        re.compile(
            r"lack of efficacy|no efficacy|insufficient efficacy|futility|"
            r"did not meet|failed to meet|interim analysis|"
            r"efficacy (was )?not (demonstrated|observed)|lack of (clinical )?benefit|"
            r"\bfutile\b|primary endpoint",
            re.I,
        ),
    ),
    (
        "pk_pd",
        re.compile(
            r"pharmacokinetic|\bpk\b|pharmacodynamic|\bpd\b profile|"
            r"target engagement|exposure|bioavailability|biomarker",
            re.I,
        ),
    ),
    (
        # Before the operational rule, which used to claim "supply" and
        # "manufacturing" and file them next to slow recruitment. Whether the
        # material can be made is its own question, and the answer is the one
        # a buyer needs before anything else.
        "cmc",
        re.compile(
            r"manufactur|\bcmc\b|\bgmp\b|batch|\blot\b|potency|sterilit|"
            r"stabilit|comparabilit|formulation|drug (product|substance).{0,20}"
            r"(shortage|unavailab|supply|quality)|supply (chain|issue|problem)|"
            r"could not be (supplied|manufactured)|product quality",
            re.I,
        ),
    ),
    (
        "recruitment",
        re.compile(
            r"recruit|enroll|accrual|slow.{0,15}(accrual|enrolment|enrollment)|"
            r"insufficient (patients|participants|subjects)|"
            r"low.{0,15}(accrual|enrolment|enrollment)",
            re.I,
        ),
    ),
    (
        "funding",
        re.compile(
            r"fund|financ|budget|sponsor.{0,20}(ceased|closed|bankrupt)|"
            r"bankrupt|insolven|company.{0,20}(closed|dissolved)|lack of resources",
            re.I,
        ),
    ),
    (
        "business",
        re.compile(
            r"business (decision|reason)|strategic|portfolio|prioriti[sz]|"
            r"deprioriti[sz]|company decision|sponsor decision|"
            r"discontinu.{0,30}(program|programme|development)|"
            r"merger|acquisition|reorgani[sz]|commercial|"
            r"development (of the )?(drug|product|compound) (was )?(stopped|halted)",
            re.I,
        ),
    ),
    (
        "regulatory",
        re.compile(r"regulator|\bfda\b|\bema\b|authority|ethics committee|\birb\b", re.I),
    ),
    (
        "operational",
        re.compile(
            r"site|investigator|logistic|protocol|"
            r"study design|administrative",
            re.I,
        ),
    ),
]


# Sponsors routinely write "no new safety signals were identified" in a
# termination notice that has nothing to do with safety. A naive keyword match
# reads that as a safety failure and inverts the conclusion — so negated
# mentions are stripped before the rules run.
_NEGATIONS = re.compile(
    r"\b(no|not|without|nor|neither)\b[^.;]{0,40}?\b"
    r"(safety|efficacy|adverse|toxicit|tolerabilit|signal|concern|issue)\w*",
    re.I,
)

# The negation rule above has one dangerous exception. "Did not meet its
# primary efficacy endpoint" is the single most common way a sponsor states an
# efficacy failure, and it is written in the negative — so blanket masking
# deletes the clearest failure signal in the corpus and reports the trial as
# "reason not stated". These patterns are read from the ORIGINAL text, before
# masking, and they win outright.
#
# The discriminator is grammatical, not lexical: a negated *noun* ("no safety
# concerns") is a reassurance; a negated *achievement verb* ("did not meet",
# "failed to demonstrate") is the failure itself.
_NEGATED_FAILURES: list[tuple[str, re.Pattern]] = [
    (
        "efficacy",
        re.compile(
            r"(did not|failed to|does not|was not able to)\s+"
            r"(meet|achieve|reach|demonstrate|show|attain|satisf\w+)"
            r"[^.;]{0,60}"
            r"(efficacy|endpoint|end[- ]point|primary outcome|significance|"
            r"significant|benefit|response|superiority|futilit)",
            re.I,
        ),
    ),
    (
        "efficacy",
        re.compile(r"\bfutility\b|\bfailed (the )?(interim|futility)\b", re.I),
    ),
]

# A go/no-go bar that was missed *despite* the drug working is a portfolio
# decision, not an efficacy failure, and the difference decides whether the
# asset is a warning or an in-licensing opportunity. These override the
# generic rules.
_OVERRIDES: list[tuple[str, re.Pattern]] = [
    (
        "business",
        re.compile(
            r"despite (demonstrat|show|achiev)\w*\s+(statistical\w*\s+)?(significan\w*\s+)?"
            r"(efficacy|benefit|improvement)"
            r"|did not meet[^.;]{0,50}(target criteria|internal (bar|criteria|threshold)|"
            r"criteria for progression|go[/ ]no[- ]go)"
            r"|not (to )?(advance|progress)[^.;]{0,40}(indication|programme|program)",
            re.I,
        ),
    ),
]


def classify_reason(text: str) -> tuple[str, str, list[str]]:
    """Classify a whyStopped string.

    Returns ``(primary_class, evidence, also_matched)``. The third element is
    what makes the output auditable: a termination notice that reads as both
    business and efficacy is reported as both, rather than being silently
    collapsed to whichever rule happened to run first.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return "unknown", "", []

    # The business overrides are checked first even here, so that "did not
    # meet internal go/no-go criteria" stays a portfolio decision rather than
    # being claimed by the efficacy pattern below it.
    for label, pattern in _OVERRIDES:
        match = pattern.search(cleaned)
        if match:
            others = [lbl for lbl, pat in _RULES if pat.search(cleaned) and lbl != label]
            return label, match.group(0), others

    # A negated achievement verb is the failure statement itself — read it
    # before the negation mask can delete it.
    for label, pattern in _NEGATED_FAILURES:
        match = pattern.search(cleaned)
        if match:
            return label, match.group(0), []

    # Blank out negated clauses so they cannot match.
    masked = _NEGATIONS.sub(" ", cleaned)

    for label, pattern in _OVERRIDES:
        match = pattern.search(masked)
        if match:
            others = [lbl for lbl, pat in _RULES if pat.search(masked) and lbl != label]
            return label, match.group(0), others

    matches = [(label, pattern.search(masked)) for label, pattern in _RULES]
    hits = [(label, m) for label, m in matches if m]
    if not hits:
        return "unknown", "", []
    primary_label, primary_match = hits[0]
    return primary_label, primary_match.group(0), [lbl for lbl, _ in hits[1:]]


def annotate(trials: list[Trial]) -> None:
    for trial in trials:
        if trial.status not in STOPPED_STATUSES:
            trial.failure_class = ""
            trial.failure_rationale = ""
            continue
        label, evidence, others = classify_reason(trial.why_stopped)
        trial.failure_class = label
        rationale = f"matched “{evidence}”" if evidence else ""
        if others:
            rationale += " · also matched: " + ", ".join(
                FAILURE_CLASSES.get(o, o) for o in others
            )
        trial.failure_rationale = rationale


def unresolved(trials: list[Trial]) -> list[Trial]:
    """Stopped trials with a stated reason the rules could not classify."""
    return [
        t
        for t in trials
        if t.status in STOPPED_STATUSES
        and t.why_stopped
        and t.failure_class in {"unknown", ""}
    ]


def summarise(trials: list[Trial]) -> dict[str, Any]:
    stopped = [t for t in trials if t.status in STOPPED_STATUSES]
    counts = Counter(t.failure_class or "unknown" for t in stopped)

    science = sum(counts[c] for c in SCIENCE_CLASSES)
    business = sum(counts[c] for c in BUSINESS_CLASSES)
    # Every stopped trial lands in exactly one of these five, so the row of
    # figures on the page adds up to the total beside it. It did not before:
    # "45 stopped, 45 gave a reason, 5 science-driven, 10 business-driven" is
    # four numbers a reader cannot reconcile, and the first two were wrong as
    # well -- a sponsor who typed "Other" into the field had given text, not a
    # reason, and was still counted as having reported one.
    operational = sum(counts[c] for c in OPERATIONAL_CLASSES)
    cmc = sum(counts[c] for c in CMC_CLASSES)
    unexplained = len(stopped) - science - business - operational - cmc

    # The headline number: of terminations where a reason was given, what
    # share is actually evidence about the target?
    denominator = science + business + operational + cmc
    science_share = (science / denominator) if denominator else None

    return {
        "n_trials": len(trials),
        "n_stopped": len(stopped),
        "n_with_reason": denominator,
        "counts": {FAILURE_CLASSES.get(k, k): v for k, v in counts.most_common()},
        "n_science": science,
        "n_business": business,
        "n_operational": operational,
        "n_cmc": cmc,
        "n_unexplained": unexplained,
        "science_share_of_stated": science_share,
        "reporting_rate": (denominator / len(stopped)) if stopped else None,
        "cases": [
            {
                "nct_id": t.nct_id,
                "phase": t.phase,
                "sponsor": t.sponsor,
                "status": t.status,
                "conditions": t.conditions[:3],
                "why_stopped": t.why_stopped,
                "class": FAILURE_CLASSES.get(t.failure_class, t.failure_class),
                "evidence": t.failure_rationale,
                "url": t.url,
            }
            # Science-class failures at the highest phases are the ones a
            # reader must see; sort so they come first.
            for t in sorted(
                [t for t in stopped if t.why_stopped],
                key=lambda x: (x.failure_class not in SCIENCE_CLASSES, -x.phase),
            )
        ],
    }
