"""Six questions, answered from the public record.

The site is not a memo generator and this module is not a verdict. Most
targets someone looks up here are new, thinly covered, or both, and a tool
that manufactures a conclusion for every one of them is worse than useless —
it produces the same confident shape whether or not the record supports it.

So this returns six answers, each one a count or a date drawn from the tables
below it, each carrying where it came from and what it does *not* establish.
The six were chosen because they are the questions a reader has to settle
before anything else matters, in the order they have to settle them:

Three of them are about whether the target works, three about what can be had
here, and each line says which. That split is the whole product: the science
and the commercial picture normally live in different databases.

  Science
  1. Has anyone made a medicine here?   Approvals, phases reached.
  2. What can the running trials show?  How much running work is controlled,
                                        and when the next readout lands.
  3. Has anything stopped?              What the sponsors said, split by kind.
  Business
  4. How contested is it?               Weighted by phase, not counted.
  5. What has been licensed?            Deals on file, and what is not on one.
  6. What has nobody tried?             A modality or indication left open.

The reader draws the conclusion. What this module owes them is the number, its
provenance, and an honest note on its limits — never an instruction on what to
think about it.
"""

from __future__ import annotations

from ..normalize import plural

from typing import Any, Optional

from ..models import Landscape

# Which of the two faces a line belongs to, and nothing else. This replaced a
# good / caution / bad scale that drove the same colours. That scale was a
# verdict -- a green edge says "this one is in your favour" -- and the same
# fact points opposite ways for two readers: "saturated" is bad news for a
# company planning its own molecule and good news for one shopping for an
# asset. Colour now says which question it is, not how to feel about it.
FACES = {"science", "business"}


def _line(key: str, label: str, value: str, face: str, detail: str, anchor: str) -> dict[str, str]:
    assert face in FACES, face
    return {
        "key": key,
        "label": label,
        "value": value,
        "face": face,
        "detail": detail,
        "anchor": anchor,
    }


def _validation_line(precedent: dict[str, Any]) -> dict[str, str]:
    tier = precedent.get("tier", "preclinical")

    n = precedent.get("n_approved", 0)
    if tier == "approved":
        years = [a.get("first_approval") for a in precedent.get("approved") or [] if a.get("first_approval")]
        since = f", first in {min(years)}" if years else ""
        value = f"{n} approved drug{'s' if n != 1 else ''} on this target{since}"
    elif tier == "late_stage":
        value = (f"{plural(precedent.get('n_phase3', 0), 'programme')} reached Phase 3, "
                 "none approved")
    elif tier == "failed":
        value = (f"{plural(precedent.get('n_science_failures', 0), 'trial')} stopped for "
                 "scientific reasons")
    elif tier == "in_flight":
        value = (f"{plural(precedent.get('n_controlled_running', 0), 'controlled trial')} "
                 "running, no readout yet")
    elif tier == "early_clinical":
        value = "In humans, but never in a controlled trial"
    else:
        value = "No clinical precedent"

    detail = (
        "Counted from approved drugs and the highest phase reached by any programme "
        "on this target. It says what has happened, not whether a new asset here is "
        "differentiated — the asset table and the mechanism split are where that is "
        "visible."
    )
    return _line("validation", "Has anyone made a medicine here?", value, "science",
                 detail, "#precedent")


def _history_line(failures: dict[str, Any], precedent: dict[str, Any]) -> Optional[dict[str, str]]:
    """One of the six, every time there is a trial to ask it about.

    This used to disappear whenever nothing had stopped, on the reasoning that
    a "0 failures" line reads as reassurance on a target nobody has tried yet.
    That reasoning still holds for a target with no trial history at all — the
    line below returns nothing there, same as before — but it does not hold
    once trials exist: "1 trial on record, none stopped" is not a default
    standing in for a fact, it is the fact, and hiding the row instead of
    stating it plainly cost the page a promised sixth answer on every target
    calm enough to have earned one.
    """
    # From ``failures``, the same dict the Terminations panel prints. It
    # used to read precedent.n_science_failures: a second module counting the
    # same thing its own way, which is how the header came to say "8 trials
    # stopped, none for scientific reasons" above a panel reading
    # "1 Science-driven".
    n_trials = failures.get("n_trials", 0)
    n_science = failures.get("n_science", 0)
    n_stopped = failures.get("n_stopped", 0)

    if not n_trials:
        return None

    if not n_stopped:
        value = f"None stopped · {plural(n_trials, 'trial')} on record"
        detail = (
            "No trial on this target has been marked terminated, withdrawn or suspended. "
            "A trial that finished on schedule is not what this line counts — it is about "
            "trials that stopped short, not about how many have concluded, so it says "
            "nothing about whether the target itself is validated."
        )
        return _line("history", "Has anything stopped?", value, "science", detail, "#failures")

    counts = failures.get("counts") or {}
    top = max(counts.items(), key=lambda kv: kv[1])[0] if counts else ""
    if n_science:
        value = f"{n_science} stopped for efficacy, safety or PK"
        detail = (
            "Classified from the sponsors' own stated reasons. Science-class reasons are "
            "the ones that bear on the target rather than on a portfolio; the notices "
            "themselves are listed under Why they stopped, with the matched wording "
            "quoted so the classification can be checked."
        )
    else:
        value = f"{plural(n_stopped, 'trial')} stopped, none for scientific reasons"
        detail = (
            f"The stated reasons are operational or commercial ({top.lower()} leading), "
            "so none of them is evidence about the mechanism. A raw termination count "
            "would not have separated the two."
        )
    return _line("history", "Has anything stopped?", value, "science", detail,
                 "#failures")


def _window_line(crowding: dict[str, Any], n_approved: int = 0) -> dict[str, str]:
    band = crowding.get("verdict", "Unknown")
    n = crowding.get("n_total", 0)
    lead = crowding.get("lead_phase") or ""
    value = f"{band} — {n} asset{'s' if n != 1 else ''}"
    if lead and lead != "Unknown":
        # Two numbers about the same target sat one line apart -- "9 approved
        # drugs" above, "one already approved" here -- and nothing said the
        # nine were part of the two hundred. Saying how many of the assets are
        # approved makes the larger count readable: 247 is the whole table,
        # nine of them reached the market.
        if lead.lower() == "approved":
            value += (f", {n_approved} already approved" if n_approved
                      else ", one already approved")
        else:
            value += f", furthest at {lead}"
    n_sponsors = crowding.get("n_sponsors", 0)
    detail = (
        f"{n_sponsors} sponsor{'' if n_sponsors == 1 else 's'}, phase-weighted score "
        f"{crowding.get('weighted_score', 0)}. "
        "Assets are weighted by phase rather than counted, because a Phase 3 competitor and "
        "a preclinical one are not the same obstacle. The band thresholds are a stated "
        "convention, not a measurement."
    )
    return _line("window", "How contested is it?", value, "business", detail,
                 "#crowding")


def _evidence_line(readouts: dict[str, Any]) -> Optional[dict[str, str]]:
    """What the running work can settle, and when the next of it lands.

    These were two lines. "What can the running trials show?" and "What reads
    out next?" are one question asked twice -- both are about the trials in
    flight, both link to the same tab, and splitting them cost the six a slot
    that the commercial side had no line for at all.

    Nothing currently running is itself an answer to the question, not an
    absence of one, as long as there is at least one trial on record to say
    it about -- a target with zero trials anywhere has nothing this line can
    speak to, and returns nothing, same as before.
    """
    n_active = readouts.get("n_active", 0)
    n_trials = readouts.get("n_trials", 0)
    if not n_active:
        if not n_trials:
            return None
        return _line(
            "evidence",
            "What can the running trials show?",
            f"None running · {plural(n_trials, 'trial')} on record, all closed",
            "science",
            readouts.get("verdict", "No trial is currently running on this target."),
            "#readouts",
        )
    n_controlled = readouts.get("n_controlled", 0)
    if readouts.get("n_undescribed", 0) == n_active:
        value = f"{n_active} running, designs not registered"
    else:
        value = (f"{n_controlled} of {n_active} running trials are controlled "
                 "efficacy studies")

    detail = readouts.get("verdict", "")
    nxt = readouts.get("next_catalyst")
    if nxt:
        estimate = " (sponsor estimate)" if nxt.get("estimated") else ""
        value += f" · next readout {nxt['date']}{estimate}"
        lead = (
            ""
            if nxt.get("is_interpretable")
            else "Nothing controlled is scheduled, so the next readout is the soonest "
                 "of any kind. "
        )
        who = " · ".join(part for part in (nxt.get("sponsor"), nxt.get("title")) if part)
        note = f" — {nxt['note']}" if nxt.get("note") else ""
        other = nxt.get("soonest_other")
        sooner = ""
        if other:
            sooner = (
                f" Something reads out sooner — {other['nct_id']}, {other['date']}, "
                f"{other['level_label'].lower()} — and every upcoming completion is "
                "listed under Trials."
            )
        detail = " ".join(part for part in (detail, lead + who + note + sooner) if part)

    return _line(
        "evidence",
        "What can the running trials show?",
        value,
        "science",
        detail,
        "#readouts",
    )


def _licensing_line(landscape: Landscape) -> Optional[dict[str, str]]:
    """What has moved, and what has not. Counts only -- no availability score.

    An earlier version scored every programme and printed "Likely available".
    The weights behind that score were set by hand and never checked against
    anything, and the label read as a finding. What a BD reader can use is the
    same two facts without the arithmetic: which programmes are on a deal, and
    which are not.
    """
    licensing = landscape.licensing or {}
    rows = (licensing.get("deals") or {}).get("deals") or []
    n_assets = len(landscape.assets or [])
    if not n_assets:
        return None
    licensed = {r.get("matched_asset") for r in rows if r.get("matched_asset")}
    unplaced = n_assets - len(licensed)
    if rows:
        value = (f"{plural(len(rows), 'deal')} on file · {unplaced} of "
                 f"{n_assets} programmes not on one")
        detail = (
            "Deals are entered by hand from the parties' own announcements, each row "
            "carrying its source; there is no free, redistributable deal database, and "
            "a section that quietly stayed empty would read as 'no deals'. A programme "
            "not tied to a deal is not therefore available — it is a programme this "
            "record cannot show a deal for."
        )
    else:
        value = f"No deal on file · {n_assets} programmes"
        detail = (
            "No deal has been entered for this target. The file is hand-maintained, so "
            "an empty one means nobody has filled it in, not that nothing has been "
            "licensed. The programme table below still shows who holds each one and "
            "how far it has gone."
        )
    return _line("licensing", "What has been licensed, and what has not?", value,
                 "business", detail, "#licensing")


def _opening_line(
    whitespace: list[dict[str, Any]], modality_rows: list[dict[str, Any]]
) -> Optional[dict[str, str]]:
    """The one line that points forward rather than backward.

    Prefers an untried modality over an untried indication, because a modality
    gap is the harder thing to notice and the more defensible position to
    take: an indication nobody has run is often a market nobody wants, whereas
    a physically-available modality nobody has tried is usually just early.
    """
    # When the target's location is unannotated every location-independent
    # modality still reports "available", which is true and useless — it would
    # let the page announce "small molecules untried here" about a protein
    # nobody has placed. If any row came back unknown, the location data is
    # missing and this line has nothing to stand on.
    location_known = not any(r.get("fit") == "unknown" for r in modality_rows)
    untried = [
        r for r in modality_rows
        if r.get("fit") == "available" and not r.get("in_use") and not r.get("speculative")
    ] if location_known else []
    if untried:
        names = ", ".join(r["key"] for r in untried[:2])
        return _line(
            "opening",
            "What has nobody tried?",
            f"Untried here: {names}",
            "business",
            "Physically available against this target — the location and family allow it — "
            "and absent from the asset table. That is a modality gap rather than a proven "
            "opportunity, and the requirements listed under each one are what a company "
            "would have to satisfy.",
            "#modalities",
        )
    if whitespace:
        top = whitespace[0]
        return _line(
            "opening",
            "What has nobody tried?",
            f"No asset in {top.get('name', 'a well-supported indication')}",
            "business",
            "Strong target–disease association with human genetic support, and nothing "
            "past preclinical. Association strength carries no information about how "
            "many patients there are.",
            "#whitespace",
        )
    return None


# There was a ``_headline`` here: one generated sentence saying what the six
# lines added up to ("validated but contested — value comes from
# differentiation, not from the mechanism"). It went unused when the headline
# was dropped from the page, and it is deleted rather than parked, because a
# verdict generator sitting in the codebase is one refactor away from being
# called again.


def read(landscape: Landscape, modality_rows: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Build the six-line read for one target."""
    precedent = landscape.precedent or {}
    readouts = landscape.readouts or {}
    # Science first, then business, and the order is the order on the page: the
    # colour legend is two words, so the grouping has to do the explaining.
    candidates = [
        _validation_line(precedent) if precedent else None,
        _evidence_line(readouts),
        _history_line(landscape.failures or {}, precedent),
        _window_line(landscape.crowding or {},
                     (landscape.precedent or {}).get("n_approved", 0)),
        _licensing_line(landscape),
        _opening_line(landscape.whitespace or [], modality_rows or []),
    ]
    lines = [line for line in candidates if line][:6]

    # No headline. A generated sentence telling the reader what the six lines
    # add up to is exactly the thing this site does not do: on most targets
    # the record does not support a conclusion, and one gets written anyway
    # because the template has a slot for it.
    return {
        "lines": lines,
        "audience": (
            "Each answer is a count or a date taken from the tables on this page, with "
            "a link to them. Read together they describe what the public record holds "
            "on this target — they are not a recommendation, and no weighting between "
            "them is implied."
        ),
    }
