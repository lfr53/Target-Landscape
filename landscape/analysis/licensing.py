"""Business development: what is available, and what has it been worth.

Every other target database answers "what exists". A BD or search-and-
evaluation team has already assumed that and is asking two further questions:

    Which of these assets could I actually get, and who do I call?
    What have comparable assets on this mechanism sold for?

Neither is in any free database, and the second has no free API at all. So:

**Availability is derived, transparently.** No licensed intelligence is needed
to notice that a Phase 2 asset whose every trial has stopped is a shelved
programme with clinical data — the classic in-licensing candidate — or that a
sponsor running trials only in China has probably not placed its ex-China
rights. Each signal is a rule over data already in the asset table, and each
one carries the evidence that fired it. A reader who disagrees can see exactly
why the tool said it.

**Deal comparables are curated, and the tool says so.** There is no free,
redistributable deal database. Pretending otherwise, or silently rendering an
empty section, would both be worse than a hand-maintained file with its
sources attached. Deals are matched to the asset table by name so a comparable
sits next to the programme it priced.

The output is never a recommendation, and it is no longer a score either. An
earlier version added weights across six signals and printed "Likely
available" above a threshold. Every weight in it was set by hand and never
checked against a single outcome, and the label read as a finding rather than
as one person's rule of thumb. What is left is the same evidence with the
arithmetic removed: who holds each programme, how far it went, whether
anything is still running, and whether a deal is on file for it. Two readers
weigh those differently, which is the point.
"""

from __future__ import annotations

from ..normalize import plural

import re
import statistics
from collections import defaultdict
from typing import Any, Optional

from ..models import PHASE_LABELS, Asset, Deal, Trial

# ---------------------------------------------------------------------------
# Sponsor scale
# ---------------------------------------------------------------------------
#
# Whether an asset is gettable turns first on who holds it. A large-cap pharma
# does not out-license an active Phase 3; a single-asset biotech is looking for
# a partner by default. Matching is on a curated name list because there is no
# free company-size API, and the list is visible here rather than buried.

LARGE_PHARMA = [
    "abbvie", "amgen", "astellas", "astrazeneca", "bayer", "biogen",
    "boehringer", "bristol", "squibb", "chugai", "daiichi", "eisai",
    "eli lilly", "lilly", "galapagos", "genentech", "gilead", "glaxo",
    "gsk", "incyte", "janssen", "johnson", "merck", "merck kgaa", "moderna",
    "novartis", "novo nordisk", "otsuka", "pfizer", "regeneron", "roche",
    "sanofi", "servier", "takeda", "teva", "ucb", "vertex", "viatris",
    "organon", "csl", "grifols", "ipsen", "leo pharma", "lundbeck",
    "sumitomo", "kyowa", "shionogi", "hengrui", "innovent", "beigene",
    "hansoh", "sino biopharm", "cspc", "fosun",
]

ACADEMIC_HINTS = [
    "university", "universit", "hospital", "college", "institute", "school",
    "medical center", "medical centre", "cancer center", "cancer centre",
    "nhs", "inserm", "cnrs", "nih", "national cancer", "foundation",
    "clinic", "academy", "research center", "research centre", "trust",
    "assistance publique", "charite", "charité", "karolinska",
]

# Major academic centres whose names carry none of the words above. Without
# these, a hospital-sponsored CAR-T reads as a private company, which inverts
# the availability signal: an academic programme is usually looking for a
# partner, a company one usually is not.
ACADEMIC_NAMES = [
    "city of hope", "mayo", "dana-farber", "dana farber", "md anderson",
    "memorial sloan", "st. jude", "st jude", "fred hutch", "moffitt",
    "cleveland", "scripps", "broad", "wistar", "salk", "jackson laboratory",
    "sanger", "crick", "curie", "gustave roussy", "netherlands cancer",
    "princess margaret", "peter maccallum", "wellcome",
]


def sponsor_scale(sponsor: str, sponsor_class: str = "") -> str:
    name = (sponsor or "").lower()
    if not name:
        return "Unknown"
    if any(token in name for token in LARGE_PHARMA):
        return "Large pharma"
    if sponsor_class and sponsor_class != "INDUSTRY":
        return "Academic or non-industry"
    if any(token in name for token in ACADEMIC_HINTS + ACADEMIC_NAMES):
        return "Academic or non-industry"
    return "Small or private company"


# ---------------------------------------------------------------------------
# Territory
# ---------------------------------------------------------------------------

_MAJOR_MARKETS = {
    "United States": "US",
    "China": "China",
    "Japan": "Japan",
}
_EU_COUNTRIES = {
    "Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Poland",
    "Austria", "Sweden", "Denmark", "Finland", "Norway", "Ireland", "Portugal",
    "Czechia", "Czech Republic", "Hungary", "Greece", "Switzerland",
    "United Kingdom",
}


def territory_profile(trials: list[Trial]) -> dict[str, Any]:
    """Which major markets a programme has actually run trials in.

    Trial geography is a weak proxy for where rights are held — a sponsor can
    hold worldwide rights and run trials in one country — so this is reported
    as a gap to check, never as a claim about who owns what.
    """
    countries: set[str] = set()
    for trial in trials:
        countries.update(trial.countries or [])
    present = {label for country, label in _MAJOR_MARKETS.items() if country in countries}
    if countries & _EU_COUNTRIES:
        present.add("EU/UK")
    covered = sorted(present)
    absent = sorted({"US", "EU/UK", "China", "Japan"} - present)
    return {"countries": sorted(countries), "covered": covered, "absent": absent}


# ---------------------------------------------------------------------------
# Availability signals
# ---------------------------------------------------------------------------


def _signal(code: str, headline: str, evidence: str) -> dict[str, Any]:
    return {"code": code, "headline": headline, "evidence": evidence}


def asset_signals(asset: Asset, trials_by_nct: dict[str, Trial]) -> dict[str, Any]:
    """Derive availability signals for one asset, with the evidence for each."""
    trials = [trials_by_nct[n] for n in asset.trials if n in trials_by_nct]
    sponsor_class = ""
    if trials:
        industry = [t for t in trials if t.sponsor_class == "INDUSTRY"]
        sponsor_class = "INDUSTRY" if industry else (trials[0].sponsor_class or "")
    scale = sponsor_scale(asset.sponsor, sponsor_class)
    territory = territory_profile(trials)

    signals: list[dict[str, Any]] = []

    # The strongest single signal in the whole module.
    if not asset.is_active and asset.max_phase >= 2:
        signals.append(_signal(
            "shelved_with_data",
            "Shelved with clinical data",
            f"Reached {PHASE_LABELS.get(asset.max_phase, 'Unknown')} and every linked "
            f"trial has stopped ({plural(len(trials), 'trial')}). An asset with human data and "
            "no active programme is the classic in-licensing candidate — the first "
            "thing to establish is why it was stopped.",
        ))
    elif not asset.is_active:
        signals.append(_signal(
            "dormant_early",
            "Dormant, early",
            "No active trial, but the programme never passed Phase 1, so there is "
            "little human data to license.",
        ))

    if scale == "Small or private company":
        signals.append(_signal(
            "small_sponsor",
            "Small or private sponsor",
            f"{asset.sponsor or 'The sponsor'} is not on the large-pharma list. "
            "Small holders partner or sell far more often than large ones, and are "
            "reachable directly.",
        ))
    elif scale == "Academic or non-industry":
        signals.append(_signal(
            "academic",
            "Academic origin",
            f"Sponsored by {asset.sponsor or 'a non-industry institution'}. Academic "
            "programmes at this stage are usually seeking a commercial partner, and "
            "the institution's tech-transfer office is the contact.",
        ))
    elif scale == "Large pharma" and asset.is_active:
        signals.append(_signal(
            "large_active",
            "Held and active at a large sponsor",
            f"{asset.sponsor} is running this programme. Unlikely to be available "
            "except regionally, or if it is deprioritised later.",
        ))

    # Only meaningful when the programme has actually run trials somewhere: a
    # gap in every market is the absence of data, not a signal about rights.
    if territory["covered"] and territory["absent"] and asset.max_phase >= 1:
        signals.append(_signal(
            "territory_gap",
            "Territory gap: " + ", ".join(territory["absent"]),
            "Trials run in " + ", ".join(territory["covered"])
            + " but not in " + ", ".join(territory["absent"])
            + ". Regional rights are often unplaced where a sponsor has not run "
            "trials; trial geography is a proxy for where rights are held, not a "
            "record of them.",
        ))
    elif not trials and asset.max_phase >= 0:
        signals.append(_signal(
            "no_linked_trials",
            "No registered trial linked",
            "Nothing in the sources swept ties a registration to this programme, so "
            "its stage and territory rest on database records alone. Expected for a "
            "preclinical or recently disclosed asset; otherwise a gap in coverage.",
        ))

    if asset.withdrawn:
        signals.append(_signal(
            "withdrawn",
            "Withdrawn from market",
            "Flagged as withdrawn in ChEMBL. Establish the reason before anything else.",
        ))

    # No total, and no "Likely available" label. The weights that produced one
    # were set by hand and never checked against a single outcome, and the
    # label read as a finding. What is left is what each signal says, with the
    # evidence attached, and the reader's own standard applied to it -- which
    # differs from mine and from the next reader's.
    return {
        "asset": asset.name,
        "sponsor": asset.sponsor,
        "sponsor_scale": scale,
        "phase": asset.max_phase,
        "phase_label": asset.phase_label,
        "mechanism": asset.mechanism_class,
        "is_active": asset.is_active,
        "territory": territory,
        "signals": signals,
    }


# ---------------------------------------------------------------------------
# Deal comparables
# ---------------------------------------------------------------------------

_STAGE_ORDER = ["Preclinical", "Phase 1", "Phase 2", "Phase 3", "Approved", "Unknown"]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def match_deals(deals: list[Deal], assets: list[Asset]) -> dict[str, Any]:
    """Attach deals to the assets they priced, and summarise by stage."""
    by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    keys = {}
    for asset in assets:
        for name in [asset.name] + list(asset.synonyms):
            if len(_norm(name)) > 2:
                keys[_norm(name)] = asset.name

    rows: list[dict[str, Any]] = []
    for deal in deals:
        matched = keys.get(_norm(deal.asset))
        if not matched:
            for key, asset_name in keys.items():
                if key and (key in _norm(deal.asset) or _norm(deal.asset) in key):
                    matched = asset_name
                    break
        row = deal.to_dict()
        row["matched_asset"] = matched
        rows.append(row)
        if matched:
            by_asset[matched].append(row)

    # Only licences are averaged. An acquisition price buys a company — its
    # platform, its cash, its other programmes — and a median that mixes one
    # into a column of asset upfronts reports a "typical Phase 3 upfront" that
    # no Phase 3 asset ever cost. The acquisitions stay in the table, counted
    # separately, because they are the right comparable for a different
    # question: what the whole programme was worth to a buyer.
    by_stage: dict[str, list[float]] = defaultdict(list)
    n_excluded = 0
    for deal in deals:
        if deal.upfront_usd_m is None:
            continue
        if (deal.deal_type or "licence").lower() != "licence":
            n_excluded += 1
            continue
        by_stage[deal.stage_at_deal or "Unknown"].append(deal.upfront_usd_m)

    stages = []
    for stage in _STAGE_ORDER:
        values = by_stage.get(stage) or []
        if not values:
            continue
        stages.append({
            "stage": stage,
            "n": len(values),
            "median_upfront": round(statistics.median(values), 1),
            "min_upfront": min(values),
            "max_upfront": max(values),
        })

    return {
        "deals": rows,
        "by_asset": dict(by_asset),
        "by_stage": stages,
        "n": len(rows),
        "n_matched": sum(1 for r in rows if r["matched_asset"]),
        "n_acquisitions": n_excluded,
        "curated": True,
    }


# ---------------------------------------------------------------------------
# Top level
# ---------------------------------------------------------------------------


def analyse(
    assets: list[Asset], trials: list[Trial], deals: Optional[list[Deal]] = None
) -> dict[str, Any]:
    trials_by_nct = {t.nct_id: t for t in trials}
    rows = [asset_signals(asset, trials_by_nct) for asset in assets]
    rows.sort(key=lambda r: (-r["phase"], r["asset"]))
    holders: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row["sponsor"] or "Unattributed"
        entry = holders.setdefault(name, {"sponsor": name, "scale": row["sponsor_scale"],
                                          "n": 0, "lead_phase": -1})
        entry["n"] += 1
        entry["lead_phase"] = max(entry["lead_phase"], row["phase"])

    return {
        "assets": rows,
        "holders": sorted(holders.values(), key=lambda h: (-h["lead_phase"], -h["n"])),
        "deals": match_deals(deals or [], assets),
    }


def narrative(licensing: dict[str, Any]) -> str:
    """One paragraph of facts. Deliberately not a recommendation.

    This used to open with "N of M programmes carry signals that they may be
    gettable" and name the strongest. That sentence was a ranking produced by
    weights nobody had validated; what survives is the same underlying facts
    with the arithmetic removed.
    """
    rows = licensing["assets"]
    holders = licensing["holders"]
    deals = licensing["deals"]

    if not rows:
        return "No programmes resolved against this target, so there is nothing to place."

    parts: list[str] = []
    lead_holder = holders[0] if holders else None
    if lead_holder:
        parts.append(
            f"{lead_holder['sponsor']} holds the most advanced programme "
            f"({PHASE_LABELS.get(lead_holder['lead_phase'], 'Unknown')})"
            + (f", and is a {lead_holder['scale'].lower()}."
               if lead_holder["scale"] != "Unknown" else ".")
        )

    # Stopped with human data behind it. A fact about the record, not a score:
    # the programme reached the clinic and nothing is running.
    dormant = [r for r in rows if not r["is_active"] and r["phase"] >= 2]
    if dormant:
        names = ", ".join(r["asset"] for r in dormant[:3])
        parts.append(
            f"{len(dormant)} of {len(rows)} programmes reached Phase 2 or beyond and "
            f"have no trial running — {names}"
            + (f" and {len(dormant) - 3} more" if len(dormant) > 3 else "")
            + ". Why each stopped is under Terminations, in the sponsor's words."
        )

    rows_with_deal = {r.get("matched_asset") for r in (deals.get("deals") or [])
                      if r.get("matched_asset")}
    if deals["n"]:
        parts.append(
            f"{deals['n']} deal(s) are on file for this target, "
            f"{len(rows_with_deal)} of them matched to a programme above; the other "
            f"{len(rows) - len(rows_with_deal)} programmes are not on one."
        )
    else:
        parts.append(
            "No deal has been entered for this target — there is no free deal database "
            "to pull one from, so this section is only as complete as its maintainer, "
            "and an empty file is not evidence that nothing has been licensed."
        )

    parts.append(
        "Everything here is public trial and sponsor data, not knowledge of any "
        "agreement, and nothing is scored: a programme not on a deal is a programme "
        "this record cannot show a deal for."
    )
    return " ".join(parts)
