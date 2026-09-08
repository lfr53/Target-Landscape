"""Modality and mechanism classification.

Counting assets against a target is a search problem. Grouping them by what
they actually do to the target is the analytical step, and it is the one that
changes a conclusion: five antibodies against a receptor are one competitive
situation if they all block the ligand and a completely different one if two
of them deplete the cell.

Two signals are used, in order:

1. **INN stems.** The WHO International Nonproprietary Name scheme encodes
   modality in the suffix — ``-mab`` antibody, ``-cept`` Fc-fusion receptor
   trap, ``-leucel`` autologous cell therapy, ``-siran`` siRNA. This is free,
   deterministic, and works on assets that have no database record at all,
   which is exactly the population the ClinicalTrials.gov sweep turns up.
2. **Mechanism text.** ChEMBL's ``mechanism_of_action`` and ``action_type``,
   plus trial titles, keyed against a mechanism vocabulary.

An optional LLM pass (``landscape.llm``) resolves only what the rules leave
unclassified. Rules first, model second — so a reviewer can reproduce most of
the table by hand, and the model is answerable for a small, inspectable set
of rows rather than the whole analysis.
"""

from __future__ import annotations

import re
from typing import Optional

from ..models import Asset

# ---------------------------------------------------------------------------
# Modality from INN stem
# ---------------------------------------------------------------------------

_INN_STEMS: list[tuple[str, str]] = [
    # Order matters: longer, more specific stems first.
    ("leucel", "Cell therapy (CAR-T)"),
    ("cabtagene", "Cell therapy (CAR-T)"),
    ("cel", "Cell therapy (CAR-T)"),
    ("siran", "Oligonucleotide"),
    ("rsen", "Oligonucleotide"),
    ("nersen", "Oligonucleotide"),
    ("vec", "Other / unclassified"),  # gene therapy vector
    ("cept", "Fc-fusion / ligand trap"),
    ("tinib", "Small molecule"),
    ("ciclib", "Small molecule"),
    ("parib", "Small molecule"),
    ("degib", "Small molecule"),
    ("rafenib", "Small molecule"),
    ("vedotin", "Antibody-drug conjugate"),
    ("deruxtecan", "Antibody-drug conjugate"),
    ("mafodotin", "Antibody-drug conjugate"),
    ("tesirine", "Antibody-drug conjugate"),
    ("govitecan", "Antibody-drug conjugate"),
    ("mab", "Monoclonal antibody"),
    ("tide", "Peptide"),
]

_MODALITY_FROM_TYPE = {
    "antibody": "Monoclonal antibody",
    "protein": "Fc-fusion / ligand trap",
    "small molecule": "Small molecule",
    "oligonucleotide": "Oligonucleotide",
    "oligosaccharide": "Other / unclassified",
    "cell": "Cell therapy (CAR-T)",
    "gene": "Other / unclassified",
    "enzyme": "Other / unclassified",
    "unknown": "Other / unclassified",
}

_TEXT_MODALITY_HINTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bcar[- ]?t\b|chimeric antigen receptor", re.I), "Cell therapy (CAR-T)"),
    # "Dual functional antibody" and "bifunctional antibody" are what Chinese
    # sponsors write on the registry form where a Western one writes
    # "bispecific". Same molecule class, and reading it as unclassified put a
    # PD-1/CTLA-4 bispecific in the same bucket as an unnamed arm label.
    (re.compile(r"\bbispecific|bi-specific|bi?[- ]?functional antibod|"
                r"dual[- ](functional|targeting|specific)|\bbite\b|"
                r"t[- ]cell engager", re.I), "Bispecific antibody"),
    (re.compile(r"antibody[- ]drug conjugate|\badc\b", re.I), "Antibody-drug conjugate"),
    (re.compile(r"\bfusion protein\b|\bdecoy receptor\b|\bfc[- ]fusion\b", re.I), "Fc-fusion / ligand trap"),
    (re.compile(r"\bsirna\b|antisense|\baso\b", re.I), "Oligonucleotide"),
    (re.compile(r"\bvaccine\b", re.I), "Vaccine"),
    # Immunisation platforms, named by the platform rather than by the word.
    # A dendritic-cell preparation, a modified vaccinia vector and a plasmid
    # DNA construct are all active immunisation, and ERBB2 held one of each
    # under "Unclassified".
    (re.compile(r"dendritic cell|\bdc1\b|pulsed dc|"
                r"\bmva[- ]|modified vaccinia|\bpumvc|plasmid dna", re.I), "Vaccine"),
    (re.compile(r"monoclonal antibody\b", re.I), "Monoclonal antibody"),
    # Last, so that bispecific, ADC and CAR win over the bare word. A record
    # that says only "antibody" still says the molecule is an antibody:
    # IL23A's "LY2525623 (IL-23 Antibody)" was the target's one unclassified
    # row, and the classification it was missing is written in its own name.
    (re.compile(r"\bantibod(y|ies)\b|\bmab\b", re.I), "Monoclonal antibody"),
]


def classify_modality(asset: Asset) -> str:
    """Return the best-supported modality label for an asset."""
    haystack = " ".join(
        filter(None, [asset.name, asset.mechanism_text, " ".join(asset.synonyms)])
    )

    # 1. Explicit text always wins — "bispecific BAFF-R/BCMA CAR T" should not
    #    be filed as a plain antibody because the name happens to end in -mab.
    for pattern, modality in _TEXT_MODALITY_HINTS:
        if pattern.search(haystack):
            return modality

    # 2. INN stem on the asset's own name.
    lowered = re.sub(r"[^a-z]", "", asset.name.lower())
    for stem, modality in _INN_STEMS:
        if lowered.endswith(stem):
            return modality

    # 3. Whatever the source database said.
    source_type = (asset.modality or "").strip().lower()
    for key, modality in _MODALITY_FROM_TYPE.items():
        if key in source_type:
            return modality
    if asset.modality in {
        "Monoclonal antibody",
        "Bispecific antibody",
        "Antibody-drug conjugate",
        "Fc-fusion / ligand trap",
        "Cell therapy (CAR-T)",
        "Small molecule",
        "Oligonucleotide",
        "Peptide",
        "Vaccine",
    }:
        return asset.modality
    return "Other / unclassified"


# ---------------------------------------------------------------------------
# Mechanism class
# ---------------------------------------------------------------------------

_DEPLETION_RE = re.compile(
    r"\badcc\b|\bcdc\b|afucosylat|defucosylat|cytolytic|b[- ]cell deplet|deplet", re.I
)
_BLOCK_RE = re.compile(r"antagonist|block|neutralis|neutraliz|inhibit", re.I)
_AGONIST_RE = re.compile(r"agonist|stimulat|activat", re.I)
# "Anti-" names an antibody against whatever follows, and what follows is not
# always a word: ChEMBL writes them as Anti-(Homo sapiens CD274 (...)), which
# the \\w version missed, leaving every such row unclassified.
_ANTI_PREFIX_RE = re.compile(r"\banti[- ][\w(\[]", re.I)
_DEGRADER_RE = re.compile(r"degrader|protac|molecular glue", re.I)

_ACTION_TYPE_MAP = {
    "INHIBITOR": "Inhibition",
    "ANTAGONIST": "Blockade / antagonism",
    "BLOCKER": "Blockade / antagonism",
    "AGONIST": "Agonism",
    "PARTIAL AGONIST": "Agonism",
    "MODULATOR": "Modulation",
    "NEGATIVE ALLOSTERIC MODULATOR": "Modulation",
    "POSITIVE ALLOSTERIC MODULATOR": "Modulation",
    "DEGRADER": "Degradation",
    "OPENER": "Modulation",
}


def classify_mechanism(asset: Asset) -> str:
    """A short mechanism-class label, combining modality and pharmacology.

    The label is the unit the memo clusters on, so it deliberately merges
    modality and action: 'Depleting antibody' and 'Blocking antibody' are
    different competitive propositions even though both are ``-mab`` /
    ``ANTAGONIST`` in every database.
    """
    label = _mechanism_from_the_record(asset)
    # Two different gaps were wearing the same label. PD-1's "Anti-PD-1
    # monoclonal antibody" came out as "Antibody — mechanism unresolved",
    # which reads as though the rules had failed on a molecule -- when the
    # string says exactly what the drug does and the only thing missing is
    # which molecule it is. The sponsor registered a Phase 2 without naming
    # the drug; that is a gap in the record, not in the classification.
    #
    # Only the fall-through labels are replaced. A CD19 CAR-T is unnamed in
    # the same way, but its record does state the mechanism, and "Cell therapy
    # — target-directed CAR" is the more useful of the two true things that
    # can be said about it.
    if getattr(asset, "named_by_class", False) and (
            "unresolved" in label.lower() or label == "Unclassified"):
        return "Named only by class"
    return label


def _mechanism_from_the_record(asset: Asset) -> str:
    text = " ".join(filter(None, [asset.mechanism_text, asset.name]))
    modality = asset.modality

    if modality == "Cell therapy (CAR-T)":
        if re.search(r"bispecific|dual[- ]target|tandem car", text, re.I):
            return "Cell therapy — bispecific CAR"
        if re.search(r"\bligand\b.{0,20}\bcar\b|uses? \w+ as the binding domain", text, re.I):
            return "Cell therapy — ligand-based CAR"
        return "Cell therapy — target-directed CAR"
    if modality == "Antibody-drug conjugate":
        return "ADC — payload delivery"
    if modality == "Bispecific antibody":
        # Not every bispecific is a T-cell engager, and collapsing them says
        # something false about most of the field's current bispecifics. A
        # CD3-binding engager redirects T-cells and carries CRS risk and a
        # step-up dosing schedule; a PD-1/VEGF bispecific such as ivonescimab
        # blocks two pathways in one molecule and behaves like a checkpoint
        # antibody. Calling the second a T-cell engager is the kind of error
        # an oncology reader spots immediately.
        if re.search(r"\bcd3\b|\bbite\b|t[- ]cell engager|redirect", text, re.I):
            return "Bispecific — T-cell engager (CD3)"
        return "Bispecific antibody — dual pathway blockade"
    if modality == "Fc-fusion / ligand trap":
        return "Ligand trap / decoy receptor"
    if modality == "Oligonucleotide":
        # The two oligonucleotide mechanisms are not interchangeable: siRNA
        # loads RISC and cuts the transcript catalytically, an antisense
        # oligonucleotide recruits RNase H, and a splice-switcher degrades
        # nothing at all. Different chemistry, different delivery, different
        # IP — "oligonucleotide" alone hides all of it.
        if re.search(r"\bsirna\b|\brnai\b|small interfering|\bsiran\b", text, re.I):
            return "siRNA — RNAi knockdown"
        if re.search(r"splice[- ]switch|exon skipping|splicing modul", text, re.I):
            return "Antisense oligonucleotide — splice-switching"
        if re.search(r"antisense|\baso\b|\brsen\b|\bnersen\b", text, re.I):
            return "Antisense oligonucleotide — RNase H knockdown"
        return "Oligonucleotide — knockdown, mechanism unresolved"
    if modality == "Vaccine":
        return "Active immunisation"

    # Adoptive transfer without a chimeric receptor. "Autologous HER2-specific
    # T cells" and "ex vivo-expanded HER2-specific T cells" are cell therapy
    # and are not CAR-T, and calling them either "CAR" or "Unclassified" says
    # something false.
    if re.search(r"\bt[- ]?(cell|lymphocyte)s?\b", text, re.I) and re.search(
            r"autologous|allogeneic|ex vivo|expanded|specific|adoptive|\btil\b",
            text, re.I):
        return "Cell therapy — adoptive T cells"

    if modality in {"Monoclonal antibody"}:
        if _DEPLETION_RE.search(text):
            return "Depleting antibody (ADCC/CDC)"
        if _AGONIST_RE.search(text) and not _BLOCK_RE.search(text):
            return "Agonist antibody"
        # "Anti-X" is how the field writes a blocking antibody, and the two
        # branches above have already taken the depleting and agonist ones. It
        # is checked here rather than inside _BLOCK_RE so that an "anti-CD40
        # agonist antibody" still reads as an agonist.
        if (_BLOCK_RE.search(text) or _ANTI_PREFIX_RE.search(text)
                or asset.action_type in {"ANTAGONIST", "INHIBITOR", "BLOCKER"}):
            return "Blocking antibody"
        return "Antibody — mechanism unresolved"

    if modality == "Small molecule":
        if _DEGRADER_RE.search(text):
            return "Small molecule — degrader"
        mapped = _ACTION_TYPE_MAP.get((asset.action_type or "").upper())
        if mapped:
            return f"Small molecule — {mapped.lower()}"
        # No action_type, but the record says what it does. A hand-entered row
        # carries a sentence rather than a database field, and "oral covalent
        # inhibitor of KRAS G12C" states the mechanism as plainly as ChEMBL's
        # INHIBITOR does.
        if _DEGRADER_RE.search(text):
            return "Small molecule — degrader"
        if _BLOCK_RE.search(text):
            return "Small molecule — inhibition"
        if _AGONIST_RE.search(text):
            return "Small molecule — activation"
        return "Small molecule — mechanism unresolved"

    mapped = _ACTION_TYPE_MAP.get((asset.action_type or "").upper())
    if mapped:
        return f"{modality} — {mapped.lower()}"
    return "Unclassified"


def annotate(assets: list[Asset]) -> None:
    for asset in assets:
        asset.modality = classify_modality(asset)
        asset.mechanism_class = classify_mechanism(asset)


def unresolved(assets: list[Asset]) -> list[Asset]:
    """Assets the rules could not place — the only rows an LLM is asked about."""
    return [
        a
        for a in assets
        if "unresolved" in a.mechanism_class.lower()
        or a.mechanism_class == "Unclassified"
        or a.modality == "Other / unclassified"
    ]


def cluster(assets: list[Asset]) -> dict[str, list[str]]:
    """mechanism_class -> asset names, ordered by how advanced the class is."""
    clusters: dict[str, list[str]] = {}
    for asset in assets:
        clusters.setdefault(asset.mechanism_class or "Unclassified", []).append(asset.name)
    best_phase = {
        label: max(
            (a.max_phase for a in assets if (a.mechanism_class or "Unclassified") == label),
            default=-1,
        )
        for label in clusters
    }
    return {
        label: sorted(names)
        for label, names in sorted(
            clusters.items(), key=lambda kv: (-best_phase[kv[0]], -len(kv[1]), kv[0])
        )
    }
