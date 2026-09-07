"""Orchestration: gene symbol in, Landscape out.

    build("TNFRSF13C")  ->  Landscape

Stages, in order:
  1. resolve the target (Open Targets)
  2. pull known drugs and disease associations (Open Targets)
  3. enrich with ChEMBL mechanism and molecule detail
  4. sweep ClinicalTrials.gov by target aliases and drug names
  5. reconcile into one asset table and discover assets no database has
  6. classify modality and mechanism; mine terminations
  7. score crowding, build the indication x mechanism matrix, screen whitespace
  8. write the narrative (LLM if available, deterministic template if not)

Any single source failing degrades the memo rather than aborting the run, and
the degradation is recorded in ``Landscape.warnings`` so the reader is told
which section is thin and why.
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any, Callable, Optional

from . import llm as llm_mod
from . import normalize
from . import relevance
from .analysis import brief as brief_mod
from .analysis import crowding as crowding_mod
from .analysis import diagram as diagram_mod
from .analysis import failures as failures_mod
from .analysis import feasibility as feasibility_mod
from .analysis import licensing as licensing_mod
from .analysis import mechanism as mechanism_mod
from .analysis import precedent as precedent_mod
from .analysis import readouts as readouts_mod
from .reference import modalities as modality_ref
from .sources import europepmc as pmc_src
from .sources import uniprot as uniprot_src
from .models import (
    PHASE_LABELS,
    Asset,
    DiseaseAssociation,
    Deal,
    Landscape,
    Provenance,
    Target,
    Trial,
)
from .sources import chembl as chembl_src
from .sources import ctgov as ctgov_src
from .sources import opentargets as ot_src


# Bumped whenever a rule that decides the asset table changes. A stored file
# carrying an older marker is re-derived when it is opened; one carrying this
# marker is served as written.
RULES_VERSION = "2026-09-07-directed-discovery"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# _search_terms lived here. It fed the registry the target's full descriptive
# name -- "mitogen-activated protein kinase kinase kinase 14" -- against a
# stemmed intervention search, and the first study that came back was a
# hypertension trial. The replacement is relevance.terms_for, which uses only
# identifiers and is also what checks the results, so the query and the check
# can never disagree about what this target is called.


# The live path takes 20-40 seconds, almost all of it waiting on three
# external APIs. A caller that cannot say which stage it is on can only show a
# spinner, so build reports its stages through an optional callback.
STAGES = [
    ("resolve", "Resolving target identity"),
    ("drugs", "Fetching known drugs"),
    ("associations", "Fetching disease associations"),
    ("chembl", "Enriching from ChEMBL"),
    ("trials", "Sweeping ClinicalTrials.gov"),
    ("reconcile", "Reconciling into one asset table"),
    ("classify", "Classifying mechanisms and terminations"),
    ("annotation", "Reading curated protein annotation"),
    ("literature", "Finding the key reviews"),
    ("analyse", "Scoring density and screening whitespace"),
]

ProgressFn = Callable[[str, str, int, int], None]


def _noop_progress(stage: str, label: str, index: int, total: int) -> None:
    return None


def build(
    symbol: str,
    *,
    use_llm: Optional[bool] = None,
    deals: Optional[list[Deal]] = None,
    on_progress: Optional[ProgressFn] = None,
) -> Landscape:
    warnings: list[str] = []
    notes: list[str] = []
    progress = on_progress or _noop_progress
    total = len(STAGES)
    _labels = dict(STAGES)

    def step(stage: str) -> None:
        index = [s for s, _ in STAGES].index(stage)
        progress(stage, _labels[stage], index, total)

    step("resolve")

    # 1. target identity -----------------------------------------------------
    ensembl_id = ot_src.resolve_target(symbol)
    if not ensembl_id:
        raise ValueError(f"could not resolve '{symbol}' to an Ensembl gene ID")
    target = ot_src.fetch_target(ensembl_id)
    # Location and family come from a separate query that fails soft: without
    # them the modality-fit read says "cannot tell" rather than guessing, and
    # nothing else in the run is affected.
    biology = ot_src.fetch_biology(ensembl_id)
    target.locations = biology["locations"]
    target.topology = biology.get("topology") or []
    target.target_class = biology["target_class"]
    if not target.locations:
        warnings.append(
            "No subcellular location available for this target, so the modality-fit "
            "read is reported as unknown rather than inferred."
        )

    # 2. known drugs and associations ---------------------------------------
    step("drugs")
    try:
        assets, linked_ncts = ot_src.fetch_known_drugs(ensembl_id)
    except Exception as exc:  # noqa: BLE001 - degrade, do not abort
        assets, linked_ncts = [], []
        warnings.append(f"Open Targets knownDrugs unavailable ({exc}); "
                        "asset table is built from ClinicalTrials.gov alone.")
    step("associations")
    try:
        associations = ot_src.fetch_associations(ensembl_id)
    except Exception as exc:  # noqa: BLE001
        associations = []
        warnings.append(f"Open Targets associations unavailable ({exc}); "
                        "whitespace screen omitted.")

    # 3. ChEMBL enrichment ---------------------------------------------------
    step("chembl")
    try:
        chembl_target_ids = chembl_src.find_target_ids(target.symbol)
        if chembl_target_ids:
            mechanisms = chembl_src.fetch_mechanisms(chembl_target_ids)
            normalize.apply_mechanisms(assets, mechanisms)
            # ChEMBL may know of assets Open Targets did not surface.
            known = {a.chembl_id for a in assets}
            for molecule_id, record in mechanisms.items():
                if molecule_id in known:
                    continue
                assets.append(
                    Asset(
                        name=molecule_id,
                        chembl_id=molecule_id,
                        mechanism_text=record.get("mechanism_of_action", ""),
                        action_type=record.get("action_type", ""),
                        max_phase=chembl_src.phase_to_int(record.get("max_phase")),
                        provenance=[chembl_src.provenance_for(molecule_id)],
                    )
                )
        else:
            # Which sources a page rests on is provenance, not a fault. ChEMBL
            # simply has no entry for some proteins; saying so in a yellow
            # alert made an ordinary page look broken, and a warning box that
            # cries wolf is one nobody reads when something is actually wrong.
            notes.append(
                f"ChEMBL holds no single-protein human entry for {target.symbol}, so "
                "action types and modality calls rest on Open Targets alone."
            )
        normalize.enrich_from_chembl(assets)
        chembl_errors = getattr(chembl_src.fetch_molecules, "last_errors", None) or []
        if chembl_errors:
            # Without synonyms the same molecule enters the table under its
            # code, its INN and its brand name as three separate programmes.
            warnings.append(
                f"ChEMBL returned an error for part of this target's molecule list "
                f"({chembl_errors[0]}). Synonyms are incomplete, so one drug may appear "
                "more than once; rebuild this target to complete them."
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"ChEMBL enrichment failed ({exc}); mechanism detail is reduced.")

    # Use the best names available before searching the registry.
    for asset in assets:
        if asset.name.startswith("CHEMBL") and asset.synonyms:
            asset.name = min(asset.synonyms, key=len)

    # 4. clinical trial sweep ------------------------------------------------
    #
    # Two sources of trials, and they are not equally trustworthy. A trial
    # Open Targets has already linked to this target carries a database's
    # assertion that the link exists. A trial the registry returned from a
    # text search carries only the fact that a search engine matched a string,
    # and that string search is why MAP3K14 acquired 228 assets from a
    # hypertension study. So the linked ones are kept, and the swept ones have
    # to name the target or one of its known drugs to stay.
    step("trials")
    trials: list[Trial] = []
    try:
        if linked_ncts:
            trials.extend(ctgov_src.fetch_by_nct(linked_ncts))
        seen = {t.nct_id for t in trials}
        terms = relevance.terms_for(target, assets)
        try:
            found = ctgov_src.search_trials(terms)
        except ctgov_src.SweepIncomplete as partial:
            # Say so. A refused request and a target nobody has studied are the
            # same empty list, and ERBB2 was published with 45 assets and zero
            # trials because the difference was never recorded.
            found = partial.trials
            warnings.append(
                "The ClinicalTrials.gov sweep was cut short by the registry "
                f"({partial}). Trial counts, terminations and readouts on this page "
                "are incomplete; rebuild this target to complete them."
            )
        swept = [t for t in found if t.nct_id not in seen]
        kept, discarded = relevance.filter_trials(swept, terms)
        trials.extend(kept)
        seen.update(t.nct_id for t in kept)
        if discarded:
            notes.append(
                f"The registry search returned {normalize.plural(len(discarded), 'trial')} "
                f"that never names {target.symbol} or any drug known to act on it. Those "
                "are not counted as work on this target."
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"ClinicalTrials.gov sweep failed ({exc}); "
                        "trial counts and termination analysis are incomplete.")

    # 5. reconcile -----------------------------------------------------------
    step("reconcile")
    unmatched = normalize.attach_trials(assets, trials)
    known_keys: set[str] = set()
    for asset in assets:
        known_keys |= normalize._keys_for(asset)  # noqa: SLF001 - same package
    # A trial that names the gene only as a way of choosing patients is real
    # work on this target's biology and belongs in the trial list, but its
    # drugs are not programmes against the target. CARD9's one trial enrols
    # carriers of the S12N risk allele and gives them posaconazole, an
    # antifungal; the page was reporting it as an approved CARD9 drug.
    drug_directed = [
        t for t in unmatched
        if relevance.names_target_as_a_drug_target(t, relevance.terms_for(target, assets))
    ]
    if len(drug_directed) < len(unmatched):
        notes.append(
            f"{normalize.plural(len(unmatched) - len(drug_directed), 'trial')} name "
            f"{target.symbol} as a genotype or a patient-selection criterion rather "
            "than as a drug target. They are listed under trials; their drugs are not "
            "counted as programmes against this target."
        )
    # Every trial is mined, whether or not it already names a known drug --
    # NCT07431281 is a study of sonesitatug vedotin that lists zolbetuximab
    # among its ten interventions as a comparator, and matching on zolbetuximab
    # used to mark the whole trial finished with. But only the drugs the trial
    # itself ties to the target are taken. See ``normalize.candidate_drugs``:
    # the alternative was PDCD1's table, where 171 of 197 rows were partner
    # drugs, supportive care and one oesophagectomy.
    own_names = relevance.target_terms(target)
    on_target = [
        t for t in trials
        if relevance.names_target_as_a_drug_target(t, relevance.terms_for(target, assets))
    ]
    mined = normalize.discover_assets_from_trials(
        on_target, known_keys, terms=own_names, words=relevance.target_words(target))
    assets.extend(mined)
    # Programmes entered by hand, for the ones the rules will not take from the
    # record. Merged before anything is counted, so every figure on the page
    # sees the same set of rows.
    assets.extend(_manual_assets_for(target.symbol))
    assets = normalize.dedupe(assets)
    set_aside = sum(
        1 for t in on_target
        if t.interventions
        and not normalize.candidate_drugs(t, own_names, relevance.target_words(target))
    )
    if set_aside:
        notes.append(
            f"{normalize.plural(set_aside, 'trial')} on this target list drugs this "
            f"record does not tie to {target.symbol} -- a chemotherapy backbone, a "
            "comparator, a supportive-care arm. Those trials are counted; their "
            "drugs are not counted as programmes against the target."
        )

    # 6. classify ------------------------------------------------------------
    step("classify")
    mechanism_mod.annotate(assets)
    failures_mod.annotate(trials)
    readouts_mod.annotate(trials)

    if use_llm is None:
        use_llm = llm_mod.available()
    llm_notes: list[str] = []
    if use_llm:
        trials_by_nct = {t.nct_id: t for t in trials}
        try:
            pending = mechanism_mod.unresolved(assets)
            if pending:
                resolutions = llm_mod.resolve_mechanisms(pending[:60], trials_by_nct)
                n = llm_mod.apply_mechanism_resolutions(assets, resolutions)
                llm_notes.append(f"{n} of {len(pending)} unresolved assets classified by model")
            pending_trials = failures_mod.unresolved(trials)
            if pending_trials:
                classifications = llm_mod.classify_failures(pending_trials[:60])
                n = llm_mod.apply_failure_classifications(trials, classifications)
                llm_notes.append(f"{n} of {len(pending_trials)} unclassified terminations resolved by model")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"LLM pass failed ({exc}); rule-based classification stands.")
            use_llm = False

    # 7. curated annotation --------------------------------------------------
    # The header brief. Fails soft for the same reason the biology query does:
    # a missing paragraph costs the reader an introduction, and an aborted run
    # costs them the whole memo.
    step("annotation")
    try:
        annotation = uniprot_src.fetch_brief(target.symbol, target.synonyms)
        if not annotation:
            warnings.append(
                f"No reviewed human UniProt entry matched '{target.symbol}', so the "
                "header carries Open Targets' one-line function and no curated brief."
            )
    except Exception as exc:  # noqa: BLE001 - never worth aborting a run for
        annotation = {}
        warnings.append(f"UniProt unavailable ({exc}); no curated brief in this build.")

    # 8. literature ----------------------------------------------------------
    step("literature")
    try:
        literature = pmc_src.fetch(target.symbol, target.synonyms)
    except Exception as exc:  # noqa: BLE001 - a reading list is never worth aborting for
        literature = {}
        warnings.append(f"Europe PMC unavailable ({exc}); no reading list in this build.")

    # 9. analyse -------------------------------------------------------------
    step("analyse")
    landscape = Landscape(
        target=target,
        assets=sorted(assets, key=lambda a: (-a.max_phase, a.name)),
        trials=sorted(trials, key=lambda t: (-t.phase, t.nct_id)),
        associations=associations,
        deals=deals or [],
        generated=_now(),
        warnings=warnings,
        notes=notes,
    )
    # One name per disease, resolved once, on the assets themselves -- so the
    # matrix, the asset table, the tab badge and the download all count the
    # same rows. Before this the page grouped raw spellings and badged PD-1
    # with 1,360 indications while the engine had resolved 915.
    omitted = crowding_mod.canonicalise_indications(
        landscape.assets, landscape.trials, landscape.target)
    landscape.mechanism_clusters = mechanism_mod.cluster(landscape.assets)
    landscape.crowding = crowding_mod.score_crowding(landscape.assets)
    landscape.crowding["matrix"] = crowding_mod.indication_matrix(landscape.assets, landscape.trials)
    landscape.crowding["indications_omitted"] = omitted
    landscape.failures = failures_mod.summarise(_trials_with_a_programme(landscape))
    landscape.whitespace = crowding_mod.find_whitespace(
        landscape.assets, associations, landscape.trials
    )
    landscape.licensing = licensing_mod.analyse(
        landscape.assets, landscape.trials, landscape.deals
    )

    # The investor layer. Each of these is computed in full and shown in
    # summary — see analysis/feasibility.py on why the page stays thin.
    landscape.precedent = precedent_mod.precedent(
        landscape.assets, landscape.trials, landscape.associations
    )
    landscape.readouts = readouts_mod.summarise(_trials_with_a_programme(landscape))
    landscape.modalities = modality_ref.options_for(
        modality_ref.compartment(target.locations),
        present=[a.modality for a in landscape.assets],
    )
    landscape.diagram = diagram_mod.build(landscape)
    landscape.literature = literature
    landscape.annotation = annotation
    landscape.header = brief_mod.compose(landscape, annotation)
    landscape.feasibility = feasibility_mod.read(landscape, landscape.modalities)

    if llm_notes:
        landscape.crowding["llm_notes"] = llm_notes

    # 9. narrative -----------------------------------------------------------
    landscape.narrative = _narrative(landscape, use_llm)
    return landscape


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------


def _summary_for_llm(landscape: Landscape) -> dict[str, Any]:
    return {
        "target": {
            "symbol": landscape.target.symbol,
            "name": landscape.target.name,
            "function": landscape.target.function[:600],
            "tractability": landscape.target.tractability,
        },
        "crowding": {k: v for k, v in landscape.crowding.items() if k != "matrix"},
        "matrix": landscape.crowding.get("matrix", {}).get("rows", [])[:20],
        "mechanism_clusters": landscape.mechanism_clusters,
        "failures": {
            k: v for k, v in landscape.failures.items() if k != "cases"
        }
        | {"cases": landscape.failures.get("cases", [])[:15]},
        "whitespace": landscape.whitespace,
        "licensing": {
            "holders": (landscape.licensing or {}).get("holders", [])[:8],
            "n_deals": ((landscape.licensing or {}).get("deals") or {}).get("n", 0),
        },
        "lead_assets": [
            {
                "name": a.name,
                "sponsor": a.sponsor,
                "phase": a.phase_label,
                "mechanism": a.mechanism_class,
                "indications": a.indications[:4],
            }
            for a in landscape.assets[:20]
        ],
        "warnings": landscape.warnings,
        "notes": landscape.notes,
    }


def _narrative(landscape: Landscape, use_llm: bool) -> dict[str, str]:
    if use_llm:
        try:
            result = llm_mod.write_narrative(_summary_for_llm(landscape))
            if result:
                result["_source"] = "model"
                return result
        except Exception:  # noqa: BLE001
            pass
    return _template_narrative(landscape)


def _template_narrative(landscape: Landscape) -> dict[str, str]:
    """Deterministic prose. Plainer than the model's, and always available."""
    crowd = landscape.crowding
    fail = landscape.failures
    symbol = landscape.target.symbol

    clusters = list(landscape.mechanism_clusters.items())
    lead = landscape.assets[0] if landscape.assets else None

    def plural(n: int, one: str, many: str = "") -> str:
        return f"{n} {one}" if n == 1 else f"{n} {many or one + 's'}"

    n_active = crowd.get("n_active", 0)
    bottom = (
        f"{symbol} carries {plural(n_active, 'active programme')} across "
        f"{plural(crowd.get('n_mechanism_classes', 0), 'mechanism class', 'mechanism classes')} "
        f"from {plural(crowd.get('n_sponsors', 0), 'named sponsor')}, reaching "
        f"{crowd.get('lead_phase', 'Unknown')}. Phase-weighted density scores "
        f"{crowd.get('weighted_score', 0)}, which this tool bands as "
        f"{crowd.get('verdict', 'Unknown')}."
    )
    if lead:
        bottom += (
            f" The most advanced asset is {lead.name}"
            + (f" ({lead.sponsor})" if lead.sponsor else "")
            + f" at {lead.phase_label}."
        )

    if not clusters:
        competitive = "No assets were resolved against this target."
    elif len(clusters) == 1:
        label, names = clusters[0]
        competitive = (
            f"Every asset sits in one mechanism class — {label} — so there is no "
            "mechanistic differentiation on this target yet: "
            f"{plural(len(names), 'programme')} competing on the same approach."
        )
    else:
        # clusters is ordered by how advanced each class is, so the first is
        # the mature one; the largest is a separate question.
        biggest = max(clusters, key=lambda kv: len(kv[1]))
        competitive = (
            f"The field splits into "
            f"{plural(len(clusters), 'mechanism class', 'mechanism classes')}. "
            f"{clusters[0][0]} is the most advanced"
        )
        if len(biggest[1]) > 1 and biggest[0] != clusters[0][0]:
            competitive += f"; {biggest[0]} is the most crowded, with {len(biggest[1])} assets."
        elif len(biggest[1]) == 1:
            competitive += (
                ", and no class holds more than one asset — the target is being "
                "approached from several directions at once rather than contested "
                "within any one of them."
            )
        else:
            competitive += f", and also the most crowded, with {len(biggest[1])} assets."
    if crowd.get("n_dormant"):
        n_dormant = crowd["n_dormant"]
        verb = "is" if n_dormant == 1 else "are"
        competitive += (
            f" A further {plural(n_dormant, 'programme')} {verb} dormant — every "
            "linked trial stopped and nothing is running — and excluded from "
            "the density score."
        )

    share = fail.get("science_share_of_stated")
    n_science, n_business = fail.get("n_science", 0), fail.get("n_business", 0)
    failures_text = (
        f"{fail.get('n_stopped', 0)} of {fail.get('n_trials', 0)} trials stopped; "
        f"{fail.get('n_with_reason', 0)} stated a reason."
    )
    if share is not None:
        was_science = "was" if n_science == 1 else "were"
        was_business = "was" if n_business == 1 else "were"
        failures_text += (
            f" Of those with a stated reason, {n_science} {was_science} "
            f"science-driven (efficacy, safety or PK/PD) and "
            f"{n_business} {was_business} business-driven."
        )
        # A percentage over two or three terminations is noise dressed as a
        # statistic, so it is only quoted once there is enough to divide.
        if fail.get("n_stopped", 0) >= 5:
            failures_text += (
                f" That is {share:.0%} of stated terminations carrying evidence "
                "about the target rather than about a sponsor's portfolio."
            )
        else:
            failures_text += (
                " At this count the split is indicative only — it is the "
                "individual notices below that carry the information, not the "
                "proportion."
            )
    else:
        failures_text += " No stated reasons were available to classify."

    if landscape.whitespace:
        top = landscape.whitespace[0]
        n_ws = len(landscape.whitespace)
        whitespace_text = (
            f"{plural(n_ws, 'disease', 'diseases')} "
            f"{'passes' if n_ws == 1 else 'pass'} the screen: association evidence "
            "above threshold, genetic support, and nothing past preclinical. The "
            f"strongest on genetic evidence is {top['disease']} "
            f"(association {top['association_score']}, genetic {top['genetic_score']}). "
            "Treat this as a hypothesis to check by hand rather than a finding — "
            "disease names are matched between EFO terms and sponsor free text, "
            "and that matching is imperfect."
        )
    else:
        whitespace_text = (
            "No disease passes the whitespace screen at the configured thresholds, "
            "either because the well-evidenced indications already carry clinical "
            "assets or because association data was unavailable."
        )

    risks = (
        "This read is bounded by what public sources carry. Preclinical and "
        "undisclosed programmes are invisible; China- and Japan-only registrations "
        "are under-represented because only ClinicalTrials.gov is swept; and "
        "termination reasons are self-reported and often absent"
    )
    rate = fail.get("reporting_rate")
    if rate is not None:
        risks += f" ({rate:.0%} of stopped trials here stated one)"
    risks += ". Deal comparables are hand-maintained and not exhaustive."
    # Run warnings are rendered in their own block at the top of the memo;
    # repeating them here would bury them in prose.

    return {
        "bottom_line": bottom,
        "competitive": competitive,
        "failures": failures_text,
        "whitespace": whitespace_text,
        "licensing": licensing_mod.narrative(landscape.licensing) if landscape.licensing else "",
        "risks": risks,
        "_source": "template",
    }


# ---------------------------------------------------------------------------
# Fixtures — offline runs and regression tests
# ---------------------------------------------------------------------------


def save_fixture(landscape: Landscape, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(landscape.to_dict(), fh, indent=2, ensure_ascii=False)


def _trials_with_a_programme(landscape: Landscape) -> list[Trial]:
    """The trials the page can actually show.

    The Trials view reaches a trial through the asset it belongs to, so a trial
    whose drugs were all set aside as partners has no row to appear in. Counted
    in the readout verdict anyway, it put a figure in the sentence that the tab
    beside it could not reach: "45 of 168 running trials" under a tab badged
    243. Those 117 trials are real and they are still counted as trials -- the
    note under the page says how many and why -- but a sentence about what the
    running trials can show should be about the ones on screen.
    """
    wanted = {nct for a in landscape.assets for nct in (a.trials or [])}
    return [t for t in landscape.trials if t.nct_id in wanted]


def _manual_assets_for(symbol: str) -> list[Asset]:
    """The hand-entered file for this target, or nothing.

    Imported inside the function: ``store`` imports this module, and a target
    with no hand-entered file — which is most of them — should not pay for the
    import at all.
    """
    from . import store

    try:
        return store.load_manual_assets(symbol or "")
    except (store.UnknownTarget, OSError):
        return []


def _asset_from_dict(d: dict[str, Any]) -> Asset:
    d = dict(d)
    d.pop("phase_label", None)
    d["provenance"] = [Provenance(**p) for p in d.get("provenance", [])]
    return Asset(**d)


def load_fixture(path: str, *, recompute: bool = True) -> Landscape:
    """Rebuild a Landscape from saved JSON.

    ``recompute`` re-runs the whole analysis layer over the stored raw records,
    which is what makes the fixture a regression test: change a weight or a
    rule and the memo changes, with no network involved.
    """
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    target_raw = dict(raw["target"])
    target_raw["provenance"] = [Provenance(**p) for p in target_raw.get("provenance", [])]
    landscape = Landscape(
        target=Target(**target_raw),
        assets=[_asset_from_dict(a) for a in raw.get("assets", [])],
        trials=[Trial(**t) for t in raw.get("trials", [])],
        associations=[DiseaseAssociation(**a) for a in raw.get("associations", [])],
        deals=[Deal(**d) for d in raw.get("deals", [])],
        generated=raw.get("generated", _now()),
        warnings=list(raw.get("warnings", [])),
        notes=list(raw.get("notes", [])),
    )
    # Stored landscapes written before the text cleaner existed still carry
    # the broken characters, and rebuilding them to fix a punctuation mark is
    # the wrong trade — so they are cleaned on the way in too.
    for trial in landscape.trials:
        normalize.clean_trial_text(trial)
    for asset in landscape.assets:
        normalize.clean_asset_text(asset)
    # Messages that describe the filter working were written into warnings
    # before notes existed. They render as a yellow alert on every page, which
    # reads as a fault and trains the reader to skip the box. Moved across on
    # load so a refresh clears them without a rebuild.
    # A stored warning that quotes the whole failed request. Trimmed here so a
    # refresh clears the wall of URL from the page and the audit report.
    landscape.warnings = [
        (w if "?" not in w else w[:w.index("?")] + " (query omitted). "
         + w.split(").", 1)[1].strip() if ")." in w else w[:w.index("?")] + " (query omitted).")
        for w in landscape.warnings or []
    ]

    moved = [w for w in landscape.warnings
             if "did not name" in w or "left out of the asset table" in w
             or "as a genotype or" in w or "never names" in w
             or "ChEMBL target matched" in w or "ChEMBL holds no" in w]
    if moved:
        landscape.warnings = [w for w in landscape.warnings if w not in moved]
        for message in moved:
            if message not in landscape.notes:
                landscape.notes.append(message)

    # Programmes a person entered by hand, for the cases the rules will not
    # take from the record. Merged only on a recompute, and that restriction is
    # the point: a row changes the asset count, the phase histogram, the
    # crowding band and the mechanism clusters, all of which are stored. Adding
    # one at read time would put a row on the page that none of the figures
    # above it knew about -- the arithmetic that had to be fixed once already.
    # So an edit to the file lands when the refresh runs, and until then the
    # consistency check says the file and the record disagree.
    if recompute:
        manual = _manual_assets_for(landscape.target.symbol)
        if manual:
            landscape.assets = normalize.dedupe(list(landscape.assets) + manual)

    # Assets minted from a trial that names the gene only as a genotype. The
    # rebuilt files carry the trial summaries, so this can be decided here
    # without going back to the network -- which means a stored library heals
    # by running the refresh rather than rebuilding every target again.
    _drop_genotype_only_assets(landscape)

    # The same NCT listed several times against one asset, because the trial
    # named its drug under several spellings and each spelling matched.
    for asset in landscape.assets:
        asset.trials = list(dict.fromkeys(asset.trials or []))

    # Arm labels that were stored as assets before they were recognised as
    # labels. "Chemotherapy", "Treatment Algorithm A" and "Matching" sat in
    # the asset table with a phase and a sponsor; on CARD9 one of them was
    # counted as an approved drug. Dropped on the way in so a stored file
    # heals without a rebuild.
    landscape.assets = [
        a for a in landscape.assets
        if not normalize.is_not_an_asset(a.name)
    ]

    # Assets the registry sweep invented, re-derived from the stored trials
    # under the current rules. Everything the decision needs is in the file --
    # each trial's title, interventions and summary -- so a library built
    # before a rule changed heals by running the refresh, with no network and
    # no rebuild. Database-sourced assets are never touched.
    # A refresh always re-derives -- that is what it is for. Serving skips the
    # work when the file on disk already says it was written by these rules.
    if recompute or raw.get("rules_version") != RULES_VERSION:
        _remine_swept_assets(landscape)

    # Stored files written before locations and topology were separated carry
    # them mixed together, so they are split on the way in as well.
    places, topology = normalize.split_locations(
        list(landscape.target.locations) + list(getattr(landscape.target, "topology", None) or []))
    landscape.target.locations = places
    landscape.target.topology = topology

    # The reading list and the curated annotation are the two layers that
    # cannot be recomputed offline — they are network results, not
    # derivations — so they are carried across from the file either way.
    landscape.literature = raw.get("literature", {})
    landscape.annotation = raw.get("annotation", {})

    if not recompute:
        landscape.mechanism_clusters = raw.get("mechanism_clusters", {})
        landscape.crowding = raw.get("crowding", {})
        landscape.failures = raw.get("failures", {})
        landscape.whitespace = raw.get("whitespace", [])
        landscape.licensing = raw.get("licensing", {})
        landscape.precedent = raw.get("precedent", {})
        landscape.readouts = raw.get("readouts", {})
        landscape.modalities = raw.get("modalities", [])
        landscape.diagram = raw.get("diagram", {})
        landscape.header = raw.get("header", {})
        landscape.feasibility = raw.get("feasibility", {})
        landscape.narrative = raw.get("narrative", {})
        return landscape

    mechanism_mod.annotate(landscape.assets)
    failures_mod.annotate(landscape.trials)
    readouts_mod.annotate(landscape.trials)
    landscape.assets.sort(key=lambda a: (-a.max_phase, a.name))
    # One name per disease, resolved once, on the assets themselves -- so the
    # matrix, the asset table, the tab badge and the download all count the
    # same rows. Before this the page grouped raw spellings and badged PD-1
    # with 1,360 indications while the engine had resolved 915.
    omitted = crowding_mod.canonicalise_indications(
        landscape.assets, landscape.trials, landscape.target)
    landscape.mechanism_clusters = mechanism_mod.cluster(landscape.assets)
    landscape.crowding = crowding_mod.score_crowding(landscape.assets)
    landscape.crowding["matrix"] = crowding_mod.indication_matrix(landscape.assets, landscape.trials)
    landscape.crowding["indications_omitted"] = omitted
    landscape.failures = failures_mod.summarise(_trials_with_a_programme(landscape))
    landscape.whitespace = crowding_mod.find_whitespace(
        landscape.assets, landscape.associations, landscape.trials
    )
    landscape.licensing = licensing_mod.analyse(
        landscape.assets, landscape.trials, landscape.deals
    )
    landscape.precedent = precedent_mod.precedent(
        landscape.assets, landscape.trials, landscape.associations
    )
    landscape.readouts = readouts_mod.summarise(_trials_with_a_programme(landscape))
    landscape.modalities = modality_ref.options_for(
        modality_ref.compartment(landscape.target.locations),
        present=[a.modality for a in landscape.assets],
    )
    landscape.diagram = diagram_mod.build(landscape)
    # Recomputed, not carried across: the therapeutic half of the header comes
    # from the asset table, so it has to move when the asset table does.
    landscape.header = brief_mod.compose(landscape, landscape.annotation)
    landscape.feasibility = feasibility_mod.read(landscape, landscape.modalities)
    landscape.narrative = _template_narrative(landscape)
    return landscape


def _drop_genotype_only_assets(landscape: Landscape) -> None:
    """Remove assets that exist only because a trial selected patients by this
    gene. Posaconazole is an antifungal; it appeared as an approved CARD9 drug
    because the trial enrols carriers of the CARD9 S12N risk allele."""
    trials = {t.nct_id: t for t in landscape.trials}
    terms = relevance.terms_for(landscape.target, landscape.assets)
    if not terms:
        return
    kept = []
    for asset in landscape.assets:
        vouched = relevance._vouched_by_a_database(asset)  # noqa: SLF001
        # The drug's own name says what it acts on, and no amount of
        # patient-selection language around it changes that. PRS-343 is filed
        # as "HER2/41BB Bispecific" in a trial whose every other mention of
        # HER2 is "HER2-positive"; reading the trial alone dropped a bispecific
        # whose name states the target.
        named = relevance.target_is_in_the_drug_name(asset.name, terms)
        linked = [trials[n] for n in (asset.trials or []) if n in trials]
        if vouched or named or not linked or any(
            relevance.names_target_as_a_drug_target(t, terms) for t in linked
        ):
            kept.append(asset)
    landscape.assets = kept


def _remine_swept_assets(landscape: Landscape) -> None:
    """Rebuild the sweep-derived half of the asset table from stored trials.

    PDCD1 was stored with 197 assets. Twenty-six came from Open Targets or
    ChEMBL. The rest were interventions taken out of combination trials, so
    the table listed carboplatin, omeprazole, trastuzumab and an
    oesophagectomy as programmes against PD-1, and the mechanism panel showed
    twenty-three antibodies whose mechanism was "unresolved" -- not because
    nobody knows what nivolumab does, but because those rows were arm labels
    rather than records of a drug.

    The rule that replaces it is in ``normalize.candidate_drugs``. Applying it
    here as well as at build time is what lets a stored library be corrected
    by ``6-REFRESH-LIBRARY.bat`` instead of a network rebuild of every target.
    """
    if not landscape.trials:
        return
    terms = relevance.target_terms(landscape.target)
    if not terms:
        return
    # Every stored file is re-mined, not only the ones that already hold a
    # swept asset. CLDN18 holds one row, zolbetuximab, from Open Targets;
    # skipping it because nothing in it came from the sweep is what kept the
    # second programme in its trials out of the table.
    from_database = [a for a in landscape.assets
                     if not relevance.from_the_sweep_alone(a)]
    words = relevance.target_words(landscape.target)
    landscape.assets = normalize.dedupe(from_database + mine_from_stored(landscape))
    normalize.attach_trials(landscape.assets, list(landscape.trials))
    # Done after the trials are attached: the rule needs to see that the rows
    # are the same sponsor's, in the same study.
    landscape.assets = normalize.fold_unnamed_rows_in_one_trial(landscape.assets, words)
    for asset in landscape.assets:
        asset.trials = list(dict.fromkeys(asset.trials or []))
    set_aside = sum(
        1 for t in landscape.trials
        if t.interventions and not normalize.candidate_drugs(t, terms, words)
    )
    note = (
        f"{normalize.plural(set_aside, 'trial')} on this target list drugs this "
        f"record does not tie to {landscape.target.symbol} -- a chemotherapy "
        "backbone, a comparator, a supportive-care arm. Those trials are counted; "
        "their drugs are not counted as programmes against the target."
    )
    landscape.notes = [n for n in (landscape.notes or [])
                       if "does not tie to" not in n]
    if set_aside:
        landscape.notes.append(note)


def mine_from_stored(landscape: Landscape) -> list[Asset]:
    """The asset rows the current rules derive from this file's own trials.

    One function so that the loader and the audit ask the question the same
    way. They used to differ by which assets seeded the search terms, and the
    two answers then disagreed about what a sponsor's unnamed programme should
    be called -- which the audit reported as a missing programme every time.
    """
    from_database = [a for a in landscape.assets
                     if not relevance.from_the_sweep_alone(a)]
    terms = relevance.target_terms(landscape.target)
    if not terms or not landscape.trials:
        return []
    known: set[str] = set()
    for asset in from_database:
        known |= normalize._keys_for(asset)  # noqa: SLF001 - same package
    full_terms = relevance.terms_for(landscape.target, from_database)
    on_target = [
        t for t in landscape.trials
        if relevance.names_target_as_a_drug_target(t, full_terms)
    ]
    return normalize.discover_assets_from_trials(
        on_target, known, terms=terms,
        words=relevance.target_words(landscape.target))


def refresh_dated(landscape: Landscape) -> Landscape:
    """Re-run only the layers whose answer depends on today's date.

    A curated file is stored fully computed so that serving it is a file read.
    Almost all of it stays true until the underlying data changes: an approval
    count, a mechanism split, a termination reason. Two layers do not.

    ``readouts`` answers "what reads out next", which filters upcoming
    completions against today and so decays every day the file sits on disk;
    ``feasibility`` reads from it. Left alone, a page built last month offers
    a readout date that has already passed, which is worse than offering none.

    So the request path skips the analysis layer and re-runs these two. On
    PDCD1 that is 0.14s against the 4.3s a full recompute costs -- and the
    full recompute was what the web layer was quietly doing on *every page
    load*, which is the thing ``precompute.py`` exists to make unnecessary.

    Everything else moves only when a rule changes, and a rule change is what
    ``scripts/recompute_curated.py`` is for.
    """
    if not landscape.trials:
        return landscape
    readouts_mod.annotate(landscape.trials)
    landscape.readouts = readouts_mod.summarise(_trials_with_a_programme(landscape))
    landscape.feasibility = feasibility_mod.read(landscape, landscape.modalities)
    return landscape
