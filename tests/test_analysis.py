"""Regression tests for the judgement layer.

These test the parts that can silently produce a wrong answer rather than an
error — which, in a tool whose whole output is a judgement, is every part that
matters. Each test corresponds to a real failure mode found while building it.

Run: python -m unittest discover tests
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import pipeline  # noqa: E402
from landscape.analysis import crowding, failures, mechanism  # noqa: E402
from landscape.models import Asset, DiseaseAssociation, Trial  # noqa: E402

FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "TNFRSF13C.json",
)


class TestFailureClassification(unittest.TestCase):
    def test_negated_safety_is_not_a_safety_failure(self):
        """'No new safety signals' must not be read as a safety termination.

        This is the single most damaging false positive in the module: it
        inverts the conclusion, turning a portfolio decision into evidence
        that the target is toxic.
        """
        label, _, _ = failures.classify_reason(
            "Sponsor decision to discontinue the programme. "
            "No new safety signals were identified."
        )
        self.assertNotEqual(label, "safety")
        self.assertEqual(label, "business")

    def test_bar_miss_despite_efficacy_is_business(self):
        label, _, also = failures.classify_reason(
            "Study did not meet the target criteria for progression despite "
            "demonstrating efficacy versus placebo."
        )
        self.assertEqual(label, "business")
        # The efficacy reading is real too and must stay visible.
        self.assertIn("efficacy", also)

    def test_genuine_efficacy_failure_is_science(self):
        label, _, _ = failures.classify_reason(
            "Terminated following interim analysis for futility; lack of efficacy."
        )
        self.assertEqual(label, "efficacy")

    def test_genuine_safety_failure_is_science(self):
        label, _, _ = failures.classify_reason(
            "Study halted due to unacceptable hepatic toxicity observed at the "
            "highest dose level."
        )
        self.assertEqual(label, "safety")

    def test_recruitment_is_not_science(self):
        label, _, _ = failures.classify_reason("Slow accrual; insufficient enrollment.")
        self.assertEqual(label, "recruitment")

    def test_empty_reason_is_unknown(self):
        self.assertEqual(failures.classify_reason("")[0], "unknown")

    def test_only_stopped_trials_are_classified(self):
        trials = [
            Trial(nct_id="NCT1", status="COMPLETED", why_stopped="lack of efficacy"),
            Trial(nct_id="NCT2", status="TERMINATED", why_stopped="lack of efficacy"),
        ]
        failures.annotate(trials)
        self.assertEqual(trials[0].failure_class, "")
        self.assertEqual(trials[1].failure_class, "efficacy")


class TestDiseaseMatching(unittest.TestCase):
    """EFO terms versus sponsor free text — where the whitespace screen breaks."""

    def assertMatches(self, a: str, b: str):
        self.assertTrue(
            crowding.same_disease(crowding.disease_key(a), crowding.disease_key(b)),
            f"expected '{a}' to match '{b}'",
        )

    def assertDiffers(self, a: str, b: str):
        self.assertFalse(
            crowding.same_disease(crowding.disease_key(a), crowding.disease_key(b)),
            f"expected '{a}' NOT to match '{b}'",
        )

    def test_syndrome_versus_disease(self):
        self.assertMatches("Sjogren syndrome", "Sjogren's Disease")

    def test_inflectional_variants(self):
        self.assertMatches("immune thrombocytopenic purpura", "Immune Thrombocytopenia")

    def test_lupus_variants_are_distinct(self):
        # The failure that matters: reporting lupus nephritis as untouched
        # because an SLE asset exists, or vice versa.
        self.assertDiffers("systemic lupus erythematosus", "Lupus Nephritis")

    def test_shared_leading_word_is_not_a_match(self):
        self.assertDiffers("multiple sclerosis", "Multiple Myeloma")

    def test_case_and_punctuation_insensitive(self):
        self.assertMatches("B-cell non-Hodgkin lymphoma", "B-Cell Non Hodgkin Lymphoma")


class TestMechanismClassification(unittest.TestCase):
    def test_afucosylated_antibody_is_depleting(self):
        asset = Asset(
            name="Ianalumab",
            modality="Antibody",
            mechanism_text="Afucosylated IgG1 anti-BAFF-R antibody; ADCC-mediated "
            "B cell depletion plus blockade of BAFF-R signalling.",
        )
        asset.modality = mechanism.classify_modality(asset)
        self.assertEqual(mechanism.classify_mechanism(asset), "Depleting antibody (ADCC/CDC)")

    def test_plain_blocking_antibody(self):
        asset = Asset(
            name="Examplemab",
            modality="Antibody",
            action_type="ANTAGONIST",
            mechanism_text="Blocks ligand binding to the receptor.",
        )
        asset.modality = mechanism.classify_modality(asset)
        self.assertEqual(mechanism.classify_mechanism(asset), "Blocking antibody")

    def test_inn_stem_identifies_ligand_trap(self):
        asset = Asset(name="Atacicept", modality="")
        self.assertEqual(mechanism.classify_modality(asset), "Fc-fusion / ligand trap")

    def test_car_t_text_beats_mab_stem(self):
        """A bispecific CAR-T must not be filed as an antibody."""
        asset = Asset(
            name="Bispecific BAFF-R/BCMA CAR-T",
            mechanism_text="Bispecific chimeric antigen receptor T cells.",
        )
        asset.modality = mechanism.classify_modality(asset)
        self.assertEqual(asset.modality, "Cell therapy (CAR-T)")
        self.assertEqual(mechanism.classify_mechanism(asset), "Cell therapy — bispecific CAR")

    def test_unresolved_assets_are_flagged_for_review(self):
        asset = Asset(name="XYZ-123", modality="")
        mechanism.annotate([asset])
        self.assertIn(asset, mechanism.unresolved([asset]))


class TestCrowding(unittest.TestCase):
    def test_phase_weighting_beats_a_flat_count(self):
        """One Phase 3 competitor outweighs three Phase 1s.

        The weights deliberately price a Phase 3 at exactly four Phase 1s
        (3.0 vs 4 x 0.75), so this asserts the boundary from below. If the
        weights in config.py are retuned, this test is the thing that says so.
        """
        one_phase3 = [Asset(name="A", max_phase=3)]
        three_phase1 = [Asset(name=f"A{i}", max_phase=1) for i in range(3)]
        self.assertGreater(
            crowding.score_crowding(one_phase3)["weighted_score"],
            crowding.score_crowding(three_phase1)["weighted_score"],
        )
        four_phase1 = [Asset(name=f"B{i}", max_phase=1) for i in range(4)]
        self.assertEqual(
            crowding.score_crowding(one_phase3)["weighted_score"],
            crowding.score_crowding(four_phase1)["weighted_score"],
        )

    def test_dormant_assets_are_excluded_from_density(self):
        assets = [Asset(name="A", max_phase=2), Asset(name="B", max_phase=2, is_active=False)]
        result = crowding.score_crowding(assets)
        self.assertEqual(result["n_active"], 1)
        self.assertEqual(result["n_dormant"], 1)
        self.assertEqual(result["weighted_score"], 1.5)

    def test_indication_phase_comes_from_trials_not_asset_maximum(self):
        """An asset in Phase 3 for one disease is not Phase 3 for all of them."""
        asset = Asset(
            name="A",
            max_phase=3,
            indications=["Disease X", "Disease Y"],
            trials=["NCT1", "NCT2"],
            mechanism_class="Blocking antibody",
        )
        trials = [
            Trial(nct_id="NCT1", phase=3, conditions=["Disease X"]),
            Trial(nct_id="NCT2", phase=2, conditions=["Disease Y"]),
        ]
        rows = {r["indication"]: r for r in crowding.indication_matrix([asset], trials)["rows"]}
        self.assertEqual(rows["Disease X"]["cells"]["Blocking antibody"], 3)
        self.assertEqual(rows["Disease Y"]["cells"]["Blocking antibody"], 2)

    def test_whitespace_requires_both_association_and_genetic_evidence(self):
        strong_no_genetics = DiseaseAssociation("EFO_1", "disease one", score=0.9, genetic_score=0.0)
        weak_with_genetics = DiseaseAssociation("EFO_2", "disease two", score=0.1, genetic_score=0.9)
        passes = DiseaseAssociation("EFO_3", "disease three", score=0.9, genetic_score=0.9)
        result = crowding.find_whitespace([], [strong_no_genetics, weak_with_genetics, passes])
        self.assertEqual([r["disease"] for r in result], ["disease three"])

    def test_whitespace_excludes_diseases_with_clinical_assets(self):
        association = DiseaseAssociation("EFO_1", "Sjogren syndrome", score=0.9, genetic_score=0.5)
        asset = Asset(name="A", max_phase=3, indications=["Sjogren's Disease"])
        self.assertEqual(crowding.find_whitespace([asset], [association]), [])


class TestFixturePipeline(unittest.TestCase):
    """End-to-end over the offline fixture — no network."""

    @classmethod
    def setUpClass(cls):
        cls.landscape = pipeline.load_fixture(FIXTURE)

    def test_renders_without_error(self):
        from landscape import render

        self.assertIn("TNFRSF13C", render.to_markdown(self.landscape))
        self.assertIn("<title>", render.to_html(self.landscape))

    def test_lead_asset_is_the_phase_3_antibody(self):
        self.assertEqual(self.landscape.assets[0].name, "Ianalumab")
        self.assertEqual(self.landscape.assets[0].max_phase, 3)

    def test_illustrative_fixture_carries_its_warning(self):
        """The memo must never present hand-entered data as a live pull."""
        self.assertTrue(any("Illustrative" in w for w in self.landscape.warnings))

    def test_cvid_surfaces_as_whitespace(self):
        diseases = [row["disease"] for row in self.landscape.whitespace]
        self.assertIn("common variable immunodeficiency", diseases)

    def test_indications_with_assets_are_not_whitespace(self):
        diseases = {row["disease"] for row in self.landscape.whitespace}
        self.assertNotIn("Sjogren syndrome", diseases)
        self.assertNotIn("rheumatoid arthritis", diseases)

    def test_hidradenitis_row_shows_phase_2_not_phase_3(self):
        rows = {r["indication"]: r for r in self.landscape.crowding["matrix"]["rows"]}
        self.assertEqual(max(rows["Hidradenitis Suppurativa"]["cells"].values()), 2)
        self.assertEqual(max(rows["Sjogren's Disease"]["cells"].values()), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestLicensing(unittest.TestCase):
    """Availability signals — the BD layer.

    These are judgements about whether an asset could be acquired, so the
    failure mode that matters is a confident wrong read: calling an active
    large-pharma Phase 3 available, or missing a shelved asset with data.
    """

    from landscape.analysis import licensing as lic  # noqa: E301

    def test_large_pharma_is_recognised_by_name(self):
        self.assertEqual(self.lic.sponsor_scale("Novartis Pharmaceuticals"), "Large pharma")
        self.assertEqual(self.lic.sponsor_scale("F. Hoffmann-La Roche Ltd"), "Large pharma")

    def test_academic_centres_without_obvious_names(self):
        """'City of Hope' contains none of the usual academic words."""
        self.assertEqual(self.lic.sponsor_scale("City of Hope"), "Academic or non-industry")
        self.assertEqual(self.lic.sponsor_scale("Dana-Farber"), "Academic or non-industry")

    def test_sponsor_class_overrides_an_unknown_name(self):
        self.assertEqual(
            self.lic.sponsor_scale("Some Unknown Body", "OTHER"), "Academic or non-industry"
        )

    def test_unrecognised_industry_name_is_small_or_private(self):
        self.assertEqual(
            self.lic.sponsor_scale("Luminary Therapeutics", "INDUSTRY"),
            "Small or private company",
        )

    def test_shelved_phase_2_asset_is_the_strongest_signal(self):
        asset = Asset(name="X", sponsor="Smallco", max_phase=2, is_active=False, trials=["NCT1"])
        trials = {"NCT1": Trial(nct_id="NCT1", status="TERMINATED", phase=2,
                                sponsor="Smallco", sponsor_class="INDUSTRY",
                                countries=["United States"])}
        result = self.lic.asset_signals(asset, trials)
        self.assertIn("shelved_with_data", [s["code"] for s in result["signals"]])
        # No overall read. The label this used to assert -- "Likely available" --
        # was a sum of hand-set weights presented as a finding.
        self.assertNotIn("read", result)
        self.assertNotIn("score", result)

    def test_active_large_pharma_asset_says_so_without_a_verdict(self):
        asset = Asset(name="Y", sponsor="Novartis Pharmaceuticals", max_phase=3,
                      is_active=True, trials=["NCT1"])
        trials = {"NCT1": Trial(nct_id="NCT1", status="RECRUITING", phase=3,
                                sponsor="Novartis Pharmaceuticals", sponsor_class="INDUSTRY",
                                countries=["United States", "Germany", "Japan", "China"])}
        result = self.lic.asset_signals(asset, trials)
        self.assertIn("large_active", [s["code"] for s in result["signals"]])
        self.assertTrue(result["is_active"])

    def test_territory_gap_needs_at_least_one_covered_market(self):
        """An asset with no trials has no territory signal — that is absence of
        data, not evidence about where rights sit."""
        asset = Asset(name="Z", sponsor="Smallco", max_phase=1, trials=[])
        codes = [s["code"] for s in self.lic.asset_signals(asset, {})["signals"]]
        self.assertNotIn("territory_gap", codes)
        self.assertIn("no_linked_trials", codes)

    def test_china_only_programme_flags_the_other_markets(self):
        asset = Asset(name="Z", sponsor="Smallco", max_phase=2, trials=["NCT1"])
        trials = {"NCT1": Trial(nct_id="NCT1", status="RECRUITING", phase=2,
                                sponsor="Smallco", sponsor_class="INDUSTRY",
                                countries=["China"])}
        signal = next(s for s in self.lic.asset_signals(asset, trials)["signals"]
                      if s["code"] == "territory_gap")
        self.assertIn("US", signal["headline"])
        self.assertIn("China", signal["evidence"])

    def test_every_signal_carries_its_evidence(self):
        """A signal with no evidence is exactly the black box this avoids."""
        landscape = pipeline.load_fixture(FIXTURE)
        for row in landscape.licensing["assets"]:
            for signal in row["signals"]:
                self.assertTrue(signal["evidence"].strip(), row["asset"])
                self.assertTrue(signal["headline"].strip(), row["asset"])

    def test_deals_match_assets_by_synonym(self):
        from landscape.models import Deal

        assets = [Asset(name="Ianalumab", synonyms=["VAY736"])]
        deals = [Deal(date="2024-01", acquirer="Acq", target_company="Tgt",
                      asset="VAY-736", stage_at_deal="Phase 2", upfront_usd_m=100.0)]
        matched = self.lic.match_deals(deals, assets)
        self.assertEqual(matched["n_matched"], 1)
        self.assertEqual(matched["deals"][0]["matched_asset"], "Ianalumab")

    def test_stage_medians_are_computed(self):
        from landscape.models import Deal

        deals = [
            Deal(date="2024-01", acquirer="A", target_company="T", asset="x",
                 stage_at_deal="Phase 2", upfront_usd_m=100.0),
            Deal(date="2024-02", acquirer="B", target_company="T", asset="y",
                 stage_at_deal="Phase 2", upfront_usd_m=300.0),
        ]
        stages = self.lic.match_deals(deals, [])["by_stage"]
        self.assertEqual(stages[0]["stage"], "Phase 2")
        self.assertEqual(stages[0]["median_upfront"], 200.0)

    def test_an_acquisition_price_is_not_averaged_into_asset_upfronts(self):
        """An acquisition buys a company — its platform, its cash, its other
        programmes. Averaging one into a column of licence upfronts reports a
        typical Phase 3 upfront that no Phase 3 asset ever cost. The row still
        shows; it is only kept out of the median."""
        from landscape.models import Deal

        deals = [
            Deal(date="2025-06", acquirer="Licensee", target_company="T", asset="x",
                 deal_type="licence", stage_at_deal="Phase 3", upfront_usd_m=125.0),
            Deal(date="2023-06", acquirer="Buyer", target_company="T", asset="y",
                 deal_type="acquisition", stage_at_deal="Phase 3", upfront_usd_m=3200.0),
        ]
        summary = self.lic.match_deals(deals, [])
        self.assertEqual(summary["n"], 2)
        self.assertEqual(summary["n_acquisitions"], 1)
        stages = summary["by_stage"]
        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["n"], 1)
        self.assertEqual(stages[0]["median_upfront"], 125.0)

    def test_a_deal_row_with_no_type_counts_as_a_licence(self):
        """Files written before the column existed keep working."""
        from landscape.models import Deal

        deals = [Deal(date="2024-01", acquirer="A", target_company="T", asset="x",
                      stage_at_deal="Phase 2", upfront_usd_m=100.0)]
        summary = self.lic.match_deals(deals, [])
        self.assertEqual(summary["n_acquisitions"], 0)
        self.assertEqual(summary["by_stage"][0]["median_upfront"], 100.0)

    def test_the_curated_deal_files_parse_and_carry_a_source(self):
        """These are shown in interviews. A figure with no source is not
        usable in a memo, and a malformed row would fail silently."""
        from landscape import store

        for symbol in ("TNFRSF13C", "PDCD1"):
            deals = store.load_deals(symbol)
            self.assertTrue(deals, symbol)
            for deal in deals:
                self.assertTrue(deal.source_url.startswith("https://"), deal.asset)
                self.assertIn(deal.deal_type, {"licence", "acquisition"}, deal.asset)
                self.assertIsNotNone(deal.upfront_usd_m, deal.asset)

    def test_narrative_is_honest_when_no_deals_are_curated(self):
        landscape = pipeline.load_fixture(FIXTURE)
        text = self.lic.narrative(landscape.licensing)
        self.assertIn("no free deal database", text)
        self.assertIn("not knowledge of any agreement", text)


class TestTargetIndex(unittest.TestCase):
    """Search has to work on the names people type, not just approved symbols."""

    from landscape import targets as idx  # noqa: E301

    def test_index_is_populated(self):
        self.assertGreater(self.idx.size(), 100)

    def test_common_aliases_resolve_to_approved_symbols(self):
        cases = {
            "HER2": "ERBB2",
            "PD-1": "PDCD1",
            "PD-L1": "CD274",
            "BAFF-R": "TNFRSF13C",
            "TL1A": "TNFSF15",
            "BCMA": "TNFRSF17",
            "CD20": "MS4A1",
            "SGLT2": "SLC5A2",
        }
        for alias, symbol in cases.items():
            self.assertEqual(self.idx.resolve_alias(alias), symbol, alias)

    def test_punctuation_and_case_are_ignored(self):
        for spelling in ["BAFF-R", "baffr", "baff r", "BaFf-R"]:
            self.assertEqual(self.idx.resolve_alias(spelling), "TNFRSF13C", spelling)

    def test_exact_symbol_outranks_everything_else(self):
        """'MET' must return MET first, not genes whose name contains 'met'."""
        self.assertEqual(self.idx.search("MET")[0]["symbol"], "MET")

    def test_name_matching_respects_word_boundaries(self):
        """A bare substring makes MET match 'methyltransferase'."""
        symbols = [r["symbol"] for r in self.idx.search("MET", limit=20)]
        self.assertEqual(symbols[0], "MET")

    def test_alias_hit_reports_what_it_matched_on(self):
        hit = self.idx.search("HER2")[0]
        self.assertEqual(hit["symbol"], "ERBB2")
        self.assertEqual(hit["matched_on"], "HER2")

    def test_unknown_query_returns_nothing_rather_than_guessing(self):
        self.assertEqual(self.idx.search("zzzznotagene"), [])
        self.assertIsNone(self.idx.resolve_alias("zzzznotagene"))

    def test_browse_filters_by_area(self):
        immunology = self.idx.browse("immunology")
        self.assertTrue(immunology)
        for record in immunology:
            self.assertIn("immunology", record["areas"])

    def test_an_ambiguous_nickname_resolves_to_the_drug_target(self):
        """PD1 is an alias of PDCD1, of SNCA (the Parkinson disease 1 locus)
        and of SPATA2. Shortest-symbol-wins served alpha-synuclein for "PD-1",
        which is not a near miss — it is a different field of medicine, and it
        was the first thing a viewer would type into this tool."""
        for spelling in ["PD-1", "PD1", "pd 1"]:
            self.assertEqual(self.idx.resolve_alias(spelling), "PDCD1", spelling)

    def test_the_dropdown_orders_an_ambiguous_nickname_the_same_way(self):
        """The list is where the reader chooses, so the ordering has to agree
        with the resolver — and the alternatives stay visible rather than
        being filtered away."""
        symbols = [r["symbol"] for r in self.idx.search("PD-1", limit=5)]
        self.assertEqual(symbols[0], "PDCD1")
        self.assertIn("SNCA", symbols)

    def test_an_exact_symbol_still_outranks_a_better_nicknamed_alias(self):
        """The tie-break runs inside a band, never across one."""
        self.assertEqual(self.idx.search("MET")[0]["symbol"], "MET")
        self.assertEqual(self.idx.resolve_alias("CD20"), "MS4A1")

    def test_every_symbol_looks_like_an_approved_symbol(self):
        """A protein nickname stored as a symbol resolves to nothing downstream."""
        import re

        for record in self.idx.browse(limit=100000):
            self.assertRegex(record["symbol"], r"^[A-Z][A-Z0-9-]{1,14}$")

    def test_browse_puts_drug_targets_before_the_rest_of_the_genome(self):
        """After the HGNC merge the index is ~28k genes, mostly not targets.

        Alphabetical order puts A1BG and A1BG-AS1 on the landing page, which
        tells a visitor nothing. The seeded drug targets have to lead.
        """
        records = [
            {"symbol": "A1BG", "name": "alpha-1-B glycoprotein", "aliases": [],
             "areas": [], "source": "hgnc"},
            {"symbol": "ZZZ3", "name": "zinc finger", "aliases": [], "areas": [],
             "source": "hgnc"},
            {"symbol": "ERBB2", "name": "erb-b2", "aliases": ["HER2"],
             "areas": ["oncology"], "source": "hgnc+seed"},
        ]
        with mock.patch.object(self.idx, "_load", return_value={
            "records": records,
            "by_symbol": {r["symbol"]: r for r in records},
            "by_key": {}, "areas": {"oncology": 1},
        }):
            order = [r["symbol"] for r in self.idx.browse(limit=10)]
            self.assertEqual(order[0], "ERBB2")
            self.assertEqual(self.idx.seeded_count(), 1)


class TestTextHygiene(unittest.TestCase):
    """Broken characters from the registries, kept off the page."""

    def setUp(self):
        from landscape import normalize

        self.normalize = normalize

    def test_a_replacement_character_is_dropped_not_rendered(self):
        """Real, from the PDCD1 build: the condition "PD-L1 TPS �00066%",
        where a greater-than-or-equal sign lost its encoding upstream of
        ClinicalTrials.gov. It renders as a black diamond and makes a whole
        indication row unreadable."""
        self.assertEqual(
            self.normalize.clean_text("PD-L1 TPS �00066%"), "PD-L1 TPS 00066%"
        )

    def test_control_characters_go_too(self):
        self.assertEqual(self.normalize.clean_text("a\x00b\x1fc"), "abc")

    def test_ordinary_text_including_unicode_is_untouched(self):
        """Dropping every non-ASCII character would be a much worse fix: the
        registries carry real accented sponsor names and Greek letters."""
        for value in ("Sjögren's Disease", "TNF-α blockade", "Böehringer"):
            self.assertEqual(self.normalize.clean_text(value), value)

    def test_a_stored_landscape_is_cleaned_on_load(self):
        """Files written before the cleaner existed still carry the broken
        characters, and rebuilding them all to fix a punctuation mark is the
        wrong trade."""
        from landscape.models import Asset, Trial

        trial = Trial(nct_id="NCT1", conditions=["PD-L1 TPS �00066%"])
        asset = Asset(name="x", indications=["PD-L1 TPS �00066%"])
        self.normalize.clean_trial_text(trial)
        self.normalize.clean_asset_text(asset)
        self.assertNotIn("�", trial.conditions[0])
        self.assertNotIn("�", asset.indications[0])

    def test_open_targets_joins_a_place_and_a_topology_into_one_string(self):
        """"Cell membrane ; Single-pass type I membrane protein" is two
        statements of different kinds: where the protein is, and how it sits
        in the membrane. Joined, they rendered with a floating semicolon and
        read as two addresses."""
        places, topology = self.normalize.split_locations(
            ["Cell membrane ; Single-pass type I membrane protein"])
        self.assertEqual(places, ["Cell membrane"])
        self.assertEqual(topology, ["Single-pass type I membrane protein"])

    def test_a_prediction_is_not_a_location(self):
        """IL23A carried "Cytosol, Predicted to be secreted, Secreted". A
        model's guess must not fill the gap that makes the modality check say
        "cannot tell", and it must never reach that verdict."""
        places, topology = self.normalize.split_locations(
            ["Cytosol", "Predicted to be secreted", "Secreted"])
        self.assertEqual(places, ["Cytoplasm", "Secreted"])
        self.assertEqual(topology, [])

    def test_the_two_atlases_do_not_name_one_place_twice(self):
        """Open Targets carries Human Protein Atlas imaging terms alongside
        UniProt's, so a kinase listed "Nucleoli fibrillar center, Nucleoplasm"
        was showing the nucleus twice in laboratory vocabulary."""
        places, _ = self.normalize.split_locations(
            ["Cytoplasm", "Nucleoplasm", "Plasma membrane", "Vesicles"])
        self.assertEqual(places, ["Cytoplasm", "Nucleus", "Cell membrane", "Vesicle"])

    def test_the_header_preview_reads_the_shape_compose_returns(self):
        """scripts/backfill_annotation.py prints a preview of the header, and
        it read compose()["text"] long after compose stopped returning a
        paragraph. Every run of 4-ADD-TARGET.bat ended in a KeyError after the
        build had already succeeded, which reads as a failed build."""
        import os
        import sys

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(root, "scripts"))
        import backfill_annotation  # noqa: E402

        source = open(backfill_annotation.__file__, encoding="utf-8").read()
        for stale in ('shown["text"]', 'shown["words"]', 'shown["segments"]'):
            self.assertNotIn(stale, source,
                             f"the preview still reads {stale}, which compose() "
                             "no longer returns")

    def test_a_place_named_at_two_levels_of_detail_keeps_the_specific_one(self):
        places, _ = self.normalize.split_locations(
            ["Cell Junctions", "Cell junction, tight junction"])
        self.assertEqual(places, ["Cell junction, tight junction"])

    def test_a_single_location_survives_and_duplicates_collapse(self):
        self.assertEqual(
            self.normalize.clean_locations(["Nucleus", "Nucleus", " Cytoplasm "]),
            ["Nucleus", "Cytoplasm"])

    def test_a_space_before_a_semicolon_never_reaches_the_reader(self):
        """The same join turns up in combination-therapy asset names."""
        self.assertEqual(self.normalize.clean_text("Canakinumab ; spartalizumab"),
                         "Canakinumab; spartalizumab")
