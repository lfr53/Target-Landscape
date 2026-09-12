"""Tests for the investor layer.

The theme running through these: every one of them checks a case where the
obvious implementation says something confidently wrong. A missing design
field read as "uncontrolled", a negated verb read as "no reason given", an
unannotated location read as "modality available" — each of those is a
sentence the page would print in good faith and a reader would act on.
"""

from __future__ import annotations

import os
import unittest
from datetime import date

from landscape.analysis import diagram, feasibility, precedent, readouts
from landscape.analysis import crowding as crowding_mod
from landscape.analysis import failures as failures_mod
from landscape.models import Asset, DiseaseAssociation, Landscape, Target, Trial
from landscape.reference import modalities


def trial(**kwargs) -> Trial:
    base = dict(nct_id="NCT00000001", status="RECRUITING", phase=2)
    base.update(kwargs)
    return Trial(**base)


# ---------------------------------------------------------------------------
# Endpoint classification
# ---------------------------------------------------------------------------


class EndpointTests(unittest.TestCase):
    def test_progression_free_survival_is_a_surrogate_not_a_hard_outcome(self):
        # "survival" appears in both; ordering decides which rule wins, and
        # getting this backwards would inflate the evidence on every oncology
        # target in the index.
        self.assertEqual(readouts.classify_endpoint("Progression free survival")["class"], "surrogate")
        self.assertEqual(readouts.classify_endpoint("Overall survival")["class"], "hard")

    def test_receptor_occupancy_is_a_biomarker(self):
        result = readouts.classify_endpoint("Peripheral B-cell receptor occupancy at week 12")
        self.assertEqual(result["class"], "biomarker")

    def test_unknown_instrument_falls_back_on_shape(self):
        # ESSDAI is in no vocabulary this file will ever hold. Its shape — a
        # change in a named score — is what identifies it, and the fallback
        # exists so a perfectly ordinary registrational endpoint is not
        # reported as unclassified.
        result = readouts.classify_endpoint("Change from baseline in ESSDAI total score")
        self.assertEqual(result["class"], "scale")

    def test_a_score_shaped_safety_measure_is_still_safety(self):
        # The generic fallback must not steal endpoints an earlier rule owns.
        result = readouts.classify_endpoint("Number of participants with adverse events")
        self.assertEqual(result["class"], "safety")

    def test_the_verbatim_measure_is_always_returned(self):
        text = "Something entirely unanticipated"
        self.assertEqual(readouts.classify_endpoint(text)["measure"], text)


# ---------------------------------------------------------------------------
# What a trial can prove
# ---------------------------------------------------------------------------


class GradeTests(unittest.TestCase):
    def test_randomised_blinded_and_large_is_confirmatory(self):
        grade = readouts.grade_trial(trial(
            allocation="RANDOMIZED", masking="QUADRUPLE", intervention_model="PARALLEL",
            enrollment=240, primary_outcomes=["Overall survival"]))
        self.assertEqual(grade["level"], "confirmatory")

    def test_single_arm_efficacy_is_only_a_signal(self):
        grade = readouts.grade_trial(trial(
            allocation="NA", intervention_model="SINGLE_GROUP", enrollment=40,
            primary_outcomes=["Objective response rate"]))
        self.assertEqual(grade["level"], "signal")
        self.assertIn("comparator", grade["note"])

    def test_a_pd_endpoint_cannot_support_efficacy_however_it_is_designed(self):
        grade = readouts.grade_trial(trial(
            allocation="RANDOMIZED", masking="QUADRUPLE", enrollment=300,
            primary_outcomes=["Change in serum IL-6 concentration"]))
        self.assertEqual(grade["level"], "mechanistic")

    def test_phase_1_safety_is_reported_as_normal_not_as_a_failing(self):
        grade = readouts.grade_trial(trial(
            phase=1, allocation="NA", enrollment=30,
            primary_outcomes=["Incidence of dose-limiting toxicity"]))
        self.assertEqual(grade["level"], "dose")

    def test_co_primary_takes_the_strongest_claim(self):
        # OS alongside adverse events is an efficacy trial. Taking the first
        # endpoint, or the commonest, would call it a safety study.
        grade = readouts.grade_trial(trial(
            allocation="RANDOMIZED", masking="DOUBLE", enrollment=400,
            primary_outcomes=["Number of participants with adverse events", "Overall survival"]))
        self.assertEqual(grade["endpoint_class"], "hard")


# ---------------------------------------------------------------------------
# Catalysts
# ---------------------------------------------------------------------------


class CatalystTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 1, 1)
        self.trials = [
            trial(nct_id="NCT1", phase=1, allocation="NA", enrollment=20,
                  primary_outcomes=["Adverse events"], completion_date="2026-06",
                  completion_date_type="ESTIMATED"),
            trial(nct_id="NCT2", phase=3, allocation="RANDOMIZED", masking="DOUBLE",
                  enrollment=300, primary_outcomes=["Overall survival"],
                  completion_date="2027-09", completion_date_type="ESTIMATED"),
            trial(nct_id="NCT3", status="TERMINATED", completion_date="2026-03"),
        ]

    def test_stopped_trials_have_no_readout(self):
        rows = readouts.next_catalysts(self.trials, today=self.today)
        self.assertNotIn("NCT3", [r["nct_id"] for r in rows])

    def test_past_dates_are_excluded(self):
        rows = readouts.next_catalysts(
            [trial(completion_date="2020-01", primary_outcomes=["Overall survival"])],
            today=self.today)
        self.assertEqual(rows, [])

    def test_headline_prefers_the_interpretable_readout_over_the_sooner_one(self):
        # A Phase 1 safety readout six months out is nearer than a Phase 3
        # efficacy readout in two years and tells you far less. Leading with
        # the nearer one would be accurate and useless.
        rows = readouts.next_catalysts(self.trials, today=self.today)
        self.assertEqual(rows[0]["nct_id"], "NCT1")
        headline = readouts.headline_catalyst(rows)
        self.assertEqual(headline["nct_id"], "NCT2")
        self.assertTrue(headline["is_interpretable"])

    def test_the_headline_is_chosen_from_every_upcoming_readout_not_the_first_page(self):
        """The Trials tab shows the soonest eight; the headline must not be
        picked from that truncated list. On PD-1 the eight soonest completions
        are all small studies, and the page led with an academic study of
        sexual function while a randomised Phase 3 sat at position forty."""
        from datetime import date
        small = [
            trial(nct_id=f"NCT{i:04d}", phase=1, completion_date="2026-01",
                  primary_outcomes=["Safety and tolerability"])
            for i in range(12)
        ]
        big = trial(nct_id="NCTBIG", phase=3, completion_date="2027-06",
                    allocation="RANDOMIZED", masking="DOUBLE", enrollment=600,
                    primary_outcomes=["Overall survival"])
        summary = readouts.summarise(small + [big], today=date(2025, 6, 1))
        self.assertEqual(summary["next_catalyst"]["nct_id"], "NCTBIG")
        self.assertTrue(summary["next_catalyst"]["is_interpretable"])
        # And the reader is told something lands before it.
        self.assertEqual(summary["next_catalyst"]["soonest_other"]["nct_id"], "NCT0000")
        # The tab itself still shows only a page of them.
        self.assertLessEqual(len(summary["catalysts"]), 8)

    def test_an_academic_sponsor_is_never_a_reason_to_skip_a_trial(self):
        """Hospital- and university-sponsored trials stay eligible for the
        headline. On PD-1 the right answer is a randomised Phase 3 run by
        Ruijin Hospital; a rule preferring industry sponsors would have
        discarded it."""
        from datetime import date
        academic = trial(nct_id="NCTACAD", phase=3, completion_date="2026-12",
                         allocation="RANDOMIZED", enrollment=400,
                         sponsor="Ruijin Hospital", sponsor_class="OTHER",
                         primary_outcomes=["Event-free survival"])
        summary = readouts.summarise([academic], today=date(2025, 6, 1))
        self.assertEqual(summary["next_catalyst"]["nct_id"], "NCTACAD")

    def test_headline_falls_back_when_nothing_controlled_is_scheduled(self):
        headline = readouts.headline_catalyst(
            readouts.next_catalysts(self.trials[:1], today=self.today))
        self.assertEqual(headline["nct_id"], "NCT1")
        self.assertFalse(headline["is_interpretable"])


class SummaryTests(unittest.TestCase):
    def test_no_registered_design_is_a_gap_in_the_record_not_a_verdict(self):
        # Every trial here is running and none registered a design. Reporting
        # "0 of 3 controlled" would turn a registry gap into a finding about
        # the target.
        summary = readouts.summarise([trial(nct_id=f"NCT{i}") for i in range(3)])
        self.assertEqual(summary["n_undescribed"], 3)
        self.assertIn("gap in the record", summary["verdict"])
        self.assertNotIn("none of them randomised", summary["verdict"])


# ---------------------------------------------------------------------------
# Termination reasons
# ---------------------------------------------------------------------------


class NegatedFailureTests(unittest.TestCase):
    def test_did_not_meet_primary_endpoint_is_an_efficacy_failure(self):
        # The commonest phrasing of an efficacy failure in the whole corpus,
        # and it is written in the negative — so the negation mask deleted it
        # and the trial was reported as "reason not stated".
        label, evidence, _ = failures_mod.classify_reason(
            "Study did not meet its primary efficacy endpoint")
        self.assertEqual(label, "efficacy")
        self.assertTrue(evidence)

    def test_negated_nouns_are_still_masked(self):
        label, _, _ = failures_mod.classify_reason(
            "No new safety signals were identified. Sponsor business decision.")
        self.assertNotEqual(label, "safety")

    def test_an_internal_bar_stays_a_business_decision(self):
        label, _, _ = failures_mod.classify_reason(
            "Did not meet pre-specified internal go/no-go criteria")
        self.assertEqual(label, "business")

    def test_futility_is_efficacy(self):
        label, _, _ = failures_mod.classify_reason("Halted for futility at interim analysis")
        self.assertEqual(label, "efficacy")


# ---------------------------------------------------------------------------
# Modality fit
# ---------------------------------------------------------------------------


class ModalityFitTests(unittest.TestCase):
    def test_unknown_location_never_returns_available_for_a_constrained_modality(self):
        # Asserting an antibody can reach a target nobody has placed is the
        # one failure in this section that would cost somebody money.
        verdict = modalities.fit(modalities.BY_KEY["Monoclonal antibody"],
                                 modalities.compartment([]))
        self.assertEqual(verdict["verdict"], "unknown")

    def test_an_antibody_is_ruled_out_by_a_nuclear_location(self):
        verdict = modalities.fit(modalities.BY_KEY["Monoclonal antibody"],
                                 modalities.compartment(["Nucleus", "Cytoplasm"]))
        self.assertEqual(verdict["verdict"], "blocked")

    def test_a_degrader_is_ruled_out_by_a_secreted_location(self):
        verdict = modalities.fit(modalities.BY_KEY["Molecular glue / degrader"],
                                 modalities.compartment(["Secreted"]))
        self.assertEqual(verdict["verdict"], "blocked")

    def test_an_adc_needs_the_membrane_not_merely_the_outside(self):
        secreted = modalities.compartment(["Secreted"])
        self.assertEqual(
            modalities.fit(modalities.BY_KEY["Antibody-drug conjugate"], secreted)["verdict"],
            "blocked")
        self.assertEqual(
            modalities.fit(modalities.BY_KEY["Monoclonal antibody"], secreted)["verdict"],
            "available")

    def test_every_entry_states_what_it_demands_of_the_target(self):
        for entry in modalities.MODALITIES:
            self.assertTrue(entry["requires"], entry["key"])
            self.assertTrue(entry["fails"], entry["key"])

    def test_aliases_resolve(self):
        self.assertEqual(modalities.lookup("ADC")["key"], "Antibody-drug conjugate")
        self.assertEqual(modalities.lookup("分子胶")["key"], "Molecular glue / degrader")


# ---------------------------------------------------------------------------
# Precedent
# ---------------------------------------------------------------------------


class PrecedentTests(unittest.TestCase):
    def test_an_approval_closes_the_mechanism_question(self):
        result = precedent.precedent(
            [Asset(name="drug", max_phase=4, first_approval=2011)], [], [])
        self.assertEqual(result["tier"], "approved")
        self.assertIn("2011", result["evidence"][0])

    def test_a_science_failure_outranks_a_clinical_stage_asset(self):
        trials = [trial(nct_id="NCT9", status="TERMINATED", phase=2,
                        why_stopped="Terminated due to lack of efficacy")]
        failures_mod.annotate(trials)
        result = precedent.precedent([Asset(name="drug", max_phase=2)], trials, [])
        self.assertEqual(result["tier"], "failed")
        self.assertIn("quoted under Terminations", " ".join(result["evidence"]))

    def test_an_operational_termination_is_not_a_failed_mechanism(self):
        trials = [trial(nct_id="NCT9", status="TERMINATED", phase=2,
                        why_stopped="Slow recruitment; site closures")]
        failures_mod.annotate(trials)
        result = precedent.precedent([Asset(name="drug", max_phase=2)], trials, [])
        self.assertNotEqual(result["tier"], "failed")

    def test_genetic_evidence_is_reported_when_it_is_absent_too(self):
        result = precedent.precedent([], [], [])
        self.assertIn("No human genetic association above threshold",
                      " ".join(result["evidence"]))
        # Absence of evidence, stated as absence. An earlier version said the
        # case "rests on pharmacology rather than genetics", which is a verdict
        # dressed as a fact.
        self.assertIn("not evidence against", " ".join(result["evidence"]))

    def test_no_visible_string_uses_a_lazy_plural_or_says_at_approved(self):
        """Two things a reader notices immediately: "1 sponsor(s)", which
        reads as an unfinished sentence, and "leader at Approved", which reads
        as a typo -- an approval is not a phase a programme sits at."""
        import re

        from landscape.analysis import feasibility as feas

        for n, sponsors, lead in ((1, 1, "Approved"), (2, 3, "Phase 2"), (0, 0, "")):
            line = feas._window_line({
                "verdict": "Contested", "n_total": n, "n_sponsors": sponsors,
                "lead_phase": lead, "weighted_score": 1.0,
            })
            text = f"{line['value']} {line['detail']}"
            self.assertIsNone(re.search(r"\(s\)", text), text)
            self.assertNotIn("at Approved", text)
        self.assertIn("one already approved",
                      feas._window_line({"verdict": "Contested", "n_total": 1,
                                         "n_sponsors": 1, "lead_phase": "Approved",
                                         "weighted_score": 1.0})["value"])

    def test_the_read_states_the_record_and_does_not_instruct_the_reader(self):
        """The tier line is prose the reader sees on the Assets tab, and the
        site does not tell anyone what to conclude. This used to open with
        "Mechanism risk is retired. Diligence moves to differentiation" and
        "Somebody with more information than you funded a Phase 3"."""
        banned = ("diligence moves", "risk is retired", "find out what",
                  "you should", "more information than you", "reprices")
        for assets, trials in (
            ([Asset(name="d", max_phase=4, first_approval=2011)], []),
            ([Asset(name="d", max_phase=3)], []),
            ([Asset(name="d", max_phase=1)], []),
            ([], []),
        ):
            read = (precedent.precedent(assets, trials, []).get("read") or "").lower()
            for phrase in banned:
                self.assertNotIn(phrase, read)


# ---------------------------------------------------------------------------
# The six lines
# ---------------------------------------------------------------------------


def build_landscape(**over) -> Landscape:
    target = Target(
        ensembl_id="ENSG0", symbol="TESTG", name="test gene",
        locations=over.pop("locations", ["Cell membrane"]),
        target_class=["Receptor"])
    assets = over.pop("assets", [
        Asset(name="alpha", modality="Monoclonal antibody", mechanism_class="Blockade",
              max_phase=3, trials=["NCT1"]),
    ])
    trials = over.pop("trials", [
        trial(nct_id="NCT1", phase=3, allocation="RANDOMIZED", masking="DOUBLE",
              enrollment=200, primary_outcomes=["Overall survival"],
              completion_date="2099-01", completion_date_type="ESTIMATED"),
    ])
    assoc = over.pop("associations", [])
    failures_mod.annotate(trials)
    readouts.annotate(trials)
    ls = Landscape(target=target, assets=assets, trials=trials, associations=assoc)
    ls.crowding = crowding_mod.score_crowding(assets)
    ls.failures = failures_mod.summarise(trials)
    ls.precedent = precedent.precedent(assets, trials, assoc)
    ls.readouts = readouts.summarise(trials)
    ls.modalities = modalities.options_for(
        modalities.compartment(target.locations), [a.modality for a in assets])
    ls.diagram = diagram.build(ls)
    ls.feasibility = feasibility.read(ls, ls.modalities)
    return ls


class FeasibilityTests(unittest.TestCase):
    def test_never_more_than_six_lines(self):
        ls = build_landscape()
        self.assertLessEqual(len(ls.feasibility["lines"]), 6)

    def test_every_line_says_which_face_it_is_and_how_to_check_it(self):
        for line in build_landscape().feasibility["lines"]:
            self.assertIn(line["face"], feasibility.FACES)
            self.assertTrue(line["anchor"])
            self.assertTrue(line["detail"])

    def test_history_line_says_none_stopped_rather_than_disappearing(self):
        # There is a real trial on record here (NCT1, still running) and none
        # of it has stopped. That is a fact worth stating plainly -- "None
        # stopped - 1 trial on record" -- not a default to hide behind
        # silence, which is what a missing sixth row would otherwise look
        # like on the page.
        ls = build_landscape()
        lines = {line["key"]: line for line in ls.feasibility["lines"]}
        self.assertIn("history", lines)
        self.assertIn("None stopped", lines["history"]["value"])

    def test_no_history_line_when_there_is_no_trial_at_all(self):
        # A target with zero trials on record has nothing this line can speak
        # to -- that case still returns nothing, same as before.
        ls = build_landscape(trials=[], assets=[])
        self.assertNotIn("history", [line["key"] for line in ls.feasibility["lines"]])

    def test_evidence_line_says_none_running_rather_than_disappearing(self):
        # Same fix, same reasoning, for the other line that used to vanish:
        # a target whose only trial has completed still has a trial on
        # record, so "what can the running trials show" gets an honest
        # "none, N on record" instead of dropping off the page.
        trials = [
            trial(nct_id="NCT1", status="COMPLETED", phase=3, allocation="RANDOMIZED",
                  masking="DOUBLE", enrollment=200, primary_outcomes=["Overall survival"],
                  completion_date="2020-01"),
        ]
        ls = build_landscape(trials=trials)
        lines = {line["key"]: line for line in ls.feasibility["lines"]}
        self.assertIn("evidence", lines)
        self.assertIn("None running", lines["evidence"]["value"])

    def test_no_evidence_line_when_there_is_no_trial_at_all(self):
        ls = build_landscape(trials=[], assets=[])
        self.assertNotIn("evidence", [line["key"] for line in ls.feasibility["lines"]])

    def test_no_verdict_sentence_is_generated(self):
        """The site reports what the record holds; it does not tell a reader
        what that adds up to. On most targets the record does not support a
        conclusion, and a template with a slot for one fills it anyway."""
        trials = [
            trial(nct_id="NCT1", status="TERMINATED", phase=2,
                  why_stopped="Study did not meet its primary efficacy endpoint"),
            trial(nct_id="NCT2", phase=3, allocation="RANDOMIZED", masking="DOUBLE",
                  enrollment=200, primary_outcomes=["Overall survival"],
                  completion_date="2099-01"),
        ]
        ls = build_landscape(trials=trials)
        self.assertNotIn("headline", ls.feasibility)

    def test_a_scientific_failure_is_still_surfaced_as_its_own_line(self):
        """Dropping the verdict must not drop the fact behind it."""
        trials = [
            trial(nct_id="NCT1", status="TERMINATED", phase=2,
                  why_stopped="Study did not meet its primary efficacy endpoint"),
        ]
        ls = build_landscape(trials=trials)
        stopped = [l for l in ls.feasibility["lines"] if l["key"] == "history"]
        self.assertTrue(stopped)
        self.assertIn("efficacy", stopped[0]["value"])
        self.assertEqual(stopped[0]["face"], "science")

    def test_the_lines_are_questions_not_assertions(self):
        ls = build_landscape()
        for line in ls.feasibility["lines"]:
            self.assertTrue(line["label"].endswith("?"), line["label"])

    def test_an_unannotated_location_suppresses_the_untried_modality_claim(self):
        # With no location, every location-independent modality reports
        # "available" — true, and no basis for telling a reader that small
        # molecules are an untried opening here.
        ls = build_landscape(locations=[])
        opening = [l for l in ls.feasibility["lines"] if l["key"] == "opening"]
        self.assertFalse([l for l in opening if "Untried here" in l["value"]])


# ---------------------------------------------------------------------------
# The figure
# ---------------------------------------------------------------------------


class DiagramTests(unittest.TestCase):
    def test_the_svg_is_self_contained(self):
        svg = build_landscape().diagram["svg"]
        self.assertTrue(svg.startswith("<svg"))
        for forbidden in ("<script", "http://", "https://www.w3.org/2000/svg\" src", "xlink:href"):
            self.assertNotIn(forbidden, svg.replace('xmlns="http://www.w3.org/2000/svg"', ""))

    def test_it_carries_a_title_and_description_for_a_screen_reader(self):
        svg = build_landscape().diagram["svg"]
        self.assertIn("<title", svg)
        self.assertIn("<desc", svg)
        self.assertIn('role="img"', svg)

    def test_target_symbols_are_escaped(self):
        ls = build_landscape()
        ls.target.symbol = '<script>x</script>'
        svg = diagram.build(ls)["svg"]
        self.assertNotIn("<script>", svg)

    def test_an_empty_target_says_so_rather_than_drawing_nothing(self):
        ls = build_landscape(assets=[], trials=[])
        self.assertIn("Nothing has been recorded", ls.diagram["svg"])

    def test_an_unannotated_location_is_marked_on_the_canvas(self):
        ls = build_landscape(locations=[])
        self.assertIn("location not annotated", ls.diagram["svg"])


if __name__ == "__main__":
    unittest.main()


class TestHeaderFacts(unittest.TestCase):
    """The header is a list of facts. Every test here is a header that would
    have told the reader what to think instead of what is on the record."""

    FIXTURE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fixtures", "TNFRSF13C.json",
    )

    def setUp(self):
        from landscape import pipeline
        from landscape.analysis import brief as brief_mod

        self.pipeline = pipeline
        self.brief = brief_mod
        self.landscape = pipeline.load_fixture(self.FIXTURE)

    def keys(self, header):
        return [row["key"] for row in header["facts"]]

    def test_the_header_is_separable_facts_not_a_paragraph(self):
        header = self.brief.compose(self.landscape, {})
        self.assertTrue(header["facts"])
        for row in header["facts"]:
            self.assertTrue(row["label"])
            self.assertTrue(row["value"])

    def test_what_is_in_development_is_counted_not_characterised(self):
        """Names, phases and counts. No sentence saying what the competitive
        question is — that is the reader's to form."""
        header = self.brief.compose(self.landscape, {})
        row = [r for r in header["facts"] if r["key"] == "development"][0]
        self.assertIn("Ianalumab", row["note"])
        self.assertIn("Phase 3", row["note"])
        for banned in ("competitive question", "worth", "rarer", "opportunity"):
            self.assertNotIn(banned, (row["value"] + row["note"]).lower())

    def test_the_lead_mechanism_is_named_not_just_the_modality(self):
        """Depleting the cells that carry a receptor and blocking its ligand
        are different medicines. That is a fact about the molecule."""
        header = self.brief.compose(self.landscape, {})
        row = [r for r in header["facts"] if r["key"] == "development"][0]
        self.assertIn("Depleting antibody (ADCC/CDC)", row["note"])

    def test_a_shouted_inn_name_is_not_left_shouting(self):
        self.assertEqual(self.brief._display_name("CEMIPLIMAB"), "Cemiplimab")
        for unchanged in ("BNT327", "LM-299", "BAFFR CAR-T"):
            self.assertEqual(self.brief._display_name(unchanged), unchanged)

    def test_indications_are_ranked_by_evidence_not_alphabetically(self):
        """Every Phase 3 row here carries the same single asset, so phase and
        asset count tie and alphabetical order decided — which put autoimmune
        hepatitis ahead of Sjogren's disease."""
        header = self.brief.compose(self.landscape, {})
        value = [r for r in header["facts"] if r["key"] == "development"][0]["value"]
        self.assertIn("Sjogren's Disease", value)
        self.assertNotIn("Autoimmune Hepatitis", value)

    def test_the_list_says_when_it_is_showing_only_part_of_the_field(self):
        header = self.brief.compose(self.landscape, {})
        value = [r for r in header["facts"] if r["key"] == "development"][0]["value"]
        self.assertIn("more at that phase", value)

    def test_a_saturated_remainder_is_stated_as_a_proportion(self):
        """"and 643 more" reads as a broken number rather than as scale."""
        self.landscape.crowding = {"matrix": {"rows": [
            {"indication": f"Cancer {i}", "n_assets": 1, "max_phase": 3}
            for i in range(646)
        ]}}
        header = self.brief.compose(self.landscape, {})
        value = [r for r in header["facts"] if r["key"] == "development"][0]["value"]
        self.assertIn("3 of 646 indications at that phase", value)

    def test_a_target_with_no_assets_says_so_rather_than_inventing_a_field(self):
        from landscape.models import Landscape, Target

        empty = Landscape(target=Target(ensembl_id="ENSG0", symbol="NEWGENE"))
        header = self.brief.compose(empty, {})
        row = [r for r in header["facts"] if r["key"] == "development"][0]
        self.assertIn("Nothing in the public record", row["value"])
        self.assertIn("Preclinical and undisclosed", row["note"])

    def test_the_header_recomputes_from_the_asset_table(self):
        landscape = self.pipeline.load_fixture(self.FIXTURE, recompute=True)
        self.assertTrue(landscape.header.get("facts"))
        self.assertIn("Ianalumab", str(landscape.header["facts"]))

    def test_the_detailed_biology_is_returned_separately_for_the_tab(self):
        """The header stays short; the reader who wants the mechanism goes to
        the Mechanisms tab for it."""
        annotation = {"brief": {"segments": [
            {"kind": "function", "text": "One. Two. Three.", "pmids": ["1"]},
            {"kind": "subunit", "text": "Homotrimer.", "pmids": ["2"]},
        ]}}
        header = self.brief.compose(self.landscape, annotation)
        fact = [r for r in header["facts"] if r["key"] == "function"][0]
        self.assertEqual(fact["value"], "One.")
        self.assertIn("Three.", header["mechanism"]["text"])
        self.assertIn("Homotrimer.", header["mechanism"]["text"])


class TestGermlineDiseasePlacement(unittest.TestCase):
    """UniProt's DISEASE comment is the Mendelian disease caused by germline
    variants — PDCD1's is an infantile autoimmune syndrome, while PD-1 is
    drugged to treat cancer. Mistaking it for the indication is the single
    most misleading thing this header could do."""

    def setUp(self):
        from landscape import pipeline
        from landscape.analysis import brief as brief_mod

        self.brief = brief_mod
        self.landscape = pipeline.load_fixture(TestHeaderFacts.FIXTURE)
        self.annotation = {
            "disease": [{"name": "Immunodeficiency, common variable, 4",
                         "acronym": "CVID4", "pmids": ["19666484"]}],
            "brief": {"segments": [
                {"kind": "function", "text": "A receptor.", "pmids": []},
                {"kind": "disease", "text": "…", "pmids": []},
            ]},
        }

    def test_it_is_its_own_labelled_row_never_mixed_into_development(self):
        header = self.brief.compose(self.landscape, self.annotation)
        row = [r for r in header["facts"] if r["key"] == "genetics"][0]
        self.assertIn("CVID4", row["value"])
        self.assertIn("not an indication", row["note"])
        development = [r for r in header["facts"] if r["key"] == "development"][0]
        self.assertNotIn("CVID", development["value"] + development["note"])

    def test_it_is_withheld_when_the_development_picture_is_not_loaded(self):
        """Alone it becomes the header's only disease and a reader takes it
        for the indication."""
        header = self.brief.compose(None, self.annotation)
        self.assertNotIn("genetics", [r["key"] for r in header["facts"]])
        self.assertTrue(header["development_unknown"])

    def test_a_missing_landscape_is_not_reported_as_an_empty_field(self):
        """"Nothing in the public record" is false on PD-1. Not having loaded
        the asset table is not evidence that it is empty."""
        header = self.brief.compose(None, self.annotation)
        self.assertNotIn("development", [r["key"] for r in header["facts"]])


class ConsistencyTests(unittest.TestCase):
    """Two figures about one fact, one line apart, disagreeing.

    The page said "9 approved drugs on this target" and, three lines below,
    "247 assets, one already approved". Both were derived correctly -- 247 is
    every molecule ever found against the target, 9 is the subset that reached
    the market -- but nothing said one contained the other, and "one already
    approved" read as a count of one.
    """

    def setUp(self):
        from landscape import consistency

        self.consistency = consistency

    def _landscape(self, **over):
        return build_landscape(**over)

    def test_the_contested_line_states_how_many_are_approved(self):
        from landscape.analysis import feasibility as feas

        crowding = {"verdict": "Saturated", "n_total": 247, "n_sponsors": 67,
                    "lead_phase": "Approved", "weighted_score": 319.8}
        self.assertIn("9 already approved", feas._window_line(crowding, 9)["value"])
        self.assertNotIn("one already approved", feas._window_line(crowding, 9)["value"])
        # And it still reads properly when there is exactly one.
        self.assertIn("1 already approved", feas._window_line(crowding, 1)["value"])

    def test_a_clean_landscape_reports_nothing(self):
        self.assertEqual(self.consistency.check(self._landscape()), [])

    def test_an_asset_count_that_disagrees_with_the_table_is_caught(self):
        landscape = self._landscape()
        landscape.crowding["n_total"] = 999
        self.assertTrue(any("999" in p for p in self.consistency.check(landscape)))

    def test_approved_more_than_the_whole_table_is_caught(self):
        landscape = self._landscape()
        landscape.precedent = dict(landscape.precedent or {}, n_approved=50)
        self.assertTrue(self.consistency.check(landscape))

    def test_assets_with_no_trials_at_all_is_caught(self):
        """ERBB2 was stored with 45 assets, 15 of them approved, and zero
        trials. Trastuzumab alone has hundreds. A sweep that failed and a
        target nobody has studied produce the same empty list."""
        landscape = self._landscape(trials=[])
        self.assertTrue(any("no trials at all" in p
                            for p in self.consistency.check(landscape)))
