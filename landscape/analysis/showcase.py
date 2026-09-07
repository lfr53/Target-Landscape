"""The six tiles on the landing page, built from a real target.

The six are the six questions the target page asks, in the same order, under
short names instead of questions -- "Termination reasons" here, "Has anything
stopped?" there. Three are about whether the target works and three about what
can be had here, and ``face`` says which; the interface colours them by it and
by nothing else.

The landing page has one job: show a first-time visitor what a target page
holds. Describing it in prose does not work — a reader who has not opened one
cannot picture it, and an essay about methodology is the thing they skip. So
the page shows the six answers for an actual target, with that target's actual
numbers, and each tile says which view carries them.

Everything here is derived from a stored landscape, so it cannot drift away
from what the target page shows. If the tile says 48 trials stopped, the
Terminations view lists 48 trials.

Emphasis is marked with ``**double asterisks**`` and split by the interface.
It is not Markdown and nothing else is supported; the point is to let the
figure stand out from the sentence around it without returning HTML from the
engine.
"""

from __future__ import annotations

from typing import Any, Optional


def _plural(n: int, one: str, many: str = "") -> str:
    return f"{n} {one}" if n == 1 else f"{n} {many or one + 's'}"


def _money(millions: float) -> str:
    """$1,250m is a figure nobody says out loud."""
    if millions >= 1000:
        return f"${millions / 1000:.2f}".rstrip("0").rstrip(".") + "bn"
    return f"${millions:,.0f}m"


def _characteristics(landscape: Any) -> Optional[dict[str, Any]]:
    header = landscape.header or {}
    facts = {row["key"]: row for row in header.get("facts") or []}
    bits: list[str] = []

    mech = (header.get("mechanism") or {}).get("text") or ""
    fn = facts.get("function")
    if mech:
        bits.append(mech.split(". ")[0].rstrip(".") + ".")
    elif fn:
        bits.append(fn["value"])

    location = facts.get("location")
    if location:
        bits.append("**" + location["value"] + "**.")
    domain = facts.get("domain")
    if domain:
        bits.append(f"Domains: **{domain['value']}**.")
    if not location:
        # The honest version, and worth showing: with no annotated location the
        # modality check reports "cannot tell" rather than "available".
        bits.append(
            "No subcellular location is annotated, so which modalities could reach "
            "it is reported as **cannot tell** — not as feasible."
        )
    # Then the answer to the first question. What the protein is and whether
    # anyone has made a medicine out of it were two tiles, and the first was
    # not a question at all -- it was a description with no reader's question
    # behind it. Together they are one: this is the target, and this is how far
    # anyone has got with it.
    precedent = landscape.precedent or {}
    n_approved = precedent.get("n_approved") or 0
    n_phase3 = precedent.get("n_phase3") or 0
    if n_approved:
        years = [a.get("first_approval") for a in precedent.get("approved") or []
                 if a.get("first_approval")]
        since = f", the first in {min(years)}" if years else ""
        bits.append(f"**{_plural(n_approved, 'approved drug')}** on this target{since}.")
        if n_phase3:
            bits.append(f"{_plural(n_phase3, 'more programme')} in Phase 3.")
    elif n_phase3:
        bits.append(f"**{_plural(n_phase3, 'programme')}** reached Phase 3, "
                    "**none approved**.")
    else:
        bits.append("**No approved drug** on this target.")

    if not bits:
        return None
    return {"key": "characteristics", "title": "Target characteristics",
            "face": "science", "text": " ".join(bits),
            "tabs": ["mechanisms", "assets"]}


def _competition(landscape: Any) -> Optional[dict[str, Any]]:
    crowding = landscape.crowding or {}
    n_assets = crowding.get("n_total") or len(landscape.assets or [])
    if not n_assets:
        return {"key": "competition", "title": "Competitive landscape",
                "face": "business",
                "text": "**Nothing in development** against this target in Open Targets, "
                        "ChEMBL or ClinicalTrials.gov.",
                "tabs": ["assets"]}
    n_classes = len(landscape.mechanism_clusters or {})
    n_sponsors = crowding.get("n_sponsors") or 0
    n_approved = (landscape.precedent or {}).get("n_approved") or 0

    text = f"**{_plural(n_assets, 'asset')}** across **{_plural(n_classes, 'mechanism class', 'mechanism classes')}**"
    if n_sponsors:
        text += f" from **{_plural(n_sponsors, 'sponsor')}**"
    text += "."
    if n_approved:
        text += f" {_plural(n_approved, 'approved drug')}."
    verdict, score = crowding.get("verdict"), crowding.get("weighted_score")
    if verdict:
        text += f" Phase-weighted density **{score} — {verdict}**."
    return {"key": "competition", "title": "Competitive landscape", "face": "business",
            "text": text, "tabs": ["assets", "mechanisms"]}


def _discontinuations(landscape: Any) -> Optional[dict[str, Any]]:
    failures = landscape.failures or {}
    n_stopped = failures.get("n_stopped") or 0
    if not n_stopped:
        return None
    n_reason = failures.get("n_with_reason") or 0
    n_science = failures.get("n_science") or 0
    n_business = failures.get("n_business") or 0

    text = f"**{_plural(n_stopped, 'trial')} stopped**"
    if n_reason:
        text += f" and {n_reason} said why"
    # The split is the point: a raw termination count would have hidden it.
    text += f" — **{n_science} for efficacy, safety or PK**."
    if n_business:
        text += (f" {_plural(n_business, 'was', 'were')} portfolio or funding decisions, "
                 "which say nothing about the target.")
    return {"key": "discontinuations", "title": "Termination reasons",
            "face": "science", "text": text, "tabs": ["stops"]}


def _licensing(landscape: Any) -> Optional[dict[str, Any]]:
    """Deals on file, and how much of the table is not on one.

    No median and no availability score. The medians were computed from four
    hand-entered rows, which is a statistic with a sample size a reader would
    reject on sight, and the score that used to sit beside them was a set of
    hand-picked weights nobody had ever checked against an outcome.
    """
    licensing = landscape.licensing or {}
    rows = (licensing.get("deals") or {}).get("deals") or []
    n_assets = len(landscape.assets or [])
    if not n_assets:
        return None
    if not rows:
        return {"key": "licensing", "title": "Licensing and deals", "face": "business",
                "text": f"**No deal on file** for this target. The programme table still "
                        f"shows who holds each of the **{n_assets}** and how far it has "
                        "gone. Deal rows are entered by hand from the parties' own "
                        "announcements, so an empty file means nobody has filled it in.",
                "tabs": ["licensing"]}
    licensed = {r.get("matched_asset") for r in rows if r.get("matched_asset")}
    text = (f"**{_plural(len(rows), 'deal')} on file**, each with the announcement it "
            f"came from. **{n_assets - len(licensed)} of {n_assets}** programmes are not "
            "on one — which is not the same as being available.")
    n_acq = sum(1 for r in rows if (r.get("deal_type") or "licence") != "licence")
    if n_acq:
        text += f" {_plural(n_acq, 'row')} is an acquisition rather than a licence."
    return {"key": "licensing", "title": "Licensing and deals", "face": "business",
            "text": text, "tabs": ["licensing"]}


def _readouts(landscape: Any) -> Optional[dict[str, Any]]:
    reads = landscape.readouts or {}
    n_active = reads.get("n_active") or 0
    if not n_active:
        return None
    n_controlled = reads.get("n_controlled") or 0
    n_undescribed = reads.get("n_undescribed") or 0

    text = f"**{_plural(n_active, 'trial')} running**"
    if n_undescribed and n_undescribed == n_active:
        # A registry gap, stated as one. Reporting "0 of 3 controlled" would
        # turn a missing field into a finding about the target.
        text += (", none of which registered a design or a primary endpoint. That is a "
                 "**gap in the registry**, not a finding about the target.")
    else:
        rest = n_active - n_controlled
        text += f"; **{n_controlled}** are controlled efficacy studies."
        if rest > 0:
            text += (f" The other {rest} cannot settle whether a drug works, however they "
                     "report — which their registered design says now.")
    return {"key": "readouts", "title": "Trial design and readouts", "face": "science",
            "text": text, "tabs": ["trials"]}


def _gaps(landscape: Any) -> Optional[dict[str, Any]]:
    whitespace = landscape.whitespace or []
    untried = [
        row["key"] for row in landscape.modalities or []
        if not row.get("in_use") and row.get("fit") == "available"
        and not row.get("speculative")
    ]
    if whitespace:
        text = (f"**{_plural(len(whitespace), 'disease')}** with association and genetic "
                f"support and nothing past preclinical — {whitespace[0]['disease']} leads.")
    else:
        text = ("**No disease** passes the gap screen. On a target this well worked "
                "that is the expected answer, and saying so is the point.")
    if untried:
        shown = untried[:3]
        listed = ", ".join(shown)
        if len(untried) > len(shown):
            text += (f" **{_plural(len(untried), 'modality', 'modalities')}** untried, "
                     f"including {listed}.")
        else:
            text += f" **{_plural(len(untried), 'modality', 'modalities')}** untried: {listed}."
    return {"key": "gaps", "title": "Untried", "face": "business", "text": text,
            "tabs": ["whitespace"]}


def tiles(landscape: Any) -> list[dict[str, Any]]:
    """Six tiles for one target. Any that the record cannot fill are dropped."""
    # Science first, then business, and in the same order as the six questions
    # on a target page. The colour legend is two words, so the grouping is what
    # explains itself.
    built = [
        _characteristics(landscape),
        _readouts(landscape),
        _discontinuations(landscape),
        _competition(landscape),
        _licensing(landscape),
        _gaps(landscape),
    ]
    return [tile for tile in built if tile]


def pick(symbols: list[str]) -> Optional[str]:
    """Which curated target to show.

    Not the biggest one. PD-1 filled all six tiles and was the wrong choice
    anyway: 106 assets and 204 running trials read as noise, its gap screen is
    empty because everything on PD-1 has been tried, and none of its four deals
    matches a row in its own asset table.

    BAFF-R is the one that demonstrates the product. Seven assets across three
    mechanism classes is a picture a reader can hold; nine stopped trials of
    which five were portfolio decisions is the line that shows what the tool is
    for; and the one gap it does report -- common variable immunodeficiency --
    is a disease with a name, not an empty box.
    """
    if not symbols:
        return None
    for preferred in ("KRAS", "TNFRSF13C", "TNFSF15", "PDCD1"):
        if preferred in symbols:
            return preferred
    return symbols[0]
