"""What each modality is, and what it demands of a target.

A modality label on an asset row is nearly useless on its own. "Antibody-drug
conjugate" tells a reader what the molecule is; it does not tell them the
thing they need, which is that an ADC only works if the antigen *internalises*
after binding, so a beautifully tumour-specific surface antigen that sits
still is a dead ADC target no matter how good the antibody is. That
requirement is stable, public, well known inside the field, and absent from
every free database — which makes it exactly the kind of thing this tool
should carry.

So each entry below has four parts, in descending order of how often they
change someone's mind:

  ``requires``  what has to be true of the target. This is the part that
                turns a landscape into a judgement, because it can be checked
                against the target's own biology — see ``fit``.
  ``fails``     how programmes on this modality actually die, as opposed to
                how they are pitched.
  ``economics`` rough time and capital to a first human readout, so that a
                seed-stage plan can be sanity-checked against it.
  ``what``      the one-line definition, for the reader who needs it.

The numbers in ``economics`` are industry rules of thumb with wide variance,
not measurements, and the interface labels them as such. They are here
because an angel investor looking at a CAR-T seed round with an 18-month
plan to the clinic needs a reference point, and a wrong-by-half reference
point still catches that.

Nothing in this file is generated. It is a hand-written reference, revised
deliberately, and the tool says so wherever it is displayed.
"""

from __future__ import annotations

from typing import Any, Optional

# Compartment vocabulary used to check a modality against a target. Derived
# from UniProt subcellular location strings, which are free text with a
# controlled-ish core.
SURFACE_HINTS = (
    "cell membrane", "plasma membrane", "cell surface", "membrane raft",
    "apical", "basolateral", "single-pass", "multi-pass", "gpi-anchor",
)
SECRETED_HINTS = ("secreted", "extracellular space", "extracellular matrix", "extracellular region")
INTRACELLULAR_HINTS = (
    "cytoplasm", "cytosol", "nucleus", "nucleoplasm", "mitochond", "endoplasmic",
    "golgi", "lysosome", "peroxisome", "endosome", "ribosome", "centrosome",
    "cytoskeleton", "chromosome",
)


def compartment(locations: list[str]) -> dict[str, Any]:
    """Reduce UniProt location strings to the distinction modalities care about.

    A protein can be in several of these at once — a receptor that is also
    shed, a kinase that shuttles to the nucleus — so this reports every
    compartment found rather than picking one, and says plainly when it found
    none. "Unknown" must never be read as "intracellular"; several of the
    checks below depend on that.
    """
    lowered = [(loc or "").lower() for loc in locations]
    found = {
        "surface": any(any(h in loc for h in SURFACE_HINTS) for loc in lowered),
        "secreted": any(any(h in loc for h in SECRETED_HINTS) for loc in lowered),
        "intracellular": any(any(h in loc for h in INTRACELLULAR_HINTS) for loc in lowered),
    }
    labels = [k for k, v in found.items() if v]
    return {
        **found,
        "known": bool(labels),
        "labels": labels,
        "accessible": found["surface"] or found["secreted"],
        "locations": locations,
    }


# ---------------------------------------------------------------------------
# The primer
# ---------------------------------------------------------------------------
#
# ``key`` matches landscape.models.MODALITIES where one exists; the extra
# entries (degrader, siRNA/ASO, mRNA, gene therapy) are modalities a reader
# will ask about even when no asset on the target uses one yet.

MODALITIES: list[dict[str, Any]] = [
    {
        "key": "Monoclonal antibody",
        "aliases": ["mAb", "antibody", "单抗"],
        "what": (
            "A single antibody binding one epitope, used to block a receptor or ligand, "
            "or to kill the cell it is bound to through Fc-mediated effector function."
        ),
        "requires": [
            "The target is on the cell surface or secreted. An antibody cannot cross the "
            "plasma membrane, so an intracellular target rules the modality out entirely.",
            "The epitope is accessible on the folded protein in vivo, not only on a "
            "recombinant fragment.",
            "For blockade: the interaction being blocked is rate-limiting for the disease. "
            "Antibodies are exquisite blockers of a single interaction and useless against "
            "a redundant pathway.",
        ],
        "fails": [
            "The biology, not the molecule. Antibody CMC and safety are now routine; the "
            "great majority of antibody failures are the target being wrong.",
            "Soluble decoy: a shed extracellular domain circulating in patients absorbs "
            "drug and flattens the dose-response.",
            "Poor tissue penetration in solid tumours and behind the blood-brain barrier "
            "(roughly 0.1% of a systemic dose reaches the CNS).",
        ],
        "economics": "≈18–30 months and $15–40M from lead to first-in-human data.",
        "checks": {"needs": "accessible"},
    },
    {
        "key": "Bispecific antibody",
        "aliases": ["bispecific", "T-cell engager", "TCE", "双抗"],
        "what": (
            "Two binding arms in one molecule: either blocking two pathways at once, or — "
            "far more commonly now — dragging a T cell onto a tumour cell by binding CD3 "
            "with one arm and a tumour antigen with the other."
        ),
        "requires": [
            "Surface expression, as for any antibody.",
            "For a T-cell engager: expression genuinely restricted to the target tissue. "
            "There is no therapeutic index to spend — the drug recruits a cytotoxic T cell "
            "to whatever it binds, so low-level expression on a vital tissue is lethal, "
            "not tolerable.",
            "Enough antigen density to form a synapse, and little antigen shedding.",
        ],
        "fails": [
            "On-target off-tumour toxicity — the dominant cause of death for this class.",
            "Cytokine release syndrome forcing step-up dosing, which lengthens every trial.",
            "Antigen loss under treatment pressure, giving deep early responses that do "
            "not last.",
        ],
        "economics": "≈2–3 years and $25–60M to first-in-human; the dose-escalation is slower "
                     "than a plain antibody because of step-up dosing.",
        "checks": {"needs": "surface"},
    },
    {
        "key": "Antibody-drug conjugate",
        "aliases": ["ADC", "抗体偶联药物"],
        "what": (
            "An antibody used as a delivery vehicle: it carries a cytotoxic payload, is "
            "taken into the cell, and releases the payload inside."
        ),
        "requires": [
            "Surface expression, AND internalisation after binding. This is the "
            "requirement people forget. A non-internalising antigen cannot deliver a "
            "payload, however specific the antibody is.",
            "A real expression differential against normal tissue — the payload is toxic "
            "to any cell it enters.",
            "High enough antigen copy number; the delivered dose scales with it.",
        ],
        "fails": [
            "Payload toxicity sets the dose, not the antibody. Neutropenia, ocular "
            "toxicity and interstitial lung disease are the recurring dose-limiters, and "
            "they are largely payload-class effects you can predict in advance.",
            "Linker instability releasing payload in circulation, which converts a "
            "targeted drug into a systemic chemotherapy.",
            "A narrow therapeutic index that looks fine in xenografts and disappears in "
            "patients with normal-tissue expression.",
        ],
        "economics": "≈2.5–4 years and $40–90M to first-in-human. Manufacturing and COGS are "
                     "materially higher than a naked antibody — worth modelling early.",
        "checks": {"needs": "surface", "note": "internalisation"},
    },
    {
        "key": "Fc-fusion / ligand trap",
        "aliases": ["ligand trap", "decoy receptor", "Fc融合"],
        "what": (
            "The receptor's binding domain fused to an antibody Fc, used to mop up a "
            "soluble ligand before it reaches its receptor."
        ),
        "requires": [
            "The ligand is soluble and is the rate-limiting element — trapping does "
            "nothing against a membrane-bound or juxtacrine signal.",
            "The trap does not also sequester a ligand you need.",
        ],
        "fails": [
            "Ligand redundancy: a trap for one cytokine in a family where three do the "
            "same job produces a clean pharmacodynamic result and no clinical effect.",
            "Very high ligand turnover demanding impractical doses.",
        ],
        "economics": "Similar to a monoclonal antibody. Often faster, because the binding "
                     "domain is the native sequence rather than a discovery problem.",
        "checks": {"needs": "accessible"},
        "bd_note": (
            "Commercially this is the modality that most often sits in a different patent "
            "estate from the receptor antibodies on the same axis — worth checking when "
            "a target looks crowded on paper."
        ),
    },
    {
        "key": "Small molecule",
        "aliases": ["小分子", "inhibitor"],
        "what": (
            "A synthetic compound, usually under 500 daltons, binding a pocket on the "
            "target to block or modulate its activity."
        ),
        "requires": [
            "A defined binding pocket. Enzymes, GPCRs, ion channels and nuclear receptors "
            "have one; flat protein–protein interfaces and scaffolding proteins largely "
            "do not, which is what 'undruggable' has historically meant.",
            "Selectivity that is achievable against the rest of the family — the "
            "practical constraint on most kinase programmes.",
        ],
        "fails": [
            "Off-target and family cross-reactivity producing dose-limiting toxicity "
            "before the target is fully engaged.",
            "Idiosyncratic hepatotoxicity, which appears late and kills programmes at "
            "Phase 2–3.",
            "Resistance mutations in the pocket, in oncology and infectious disease.",
        ],
        "economics": "≈3–5 years and $10–30M from hit to first-in-human — cheaper per step "
                     "than a biologic, with a longer discovery phase.",
        "checks": {"needs": "any", "prefers_intracellular": True},
        "bd_note": (
            "The only class here that routinely reaches intracellular targets and the CNS, "
            "and the only one where oral dosing is the default. Both matter more to "
            "commercial value than potency does."
        ),
    },
    {
        "key": "Molecular glue / degrader",
        "aliases": ["PROTAC", "degrader", "分子胶", "molecular glue"],
        "what": (
            "A small molecule that forces the target into contact with an E3 ubiquitin "
            "ligase, so the cell's own machinery destroys it. Removing the protein rather "
            "than inhibiting it."
        ),
        "requires": [
            "An intracellular target — the machinery is cytoplasmic.",
            "A ligandable surface anywhere on the protein. Crucially this need NOT be a "
            "functional active site, which is why degraders reach scaffolding and "
            "transcription-factor targets that defeated inhibitors.",
            "The relevant E3 ligase is expressed in the tissue you are treating. "
            "Cereblon and VHL are the workhorses and their expression is not uniform.",
        ],
        "fails": [
            "Drug-like properties: bifunctional degraders are large and greasy, and oral "
            "bioavailability is the recurring reason a good degrader never becomes a drug. "
            "Monovalent glues avoid much of this and are correspondingly sought after.",
            "The hook effect — too much drug forms binary rather than ternary complexes "
            "and degradation falls off at high dose, inverting the usual dose intuition.",
            "Resistance through loss of the E3 ligase itself, seen clinically with "
            "cereblon.",
        ],
        "economics": "≈3–5 years to first-in-human. Ternary-complex optimisation is the long "
                     "pole; budget more medicinal chemistry than a conventional inhibitor.",
        "checks": {"needs": "intracellular"},
        "bd_note": (
            "The reason to care commercially: a degrader can open a target that an "
            "inhibitor could not, which resets the competitive clock on a mechanism that "
            "otherwise looks worked-out."
        ),
    },
    {
        "key": "Oligonucleotide",
        "aliases": ["siRNA", "ASO", "antisense", "RNAi", "核酸药物"],
        "what": (
            "A short nucleic acid that degrades or blocks the target's mRNA, lowering the "
            "amount of protein made rather than blocking the protein itself."
        ),
        "requires": [
            "Only that the target is a gene. Protein structure is irrelevant, so "
            "'undruggable' in the small-molecule sense does not apply — this is the "
            "modality's whole appeal.",
            "That the disease-relevant tissue can be reached. This is the entire risk. "
            "GalNAc conjugation makes hepatocyte targets close to routine; intrathecal "
            "dosing reaches the CNS; the eye is feasible. Most other tissues are still an "
            "open delivery problem.",
            "That lowering the protein is therapeutic — a loss-of-function target, not a "
            "gain-of-function one.",
        ],
        "fails": [
            "Delivery, overwhelmingly. A programme aimed outside liver, CNS and eye is "
            "underwriting a delivery invention, and should be priced as one.",
            "Durable knockdown creating durable toxicity, with no way to withdraw the drug.",
            "Hepatotoxicity and thrombocytopenia as class effects for some chemistries.",
        ],
        "economics": "≈2–3 years and $15–35M to first-in-human for a liver target, and "
                     "considerably more anywhere else. Discovery is fast because the "
                     "sequence is designed rather than screened.",
        "checks": {"needs": "any", "tissue_gate": True},
    },
    {
        "key": "mRNA",
        "aliases": ["mRNA", "信使RNA"],
        "what": (
            "Delivered mRNA instructing the patient's own cells to make a protein — a "
            "vaccine antigen, a missing enzyme, or a therapeutic antibody."
        ),
        "requires": [
            "That ADDING protein helps. This inverts the usual target logic: mRNA suits "
            "loss-of-function biology, and has nothing to offer against a target you want "
            "to block.",
            "That transient expression is enough, or that repeat dosing is tolerable.",
            "A delivery route to the relevant tissue — in practice muscle for vaccines and "
            "liver for systemic LNPs.",
        ],
        "fails": [
            "Durability: expression is measured in days, so chronic replacement means "
            "chronic redosing.",
            "Reactogenicity from the lipid nanoparticle, which limits dose.",
            "Redosing immunogenicity against the carrier.",
        ],
        "economics": "Fast to a first construct — weeks — and slow through CMC. ≈2–3 years "
                     "and $20–50M to first-in-human outside the vaccine setting.",
        "checks": {"needs": "any", "direction": "restore"},
        "speculative": True,
    },
    {
        "key": "Cell therapy (CAR-T)",
        "aliases": ["CAR-T", "cell therapy", "细胞治疗"],
        "what": (
            "A patient's or donor's T cells engineered with a receptor against a surface "
            "antigen, expanded, and infused back as a living drug."
        ),
        "requires": [
            "Surface expression with near-absolute tissue restriction. The cells persist "
            "and multiply, so there is no dose to back off — anything the CAR recognises "
            "will be destroyed for as long as the cells live.",
            "The antigen is present on essentially every malignant cell, or escape is "
            "immediate.",
            "A tolerable consequence if the normal tissue carrying the antigen is also "
            "destroyed — B-cell aplasia after CD19 is survivable, and that is why CD19 "
            "worked first.",
        ],
        "fails": [
            "On-target off-tumour toxicity, which in this modality has been fatal rather "
            "than dose-limiting.",
            "Antigen escape driving relapse after deep remission.",
            "The solid-tumour wall: trafficking, persistence and an immunosuppressive "
            "microenvironment. Success remains overwhelmingly haematological.",
            "Manufacturing — vein-to-vein time, failure rates and cost of goods are "
            "commercial risks, not technical footnotes.",
        ],
        "economics": "≈3–5 years and $50–150M to meaningful clinical data, with process "
                     "development a large fraction of it. Any seed plan much shorter than "
                     "this is worth interrogating.",
        "checks": {"needs": "surface", "note": "restriction"},
    },
    {
        "key": "Peptide",
        "aliases": ["peptide", "多肽"],
        "what": "A short chain of amino acids, typically engaging an extracellular receptor "
                "or a protein–protein interface too flat for a small molecule.",
        "requires": [
            "An extracellular or accessible binding site, unless a cell-penetrating "
            "strategy is part of the plan.",
            "A tolerable half-life, which usually means engineering — lipidation, "
            "cyclisation or fusion. Native peptides are cleared in minutes.",
        ],
        "fails": [
            "Pharmacokinetics rather than pharmacology.",
            "Injection-only delivery in an oral market, which caps commercial value even "
            "when the biology works.",
        ],
        "economics": "≈2–3 years and $10–30M to first-in-human.",
        "checks": {"needs": "accessible"},
    },
    {
        "key": "Gene therapy",
        "aliases": ["AAV", "gene therapy", "基因治疗"],
        "what": "A viral vector delivering a working copy of a gene, intended as a single "
                "administration.",
        "requires": [
            "Monogenic loss-of-function biology with a well-understood causal gene.",
            "A tissue an AAV serotype actually reaches, at a dose that is safe.",
            "Patients without pre-existing neutralising antibodies to the capsid, which "
            "excludes a large fraction of any population.",
        ],
        "fails": [
            "Dose-dependent hepatotoxicity and complement activation at the high systemic "
            "doses that non-CNS, non-ocular tissues require.",
            "One-shot dosing with no redose path if expression fades.",
            "A commercial model that has repeatedly failed on tiny populations and very "
            "high prices — a real diligence issue, not only a scientific one.",
        ],
        "economics": "≈4–6 years and $80M+ to clinical data; CMC dominates the budget.",
        "checks": {"needs": "any", "direction": "restore"},
        "speculative": True,
    },
    {
        "key": "Vaccine",
        "aliases": ["vaccine", "疫苗"],
        "what": "An immunogen intended to raise the patient's own immune response against "
                "the target or the cells carrying it.",
        "requires": [
            "The target is immunogenic and not subject to central tolerance — the "
            "recurring obstacle for self-antigen cancer vaccines.",
            "A patient population with an immune system intact enough to respond.",
        ],
        "fails": [
            "Immune responses that are measurable and clinically inert — the most common "
            "outcome in therapeutic cancer vaccines.",
            "Long, large, slow efficacy trials that are expensive to run.",
        ],
        "economics": "Highly variable. Prophylactic trials are among the largest in medicine.",
        "checks": {"needs": "any"},
        "speculative": True,
    },
]

BY_KEY = {entry["key"]: entry for entry in MODALITIES}

_ALIAS_INDEX: dict[str, dict[str, Any]] = {}
for _entry in MODALITIES:
    _ALIAS_INDEX[_entry["key"].lower()] = _entry
    for _alias in _entry.get("aliases") or []:
        _ALIAS_INDEX[_alias.lower()] = _entry


def lookup(name: str) -> Optional[dict[str, Any]]:
    """Find a primer entry by modality name or common alias."""
    return _ALIAS_INDEX.get((name or "").strip().lower())


# ---------------------------------------------------------------------------
# Fit
# ---------------------------------------------------------------------------

FIT_VERDICTS = {
    "available": "Physically available",
    "concern": "Check before committing",
    "blocked": "Ruled out by location",
    "unknown": "Cannot tell from public data",
}


def fit(entry: dict[str, Any], target_compartment: dict[str, Any]) -> dict[str, str]:
    """Is this modality physically available against this target?

    A deliberately narrow question. It answers only whether the target is in a
    place the modality can reach — which is a hard constraint, unlike potency
    or selectivity, and therefore the one worth automating. Everything else in
    ``requires`` needs a human, and the interface shows those requirements
    next to this verdict rather than pretending to have checked them.

    Unknown location returns "unknown", never a pass. Asserting that an
    antibody can reach a target whose location nobody has annotated would be
    the one failure mode of this section that actually costs someone money.
    """
    needs = (entry.get("checks") or {}).get("needs", "any")
    comp = target_compartment

    if needs == "any":
        return {"verdict": "available", "label": FIT_VERDICTS["available"],
                "reason": "This modality is not constrained by where the protein sits."}

    if not comp.get("known"):
        return {"verdict": "unknown", "label": FIT_VERDICTS["unknown"],
                "reason": "No subcellular location is annotated for this target, so the "
                          "physical constraint cannot be checked either way."}

    where = ", ".join(comp["labels"])

    if needs == "surface":
        if comp["surface"]:
            return {"verdict": "available", "label": FIT_VERDICTS["available"],
                    "reason": f"Annotated at the cell surface ({where})."}
        if comp["secreted"]:
            return {"verdict": "blocked", "label": FIT_VERDICTS["blocked"],
                    "reason": "Secreted, not membrane-bound. There is no cell to bind, so "
                              "payload delivery and cell killing have nothing to act on."}
        return {"verdict": "blocked", "label": FIT_VERDICTS["blocked"],
                "reason": f"Annotated {where} only — nothing on the surface to bind."}

    if needs == "accessible":
        if comp["accessible"]:
            return {"verdict": "available", "label": FIT_VERDICTS["available"],
                    "reason": f"Reachable from outside the cell ({where})."}
        return {"verdict": "blocked", "label": FIT_VERDICTS["blocked"],
                "reason": f"Annotated {where}. Antibodies do not cross the plasma membrane."}

    if needs == "intracellular":
        if comp["intracellular"]:
            return {"verdict": "available", "label": FIT_VERDICTS["available"],
                    "reason": f"Intracellular ({where}), where the degradation machinery is."}
        return {"verdict": "blocked", "label": FIT_VERDICTS["blocked"],
                "reason": f"Annotated {where}. The ubiquitin–proteasome system cannot reach "
                          "a protein outside the cell."}

    return {"verdict": "unknown", "label": FIT_VERDICTS["unknown"], "reason": ""}


def options_for(target_compartment: dict[str, Any], present: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """The full modality table for one target, with fit and what is already tried.

    ``present`` is the set of modalities that already appear in the asset
    table. Showing which modalities are physically available but *unused* is
    the modality-level equivalent of indication whitespace, and it is usually
    the most interesting column on the page for someone looking at an early
    company: a target where antibodies are crowded and degraders are
    untouched is a different investment from one where everything has been
    tried.
    """
    present_set = {p.strip().lower() for p in (present or [])}
    rows: list[dict[str, Any]] = []
    for entry in MODALITIES:
        verdict = fit(entry, target_compartment)
        in_use = entry["key"].lower() in present_set
        rows.append({
            "key": entry["key"],
            "what": entry["what"],
            "requires": entry["requires"],
            "fails": entry["fails"],
            "economics": entry["economics"],
            "bd_note": entry.get("bd_note", ""),
            "fit": verdict["verdict"],
            "fit_label": verdict["label"],
            "fit_reason": verdict["reason"],
            "in_use": in_use,
            # Modalities that reach any target are not thereby an opportunity
            # on every target. A vaccine or a gene therapy needs a reason of
            # its own — loss-of-function biology, an immunogenic antigen —
            # that no location check can supply, so they are marked and never
            # promoted as an untried opening.
            "speculative": bool(entry.get("speculative")),
        })
    order = {"available": 0, "unknown": 1, "concern": 2, "blocked": 3}
    rows.sort(key=lambda r: (r["speculative"], order.get(r["fit"], 4), not r["in_use"], r["key"]))
    return rows
