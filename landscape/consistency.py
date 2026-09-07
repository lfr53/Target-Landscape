"""Do the numbers on a target page agree with each other?

A page that says "9 approved drugs on this target" three lines above
"247 assets, one already approved" has told the reader two different things
about the same fact. Neither figure was wrong -- 247 is every molecule ever
found against the target and 9 is the subset that reached the market -- but
nothing on the page said one contained the other, and the second line's
wording implied a count of one.

That is not a typo to fix once. Every count shown is derived by a different
module from the same asset table, and any of them can drift apart when a rule
changes: the approved count comes from ``precedent``, the asset count from
``crowding``, the tab badges from the lists themselves, the running-trial
figures from ``readouts``. This module states what has to remain true between
them and checks it, so a drift is caught on the next refresh rather than by a
reader who notices two numbers disagreeing.

Each check returns a sentence naming both figures and where they came from.
Nothing here changes the data; it only reports.
"""

from __future__ import annotations

import datetime
from typing import Any


def _n(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def check(landscape: Any) -> list[str]:
    """Every disagreement between figures the page shows. Empty means they agree."""
    problems: list[str] = []
    assets = list(landscape.assets or [])
    trials = list(landscape.trials or [])
    crowding = landscape.crowding or {}
    precedent = landscape.precedent or {}
    readouts = landscape.readouts or {}
    failures = landscape.failures or {}

    # -- the asset table -----------------------------------------------------
    if _n(crowding.get("n_total")) != len(assets):
        problems.append(
            f"crowding counts {_n(crowding.get('n_total'))} assets but the table holds "
            f"{len(assets)}; the Assets tab badge and the contested line would disagree."
        )
    if _n(crowding.get("n_active")) + _n(crowding.get("n_dormant")) != len(assets):
        problems.append(
            f"active ({_n(crowding.get('n_active'))}) plus dormant "
            f"({_n(crowding.get('n_dormant'))}) is not the asset count ({len(assets)})."
        )

    # -- approved ------------------------------------------------------------
    # The one that produced "247 assets, one already approved" beside
    # "9 approved drugs". Two modules count approval differently: precedent
    # accepts an approval year even when the phase field never said 4, while
    # the phase histogram goes by phase alone.
    n_approved = _n(precedent.get("n_approved"))
    by_phase_approved = _n((crowding.get("by_phase") or {}).get("Approved"))
    phase4 = [a for a in assets if getattr(a, "max_phase", -1) >= 4]
    if n_approved and n_approved < by_phase_approved:
        problems.append(
            f"precedent reports {n_approved} approved but the phase histogram shows "
            f"{by_phase_approved} at Approved."
        )
    if n_approved > len(assets):
        problems.append(
            f"{n_approved} approved is more than the {len(assets)} assets in the table."
        )
    if phase4 and not n_approved:
        problems.append(
            f"{len(phase4)} asset(s) sit at Approved but precedent reports none."
        )
    lead = str(crowding.get("lead_phase") or "")
    if lead.lower() == "approved" and not n_approved:
        problems.append(
            "the contested line says the furthest asset is approved, but the approved "
            "count is zero."
        )
    if n_approved and lead and lead.lower() != "approved":
        problems.append(
            f"{n_approved} approved drug(s), but the furthest active asset is "
            f"{lead}; one of the two is reading a different table."
        )

    # -- the tab badges ------------------------------------------------------
    #
    # Every badge is counted in the browser, from the asset table, so that
    # filtering redraws it. The sentences inside the panel come from the
    # engine. Where the two count the same thing they have to land on the same
    # number, and each of these caught a case where they did not.
    from collections import Counter

    on_the_page: Counter = Counter()
    for asset in assets:
        for indication in (getattr(asset, "indications", None) or ["(not stated)"]):
            on_the_page[indication] += 1
    matrix = crowding.get("matrix") or {}
    engine_rows = len(matrix.get("rows") or [])
    # Only when the engine has actually built one. A landscape assembled
    # without the analysis layer has no matrix, and that is not a disagreement.
    if assets and matrix and len(on_the_page) != engine_rows:
        problems.append(
            f"the Indications tab would badge {len(on_the_page)} rows and the engine's "
            f"matrix holds {engine_rows}; one of them is counting spellings."
        )

    clusters = {getattr(a, "mechanism_class", "") or "Unclassified" for a in assets}
    stored_clusters = set(landscape.mechanism_clusters or {})
    if assets and stored_clusters and clusters != stored_clusters:
        problems.append(
            f"the Mechanisms tab would badge {len(clusters)} classes and the stored "
            f"clusters hold {len(stored_clusters)}"
            + (f" ({', '.join(sorted(clusters ^ stored_clusters))[:80]})"
               if clusters ^ stored_clusters else "") + "."
        )

    names = {getattr(a, "name", "") for a in assets}
    licensing = landscape.licensing or {}
    orphaned = [r for r in (licensing.get("assets") or [])
                if (r.get("asset") if isinstance(r, dict) else getattr(r, "asset", ""))
                not in names]
    if orphaned:
        problems.append(
            f"{len(orphaned)} row(s) in the licensing view name an asset the table does "
            "not hold, so the tab badge would be short of the panel's own count."
        )

    # Two rows for one molecule. Open Targets lists a drug and its salt as
    # separate entries -- "NERATINIB" and "NERATINIB MALEATE" -- and both were
    # counted, so EGFR reported five programmes it does not have. Rows the
    # registry named only by class are excluded: five companies each run
    # something called "BAFF-R CAR-T" and those are five programmes.
    from . import normalize  # local: consistency is imported early

    same_name: dict[str, list[str]] = {}
    for asset in assets:
        if getattr(asset, "named_by_class", False):
            continue
        same_name.setdefault(normalize._name_key(asset.name), []).append(  # noqa: SLF001
            asset.name)
    twinned = {k: v for k, v in same_name.items() if len(v) > 1}
    if twinned:
        shown = "; ".join(" / ".join(v) for v in list(twinned.values())[:3])
        problems.append(
            f"{len(twinned)} molecule(s) appear twice in the asset table ({shown}); "
            "the asset count and the crowding band count them twice."
        )

    # -- trials --------------------------------------------------------------
    n_active = _n(readouts.get("n_active"))
    n_controlled = _n(readouts.get("n_controlled"))
    if n_controlled > n_active:
        problems.append(
            f"{n_controlled} controlled trials out of {n_active} running is impossible."
        )
    # Against the trials the Trials tab can list, not every stored trial: the
    # tab reaches a trial through its asset, and a trial whose drugs were all
    # partner drugs has no row to appear in.
    from . import pipeline as _pipeline  # local: consistency is imported early

    listable = len(_pipeline._trials_with_a_programme(landscape))
    if _n(readouts.get("n_trials")) != listable:
        problems.append(
            f"readouts counts {_n(readouts.get('n_trials'))} trials but the Trials tab "
            f"can list {listable}; the badge and the sentence would disagree."
        )
    # The five termination buckets partition the stopped trials, and the page
    # prints them side by side under the total. If they stop adding up, the
    # reader sees it before anyone else does.
    parts = sum(_n(failures.get(k)) for k in
                ("n_science", "n_business", "n_operational", "n_cmc", "n_unexplained"))
    if failures and parts != _n(failures.get("n_stopped")):
        problems.append(
            f"the termination buckets add to {parts} but {_n(failures.get('n_stopped'))} "
            "trials stopped; the row of figures would not sum."
        )
    n_stopped = _n(failures.get("n_stopped"))
    if n_stopped > len(trials):
        problems.append(
            f"{n_stopped} stopped trials is more than the {len(trials)} trials held."
        )
    for key, label in (("n_science", "scientific"), ("n_business", "business")):
        if _n(failures.get(key)) > n_stopped:
            problems.append(
                f"{_n(failures.get(key))} {label} stops out of {n_stopped} stopped."
            )
    if n_active + n_stopped > len(trials):
        problems.append(
            f"{n_active} running plus {n_stopped} stopped is more than the "
            f"{len(trials)} trials held."
        )

    # -- shapes that are arithmetically fine and still wrong ------------------
    #
    # These two came from reading a page rather than from a failing sum. Every
    # count agreed with every other count, and the picture was still not
    # possible.
    #
    # ERBB2 was stored with 45 assets, 15 of them approved, and zero trials.
    # Trastuzumab alone has hundreds of registered studies. The sweep returns
    # an empty list when ClinicalTrials.gov refuses a request, and an empty
    # list is also what "this target has no trials" looks like, so a failed
    # sweep was recorded as a finding.
    if assets and not trials:
        problems.append(
            f"{len(assets)} assets and no trials at all. A registry sweep that failed "
            "and a target nobody has run a trial on look identical here; rebuild this "
            "target to tell them apart."
        )
    # CLDN18 was stored with 22 trials naming zolbetuximab and AZD0901, and an
    # asset table holding one molecule: NCT07431281 is a sonesitatug vedotin
    # study that lists zolbetuximab as a comparator, and matching on the
    # comparator marked the whole trial finished with.
    #
    # The question is not "few assets for many trials" -- CLDN18 really does
    # have twenty zolbetuximab trials and one other drug -- but "does a trial
    # name a programme against this target that the table does not hold". So
    # it is asked exactly that way, with the rule the build itself uses.
    missing = _programmes_the_table_is_missing(landscape, assets)
    if missing:
        problems.append(
            f"{len(missing)} programme(s) named in this target's trials are not in the "
            f"asset table ({', '.join(sorted(missing)[:3])}). The discovery step "
            "dropped them."
        )

    # A hand-entered file that the stored record has not caught up with. The
    # rows are merged on a recompute, so an edit made after the last refresh is
    # on disk and not on the page -- and every figure would be a row short if
    # it were shown anyway. Cheaper to say so than to let a maintainer wonder
    # why the programme they typed in is missing.
    unmerged = _hand_entered_rows_not_in_the_table(landscape, assets)
    if unmerged:
        problems.append(
            f"{len(unmerged)} hand-entered programme(s) in data/assets/"
            f"{landscape.target.symbol}.csv are not in this record "
            f"({', '.join(sorted(unmerged)[:3])}). Run the refresh to merge them."
        )

    # A build that was cut short says so in its warnings. Surfaced here too, so
    # the refresh lists it beside the figures it explains.
    for warning in landscape.warnings or []:
        if "cut short" in warning or "Synonyms are incomplete" in warning:
            problems.append(warning)

    # -- the featured readout ------------------------------------------------
    nxt = readouts.get("next_catalyst") or {}
    when = str(nxt.get("date_iso") or "")[:10]
    if when and when < datetime.date.today().isoformat():
        problems.append(
            f"the featured readout ({nxt.get('nct_id')}) is dated {when}, already past."
        )
    if nxt and not any(t.nct_id == nxt.get("nct_id") for t in trials):
        problems.append(
            f"the featured readout {nxt.get('nct_id')} is not in this target's trials."
        )

    return problems


def _programmes_the_table_is_missing(landscape: Any, assets: list) -> set[str]:
    """Drugs the trials tie to this target that no asset row holds."""
    from . import normalize, pipeline  # local: consistency is imported early

    # The build's own discovery step, run again over the stored trials. Any
    # row it produces that the table does not already hold is a programme the
    # file lost -- which is what a stale curated file looks like from here.
    mined = pipeline.mine_from_stored(landscape)
    if not mined:
        return set()
    # A mined row that the merge would fold into an existing one is not a
    # missing programme, it is the same programme written differently. Asked
    # through ``dedupe`` so the answer uses the same merge rule the build does.
    before = {id(a) for a in assets}
    merged = normalize.dedupe(list(assets) + mined)
    return {a.name for a in merged if id(a) not in before}


def _hand_entered_rows_not_in_the_table(landscape: Any, assets: list) -> set[str]:
    """Rows in data/assets/<SYMBOL>.csv that this stored record does not hold.

    Asked through ``dedupe``, the same way, so a hand row that folds into a
    database row does not read as missing.
    """
    from . import normalize, pipeline  # local: consistency is imported early

    manual = pipeline._manual_assets_for(getattr(landscape.target, "symbol", ""))
    if not manual:
        return set()
    before = {id(a) for a in assets}
    merged = normalize.dedupe(list(assets) + manual)
    return {a.name for a in merged if id(a) not in before}


def report(landscape: Any) -> str:
    """One line per disagreement, indented, or an empty string."""
    return "\n".join(f"      ! {p}" for p in check(landscape))
