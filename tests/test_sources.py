"""Parser contract tests for the three source adapters.

These run with no network. They exist because the retrieval path is the part
of this tool most likely to break without anyone noticing: the public APIs
change field names between releases, and a parser that starts returning empty
lists produces a memo that looks fine and says nothing.

Each test pins one parsing decision against a realistic payload from
``tests/payloads.py``, including the malformed shapes these APIs actually
emit — null phases, missing modules, records with no identifier.
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import normalize  # noqa: E402
from landscape.http import HTTPError  # noqa: E402
from landscape.sources import chembl as chembl_src  # noqa: E402
from landscape.sources import ctgov as ctgov_src  # noqa: E402
from landscape.sources import europepmc as pmc_src  # noqa: E402
from landscape.sources import opentargets as ot_src  # noqa: E402
from landscape.sources import uniprot as uniprot_src  # noqa: E402
from landscape.models import Asset, Provenance, Target, Trial  # noqa: E402
from tests import payloads  # noqa: E402


class TestOpenTargets(unittest.TestCase):
    def test_resolve_prefers_exact_symbol_over_paralogue(self):
        """/search is fuzzy and returns family members. Exact match must win."""
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_SEARCH):
            self.assertEqual(ot_src.resolve_target("TNFRSF13C"), "ENSG00000159958")

    def test_resolve_passes_through_an_ensembl_id(self):
        # No network call should be needed at all.
        with mock.patch.object(ot_src, "post_json", side_effect=AssertionError("called")):
            self.assertEqual(ot_src.resolve_target("ENSG00000159958"), "ENSG00000159958")

    def test_target_keeps_only_true_tractability_buckets(self):
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_TARGET):
            target = ot_src.fetch_target("ENSG00000159958")
        self.assertEqual(target.symbol, "TNFRSF13C")
        self.assertIn("AB", target.tractability)
        # value: False means the target is not in that bucket.
        self.assertNotIn("SM", target.tractability)
        self.assertEqual(len(target.tractability["AB"]), 2)
        self.assertIn("Advanced Clinical", target.tractability["AB"])

    def test_target_drops_empty_synonyms_and_takes_first_function(self):
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_TARGET):
            target = ot_src.fetch_target("ENSG00000159958")
        self.assertEqual(target.synonyms, ["BAFF-R", "BR3", "CD268"])
        self.assertTrue(target.function.startswith("Receptor for TNFSF13B"))

    def test_platform_26_candidates_shape(self):
        """The 26.x schema: string phases, nested trials, one row per drug."""
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_CANDIDATES):
            assets, ncts = ot_src.fetch_known_drugs("ENSG00000159958")
        by_name = {a.name: a for a in assets}
        self.assertEqual(len(assets), 2)

        ianalumab = by_name["IANALUMAB"]
        self.assertEqual(ianalumab.max_phase, 3)
        self.assertEqual(ianalumab.chembl_id, "CHEMBL4594357")
        self.assertEqual(ianalumab.action_type, "BINDING AGENT")
        self.assertIn("binding agent", ianalumab.mechanism_text)
        # Same disease from two source spellings must fold to one indication.
        self.assertEqual(ianalumab.indications.count("Sjogren syndrome"), 1)
        self.assertEqual(sorted(ianalumab.trials), ["NCT03827798", "NCT05350072"])

        self.assertEqual(by_name["EXAMPLEMAB"].max_phase, 0)
        self.assertEqual(sorted(ncts), ["NCT03827798", "NCT05350072"])

    def test_literature_records_do_not_become_trial_ids(self):
        """clinicalReports mixes registries and literature; only NCT ids count."""
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_CANDIDATES):
            _, ncts = ot_src.fetch_known_drugs("ENSG00000159958")
        self.assertNotIn("PMID12345678", ncts)

    def test_phase_parsing_handles_both_schemas(self):
        cases = {3: 3, "PHASE_3": 3, "PRECLINICAL": 0, "EARLY_PHASE1": 1,
                 "APPROVED": 4, "PHASE_1_2": 2, None: -1, "": -1, "nonsense": -1}
        for value, expected in cases.items():
            self.assertEqual(ot_src._phase_to_int(value), expected, repr(value))

    def test_known_drugs_fold_rows_into_one_asset_per_drug(self):
        rows = payloads.OT_KNOWN_DRUGS["data"]["target"]["knownDrugs"]["rows"]
        assets, ncts = ot_src._assets_from_known_drugs(rows)
        by_id = {a.drug_id: a for a in assets}
        self.assertEqual(len(assets), 2)
        ianalumab = by_id["CHEMBL4297516"]
        # Three rows, two diseases, max phase wins over the later lower phase.
        self.assertEqual(ianalumab.max_phase, 3)
        self.assertEqual(len(ianalumab.indications), 2)
        self.assertEqual(sorted(ianalumab.trials), ["NCT03827798", "NCT05349214", "NCT05350072"])
        self.assertEqual(sorted(ncts), ["NCT03827798", "NCT05349214", "NCT05350072"])

    def test_null_phase_degrades_to_unknown(self):
        rows = payloads.OT_KNOWN_DRUGS["data"]["target"]["knownDrugs"]["rows"]
        assets, _ = ot_src._assets_from_known_drugs(rows)
        example = next(a for a in assets if a.drug_id == "CHEMBL9999999")
        self.assertEqual(example.max_phase, -1)
        self.assertEqual(example.phase_label, "Unknown")

    def test_associations_extract_the_genetic_component(self):
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_ASSOCIATIONS):
            associations = ot_src.fetch_associations("ENSG00000159958")
        self.assertEqual(associations[0].genetic_score, 0.42)
        # No genetic datatype present at all.
        self.assertEqual(associations[1].genetic_score, 0.0)

    def test_graphql_errors_are_raised_not_swallowed(self):
        """Schema drift must surface, so the pipeline can record a warning."""
        with mock.patch.object(ot_src, "post_json", return_value=payloads.OT_ERROR):
            with self.assertRaises(HTTPError) as ctx:
                ot_src.fetch_target("ENSG00000159958")
        self.assertIn("tractability", str(ctx.exception))


class TestChEMBL(unittest.TestCase):
    def test_target_search_keeps_only_single_human_proteins(self):
        with mock.patch.object(chembl_src, "get_json", return_value=payloads.CHEMBL_TARGET_SEARCH):
            ids = chembl_src.find_target_ids("TNFRSF13C")
        self.assertEqual(ids, ["CHEMBL1795194"])

    def test_target_search_requires_the_symbol_in_synonyms(self):
        """/target/search is full text; a description hit is not a match."""
        payload = {
            "targets": [
                {
                    "target_chembl_id": "CHEMBL111",
                    "pref_name": "Unrelated kinase",
                    "organism": "Homo sapiens",
                    "target_type": "SINGLE PROTEIN",
                    "target_components": [
                        {"target_component_synonyms": [{"component_synonym": "ABL1"}]}
                    ],
                }
            ]
        }
        with mock.patch.object(chembl_src, "get_json", return_value=payload):
            self.assertEqual(chembl_src.find_target_ids("TNFRSF13C"), [])

    def test_mechanisms_key_by_molecule(self):
        with mock.patch.object(chembl_src, "get_json", return_value=payloads.CHEMBL_MECHANISMS):
            mechanisms = chembl_src.fetch_mechanisms(["CHEMBL1795194"])
        self.assertEqual(mechanisms["CHEMBL4297516"]["action_type"], "ANTAGONIST")

    def test_molecules_parse_synonyms_and_flags(self):
        with mock.patch.object(chembl_src, "get_json", return_value=payloads.CHEMBL_MOLECULES):
            molecules = chembl_src.fetch_molecules(["CHEMBL4297516"])
        record = molecules["CHEMBL4297516"]
        self.assertEqual(record["molecule_type"], "Antibody")
        self.assertFalse(record["withdrawn_flag"])
        self.assertIn("VAY-736", record["synonyms"])

    def test_phase_handles_floats_and_none(self):
        self.assertEqual(chembl_src.phase_to_int(3.0), 3)
        self.assertEqual(chembl_src.phase_to_int("4"), 4)
        self.assertEqual(chembl_src.phase_to_int(None), -1)
        self.assertEqual(chembl_src.phase_to_int("not a phase"), -1)

    def test_search_failure_returns_empty_not_an_exception(self):
        """ChEMBL is enrichment; losing it must not abort a run."""
        with mock.patch.object(chembl_src, "get_json", side_effect=HTTPError("503")):
            self.assertEqual(chembl_src.find_target_ids("TNFRSF13C"), [])


class TestClinicalTrials(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(ctgov_src, "get_json", return_value=payloads.CTGOV_PAGE)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.trials = {t.nct_id: t for t in ctgov_src.search_trials(["ianalumab", "BAFF-R"])}

    def test_records_without_an_identifier_are_dropped(self):
        self.assertEqual(len(self.trials), 3)
        self.assertNotIn("", self.trials)

    def test_non_drug_interventions_are_excluded(self):
        interventions = self.trials["NCT05350072"].interventions
        self.assertIn("Ianalumab", interventions)
        self.assertIn("VAY736", interventions)  # otherNames are kept
        self.assertNotIn("Salivary gland biopsy", interventions)

    def test_why_stopped_is_stripped(self):
        why = self.trials["NCT03827798"].why_stopped
        self.assertTrue(why.startswith("Study did not meet"))
        self.assertFalse(why.endswith(" "))

    def test_countries_are_deduplicated(self):
        self.assertEqual(self.trials["NCT05350072"].countries, ["Japan", "United States"])

    def test_sparse_record_parses_with_defaults(self):
        """No sponsor module, no interventions, no locations, phase NA."""
        sparse = self.trials["NCT00000001"]
        self.assertEqual(sparse.phase, -1)
        self.assertEqual(sparse.sponsor, "")
        self.assertEqual(sparse.interventions, [])
        self.assertEqual(sparse.countries, [])
        self.assertIsNone(sparse.enrollment)

    def test_phase_takes_the_maximum_of_a_multi_phase_study(self):
        self.assertEqual(ctgov_src._phases_to_int(["PHASE1", "PHASE2"]), 2)
        self.assertEqual(ctgov_src._phases_to_int(["EARLY_PHASE1"]), 1)
        self.assertEqual(ctgov_src._phases_to_int([]), -1)
        self.assertEqual(ctgov_src._phases_to_int(None), -1)

    def test_search_with_no_usable_terms_makes_no_call(self):
        with mock.patch.object(ctgov_src, "get_json", side_effect=AssertionError("called")):
            self.assertEqual(ctgov_src.search_trials(["a", "", "xy"]), [])


class TestReconciliation(unittest.TestCase):
    """The join between sources — where double counting comes from."""

    def test_dose_and_formulation_noise_is_stripped_from_the_key(self):
        self.assertEqual(
            normalize._name_key("VAY736 300 mg SC monthly"),
            normalize._name_key("VAY736"),
        )

    def test_trials_attach_by_intervention_name(self):
        from landscape.models import Asset, Trial

        asset = Asset(name="Ianalumab", synonyms=["VAY736"])
        trials = [
            Trial(
                nct_id="NCT1",
                phase=3,
                sponsor="Novartis",
                sponsor_class="INDUSTRY",
                status="RECRUITING",
                conditions=["Sjogren's Disease"],
                interventions=["VAY736 300 mg"],
            )
        ]
        unmatched = normalize.attach_trials([asset], trials)
        self.assertEqual(unmatched, [])
        self.assertEqual(asset.trials, ["NCT1"])
        self.assertEqual(asset.max_phase, 3)
        self.assertEqual(asset.sponsor, "Novartis")

    def test_unmatched_trials_become_discovered_assets(self):
        from landscape.models import Trial

        trials = [
            Trial(
                nct_id="NCT2",
                phase=1,
                sponsor="Some Hospital",
                sponsor_class="OTHER",
                status="RECRUITING",
                conditions=["B-cell Lymphoma"],
                interventions=["BAFFR CAR-T cells", "Placebo"],
            )
        ]
        discovered = normalize.discover_assets_from_trials(trials, set())
        names = {a.name for a in discovered}
        self.assertIn("BAFFR CAR-T cells", names)
        # Placebo must never become an asset.
        self.assertFalse(any("placebo" in n.lower() for n in names))

    def test_dedupe_merges_assets_sharing_a_synonym(self):
        from landscape.models import Asset

        merged = normalize.dedupe([
            Asset(name="Ianalumab", max_phase=2, synonyms=["VAY736"]),
            Asset(name="VAY736", max_phase=3, indications=["Lupus Nephritis"]),
        ])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].max_phase, 3)
        self.assertIn("Lupus Nephritis", merged[0].indications)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestDoctor(unittest.TestCase):
    """The pre-flight check has to be fast and has to not lie."""

    def test_fail_fast_restores_the_normal_retry_policy(self):
        from landscape import doctor, http as http_mod

        before = (http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT)
        with doctor.fail_fast():
            self.assertEqual(http_mod.MAX_RETRIES, 1)
        self.assertEqual((http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT), before)

    def test_fail_fast_restores_even_when_a_probe_raises(self):
        from landscape import doctor, http as http_mod

        before = (http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT)
        with self.assertRaises(ValueError):
            with doctor.fail_fast():
                raise ValueError("boom")
        self.assertEqual((http_mod.MAX_RETRIES, http_mod.REQUEST_TIMEOUT), before)

    def test_a_returned_string_is_a_warning_not_a_failure(self):
        from landscape import doctor

        check = doctor._run("probe", "fix it", lambda: "something is thin")
        self.assertEqual(check.status, doctor.WARN)
        self.assertIn("thin", check.detail)

    def test_a_raised_error_is_a_failure_carrying_the_fix(self):
        from landscape import doctor

        def boom():
            raise HTTPError("field 'tractability' does not exist")

        check = doctor._run("probe", "update _TARGET_QUERY", boom)
        self.assertEqual(check.status, doctor.FAIL)
        self.assertIn("tractability", check.detail)
        self.assertIn("_TARGET_QUERY", check.report())

    def test_clean_probe_is_ok(self):
        from landscape import doctor

        self.assertEqual(doctor._run("probe", "fix", lambda: None).status, doctor.OK)


class TestEuropePMC(unittest.TestCase):
    """The reading list.

    Metadata only, on purpose: abstracts are under publisher terms and a tool
    that stores them for redistribution has a licensing problem it does not
    need.
    """

    def test_records_carry_a_link_and_a_citation_count(self):
        with mock.patch.object(pmc_src, "get_json", return_value=payloads.EUROPEPMC_SEARCH):
            rows = pmc_src.reviews("TNFRSF13C", ["BAFF-R"])
        self.assertEqual(rows[0]["citations"], 412)
        self.assertIn("europepmc.org/article/MED/31234567", rows[0]["url"])
        self.assertTrue(rows[0]["open_access"])

    def test_a_record_with_no_identifiers_does_not_crash_the_parser(self):
        with mock.patch.object(pmc_src, "get_json", return_value=payloads.EUROPEPMC_SEARCH):
            rows = pmc_src.reviews("TNFRSF13C")
        unlinkable = [r for r in rows if r["title"].startswith("A preprint")]
        self.assertEqual(len(unlinkable), 1)
        self.assertEqual(unlinkable[0]["url"], "")
        self.assertEqual(unlinkable[0]["citations"], 0)

    def test_no_abstract_text_is_ever_stored(self):
        with mock.patch.object(pmc_src, "get_json", return_value=payloads.EUROPEPMC_SEARCH):
            rows = pmc_src.reviews("TNFRSF13C")
        for row in rows:
            self.assertNotIn("abstract", row)

    def test_reviews_are_ranked_by_citation_count(self):
        with mock.patch.object(pmc_src, "get_json", return_value=payloads.EUROPEPMC_SEARCH):
            rows = pmc_src.reviews("TNFRSF13C")
        self.assertEqual([r["citations"] for r in rows], sorted(
            [r["citations"] for r in rows], reverse=True))

    def test_the_query_searches_titles_and_abstracts_not_full_text(self):
        # A gene mentioned once in a methods section is not a paper about the
        # target, and full-text search returns thousands of them.
        seen = {}

        def capture(url, params=None):
            seen["query"] = (params or {}).get("query", "")
            return payloads.EUROPEPMC_SEARCH

        with mock.patch.object(pmc_src, "get_json", side_effect=capture):
            pmc_src.reviews("TNFRSF13C", ["BAFF-R"])
        self.assertIn('TITLE_ABS:"TNFRSF13C"', seen["query"])
        self.assertIn('TITLE_ABS:"BAFF-R"', seen["query"])
        self.assertIn('PUB_TYPE:"review"', seen["query"])

    def test_mechanism_papers_are_windowed_before_they_are_ranked(self):
        # Sorting a target's whole literature by citations returns the same
        # foundational papers for every gene and says nothing about where the
        # field is now.
        seen = {}

        def capture(url, params=None):
            seen["query"] = (params or {}).get("query", "")
            return payloads.EUROPEPMC_SEARCH

        with mock.patch.object(pmc_src, "get_json", side_effect=capture):
            pmc_src.mechanism_papers("TNFRSF13C", years=5)
        self.assertIn("FIRST_PDATE:[", seen["query"])

    def test_an_outage_returns_an_empty_list_rather_than_failing_the_build(self):
        with mock.patch.object(pmc_src, "get_json", side_effect=HTTPError("503")):
            self.assertEqual(pmc_src.reviews("TNFRSF13C"), [])
            self.assertEqual(pmc_src.mechanism_papers("TNFRSF13C"), [])


class TestCtgovDesignFields(unittest.TestCase):
    """Design and endpoint parsing.

    These fields are what let the tool say, before a trial reports, whether
    its result will mean anything. A rename upstream would turn every trial
    into "design not stated" — a page full of shrugs that still looks like it
    is working.
    """

    def parse(self):
        return [t for t in (ctgov_src._parse_study(s)
                            for s in payloads.CTGOV_DESIGN_PAGE["studies"]) if t]

    def test_design_fields_are_normalised_to_upper_case(self):
        trial = self.parse()[0]
        self.assertEqual(trial.allocation, "RANDOMIZED")
        self.assertEqual(trial.masking, "QUADRUPLE")
        self.assertEqual(trial.intervention_model, "PARALLEL")
        self.assertEqual(trial.completion_date_type, "ESTIMATED")

    def test_blank_endpoint_measures_are_dropped(self):
        trial = self.parse()[0]
        self.assertEqual(trial.primary_outcomes,
                         ["Complete renal response rate at week 52"])

    def test_a_record_with_no_design_module_leaves_the_fields_empty(self):
        # Empty, not defaulted: "no design registered" and "not randomised"
        # are different statements and the analysis depends on the difference.
        trial = self.parse()[1]
        self.assertEqual(trial.allocation, "")
        self.assertEqual(trial.masking, "")
        self.assertEqual(trial.primary_outcomes, [])

    def test_an_estimated_completion_date_is_flagged_as_an_estimate(self):
        trial = self.parse()[0]
        self.assertNotEqual(trial.completion_date_type, "ACTUAL")
        self.assertEqual(trial.completion_date, "2027-06")


class TestUniProt(unittest.TestCase):
    """The header brief. Every test here is a wrong paragraph avoided."""

    def fetch(self):
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_SEARCH):
            return uniprot_src.fetch("TNFRSF13C")

    def test_exact_gene_name_wins_over_a_paralogue_listed_first(self):
        """``gene:`` is not exact. The first hit here is TNFRSF13B, which
        merely carries this symbol as a synonym — printing its function under
        this target's name is worse than printing nothing."""
        record = self.fetch()
        self.assertEqual(record["accession"], "Q96RJ3")
        self.assertIn("TNFSF13B", record["function"][0]["text"])

    def test_inline_evidence_markers_become_links_not_prose(self):
        record = self.fetch()
        text = record["function"][0]["text"]
        self.assertNotIn("PubMed:", text)
        self.assertNotIn("By similarity", text)
        self.assertNotIn("{ECO:", text)
        # …and the identifiers survive as citations rather than being dropped.
        for pmid in ("11460154", "12242343", "12429838"):
            self.assertIn(pmid, record["function"][0]["pmids"])

    def test_only_pubmed_evidence_is_kept_as_a_citation(self):
        record = self.fetch()
        # An ECO:0000250 inference from an orthologue's UniProtKB record is
        # not a paper and must not be offered to the reader as one.
        self.assertNotIn("Q9EQS7", record["function"][0]["pmids"])

    def test_repeated_domains_collapse_to_one_architectural_fact(self):
        record = self.fetch()
        names = [d["name"] for d in record["domains"]]
        self.assertEqual(names, ["TNFR-Cys"])
        self.assertEqual(record["domains"][0]["count"], 3)
        # A feature with a blank description is dropped, and a transmembrane
        # helix is not a domain.
        self.assertEqual(len(record["domains"]), 1)

    def test_disease_carries_its_acronym_mim_and_evidence(self):
        disease = self.fetch()["disease"][0]
        self.assertEqual(disease["acronym"], "CVID4")
        self.assertEqual(disease["mim"], "613494")
        self.assertIn("19017632", disease["pmids"])

    def test_a_rejected_field_selection_retries_without_it(self):
        """UniProt rejects an unknown return field with a 400 for the whole
        query. Field names drift, and a drifted one would take the brief off
        every target at once — silently, because the caller cannot tell a
        renamed field from a gene with no entry. The full entry carries
        everything read here, so the selection is dropped and retried."""
        calls = []

        def flaky(url, params=None, **kwargs):
            calls.append(params or {})
            if "fields" in (params or {}):
                raise HTTPError("400 Bad Request: invalid field")
            return payloads.UNIPROT_SEARCH

        with mock.patch.object(uniprot_src, "get_json", side_effect=flaky):
            record = uniprot_src.fetch("TNFRSF13C")

        self.assertEqual(len(calls), 2)
        self.assertNotIn("fields", calls[1])
        self.assertEqual(record["accession"], "Q96RJ3")

    def test_a_dead_uniprot_raises_rather_than_claiming_no_entry(self):
        """The one wrong answer here. Returning {} on a failed request makes
        the page say "no reviewed UniProt entry" — a statement about the
        protein that the run has no evidence for. The pipeline catches this
        and records it as a run warning instead."""
        with mock.patch.object(uniprot_src, "get_json", side_effect=HTTPError("503")):
            with self.assertRaises(HTTPError):
                uniprot_src.fetch("TNFRSF13C")

    def test_an_empty_result_set_is_a_real_answer_and_returns_nothing(self):
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_EMPTY):
            self.assertEqual(uniprot_src.fetch("NOTAGENE"), {})

    def test_citations_are_counted_from_either_response_shape(self):
        """The field-selected response and the full entry put the citation
        list in different places; the count must not depend on which came."""
        full = {"results": [dict(payloads.UNIPROT_SEARCH["results"][1])]}
        full["results"][0].pop("uniProtKBCrossReferences")
        full["results"][0]["references"] = [
            {"citation": {"citationCrossReferences": [
                {"database": "PubMed", "id": "11460154"}]}},
            {"citation": {"citationCrossReferences": [
                {"database": "DOI", "id": "10.1000/x"}]}},
        ]
        with mock.patch.object(uniprot_src, "get_json", return_value=full):
            self.assertEqual(uniprot_src.fetch("TNFRSF13C")["n_citations"], 1)

    def test_the_query_asks_for_reviewed_human_entries_only(self):
        seen = {}

        def capture(url, params=None, **kwargs):
            seen.update(params or {})
            return payloads.UNIPROT_SEARCH

        with mock.patch.object(uniprot_src, "get_json", side_effect=capture):
            uniprot_src.fetch("TNFRSF13C")
        self.assertIn("organism_id:9606", seen["query"])
        self.assertIn("reviewed:true", seen["query"])
        for field in ("cc_function", "cc_subunit", "ft_domain", "cc_disease"):
            self.assertIn(field, seen["fields"])


class TestUniProtBrief(unittest.TestCase):
    def brief(self):
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_SEARCH):
            return uniprot_src.fetch_brief("TNFRSF13C")["brief"]

    def test_the_paragraph_lands_inside_its_word_budget(self):
        words = self.brief()["words"]
        self.assertGreaterEqual(words, 40)
        self.assertLessEqual(words, uniprot_src.WORD_CEILING)

    def test_the_function_sentences_are_curated_text_verbatim(self):
        """Nothing here is paraphrased. If this ever starts failing because
        the text was 'improved', the block has stopped being an annotation."""
        text = self.brief()["text"]
        self.assertIn("Receptor for TNFSF13B/TALL-1/BAFF/BLyS", text)
        self.assertIn("Promotes the survival of mature B-cells", text)
        # Three sentences of FUNCTION and no more.
        self.assertNotIn("A fourth sentence", text)

    def test_the_generated_sentences_state_only_what_is_annotated(self):
        text = self.brief()["text"]
        self.assertIn("three TNFR-Cys domains", text)
        self.assertIn("common variable, 4 (CVID4)", text)
        self.assertIn("genetic validation of the target", text)

    def test_every_segment_carries_the_records_behind_it(self):
        segments = self.brief()["segments"]
        kinds = [s["kind"] for s in segments]
        self.assertEqual(kinds[0], "function")
        self.assertTrue(segments[0]["pmids"])
        disease = [s for s in segments if s["kind"] == "disease"][0]
        self.assertIn("19017632", disease["pmids"])

    def test_a_terse_entry_yields_only_what_is_annotated(self):
        """The real TNFRSF13C entry has no SUBUNIT comment and no Domain
        features. The curated half is short and that is correct — the length
        is made up by the therapeutic sentence in analysis/brief.py, not by
        padding this one."""
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_TERSE):
            brief = uniprot_src.fetch_brief("TNFRSF13C")["brief"]

        self.assertEqual([s["kind"] for s in brief["segments"]], ["function", "disease"])
        self.assertLessEqual(brief["words"], uniprot_src.WORD_CEILING)

    def test_the_clinical_description_of_the_germline_disease_is_left_out(self):
        """A paragraph of CVID symptomatology under a BAFF-R header reads as
        the indication. It is not one: the field is developing BAFF-R
        depletion for Sjogren's, ITP and lupus."""
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_TERSE):
            brief = uniprot_src.fetch_brief("TNFRSF13C")["brief"]
        self.assertNotIn("hypogammaglobulinemia", brief["text"])
        self.assertNotIn("disease_detail", [s["kind"] for s in brief["segments"]])

    def test_a_curated_sentence_with_no_full_stop_gets_one(self):
        """UniProt's TNFRSF13C FUNCTION ends "…and the B-cell response". Joined
        on a space alone it runs straight into the next segment."""
        with mock.patch.object(uniprot_src, "get_json", return_value=payloads.UNIPROT_TERSE):
            text = uniprot_src.fetch_brief("TNFRSF13C")["brief"]["text"]
        self.assertIn("the B-cell response. Separately, germline variants", text)

    def test_the_disease_sentence_agrees_with_its_own_subject(self):
        """"Germline variants ... is" appeared on every single-disease target,
        which is most of them."""
        record = {
            "accession": "X", "url": "",
            "function": [{"text": "Does a thing.", "pmids": []}],
            "subunit": [], "domains": [],
            "disease": [{"name": "One disease", "acronym": "OD",
                         "description": "", "pmids": []}],
        }
        text = uniprot_src.brief(record, "GENE")["text"]
        self.assertIn("germline variants in GENE cause", text)
        self.assertIn("not an indication being pursued", text)

    def test_an_entry_with_no_function_comment_produces_no_brief(self):
        """Domains and a disease link describe a protein nobody has said does
        anything. That reads as evasion; the page says nothing instead."""
        record = dict(self.__class__ and uniprot_src.fetch.__doc__ and {})
        record = {"accession": "X", "function": [], "domains": [{"name": "D", "count": 1}],
                  "disease": [{"name": "Something", "acronym": "", "pmids": []}]}
        self.assertEqual(uniprot_src.brief(record, "GENE"), {})

    def test_no_record_produces_no_brief(self):
        self.assertEqual(uniprot_src.brief({}, "GENE"), {})


# ---------------------------------------------------------------------------
# Relevance: does this trial have anything to do with this target?
# ---------------------------------------------------------------------------


class RelevanceTests(unittest.TestCase):
    """The registry sweep used to invent whole competitive landscapes.

    MAP3K14 was searched as "mitogen-activated protein kinase kinase kinase
    14" against a stemmed intervention search. It came back with NCT00896389,
    "Salt Loading and Thiazide Intervention Study", whose eight interventions
    are all brand names of hydrochlorothiazide. Each became an asset, each was
    Phase 4, and the page reported thirteen approved drugs against a kinase
    that has never had a molecule in the clinic. All 228 of its assets came
    from trials that never mention the target.
    """

    def setUp(self):
        from landscape import relevance

        self.relevance = relevance

    def _trial(self, title, interventions, summary=""):
        return Trial(nct_id="NCT1", title=title, interventions=interventions,
                     brief_summary=summary)

    def test_a_descriptive_protein_name_is_not_a_search_term(self):
        self.assertFalse(
            self.relevance.is_specific("mitogen-activated protein kinase kinase kinase 14"))
        self.assertFalse(self.relevance.is_specific("interleukin 23 subunit alpha"))
        self.assertTrue(self.relevance.is_specific("MAP3K14"))
        self.assertTrue(self.relevance.is_specific("IL23A"))

    def test_the_hypertension_trial_is_rejected(self):
        trial = self._trial(
            "Salt Loading and Thiazide Intervention Study",
            ["Apo-Hydro", "Aquazide H", "Dichlotride", "Esidrex", "HCTZ",
             "HydroSaluric", "Hydrochlorothiazide", "Hydrochlorothiazide (HCTZ)"])
        self.assertFalse(
            self.relevance.trial_is_on_target(trial, ["MAP3K14", "NIK", "HSNIK"]))

    def test_a_trial_naming_the_target_is_kept(self):
        trial = self._trial("A Study of Anti-BAFF-R CAR-T in Refractory Lupus", ["CD19/BAFF-R CAR-T"])
        self.assertTrue(self.relevance.trial_is_on_target(trial, ["TNFRSF13C", "BAFF-R"]))

    def test_separators_inside_a_name_do_not_matter(self):
        for spelling in ("BAFF-R", "BAFF R", "BAFFR"):
            trial = self._trial(f"A study of anti-{spelling} therapy", ["drug"])
            self.assertTrue(self.relevance.trial_is_on_target(trial, ["BAFF-R"]),
                            spelling)

    def test_a_summary_naming_the_target_is_enough(self):
        """The registry matches against text the trial record does not repeat
        in its title. Without the summary, a real TL1A antibody trial looks
        exactly like a hypertension trial: neither one says TL1A in its title
        or its intervention list."""
        trial = self._trial(
            "A Study to Evaluate Efficacy and Safety of Tulisokibart",
            ["IV Tulisokibart", "MK-7240"],
            "Tulisokibart is a monoclonal antibody directed against TL1A.")
        self.assertTrue(self.relevance.trial_is_on_target(trial, ["TNFSF15", "TL1A"]))

    def test_a_drug_the_sweep_itself_invented_cannot_vouch_for_a_trial(self):
        """The first version of this filter passed everything, because the
        bogus asset and the bogus trial vouched for each other: the trial was
        kept for mentioning hydrochlorothiazide, and hydrochlorothiazide was
        an asset only because that trial had named it."""
        target = Target(ensembl_id="ENSG0", symbol="MAP3K14", name="a long protein name",
                        synonyms=["NIK"])
        swept_only = Asset(name="Hydrochlorothiazide", max_phase=4,
                           provenance=[Provenance(source="ctgov", identifier="NCT1")])
        terms = self.relevance.terms_for(target, [swept_only])
        self.assertNotIn("Hydrochlorothiazide", terms)
        self.assertIn("MAP3K14", terms)

    def test_a_database_vouched_drug_may_speak_for_the_target(self):
        target = Target(ensembl_id="ENSG0", symbol="PDCD1", name="programmed cell death 1")
        known = Asset(name="Nivolumab", max_phase=4,
                      provenance=[Provenance(source="opentargets", identifier="CHEMBL1")])
        self.assertIn("Nivolumab", self.relevance.terms_for(target, [known]))

    def test_the_target_description_never_becomes_a_query_term(self):
        target = Target(ensembl_id="ENSG0", symbol="MAP3K14",
                        name="mitogen-activated protein kinase kinase kinase 14")
        self.assertEqual(self.relevance.terms_for(target, []), ["MAP3K14"])

    def test_a_gene_used_to_choose_patients_is_not_a_drug_target(self):
        """CARD9's only trial is "Pilot Study of Posaconazole in Crohn's
        Disease", enrolling carriers of the CARD9 S12N risk allele.
        Posaconazole is an antifungal acting on fungal CYP51. The trial is
        real work on people defined by this gene and belongs in the trial
        list; its drugs are not programmes against CARD9, and the page was
        reporting posaconazole as an approved CARD9 drug."""
        trial = Trial(
            nct_id="NCT04966585",
            title="Pilot Study of Posaconazole in Crohn's Disease",
            conditions=["Crohn Disease", "CARD9 S12N Risk Allele"],
            interventions=["Noxafil", "Posaconazole Delayed Release Oral Tablet"],
            brief_summary=("This trial is designed to evaluate the effects of oral "
                           "antifungal treatment with posaconazole on active Crohn's "
                           "disease in CD patients with the caspase recruitment domain "
                           "family member 9 (CARD9) S12N risk allele."))
        # It mentions the gene, so it stays in the trial list.
        self.assertTrue(self.relevance.trial_is_on_target(trial, ["CARD9"]))
        # But nothing in it is a programme against the gene.
        self.assertFalse(self.relevance.names_target_as_a_drug_target(trial, ["CARD9"]))

    def test_a_marker_selected_population_is_the_same_pattern(self):
        trial = Trial(nct_id="NCT2",
                      title="Chemotherapy in HER2-positive breast cancer",
                      conditions=["HER2-positive Breast Cancer"],
                      interventions=["Docetaxel"])
        self.assertFalse(
            self.relevance.names_target_as_a_drug_target(trial, ["ERBB2", "HER2"]))

    def test_a_drug_actually_aimed_at_the_target_still_counts(self):
        for title, terms in (
            ("Safety and Efficacy of BAFFR CAR-T Therapy for Relapsed B-cell Lymphoma",
             ["TNFRSF13C", "BAFF-R", "BAFFR"]),
            ("Nivolumab, an anti-PD-1 antibody, in NSCLC", ["PDCD1", "PD-1"]),
        ):
            trial = Trial(nct_id="NCT3", title=title, interventions=["a drug"])
            self.assertTrue(
                self.relevance.names_target_as_a_drug_target(trial, terms), title)

    def test_a_qualified_placebo_is_not_a_drug(self):
        """"Matching Placebo Tablet" never matches an exact-name list, because
        a sponsor can qualify the word any way they like."""
        from landscape import normalize as norm

        for label in ("Matching Placebo Tablet", "Placebo Oral Solution",
                      "Sham Injection"):
            self.assertTrue(norm.is_not_an_asset(label), label)
        for label in ("Posaconazole Delayed Release Oral Tablet", "Ianalumab"):
            self.assertFalse(norm.is_not_an_asset(label), label)

    def test_a_trial_with_no_text_at_all_is_not_deleted(self):
        """A sparse record contributes no asset either way, and deleting it
        would remove a registered trial from the trial count for the crime of
        having an empty title."""
        self.assertTrue(
            self.relevance.trial_is_on_target(self._trial("", []), ["MAP3K14"]))


class NearbyIsNotDirectedAtTests(unittest.TestCase):
    """Route 2 admits a drug when the title names the target beside it. Beside
    was not enough: three rows got in on proximity alone, and none of the three
    drugs acts on the target it was filed under."""

    def setUp(self):
        from landscape import relevance

        self.relevance = relevance

    def _directed(self, name, title, terms, summary=""):
        trial = Trial(nct_id="NCT1", title=title, brief_summary=summary,
                      interventions=[name])
        return self.relevance.drug_is_directed_at_target(trial, name, terms)

    def test_a_chemotherapy_backbone_beside_the_target_is_not_a_programme(self):
        """CAPOX is capecitabine and oxaliplatin. It sat four characters from
        the target's name in the CLDN18 table."""
        self.assertFalse(self._directed(
            "CAPOX",
            "Zolbetuximab With mFOLFOX6 or CAPOX in Claudin 18.2 Overexpressed "
            "Advanced or Metastatic Biliary Tract Cancers",
            ["CLDN18", "Claudin 18.2"]))

    def test_a_claim_about_the_drug_is_not_a_description_of_it(self):
        """MS-20 is a fermented soybean adjuvant. Its own summary says it makes
        someone else's PD-1 antibody work better, which is the opposite of
        acting on PD-1 -- and that sentence put it in the PD-1 asset table."""
        self.assertFalse(self._directed(
            "MS-20",
            "A Randomized, Placebo Controlled Study to Evaluate the Safety and "
            "Potential Efficacy of MS-20 in Combination with Pembrolizumab",
            ["PDCD1", "PD-1"],
            "MS-20 has also been shown to be anti-PD-1 booster by activating "
            "tumor-infiltrating lymphocytes."))

    def test_apposition_does_not_survive_a_full_stop(self):
        """NCT02332512 ends its title "(EGFR)" and opens its summary "Apatinib
        is a...". Run together, that reads as an appositive; it is two
        sentences, and the second one says apatinib inhibits VEGFR2."""
        self.assertFalse(self._directed(
            "Apatinib",
            "Study of Apatinib as 3rd/4th Line Treatment in Patients With "
            "Advanced NSCLC Harboring Wild-type Epidermal Growth Factor "
            "Receptor (EGFR)",
            ["EGFR", "Epidermal growth factor receptor"],
            "Apatinib is a new kind of selective Vascular Endothelial Growth "
            "Factor Receptor 2 (VEGFR-2) tyrosine kinase inhibitor."))

    def test_a_record_that_says_what_the_drug_is_still_passes(self):
        """The rule has to keep the cases it was built around."""
        self.assertTrue(self._directed(
            "BCD-100",
            "Efficacy and Safety of BCD-100 (Anti-PD-1) in Combination With "
            "Platinum-Based Chemotherapy",
            ["PDCD1", "PD-1"]))
        self.assertTrue(self._directed(
            "ALLO-715",
            "Safety and Efficacy of ALLO-715 BCMA Allogenic CAR T Cells in "
            "Adults With Relapsed or Refractory Multiple Myeloma",
            ["TNFRSF17", "BCMA"]))
        self.assertTrue(self._directed(
            "MK-7240",
            "A Study of MK-7240, an Anti-TL1A Antibody, in Ulcerative Colitis",
            ["TNFSF15", "TL1A"]))

    def test_the_receptor_is_not_the_ligand(self):
        """"BAFF" is found inside every "BAFF-R". Four BAFF-R programmes,
        Novartis's anti-BAFF-R antibody among them, sat in the BAFF table --
        while Open Targets files that antibody under TNFRSF13C one page away.

        No list of receptors is needed. The receptor's own synonyms carry the
        suffix, so its pattern consumes it and has nothing left to trip on."""
        title = "A Study of VAY736, an Anti-BAFF-R Antibody, in Sjogren's Syndrome"
        self.assertFalse(self._directed("VAY736", title, ["TNFSF13B", "BAFF", "BLyS"]))
        self.assertTrue(self._directed("VAY736", title, ["TNFRSF13C", "BAFF-R", "BAFFR"]))

    def test_a_ligand_based_car_still_belongs_to_the_ligand(self):
        """A CAR that uses BAFF itself as the binding domain is a BAFF asset.
        The suffix rule must not take it."""
        self.assertTrue(self._directed(
            "CD19-BAFF Targeted CAR T-cells",
            "CD19-BAFF Targeted CAR T-cells for Refractory B-cell Malignancies",
            ["TNFSF13B", "BAFF"]))


class ACategoryIsNotAProgrammeTests(unittest.TestCase):
    """A plural class label is what an investigator writes when the protocol
    lets each site use whichever marketed drug it stocks."""

    def setUp(self):
        from landscape import relevance

        self.relevance = relevance

    def test_the_plural_is_a_category(self):
        for label in ("PD-1 inhibitors", "Anti-PD-1 antibodies",
                      "Immune checkpoint inhibitors", "TKI drugs"):
            self.assertTrue(self.relevance.names_a_category(label), label)

    def test_the_singular_is_one_unnamed_programme(self):
        """"Anti-PD-1 monoclonal antibody" is one drug in one Phase 2 whose
        sponsor did not name it. That programme is real."""
        for label in ("Anti-PD-1 monoclonal antibody", "PD-1 antibody",
                      "BCMA CAR-T", "Ianalumab"):
            self.assertFalse(self.relevance.names_a_category(label), label)


class SweptRowsThatAreNotProgrammesTests(unittest.TestCase):
    """A second pass over every sweep-derived row in the library, after the
    partner-drug rule had cleared out the chemotherapy. What was left was not
    other people's drugs -- it was the registry's own furniture."""

    def setUp(self):
        from landscape import normalize, relevance

        self.normalize = normalize
        self.relevance = relevance

    def test_a_drug_class_with_an_approved_member_is_not_an_approved_drug(self):
        """"EGFR-TKI" sat in the EGFR table at Phase 4. Its trial is a real
        study of icotinib whose intervention field names the class; the class
        then inherited the phase of the best drug in it. An approved drug that
        is not a drug is the MAP3K14 failure with a different class word."""
        for label in ("EGFR-TKI", "Third-generation EGFR-TKI", "EGFR TKIs"):
            self.assertTrue(
                self.relevance.names_no_molecule(label, ["EGFR"], {"egfr"}), label)
        self.assertFalse(
            self.relevance.names_no_molecule("Icotinib", ["EGFR"], {"egfr"}))

    def test_making_a_cell_product_is_not_the_product(self):
        for label in ("CD3/CD19 depletion using cliniMACs device",
                      "Anti-CD19 CAR T Cells Preparation",
                      "Depletion of CD3/CD19 in an autologous stem cell transplant"):
            self.assertTrue(self.normalize.is_not_an_asset(label), label)
        self.assertFalse(self.normalize.is_not_an_asset("CD19 CAR-T cells"))

    def test_the_registrys_own_field_label_is_not_part_of_the_name(self):
        """"Assigned Interventions" is the heading of the column the sponsor
        was filling in, typed into the column itself."""
        self.assertEqual(
            self.normalize.tidy_name("Assigned Interventions CD19/BCMA CAR T-cells"),
            "CD19/BCMA CAR T-cells")
        self.assertEqual(self.normalize.tidy_name("Drug: Zolbetuximab"), "Zolbetuximab")

    def test_a_bracket_the_sponsor_never_closed(self):
        """CD19's AUTO3 is filed as "AUTO3 (CD19/22 CAR T cells". The registry
        keeps whatever was typed."""
        self.assertEqual(
            self.normalize.tidy_name("AUTO3 (CD19/22 CAR T cells"), "AUTO3")
        # A balanced bracket is left alone.
        self.assertEqual(
            self.normalize.tidy_name("Azacitidine (5-Azacytidine, Ladakamycin)"),
            "Azacitidine (5-Azacytidine, Ladakamycin)")

    def test_two_dose_arms_are_one_programme(self):
        """"CD19-BCMA Targeted CAR-T Dose 1" and "Dose 2" are the two dose
        levels of one Phase 1. Stripping "Dose" and leaving the number behind
        made them two competitors."""
        key = self.normalize._name_key
        self.assertEqual(key("CD19-BCMA Targeted CAR-T Dose 1"),
                         key("CD19-BCMA Targeted CAR-T Dose 2"))
        self.assertEqual(key("CD19.CAR-multiVST for Group A"),
                         key("CD19.CAR-multiVST for Group B"))
        for dose in ("0.50 x 10^6", "0.75 x10^6", "2.5 x 10^6"):
            self.assertEqual(key(f"BCMA-TGF CAR-T cells ({dose} cells/kg)"),
                             key("BCMA-TGF CAR-T cells"), dose)

    def test_a_trailing_number_is_only_an_arm_when_a_word_says_so(self):
        """"Interleukin 2" must keep its 2."""
        key = self.normalize._name_key
        self.assertNotEqual(key("Interleukin 2"), key("Interleukin 3"))
        self.assertNotEqual(key("Sym 021"), key("Sym 024"))

    def test_a_preposition_left_hanging_is_dropped(self):
        self.assertEqual(
            self.normalize.tidy_name(
                self.normalize._NOISE_RE.sub(" ", "CD19.CAR-multiVST for Group A")),
            "CD19.CAR-multiVST")


class HandEnteredProgrammesTests(unittest.TestCase):
    """The escape hatch for what the rules will not take from the record.

    CLDN18's NCT07431281 names Claudin18.2 three times and all three are
    "Expressing" or "-positive" -- the enrolment criterion. The rule that reads
    that as a population is the rule that keeps posaconazole off CARD9, so it
    stays, and a person supplies the row with a citation instead.
    """

    def setUp(self):
        import tempfile

        from landscape import store

        self.store = store
        self.dir = tempfile.mkdtemp()
        self._saved = store.ASSETS_DIR
        store.ASSETS_DIR = self.dir

    def tearDown(self):
        self.store.ASSETS_DIR = self._saved

    def _write(self, symbol, body):
        with open(os.path.join(self.dir, f"{symbol}.csv"), "w", encoding="utf-8") as fh:
            fh.write(body)

    def test_a_row_without_a_source_is_not_loaded(self):
        """The rest of the table is checkable. An unsourced row would borrow
        that credibility."""
        self._write("CLDN18",
                    "name,max_phase,source_url\n"
                    "Sonesitatug vedotin,Phase 3,https://example.org/a\n"
                    "Something I remember,Phase 3,\n")
        rows = self.store.load_manual_assets("CLDN18")
        self.assertEqual([a.name for a in rows], ["Sonesitatug vedotin"])
        self.assertEqual(rows[0].max_phase, 3)
        self.assertEqual(rows[0].provenance[0].source, "manual")
        self.assertEqual(rows[0].provenance[0].url, "https://example.org/a")

    def test_phase_words_and_numbers_mean_the_same_thing(self):
        parse = self.store.parse_phase
        self.assertEqual(parse("Approved"), 4)
        self.assertEqual(parse("Phase 3"), 3)
        self.assertEqual(parse("III"), 3)
        self.assertEqual(parse("Preclinical"), 0)
        self.assertEqual(parse("sometime soon"), -1)

    def test_a_hand_row_corrects_the_database_rather_than_duplicating_it(self):
        """Open Targets records zolbetuximab as a "Claudin-18 binding agent" at
        Phase 3. It is a chimeric IgG1 that kills through ADCC and CDC, and the
        FDA approved it in October 2024."""
        from landscape import normalize
        from landscape.analysis import mechanism
        from landscape.models import Provenance

        stored = Asset(name="ZOLBETUXIMAB", max_phase=3,
                       modality="Monoclonal antibody",
                       mechanism_text="Claudin-18 binding agent",
                       action_type="BINDING AGENT",
                       provenance=[Provenance(source="opentargets", identifier="x")])
        self._write("CLDN18",
                    "name,modality,mechanism,max_phase,source_url\n"
                    "Zolbetuximab,Monoclonal antibody,"
                    "Chimeric IgG1 against CLDN18.2; kills through ADCC and CDC,"
                    "Approved,https://www.fda.gov/x\n")
        merged = normalize.dedupe([stored] + self.store.load_manual_assets("CLDN18"))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].max_phase, 4)
        self.assertIn("ADCC", merged[0].mechanism_text)
        mechanism.annotate(merged)
        self.assertEqual(merged[0].mechanism_class, "Depleting antibody (ADCC/CDC)")

    def test_two_unnamed_programmes_still_do_not_merge(self):
        """The sponsor-scoped key is what keeps five companies' "BAFF-R CAR-T"
        apart. Narrowing it to rows with no name of their own must not widen
        it."""
        from landscape import normalize

        a = Asset(name="BAFF-R CAR-T", sponsor="PeproMene Bio", named_by_class=True)
        b = Asset(name="BAFF-R CAR-T", sponsor="Mayo Clinic", named_by_class=True)
        self.assertEqual(len(normalize.dedupe([a, b])), 2)


class ArmLabelTests(unittest.TestCase):
    """A registry intervention field holds whatever the sponsor typed."""

    def setUp(self):
        from landscape import normalize

        self.normalize = normalize

    def test_arm_labels_do_not_become_assets(self):
        for label in ("Chemotherapy", "Immunotherapy", "Targeted Systemic Therapy",
                      "Treatment Algorithm A", "Arm B", "Regimen 2", "Matching"):
            key = self.normalize._name_key(label)
            self.assertTrue(
                key in self.normalize._NON_ASSETS or self.normalize._is_arm_label(label),
                f"{label!r} would be listed as a drug programme")

    def test_real_drug_names_survive(self):
        for name in ("Tulisokibart", "MK-7240", "Zolbetuximab", "Ianalumab",
                     "BNT327", "VAY736", "Nivolumab"):
            key = self.normalize._name_key(name)
            self.assertFalse(
                key in self.normalize._NON_ASSETS or self.normalize._is_arm_label(name),
                f"{name!r} was dropped as an arm label")


class IncompleteBuildTests(unittest.TestCase):
    """A refused request and an empty answer are the same empty list.

    ERBB2 was stored with 45 assets, 15 of them approved, and zero trials.
    Trastuzumab alone has hundreds of registered studies. The sweep swallowed
    the registry's refusal and returned what it had, so a failed request was
    published as a finding about the target. CLDN18 lost its ChEMBL synonyms
    the same way, which is why zolbetuximab was about to enter the asset table
    three times, as itself, as IMAB362 and as Vyloy.
    """

    def test_a_refused_sweep_raises_rather_than_returning_silence(self):
        from unittest import mock

        from landscape.sources import ctgov

        with mock.patch.object(ctgov, "_fetch_page",
                               side_effect=HTTPError("429 Too Many Requests")):
            with self.assertRaises(ctgov.SweepIncomplete) as caught:
                ctgov.search_trials(["PDCD1"])
        self.assertEqual(caught.exception.trials, [])
        self.assertIn("429", str(caught.exception))

    def test_the_error_does_not_carry_the_whole_query_back(self):
        """ClinicalTrials.gov echoes the request in its error, and a
        well-drugged target's query runs to four thousand characters. Printed
        in full it filled the terminal and the page's warning box with a URL
        nobody can read."""
        from landscape.sources import ctgov

        long = ("400 Bad Request for https://clinicaltrials.gov/api/v2/studies?"
                "query.intr=" + "%22DRUG%22+OR+" * 400)
        short = ctgov._short_error(long)
        self.assertLess(len(short), 200)
        self.assertIn("400 Bad Request", short)
        self.assertNotIn("%22DRUG%22", short)
        self.assertEqual(ctgov._short_error("429 Too Many Requests"),
                         "429 Too Many Requests")

    def test_a_partial_sweep_keeps_what_it_got(self):
        from unittest import mock

        from landscape.sources import ctgov

        page = ([Trial(nct_id="NCT1", title="a study")], "token")
        with mock.patch.object(ctgov, "_fetch_page",
                               side_effect=[page, HTTPError("500")]):
            with self.assertRaises(ctgov.SweepIncomplete) as caught:
                ctgov.search_trials(["PDCD1"])
        self.assertEqual([t.nct_id for t in caught.exception.trials], ["NCT1"])

    def test_a_clean_sweep_still_returns_a_plain_list(self):
        from unittest import mock

        from landscape.sources import ctgov

        with mock.patch.object(ctgov, "_fetch_page",
                               return_value=([Trial(nct_id="NCT1")], None)):
            self.assertEqual([t.nct_id for t in ctgov.search_trials(["PDCD1"])],
                             ["NCT1"])

    def test_a_long_term_list_is_split_so_the_url_cannot_overflow(self):
        """ERBB2 has 45 known drugs. Each contributes a name and up to three
        synonyms, so the intervention query came to about 180 quoted terms and
        four thousand characters, and ClinicalTrials.gov answered 400 Bad
        Request every single time. The sweep did not fail intermittently on
        ERBB2 -- it could never succeed -- and the page was published with 45
        assets, 15 of them approved, and no trials at all."""
        from unittest import mock

        from landscape.sources import ctgov

        issued = []

        def fake(params):
            issued.append(params["query.intr"])
            return ([Trial(nct_id=f"NCT{len(issued)}")], None)

        terms = [f"DRUGNAME{i:03d}" for i in range(180)]
        with mock.patch.object(ctgov, "_fetch_page", side_effect=fake):
            found = ctgov.search_trials(terms)
        self.assertGreater(len(issued), 1, "180 terms went out as one query")
        self.assertTrue(all(len(q) < 2000 for q in issued),
                        f"longest query was {max(len(q) for q in issued)} characters")
        self.assertEqual(len(found), len(issued))

    def test_a_short_term_list_still_goes_out_as_one_query(self):
        from unittest import mock

        from landscape.sources import ctgov

        issued = []

        def fake(params):
            issued.append(params["query.intr"])
            return ([Trial(nct_id="NCT1")], None)

        with mock.patch.object(ctgov, "_fetch_page", side_effect=fake):
            ctgov.search_trials(["PDCD1", "PD-1", "nivolumab"])
        self.assertEqual(len(issued), 1)

    def test_a_failed_molecule_fetch_is_recorded(self):
        from unittest import mock

        from landscape.sources import chembl

        with mock.patch.object(chembl, "_paged", side_effect=HTTPError("503")):
            chembl.fetch_molecules(["CHEMBL1"])
        self.assertTrue(getattr(chembl.fetch_molecules, "last_errors", None))


class SubjectDrugTests(unittest.TestCase):
    """A trial is attributed to the first asset it names, and every other drug
    in it becomes invisible.

    NCT07431281 studies sonesitatug vedotin, an anti-CLDN18.2 ADC, and lists
    ten interventions -- among them zolbetuximab, as a comparator. Matching on
    zolbetuximab marked the trial done, so AZD0901 never entered the table and
    the CLDN18 page showed one programme where the field has two.
    """

    def setUp(self):
        from landscape import normalize

        self.normalize = normalize

    def test_the_subject_is_the_drug_the_title_leads_with(self):
        trial = Trial(
            nct_id="NCT07431281",
            title=("Sonesitatug Vedotin in Combination With Capecitabine With or "
                   "Without Rilvegostomig in Participants With Gastric Cancer"),
            interventions=["5-Fluorouracil", "AZD0901", "Capecitabine", "Nivolumab",
                           "Sonesitatug vedotin", "Zolbetuximab"])
        self.assertEqual(self.normalize.subject_intervention(trial),
                         "Sonesitatug vedotin")

    def test_a_zolbetuximab_trial_still_resolves_to_zolbetuximab(self):
        trial = Trial(
            nct_id="NCT03504397",
            title="A Study to Compare Zolbetuximab and Chemotherapy in Gastric Cancer",
            interventions=["zolbetuximab", "oxaliplatin", "fluorouracil"])
        self.assertEqual(self.normalize.subject_intervention(trial), "zolbetuximab")

    def test_the_chemotherapy_backbone_is_never_the_subject(self):
        trial = Trial(nct_id="NCT1",
                      title="Chemotherapy With or Without AZD0901 in Gastric Cancer",
                      interventions=["Chemotherapy", "AZD0901", "Capecitabine"])
        self.assertEqual(self.normalize.subject_intervention(trial), "AZD0901")

    def test_a_trial_whose_title_names_no_drug_has_no_subject(self):
        trial = Trial(nct_id="NCT1",
                      title="Precision Targeted Therapy Strategies for Gastric Cancer",
                      interventions=["Capecitabine", "Oxaliplatin"])
        self.assertIsNone(self.normalize.subject_intervention(trial))
