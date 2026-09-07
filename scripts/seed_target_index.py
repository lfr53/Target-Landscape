#!/usr/bin/env python3
"""Write the seed target index.

    python scripts/seed_target_index.py

Autocomplete has to work on the names people actually type. Nobody searches
``TNFRSF13C``; they search BAFF-R. Nobody searches ``ERBB2``; they search HER2.
An index of approved symbols alone fails on the most common query there is.

So this writes a hand-checked index of the targets that actually come up in
drug development, each with the aliases in real use and a coarse therapeutic
area for browsing. Ensembl IDs are deliberately *not* included: they would be
the one field here that is easy to get subtly wrong from memory, and the
pipeline resolves symbol → Ensembl through Open Targets anyway.

``scripts/build_target_index.py`` expands this to the full HGNC gene set when
a network is available. The seed is what makes the site usable before that,
and it stays merged in afterwards because HGNC's alias fields miss a lot of
the vernacular ("PD-1" is in HGNC; "BAFF-R" and "TL1A" are patchier).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "target_index.json"
)

# (symbol, name, aliases, areas)
SEED: list[tuple[str, str, list[str], list[str]]] = [
    # ── Immuno-oncology checkpoints ────────────────────────────────────────
    ("PDCD1", "programmed cell death 1", ["PD-1", "PD1", "CD279"], ["oncology", "immunology"]),
    ("CD274", "CD274 molecule", ["PD-L1", "PDL1", "B7-H1"], ["oncology", "immunology"]),
    ("PDCD1LG2", "programmed cell death 1 ligand 2", ["PD-L2", "B7-DC"], ["oncology"]),
    ("CTLA4", "cytotoxic T-lymphocyte associated protein 4", ["CTLA-4", "CD152"], ["oncology", "immunology"]),
    ("LAG3", "lymphocyte activating 3", ["LAG-3", "CD223"], ["oncology", "immunology"]),
    ("HAVCR2", "hepatitis A virus cellular receptor 2", ["TIM-3", "TIM3", "CD366"], ["oncology"]),
    ("TIGIT", "T cell immunoreceptor with Ig and ITIM domains", ["TIGIT", "VSTM3"], ["oncology"]),
    ("VSIR", "V-set immunoregulatory receptor", ["VISTA", "B7-H5", "VSIR"], ["oncology"]),
    ("BTLA", "B and T lymphocyte associated", ["CD272"], ["oncology"]),
    ("TNFRSF9", "TNF receptor superfamily member 9", ["4-1BB", "CD137"], ["oncology"]),
    ("TNFRSF4", "TNF receptor superfamily member 4", ["OX40", "CD134"], ["oncology"]),
    ("TNFRSF18", "TNF receptor superfamily member 18", ["GITR", "CD357"], ["oncology"]),
    ("CD47", "CD47 molecule", ["CD47", "IAP"], ["oncology"]),
    ("SIRPA", "signal regulatory protein alpha", ["SIRP-alpha", "CD172a"], ["oncology"]),
    ("CD40", "CD40 molecule", ["CD40", "TNFRSF5"], ["oncology", "immunology"]),
    ("CD40LG", "CD40 ligand", ["CD40L", "CD154"], ["immunology"]),
    ("ICOS", "inducible T cell costimulator", ["CD278"], ["oncology", "immunology"]),
    ("ENTPD1", "ectonucleoside triphosphate diphosphohydrolase 1", ["CD39"], ["oncology"]),
    ("NT5E", "5'-nucleotidase ecto", ["CD73"], ["oncology"]),
    ("ADORA2A", "adenosine A2a receptor", ["A2AR", "A2A"], ["oncology", "neurology"]),
    ("IDO1", "indoleamine 2,3-dioxygenase 1", ["IDO", "IDO-1"], ["oncology"]),

    # ── Oncology cell-surface and CAR-T targets ────────────────────────────
    ("MS4A1", "membrane spanning 4-domains A1", ["CD20"], ["oncology", "immunology"]),
    ("CD19", "CD19 molecule", ["CD19"], ["oncology", "immunology"]),
    ("TNFRSF17", "TNF receptor superfamily member 17", ["BCMA", "CD269"], ["oncology"]),
    ("CD22", "CD22 molecule", ["CD22", "Siglec-2"], ["oncology"]),
    ("SDC1", "syndecan 1", ["CD138"], ["oncology"]),
    ("GPRC5D", "G protein-coupled receptor class C group 5 member D", ["GPRC5D"], ["oncology"]),
    ("FCRL5", "Fc receptor like 5", ["FCRH5", "CD307e"], ["oncology"]),
    ("TNFRSF13B", "TNF receptor superfamily member 13B", ["TACI", "CD267"], ["immunology"]),
    ("TNFRSF13C", "TNF receptor superfamily member 13C", ["BAFF-R", "BAFFR", "BR3", "CD268"], ["immunology"]),
    ("TNFSF13B", "TNF superfamily member 13b", ["BAFF", "BLyS", "TALL-1"], ["immunology"]),
    ("TNFSF13", "TNF superfamily member 13", ["APRIL", "TALL-2"], ["immunology"]),
    ("CEACAM5", "CEA cell adhesion molecule 5", ["CEA", "CD66e"], ["oncology"]),
    ("MSLN", "mesothelin", ["MSLN"], ["oncology"]),
    ("FOLH1", "folate hydrolase 1", ["PSMA"], ["oncology"]),
    ("KLK3", "kallikrein related peptidase 3", ["PSA"], ["oncology"]),
    ("DLL3", "delta like canonical Notch ligand 3", ["DLL3"], ["oncology"]),
    ("CLDN18", "claudin 18", ["CLDN18.2", "Claudin-18.2"], ["oncology"]),
    ("CLDN6", "claudin 6", ["CLDN6"], ["oncology"]),
    ("TACSTD2", "tumor associated calcium signal transducer 2", ["TROP2", "TROP-2"], ["oncology"]),
    ("NECTIN4", "nectin cell adhesion molecule 4", ["Nectin-4", "PVRL4"], ["oncology"]),
    ("ERBB2", "erb-b2 receptor tyrosine kinase 2", ["HER2", "HER-2", "neu"], ["oncology"]),
    ("ERBB3", "erb-b2 receptor tyrosine kinase 3", ["HER3"], ["oncology"]),
    ("EGFR", "epidermal growth factor receptor", ["HER1", "ERBB1"], ["oncology"]),
    ("MET", "MET proto-oncogene, receptor tyrosine kinase", ["c-Met", "HGFR"], ["oncology"]),
    ("ALK", "ALK receptor tyrosine kinase", ["ALK"], ["oncology"]),
    ("ROS1", "ROS proto-oncogene 1", ["ROS1"], ["oncology"]),
    ("RET", "ret proto-oncogene", ["RET"], ["oncology"]),
    ("KIT", "KIT proto-oncogene, receptor tyrosine kinase", ["c-Kit", "CD117"], ["oncology"]),
    ("FLT3", "fms related receptor tyrosine kinase 3", ["FLT3", "CD135"], ["oncology"]),
    ("KDR", "kinase insert domain receptor", ["VEGFR2", "VEGFR-2", "CD309"], ["oncology"]),
    ("VEGFA", "vascular endothelial growth factor A", ["VEGF", "VEGF-A"], ["oncology", "ophthalmology"]),
    ("BRAF", "B-Raf proto-oncogene", ["BRAF", "B-Raf"], ["oncology"]),
    ("KRAS", "KRAS proto-oncogene", ["KRAS", "K-Ras", "KRAS G12C"], ["oncology"]),
    ("NRAS", "NRAS proto-oncogene", ["NRAS"], ["oncology"]),
    ("PIK3CA", "phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha", ["PI3K alpha", "p110alpha"], ["oncology"]),
    ("AKT1", "AKT serine/threonine kinase 1", ["AKT", "PKB"], ["oncology"]),
    ("MTOR", "mechanistic target of rapamycin kinase", ["mTOR", "FRAP1"], ["oncology"]),
    ("CDK4", "cyclin dependent kinase 4", ["CDK4"], ["oncology"]),
    ("CDK6", "cyclin dependent kinase 6", ["CDK6"], ["oncology"]),
    ("CDK7", "cyclin dependent kinase 7", ["CDK7"], ["oncology"]),
    ("CDK9", "cyclin dependent kinase 9", ["CDK9"], ["oncology"]),
    ("PARP1", "poly(ADP-ribose) polymerase 1", ["PARP", "PARP-1"], ["oncology"]),
    ("ATM", "ATM serine/threonine kinase", ["ATM"], ["oncology"]),
    ("ATR", "ATR serine/threonine kinase", ["ATR"], ["oncology"]),
    ("WEE1", "WEE1 G2 checkpoint kinase", ["WEE1"], ["oncology"]),
    ("CHEK1", "checkpoint kinase 1", ["CHK1"], ["oncology"]),
    ("BCL2", "BCL2 apoptosis regulator", ["Bcl-2"], ["oncology"]),
    ("MCL1", "MCL1 apoptosis regulator", ["MCL-1"], ["oncology"]),
    ("MDM2", "MDM2 proto-oncogene", ["MDM2", "HDM2"], ["oncology"]),
    ("TP53", "tumor protein p53", ["p53"], ["oncology"]),
    ("EZH2", "enhancer of zeste 2 polycomb repressive complex 2 subunit", ["EZH2"], ["oncology"]),
    ("KMT2A", "lysine methyltransferase 2A", ["MLL", "MLL1"], ["oncology"]),
    ("MEN1", "menin 1", ["menin"], ["oncology"]),
    ("IDH1", "isocitrate dehydrogenase (NADP(+)) 1", ["IDH1"], ["oncology"]),
    ("IDH2", "isocitrate dehydrogenase (NADP(+)) 2", ["IDH2"], ["oncology"]),
    ("BTK", "Bruton tyrosine kinase", ["BTK"], ["oncology", "immunology"]),
    ("BCR", "BCR activator of RhoGEF and GTPase", ["BCR-ABL", "BCR::ABL1"], ["oncology"]),
    ("ABL1", "ABL proto-oncogene 1", ["ABL", "c-Abl"], ["oncology"]),
    ("JAK1", "Janus kinase 1", ["JAK1"], ["immunology", "oncology"]),
    ("JAK2", "Janus kinase 2", ["JAK2"], ["oncology", "haematology"]),
    ("JAK3", "Janus kinase 3", ["JAK3"], ["immunology"]),
    ("TYK2", "tyrosine kinase 2", ["TYK2"], ["immunology"]),
    ("FGFR1", "fibroblast growth factor receptor 1", ["FGFR1"], ["oncology"]),
    ("FGFR2", "fibroblast growth factor receptor 2", ["FGFR2"], ["oncology"]),
    ("FGFR3", "fibroblast growth factor receptor 3", ["FGFR3"], ["oncology"]),
    ("PDGFRA", "platelet derived growth factor receptor alpha", ["PDGFR-alpha"], ["oncology"]),
    ("AR", "androgen receptor", ["AR"], ["oncology"]),
    ("ESR1", "estrogen receptor 1", ["ER", "ER-alpha"], ["oncology"]),
    ("PGR", "progesterone receptor", ["PR"], ["oncology"]),
    ("SMO", "smoothened, frizzled class receptor", ["SMO"], ["oncology"]),
    ("CSF1R", "colony stimulating factor 1 receptor", ["CSF1R", "CD115"], ["oncology"]),
    ("CXCR4", "C-X-C motif chemokine receptor 4", ["CXCR4", "CD184"], ["oncology"]),
    ("STING1", "stimulator of interferon response cGAMP interactor 1", ["STING", "TMEM173"], ["oncology"]),
    ("CGAS", "cyclic GMP-AMP synthase", ["cGAS", "MB21D1"], ["oncology", "immunology"]),
    ("TLR7", "toll like receptor 7", ["TLR7"], ["immunology", "oncology"]),
    ("TLR9", "toll like receptor 9", ["TLR9"], ["immunology"]),

    # ── Immunology and inflammation ────────────────────────────────────────
    ("TNF", "tumor necrosis factor", ["TNF-alpha", "TNFA", "TNFα"], ["immunology"]),
    ("IL6", "interleukin 6", ["IL-6"], ["immunology"]),
    ("IL6R", "interleukin 6 receptor", ["IL-6R", "CD126"], ["immunology"]),
    ("IL1B", "interleukin 1 beta", ["IL-1beta", "IL-1b"], ["immunology"]),
    ("IL17A", "interleukin 17A", ["IL-17A", "IL-17"], ["immunology"]),
    ("IL17RA", "interleukin 17 receptor A", ["IL-17RA", "CD217"], ["immunology"]),
    ("IL23A", "interleukin 23 subunit alpha", ["IL-23", "IL-23p19", "p19"], ["immunology"]),
    ("IL12B", "interleukin 12B", ["IL-12p40", "p40"], ["immunology"]),
    ("IL4", "interleukin 4", ["IL-4"], ["immunology"]),
    ("IL4R", "interleukin 4 receptor", ["IL-4Ralpha", "CD124"], ["immunology"]),
    ("IL5", "interleukin 5", ["IL-5"], ["immunology"]),
    ("IL13", "interleukin 13", ["IL-13"], ["immunology"]),
    ("IL33", "interleukin 33", ["IL-33"], ["immunology"]),
    ("IL1RL1", "interleukin 1 receptor like 1", ["ST2", "IL-33R"], ["immunology"]),
    ("TSLP", "thymic stromal lymphopoietin", ["TSLP"], ["immunology"]),
    ("IL2", "interleukin 2", ["IL-2"], ["immunology", "oncology"]),
    ("IL2RA", "interleukin 2 receptor subunit alpha", ["CD25", "IL-2Ralpha"], ["immunology", "oncology"]),
    ("IL15", "interleukin 15", ["IL-15"], ["immunology", "oncology"]),
    ("IL18", "interleukin 18", ["IL-18"], ["immunology"]),
    ("IFNG", "interferon gamma", ["IFN-gamma", "IFNg"], ["immunology"]),
    ("IFNAR1", "interferon alpha and beta receptor subunit 1", ["IFNAR1", "IFNAR"], ["immunology"]),
    ("TNFSF15", "TNF superfamily member 15", ["TL1A", "VEGI"], ["immunology"]),
    ("TNFRSF25", "TNF receptor superfamily member 25", ["DR3"], ["immunology"]),
    ("ITGA4", "integrin subunit alpha 4", ["VLA-4", "CD49d"], ["immunology", "neurology"]),
    ("ITGB7", "integrin subunit beta 7", ["beta7 integrin"], ["immunology"]),
    ("ITGAE", "integrin subunit alpha E", ["CD103"], ["immunology"]),
    ("MADCAM1", "mucosal vascular addressin cell adhesion molecule 1", ["MAdCAM-1"], ["immunology"]),
    ("S1PR1", "sphingosine-1-phosphate receptor 1", ["S1P1", "S1PR1"], ["immunology", "neurology"]),
    ("C5", "complement C5", ["C5"], ["immunology", "haematology"]),
    ("C3", "complement C3", ["C3"], ["immunology", "ophthalmology"]),
    ("CFB", "complement factor B", ["Factor B"], ["immunology"]),
    ("MASP2", "MBL associated serine protease 2", ["MASP-2"], ["immunology"]),
    ("FCGRT", "Fc gamma receptor and transporter", ["FcRn"], ["immunology", "neurology"]),
    ("CD38", "CD38 molecule", ["CD38"], ["oncology", "immunology"]),
    ("MAP3K14", "mitogen-activated protein kinase kinase kinase 14", ["NIK"], ["immunology"]),
    ("IRAK4", "interleukin 1 receptor associated kinase 4", ["IRAK4", "IRAK-4"], ["immunology"]),
    ("RIPK1", "receptor interacting serine/threonine kinase 1", ["RIP1", "RIPK1"], ["immunology"]),
    ("NLRP3", "NLR family pyrin domain containing 3", ["NLRP3", "cryopyrin"], ["immunology"]),
    ("STAT3", "signal transducer and activator of transcription 3", ["STAT3"], ["immunology", "oncology"]),
    ("STAT6", "signal transducer and activator of transcription 6", ["STAT6"], ["immunology"]),
    ("PDE4B", "phosphodiesterase 4B", ["PDE4B", "PDE4"], ["immunology", "respiratory"]),
    ("SYK", "spleen associated tyrosine kinase", ["SYK"], ["immunology", "haematology"]),
    ("LILRB4", "leukocyte immunoglobulin like receptor B4", ["ILT3", "LILRB4"], ["oncology", "immunology"]),
    ("SIGLEC8", "sialic acid binding Ig like lectin 8", ["Siglec-8"], ["immunology"]),
    ("KIT", "KIT proto-oncogene", ["c-Kit", "CD117"], ["immunology", "oncology"]),
    ("CCR9", "C-C motif chemokine receptor 9", ["CCR9"], ["immunology"]),
    ("CX3CR1", "C-X3-C motif chemokine receptor 1", ["CX3CR1"], ["immunology", "neurology"]),

    # ── Metabolic and cardiovascular ───────────────────────────────────────
    ("GLP1R", "glucagon like peptide 1 receptor", ["GLP-1R", "GLP1R"], ["metabolic"]),
    ("GIPR", "gastric inhibitory polypeptide receptor", ["GIPR", "GIP receptor"], ["metabolic"]),
    ("GCGR", "glucagon receptor", ["GCGR"], ["metabolic"]),
    ("PCSK9", "proprotein convertase subtilisin/kexin type 9", ["PCSK9"], ["cardiovascular"]),
    ("LPA", "lipoprotein(a)", ["Lp(a)", "apo(a)"], ["cardiovascular"]),
    ("ANGPTL3", "angiopoietin like 3", ["ANGPTL3"], ["cardiovascular"]),
    ("APOC3", "apolipoprotein C3", ["ApoC-III"], ["cardiovascular"]),
    ("HMGCR", "3-hydroxy-3-methylglutaryl-CoA reductase", ["HMG-CoA reductase"], ["cardiovascular"]),
    ("SLC5A2", "solute carrier family 5 member 2", ["SGLT2", "SGLT-2"], ["metabolic"]),
    ("DPP4", "dipeptidyl peptidase 4", ["DPP-4", "CD26"], ["metabolic"]),
    ("MC4R", "melanocortin 4 receptor", ["MC4R"], ["metabolic"]),
    ("GDF15", "growth differentiation factor 15", ["GDF15", "MIC-1"], ["metabolic"]),
    ("FGF21", "fibroblast growth factor 21", ["FGF21"], ["metabolic"]),
    ("THRB", "thyroid hormone receptor beta", ["THR-beta"], ["metabolic"]),
    ("ACVR1C", "activin A receptor type 1C", ["ALK7"], ["metabolic"]),
    ("MSTN", "myostatin", ["GDF8", "myostatin"], ["metabolic"]),
    ("ACVR2A", "activin A receptor type 2A", ["ActRIIA"], ["metabolic"]),
    ("NPPA", "natriuretic peptide A", ["ANP"], ["cardiovascular"]),
    ("MYBPC3", "myosin binding protein C3", ["MYBPC3"], ["cardiovascular"]),
    ("MYH7", "myosin heavy chain 7", ["beta-myosin"], ["cardiovascular"]),
    ("TTR", "transthyretin", ["TTR", "prealbumin"], ["cardiovascular", "neurology"]),
    ("F11", "coagulation factor XI", ["Factor XI", "FXI"], ["cardiovascular", "haematology"]),
    ("F12", "coagulation factor XII", ["Factor XII", "FXII"], ["haematology"]),
    ("KLKB1", "kallikrein B1", ["plasma kallikrein"], ["immunology"]),
    ("SERPING1", "serpin family G member 1", ["C1-INH", "C1 esterase inhibitor"], ["immunology"]),

    # ── Neurology and psychiatry ───────────────────────────────────────────
    ("SNCA", "synuclein alpha", ["alpha-synuclein", "a-syn"], ["neurology"]),
    ("MAPT", "microtubule associated protein tau", ["tau"], ["neurology"]),
    ("APP", "amyloid beta precursor protein", ["APP", "amyloid beta", "Abeta"], ["neurology"]),
    ("APOE", "apolipoprotein E", ["ApoE", "ApoE4"], ["neurology"]),
    ("TREM2", "triggering receptor expressed on myeloid cells 2", ["TREM2"], ["neurology"]),
    ("LRRK2", "leucine rich repeat kinase 2", ["LRRK2"], ["neurology"]),
    ("GBA1", "glucosylceramidase beta 1", ["GBA", "GCase"], ["neurology"]),
    ("HTT", "huntingtin", ["huntingtin", "HTT"], ["neurology"]),
    ("SOD1", "superoxide dismutase 1", ["SOD1"], ["neurology"]),
    ("SMN1", "survival of motor neuron 1", ["SMN1", "SMN"], ["neurology"]),
    ("DMD", "dystrophin", ["dystrophin"], ["neurology"]),
    ("CALCA", "calcitonin related polypeptide alpha", ["CGRP", "alpha-CGRP"], ["neurology"]),
    ("CALCRL", "calcitonin receptor like receptor", ["CGRP receptor", "CLR"], ["neurology"]),
    ("HCRTR2", "hypocretin receptor 2", ["OX2R", "orexin receptor 2"], ["neurology"]),
    ("SCN9A", "sodium voltage-gated channel alpha subunit 9", ["Nav1.7", "NaV1.7"], ["neurology"]),
    ("SCN2A", "sodium voltage-gated channel alpha subunit 2", ["Nav1.2"], ["neurology"]),
    ("KCNT1", "potassium sodium-activated channel subfamily T member 1", ["KCNT1", "Slack"], ["neurology"]),
    ("CHRM1", "cholinergic receptor muscarinic 1", ["M1 receptor"], ["neurology", "psychiatry"]),
    ("CHRM4", "cholinergic receptor muscarinic 4", ["M4 receptor"], ["psychiatry"]),
    ("GRIN2B", "glutamate ionotropic receptor NMDA type subunit 2B", ["NR2B", "NMDA"], ["psychiatry"]),
    ("HTR2A", "5-hydroxytryptamine receptor 2A", ["5-HT2A"], ["psychiatry"]),
    ("TAAR1", "trace amine associated receptor 1", ["TAAR1"], ["psychiatry"]),
    ("OPRK1", "opioid receptor kappa 1", ["KOR", "kappa opioid receptor"], ["psychiatry"]),

    # ── Respiratory, renal, ophthalmology, fibrosis ────────────────────────
    ("CFTR", "CF transmembrane conductance regulator", ["CFTR"], ["respiratory"]),
    ("SERPINA1", "serpin family A member 1", ["alpha-1 antitrypsin", "AAT"], ["respiratory"]),
    ("TGFB1", "transforming growth factor beta 1", ["TGF-beta1", "TGFb"], ["fibrosis", "oncology"]),
    ("LOXL2", "lysyl oxidase like 2", ["LOXL2"], ["fibrosis"]),
    ("ITGAV", "integrin subunit alpha V", ["alphaV integrin"], ["fibrosis"]),
    ("AGT", "angiotensinogen", ["AGT", "angiotensinogen"], ["cardiovascular"]),
    ("APOL1", "apolipoprotein L1", ["APOL1"], ["renal"]),
    ("SCNN1A", "sodium channel epithelial 1 subunit alpha", ["ENaC", "alpha-ENaC"], ["respiratory", "renal"]),
    ("CFH", "complement factor H", ["Factor H", "CFH"], ["ophthalmology"]),
    ("ANGPT2", "angiopoietin 2", ["Ang-2"], ["ophthalmology"]),
    ("HIF1A", "hypoxia inducible factor 1 subunit alpha", ["HIF-1alpha"], ["oncology", "renal"]),
    ("EPAS1", "endothelial PAS domain protein 1", ["HIF-2alpha", "HIF2A"], ["oncology", "renal"]),

    # ── Infectious disease ─────────────────────────────────────────────────
    ("ACE2", "angiotensin converting enzyme 2", ["ACE2"], ["infectious disease"]),
    ("TMPRSS2", "transmembrane serine protease 2", ["TMPRSS2"], ["infectious disease", "oncology"]),
    ("CCR5", "C-C motif chemokine receptor 5", ["CCR5", "CD195"], ["infectious disease"]),
]


def main() -> int:
    seen: dict[str, dict] = {}
    for symbol, name, aliases, areas in SEED:
        if symbol in seen:
            # Merge duplicates rather than letting the later one win silently.
            seen[symbol]["aliases"] = sorted(set(seen[symbol]["aliases"]) | set(aliases))
            seen[symbol]["areas"] = sorted(set(seen[symbol]["areas"]) | set(areas))
            continue
        seen[symbol] = {
            "symbol": symbol,
            "name": name,
            "aliases": sorted(set(aliases) - {symbol}),
            "areas": sorted(areas),
            "source": "seed",
        }

    # Guard against pseudo-symbols. A record whose "symbol" is really a
    # protein nickname (Nav1.7, SGLT2, ENaC) resolves to nothing downstream,
    # so it must be an alias of the approved symbol instead.
    import re

    bad = [s_ for s_ in seen if not re.match(r"^[A-Z][A-Z0-9-]{1,14}$", s_)]
    if bad:
        raise SystemExit("not approved gene symbols: " + ", ".join(bad))

    records = [seen[k] for k in sorted(seen)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "records": records}, fh, ensure_ascii=False, indent=1)

    areas: dict[str, int] = {}
    for record in records:
        for area in record["areas"]:
            areas[area] = areas.get(area, 0) + 1
    print(f"{OUT} — {len(records)} targets")
    for area, count in sorted(areas.items(), key=lambda kv: -kv[1]):
        print(f"  {area:20} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
