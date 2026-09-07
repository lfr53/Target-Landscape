"""Realistic API payloads, trimmed to the fields the adapters read.

These are hand-built from the documented response shapes of each API rather
than recorded from a live call, so they are small enough to read and to reason
about. Their job is to pin down the parsing contract: if an adapter starts
reading a field that is not here, or stops reading one that is, the tests say
so without anyone needing network access.

Where an API is known to be inconsistent, the payload reproduces the
inconsistency on purpose — a null phase, a missing sponsor class, a study with
no interventions module. Those are the shapes that crash a parser in
production, and a payload full of well-formed records tests nothing.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Open Targets GraphQL
# ---------------------------------------------------------------------------

OT_SEARCH = {
    "data": {
        "search": {
            "hits": [
                {
                    "id": "ENSG00000159958",
                    "entity": "target",
                    "object": {
                        "id": "ENSG00000159958",
                        "approvedSymbol": "TNFRSF13C",
                        "approvedName": "TNF receptor superfamily member 13C",
                        "biotype": "protein_coding",
                    },
                },
                {
                    # A paralogue the fuzzy search returns; must not win.
                    "id": "ENSG00000102383",
                    "entity": "target",
                    "object": {
                        "id": "ENSG00000102383",
                        "approvedSymbol": "TNFRSF13B",
                        "approvedName": "TNF receptor superfamily member 13B",
                        "biotype": "protein_coding",
                    },
                },
            ]
        }
    }
}

OT_TARGET = {
    "data": {
        "target": {
            "id": "ENSG00000159958",
            "approvedSymbol": "TNFRSF13C",
            "approvedName": "TNF receptor superfamily member 13C",
            "biotype": "protein_coding",
            "synonyms": [
                {"label": "BAFF-R", "source": "uniprot"},
                {"label": "BR3", "source": "uniprot"},
                {"label": "CD268", "source": "hgnc"},
                # Empty labels appear in the wild and must be dropped.
                {"label": "", "source": "hgnc"},
            ],
            "functionDescriptions": [
                "Receptor for TNFSF13B/BAFF; promotes B cell survival.",
                "Second description that should be ignored.",
            ],
            # Platform 26.x renamed this field from "id" to "label".
            "tractability": [
                {"label": "Advanced Clinical", "modality": "AB", "value": True},
                {"label": "GO CC high conf", "modality": "AB", "value": True},
                # value False means the target is NOT in this bucket.
                {"label": "Small molecule binder", "modality": "SM", "value": False},
            ],
        }
    }
}

OT_KNOWN_DRUGS = {
    "data": {
        "target": {
            "knownDrugs": {
                "count": 3,
                "rows": [
                    {
                        "drugId": "CHEMBL4297516",
                        "prefName": "IANALUMAB",
                        "drugType": "Antibody",
                        "mechanismOfAction": "B-cell activating factor receptor antagonist",
                        "phase": 3,
                        "status": "Completed",
                        "ctIds": ["NCT05350072", "NCT05349214"],
                        "disease": {"id": "EFO_0000699", "name": "Sjogren syndrome"},
                    },
                    {
                        # Same drug, second disease — must fold into one asset,
                        # and the lower phase must not overwrite the higher.
                        "drugId": "CHEMBL4297516",
                        "prefName": "IANALUMAB",
                        "drugType": "Antibody",
                        "mechanismOfAction": "B-cell activating factor receptor antagonist",
                        "phase": 2,
                        "status": "Terminated",
                        "ctIds": ["NCT03827798"],
                        "disease": {"id": "EFO_1000772", "name": "hidradenitis suppurativa"},
                    },
                    {
                        # Null phase happens; must degrade to -1, not crash.
                        "drugId": "CHEMBL9999999",
                        "prefName": "EXAMPLEMAB",
                        "drugType": "Antibody",
                        "mechanismOfAction": None,
                        "phase": None,
                        "status": None,
                        "ctIds": [],
                        "disease": {"id": "EFO_0002690", "name": "systemic lupus erythematosus"},
                    },
                ],
            }
        }
    }
}

OT_ASSOCIATIONS = {
    "data": {
        "target": {
            "associatedDiseases": {
                "count": 2,
                "rows": [
                    {
                        "score": 0.71,
                        "datatypeScores": [
                            {"id": "genetic_association", "score": 0.42},
                            {"id": "known_drug", "score": 0.9},
                        ],
                        "disease": {"id": "EFO_0000699", "name": "Sjogren syndrome"},
                    },
                    {
                        # No genetic component at all — genetic_score must be 0.0.
                        "score": 0.4,
                        "datatypeScores": [{"id": "literature", "score": 0.4}],
                        "disease": {"id": "EFO_0006812", "name": "autoimmune hepatitis"},
                    },
                ],
            }
        }
    }
}

OT_ERROR = {
    "errors": [{"message": "Cannot query field 'tractability' on type 'Target'"}],
    "data": None,
}

# ---------------------------------------------------------------------------
# ChEMBL REST
# ---------------------------------------------------------------------------

CHEMBL_TARGET_SEARCH = {
    "targets": [
        {
            "target_chembl_id": "CHEMBL1795194",
            "pref_name": "B-cell activating factor receptor",
            "organism": "Homo sapiens",
            "target_type": "SINGLE PROTEIN",
            "target_components": [
                {
                    "target_component_synonyms": [
                        {"component_synonym": "TNFRSF13C"},
                        {"component_synonym": "BAFF-R"},
                    ]
                }
            ],
        },
        {
            # Protein family — must be excluded, or every family member's
            # drugs join the asset table.
            "target_chembl_id": "CHEMBL2094253",
            "pref_name": "TNF receptor superfamily",
            "organism": "Homo sapiens",
            "target_type": "PROTEIN FAMILY",
            "target_components": [
                {"target_component_synonyms": [{"component_synonym": "TNFRSF13C"}]}
            ],
        },
        {
            # Non-human — must be excluded.
            "target_chembl_id": "CHEMBL3000001",
            "pref_name": "B-cell activating factor receptor",
            "organism": "Mus musculus",
            "target_type": "SINGLE PROTEIN",
            "target_components": [
                {"target_component_synonyms": [{"component_synonym": "TNFRSF13C"}]}
            ],
        },
    ]
}

CHEMBL_MECHANISMS = {
    "mechanisms": [
        {
            "molecule_chembl_id": "CHEMBL4297516",
            "action_type": "ANTAGONIST",
            "mechanism_of_action": "B-cell activating factor receptor antagonist",
            "target_chembl_id": "CHEMBL1795194",
            "max_phase": 3,
        }
    ],
    "page_meta": {"next": None},
}

CHEMBL_MOLECULES = {
    "molecules": [
        {
            "molecule_chembl_id": "CHEMBL4297516",
            "pref_name": "IANALUMAB",
            "molecule_type": "Antibody",
            "max_phase": 3.0,
            "first_approval": None,
            "withdrawn_flag": False,
            "molecule_synonyms": [
                {"molecule_synonym": "VAY-736"},
                {"molecule_synonym": "Ianalumab"},
            ],
        }
    ],
    "page_meta": {"next": None},
}

# ---------------------------------------------------------------------------
# ClinicalTrials.gov API v2
# ---------------------------------------------------------------------------

CTGOV_PAGE = {
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT05350072",
                    "briefTitle": "Two-arm Study of Ianalumab in Active Sjogren's Syndrome",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2022-06"},
                    "primaryCompletionDateStruct": {"date": "2025-05"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Novartis Pharmaceuticals", "class": "INDUSTRY"}
                },
                "designModule": {
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 275},
                },
                "conditionsModule": {"conditions": ["Sjogren's Disease"]},
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Ianalumab", "otherNames": ["VAY736"]},
                        {"type": "DRUG", "name": "Placebo"},
                        # Must be filtered out — not an asset.
                        {"type": "PROCEDURE", "name": "Salivary gland biopsy"},
                    ]
                },
                "contactsLocationsModule": {
                    "locations": [
                        {"country": "United States", "city": "Boston"},
                        {"country": "Japan", "city": "Tokyo"},
                        {"country": "United States", "city": "Chicago"},
                    ]
                },
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT03827798",
                    "briefTitle": "VAY736 in Moderate to Severe Hidradenitis Suppurativa",
                },
                "statusModule": {
                    "overallStatus": "TERMINATED",
                    "whyStopped": "  Study did not meet the target criteria for progression "
                    "despite demonstrating efficacy versus placebo. No new safety "
                    "signals were identified.  ",
                    "startDateStruct": {"date": "2019-04"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Novartis Pharmaceuticals", "class": "INDUSTRY"}
                },
                "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 248}},
                "conditionsModule": {"conditions": ["Hidradenitis Suppurativa"]},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "VAY736"}]
                },
                "contactsLocationsModule": {"locations": [{"country": "Germany"}]},
            }
        },
        {
            # Minimal study: no sponsor class, no interventions module, no
            # locations, phase NA. This is the shape that crashes parsers.
            "protocolSection": {
                "identificationModule": {"nctId": "NCT00000001", "briefTitle": "Sparse record"},
                "statusModule": {"overallStatus": "UNKNOWN"},
                "designModule": {"phases": ["NA"]},
                "conditionsModule": {"conditions": []},
            }
        },
        {
            # No nctId at all — must be dropped silently, not crash.
            "protocolSection": {"identificationModule": {"briefTitle": "Broken record"}}
        },
    ],
    "nextPageToken": None,
}


# ---------------------------------------------------------------------------
# Open Targets Platform 26.x — drugAndClinicalCandidates
# ---------------------------------------------------------------------------
#
# The 26.x release replaced knownDrugs with a shape that is one row per drug
# rather than per (drug, disease, phase), reports phase as a string enum, and
# nests the trial records. Captured from the live API rather than invented.

OT_CANDIDATES = {
    "data": {
        "target": {
            "drugAndClinicalCandidates": {
                "count": 2,
                "rows": [
                    {
                        "id": "5d248f509da099d49dec5806",
                        "maxClinicalStage": "PHASE_3",
                        "drug": {
                            "id": "CHEMBL4594357",
                            "name": "IANALUMAB",
                            "drugType": "Antibody",
                            "maximumClinicalStage": "PHASE_3",
                            "mechanismsOfAction": {
                                "rows": [
                                    {
                                        "mechanismOfAction": "Tumor necrosis factor receptor "
                                        "superfamily member 13C binding agent",
                                        "actionType": "BINDING AGENT",
                                    }
                                ]
                            },
                        },
                        "diseases": [
                            {"diseaseFromSource": "Sjogren's syndrome",
                             "disease": {"id": "MONDO_0010030", "name": "Sjogren syndrome"}},
                            {"diseaseFromSource": "lupus nephritis",
                             "disease": {"id": "MONDO_0005556", "name": "lupus nephritis"}},
                            # Same disease twice from different source spellings.
                            {"diseaseFromSource": "Sj\u00f6gren's syndrome",
                             "disease": {"id": "MONDO_0010030", "name": "Sjogren syndrome"}},
                        ],
                        "clinicalReports": [
                            {"id": "NCT05350072", "source": "ClinicalTrials.gov",
                             "trialPhase": "PHASE_3", "trialOverallStatus": "Completed",
                             "trialWhyStopped": None},
                            {"id": "NCT03827798", "source": "ClinicalTrials.gov",
                             "trialPhase": "PHASE_2", "trialOverallStatus": "Terminated",
                             "trialWhyStopped": "Study did not meet the target criteria."},
                            # Not a registry record — must not become an NCT id.
                            {"id": "PMID12345678", "source": "Europe PMC",
                             "trialPhase": None, "trialOverallStatus": None,
                             "trialWhyStopped": None},
                        ],
                    },
                    {
                        # Preclinical, no drug name resolved beyond the id, no trials.
                        "id": "abc123",
                        "maxClinicalStage": "PRECLINICAL",
                        "drug": {
                            "id": "CHEMBL9999999",
                            "name": "EXAMPLEMAB",
                            "drugType": "Antibody",
                            "maximumClinicalStage": "PRECLINICAL",
                            "mechanismsOfAction": {"rows": []},
                        },
                        "diseases": [],
                        "clinicalReports": [],
                    },
                ],
            }
        }
    }
}


# ── Europe PMC ────────────────────────────────────────────────────────────
#
# Shape of a /search response with resultType=lite. Deliberately includes the
# cases the parser has to survive: a record with no DOI, one with no citation
# count, and one whose id is missing entirely.

EUROPEPMC_SEARCH = {
    "hitCount": 3,
    "resultList": {
        "result": [
            {
                "id": "31234567",
                "source": "MED",
                "pmid": "31234567",
                "doi": "10.1038/nri.2019.1",
                "title": "BAFF and APRIL in autoimmunity: a review.",
                "authorString": "Smith J, Patel R.",
                "journalTitle": "Nature Reviews Immunology",
                "pubYear": "2019",
                "citedByCount": 412,
                "isOpenAccess": "Y",
            },
            {
                "id": "28123456",
                "source": "MED",
                "pmid": "28123456",
                "title": "Structure of the BAFF-R ectodomain",
                "authorString": "Chen L.",
                "journalTitle": "J Biol Chem",
                "pubYear": "2017",
                # No citedByCount and no DOI at all.
                "isOpenAccess": "N",
            },
            {
                # No id and no doi: unlinkable, but must not crash the parser.
                "source": "PPR",
                "title": "A preprint with no identifiers",
                "pubYear": "2025",
            },
        ]
    },
}


# A study carrying the design and endpoint fields, plus one that carries none
# of them — the pair the parser has to tell apart, because "no design
# registered" and "not randomised" are different statements.
CTGOV_DESIGN_PAGE = {
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT05000001",
                    "briefTitle": "A randomised, double-blind study of X in lupus nephritis",
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "startDateStruct": {"date": "2025-02-01"},
                    "primaryCompletionDateStruct": {"date": "2027-06", "type": "ESTIMATED"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Novartis Pharmaceuticals", "class": "INDUSTRY"}
                },
                "designModule": {
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 240},
                    "designInfo": {
                        "allocation": "RANDOMIZED",
                        "interventionModel": "PARALLEL",
                        "primaryPurpose": "TREATMENT",
                        "maskingInfo": {"masking": "QUADRUPLE"},
                    },
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {"measure": "Complete renal response rate at week 52"},
                        {"measure": "  "},
                    ]
                },
                "armsInterventionsModule": {
                    "interventions": [{"name": "ianalumab", "type": "DRUG"}]
                },
                "conditionsModule": {"conditions": ["Lupus Nephritis"]},
                "contactsLocationsModule": {"locations": [{"country": "United States"}]},
            }
        },
        {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT05000002", "briefTitle": "An older record"},
                "statusModule": {"overallStatus": "RECRUITING"},
                "designModule": {"phases": ["PHASE2"]},
            }
        },
    ]
}


# ---------------------------------------------------------------------------
# UniProt — the curated annotation behind the header brief
# ---------------------------------------------------------------------------
#
# Shaped like a real UniProtKB search response with a field selection applied,
# and carrying the awkward parts on purpose: a paralogue returned first
# because ``gene:`` is not an exact-match field, inline "(PubMed:…)" and
# "(By similarity)" markers inside curated text, three repeats of one domain,
# and a Domain feature with no description.

UNIPROT_SEARCH = {
    "results": [
        # A family member that merely lists the symbol as a synonym. It is
        # first in the response, and taking the first hit would file its
        # annotation under the wrong target.
        {
            "primaryAccession": "O14836",
            "uniProtkbId": "TNR13_HUMAN",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Decoy receptor, not this target"}}
            },
            "genes": [{"geneName": {"value": "TNFRSF13B"},
                       "synonyms": [{"value": "TNFRSF13C"}]}],
            "comments": [
                {"commentType": "FUNCTION",
                 "texts": [{"value": "Should never appear in the brief."}]}
            ],
        },
        {
            "primaryAccession": "Q96RJ3",
            "uniProtkbId": "TR13C_HUMAN",
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Tumor necrosis factor receptor superfamily member 13C"}
                }
            },
            "genes": [{"geneName": {"value": "TNFRSF13C"},
                       "synonyms": [{"value": "BAFFR"}, {"value": "BR3"}]}],
            "comments": [
                {
                    "commentType": "FUNCTION",
                    "texts": [{
                        "value": (
                            "Receptor for TNFSF13B/TALL-1/BAFF/BLyS that binds the ligand "
                            "at the cell surface (PubMed:11460154). Promotes the survival "
                            "of mature B-cells and the humoral immune response (By "
                            "similarity). Activates NF-kappa-B signaling "
                            "(PubMed:12242343, PubMed:12429838). A fourth sentence that "
                            "the brief should not carry."
                        ),
                        "evidences": [
                            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": "11460154"},
                            {"evidenceCode": "ECO:0000250", "source": "UniProtKB", "id": "Q9EQS7"},
                        ],
                    }],
                },
                {
                    "commentType": "SUBUNIT",
                    "texts": [{
                        "value": "Homotrimer. Interacts with TRAF3.",
                        "evidences": [
                            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": "12429838"}
                        ],
                    }],
                },
                {
                    "commentType": "DISEASE",
                    "disease": {
                        "diseaseId": "Immunodeficiency, common variable, 4",
                        "diseaseAccession": "DI-02012",
                        "acronym": "CVID4",
                        "description": (
                            "A primary immunodeficiency characterized by antibody "
                            "deficiency, hypogammaglobulinemia and recurrent bacterial "
                            "infections."
                        ),
                        "diseaseCrossReference": {"database": "MIM", "id": "613494"},
                        "evidences": [
                            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": "19017632"}
                        ],
                    },
                    "note": {"texts": [{"value": "Disease susceptibility may be associated."}]},
                },
            ],
            "features": [
                {"type": "Domain", "description": "TNFR-Cys",
                 "location": {"start": {"value": 19}, "end": {"value": 35}}},
                {"type": "Domain", "description": "TNFR-Cys",
                 "location": {"start": {"value": 36}, "end": {"value": 52}}},
                {"type": "Domain", "description": "TNFR-Cys",
                 "location": {"start": {"value": 53}, "end": {"value": 69}}},
                {"type": "Domain", "description": "  ",
                 "location": {"start": {"value": 70}, "end": {"value": 80}}},
                {"type": "Transmembrane", "description": "Helical",
                 "location": {"start": {"value": 78}, "end": {"value": 98}}},
            ],
            "uniProtKBCrossReferences": [
                {"database": "PubMed", "id": "11460154"},
                {"database": "PubMed", "id": "12429838"},
                {"database": "PDB", "id": "1OQD"},
            ],
        },
    ]
}

# A gene with no reviewed human entry. The header must say so rather than
# assembling a brief from nothing.
UNIPROT_EMPTY = {"results": []}


# The real TNFRSF13C entry, in the shape UniProt actually returns it: a two
# sentence FUNCTION, no SUBUNIT comment, no Domain features (the cysteine-rich
# region is annotated as a Repeat), and a DISEASE comment carrying a curated
# description. Function plus the disease sentence is about fifty words, which
# is why the brief reaches for the description on entries like this one.
UNIPROT_TERSE = {
    "results": [
        {
            "primaryAccession": "Q96RJ3",
            "uniProtkbId": "TR13C_HUMAN",
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Tumor necrosis factor receptor superfamily member 13C"}
                }
            },
            "genes": [{"geneName": {"value": "TNFRSF13C"}}],
            "comments": [
                {
                    "commentType": "FUNCTION",
                    "texts": [{
                        "value": (
                            "B-cell receptor specific for TNFSF13B/TALL1/BAFF/BLyS. "
                            "Promotes the survival of mature B-cells and the B-cell response"
                        ),
                        "evidences": [
                            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": "11460154"}
                        ],
                    }],
                },
                {
                    "commentType": "DISEASE",
                    "disease": {
                        "diseaseId": "Immunodeficiency, common variable, 4",
                        "acronym": "CVID4",
                        "description": (
                            "A primary immunodeficiency characterized by antibody deficiency, "
                            "hypogammaglobulinemia, recurrent bacterial infections and an "
                            "inability to mount an antibody response to antigen. The defect "
                            "results from impaired B-cell differentiation with impaired "
                            "secretion of immunoglobulins."
                        ),
                        "diseaseCrossReference": {"database": "MIM", "id": "613494"},
                        "evidences": [
                            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": "19017632"}
                        ],
                    },
                },
            ],
            "features": [],
        }
    ]
}
