"""Has anyone made a medicine out of this target before?

For an early-stage investor this is the first question and it dominates every
other. A target with an approved drug on it has had its central risk removed
by someone else's money: the mechanism demonstrably changes the disease in
humans. What remains is a competitive and commercial problem, which is a
different kind of problem and is priced differently. A target with no approval
carries live mechanism risk, and every seed deck on it is asking the investor
to underwrite the biology.

The awkward middle is where most of the value and most of the mistakes sit,
and it splits three ways that a trial count cannot distinguish:

  * **Untested.** Nothing has reached a controlled efficacy trial. The
    biology is a hypothesis. Genetic evidence is the only real prior
    available, and it is a meaningful one.
  * **In flight.** Controlled trials are running and have not reported. The
    mechanism is about to be de-risked or killed by someone else, on a date
    that is public.
  * **Tested and failed.** Someone took this mechanism into a controlled
    trial and it did not work. This is the case that a database of "assets in
    development" hides completely, because failed programmes leave the asset
    table. A new company on a target where three Phase 3s failed for lack of
    efficacy is not an early opportunity; it is a claim that everyone before
    was wrong, and it needs to be argued rather than assumed.

The tier assigned here is a reading of the public record, not a verdict on any
company. It always names the evidence it read.
"""

from __future__ import annotations

from ..normalize import plural

from typing import Any

from ..models import SCIENCE_CLASSES, Asset, DiseaseAssociation, Trial

# Human genetic evidence for a target-disease link is the single best public
# predictor of clinical success — programmes with genetic support succeed at
# roughly twice the rate (Nelson et al., Nature Genetics 2015; replicated by
# Minikel et al., Nature 2024). Open Targets' genetic association score is the
# free proxy for it. This threshold is the tool's convention, not a published
# cutoff, and it is stated so it can be argued with.
STRONG_GENETIC = 0.30
SOME_GENETIC = 0.05

TIERS = {
    "approved": "Approved drug on this target",
    "late_stage": "Reached Phase 3, no approval",
    "failed": "Tested in the clinic and failed",
    "in_flight": "Controlled trials running, no readout yet",
    "early_clinical": "Early clinical only",
    "preclinical": "Preclinical",
}


def approved_assets(assets: list[Asset]) -> list[Asset]:
    """Assets that reached the market, most recently approved first.

    ``first_approval`` comes from ChEMBL and is absent on plenty of approved
    biologics, so phase 4 alone also qualifies — losing a real approval is a
    much worse error here than showing one without a year against it.
    """
    approved = [a for a in assets if a.max_phase >= 4 or a.first_approval]
    return sorted(
        approved,
        key=lambda a: (-(a.first_approval or 0), a.name.lower()),
    )


def precedent(
    assets: list[Asset],
    trials: list[Trial],
    associations: list[DiseaseAssociation],
) -> dict[str, Any]:
    """Classify how far this target has been validated in humans.

    Trials must already have been through ``analysis.failures.annotate`` —
    the failure class is read off them here rather than recomputed.
    """
    approved = approved_assets(assets)
    withdrawn = [a for a in approved if a.withdrawn]
    phase3 = [a for a in assets if a.max_phase == 3]

    from . import readouts  # local import: readouts imports nothing from here

    controlled_running = [
        t for t in trials
        if readouts.grade_trial(t)["level"] in {"confirmatory", "controlled"}
        and t.status in {"RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING",
                         "ENROLLING_BY_INVITATION"}
    ]

    # A science-driven termination at Phase 2 or beyond is the evidence that
    # matters: it means someone dosed patients and the mechanism did not
    # deliver. Operational and business terminations say nothing about biology.
    science_failures = [
        t for t in trials if t.failure_class in SCIENCE_CLASSES and t.phase >= 2
    ]

    genetic = max((a.genetic_score for a in associations), default=0.0)
    top_genetic = max(associations, key=lambda a: a.genetic_score, default=None)

    if approved:
        tier = "approved"
    elif science_failures and not controlled_running:
        tier = "failed"
    elif phase3:
        tier = "late_stage"
    elif controlled_running:
        tier = "in_flight"
    elif any(a.max_phase >= 1 for a in assets):
        tier = "early_clinical"
    else:
        tier = "preclinical"

    evidence: list[str] = []
    if approved:
        years = [a.first_approval for a in approved if a.first_approval]
        first = f" — first in {min(years)}" if years else ""
        evidence.append(
            f"{plural(len(approved), 'approved drug')} "
            f"{'acts' if len(approved) == 1 else 'act'} on this target{first}. The "
            "mechanism changes the disease in humans; that question is closed."
        )
    if withdrawn:
        evidence.append(
            f"{len(withdrawn)} of them "
            f"{'was' if len(withdrawn) == 1 else 'were'} withdrawn from a market, so an approval and a "
            "withdrawal both sit in this target's record."
        )
    if science_failures:
        indications = sorted({c for t in science_failures for c in (t.conditions or [])[:1]})
        where = f" ({', '.join(indications[:3])})" if indications else ""
        evidence.append(
            f"{plural(len(science_failures), 'trial')} at Phase 2 or later stopped for "
            f"efficacy, "
            f"safety or PK reasons{where}. Each sponsor's own stated reason is quoted "
            "under Terminations."
        )
    if controlled_running:
        evidence.append(
            f"{plural(len(controlled_running), 'controlled efficacy trial')} "
            f"{'is' if len(controlled_running) == 1 else 'are'} running now, so the "
            "mechanism is being tested on a public timetable."
        )
    if genetic >= STRONG_GENETIC and top_genetic is not None:
        evidence.append(
            f"Human genetic association with {top_genetic.name} scores {genetic:.2f} in Open "
            "Targets. Genetically supported targets have historically succeeded at about "
            "twice the base rate, which is the strongest prior available before any "
            "clinical data exists."
        )
    elif genetic >= SOME_GENETIC and top_genetic is not None:
        evidence.append(
            f"Some human genetic support ({top_genetic.name}, {genetic:.2f}) — below the "
            "threshold this tool treats as strong."
        )
    else:
        evidence.append(
            "No human genetic association above threshold in Open Targets. Genetic "
            "evidence is absent from the record here; it is not evidence against."
        )

    # What the record shows, not what to do about it. These used to be
    # advice — "mechanism risk is retired, diligence moves to
    # differentiation" — which is a verdict the tool has not earned and the
    # reader is better placed to form.
    reads = {
        "approved": (
            "A drug against this target has been approved, so the mechanism has worked in "
            "patients. Whether a new asset differs from the approved one is a question "
            "about the asset rather than the target; the mechanism split and the asset "
            "table are where that shows."
        ),
        "late_stage": (
            "A programme on this mechanism reached Phase 3 and none has been approved. "
            "What the Phase 2 showed and what became of the Phase 3 are the two records "
            "that carry the most here, and both are listed below."
        ),
        "failed": (
            "The mechanism has been tested in patients and trials stopped for scientific "
            "reasons. The sponsors' own wording is quoted under Terminations. Whether "
            "a prior failure applies to a different population, level of engagement or "
            "tissue is not something the public record settles."
        ),
        "in_flight": (
            "Controlled trials are running and have not reported. Their registered designs "
            "and completion dates are under Trials, with what a positive result in each "
            "could support."
        ),
        "early_clinical": (
            "The target has been in humans, but no controlled trial has reported. Nothing "
            "in the record yet separates the mechanism working from the mechanism being "
            "untested."
        ),
        "preclinical": (
            "No clinical precedent in the public record. What is here is the genetics, the "
            "tractability and the modality fit — and preclinical work is invisible to all "
            "of the sources this is built from."
        ),
    }

    return {
        "tier": tier,
        "tier_label": TIERS[tier],
        "read": reads[tier],
        "evidence": evidence,
        "approved": [a.to_dict() for a in approved],
        "n_approved": len(approved),
        "n_withdrawn": len(withdrawn),
        "n_phase3": len(phase3),
        "n_controlled_running": len(controlled_running),
        "n_science_failures": len(science_failures),
        "genetic_score": round(genetic, 3),
        "genetic_disease": top_genetic.name if top_genetic else "",
    }
