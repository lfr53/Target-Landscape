"""Fold three sources into one asset table.

This is where most of the real work is. The sources disagree about what a
drug is called, which phase it has reached and who owns it, and a landscape
memo built on an unreconciled union of them will double-count competitors —
the failure mode that makes automated CI untrustworthy in the first place.

Reconciliation rules, in order of authority:
  * identity    — ChEMBL ID where both sources have one, otherwise a
                  normalised name key built from every known synonym.
  * phase       — the maximum across sources. ChEMBL's max_phase lags; a
                  Phase 3 trial on ClinicalTrials.gov is evidence ChEMBL has
                  not caught up with, not a contradiction.
  * modality    — ChEMBL molecule_type wins over Open Targets drugType,
                  refined by name and mechanism heuristics (see analysis.mechanism).
  * sponsor     — the industry lead sponsor of the asset's highest-phase
                  trial. Academic sponsors are kept but flagged, because an
                  investigator-initiated Phase 1 is not a competitor in the
                  way a pharma Phase 1 is.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from . import relevance
from .config import ACTIVE_STATUSES, STOPPED_STATUSES
from .models import Asset, Provenance, Trial
from .sources import chembl as chembl_src
from .sources.ctgov import normalise_drug_name


# ---------------------------------------------------------------------------
# Text hygiene
# ---------------------------------------------------------------------------

# Registry free text arrives with the occasional broken character. A real one,
# from the PDCD1 build: the condition "PD-L1 TPS \ufffd00066%", where a
# "greater than or equal" sign lost its encoding somewhere upstream of
# ClinicalTrials.gov. It renders as a black diamond, it makes an indication
# row unreadable, and no reader can do anything about it — so the replacement
# character and the C0 controls are dropped on the way in rather than shown as
# though they were data.
_UNRENDERABLE = re.compile(r"[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]")


def plural(n: int, one: str, many: Optional[str] = None) -> str:
    """"1 trial", "2 trials".

    The lazy "trial(s)" reads as an unfinished sentence, and these strings are
    the six lines a reader sees first. Irregular plurals are passed in.
    """
    return f"{n} {one}" if n == 1 else f"{n} {many or one + 's'}"


def clean_text(value: str) -> str:
    """Drop unrenderable characters and close the gap they leave."""
    cleaned = _UNRENDERABLE.sub("", str(value or ""))
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # Open Targets joins several values into one string with " ; ". A space
    # before a semicolon reads as a typo wherever it lands, and the string is
    # shown to the reader unchanged in a dozen places.
    return cleaned.replace(" ; ", "; ")


# Sponsors type intervention names on whatever keyboard they have. A Chinese
# sponsor filing in English leaves the full-width bracket and comma behind:
# "Paclitaxel For （Albumin Bound）", "Adebrelimab，Fruquintinib",
# "Temozolomide、Fruquintinib、Cadonilimab". Those characters are twice as wide
# as the surrounding Latin text and break the line rhythm of a whole table.
#
# The registry also has no field for a trade mark, so it goes in the name:
# "Pembrolizumab (KEYTRUDA®)", "Nivolumab (OpdivoTM, / )" -- and when a
# sponsor's dose text is stripped out by an upstream tool, the brackets that
# held it stay: "Sintilimab , intravenously ( ) every 3 weeks( )".
_FULLWIDTH = str.maketrans({
    "（": "(", "）": ")", "［": "[", "］": "]", "｛": "{", "｝": "}",
    "，": ", ", "、": ", ", "；": "; ", "：": ": ", "．": ".",
    "％": "%", "＋": "+", "－": "-", "／": "/", "　": " ",
    "＜": "<", "＞": ">", "＝": "=", "！": "!", "？": "?",
})
_TRADEMARK_RE = re.compile(r"[®™©]|\(\s*(tm|r|c)\s*\)|(?<=[a-z])TM\b")
# A bracket holding no word at all: "( )", "()", "( / )", "(, )".
_EMPTY_BRACKET_RE = re.compile(r"[(\[]\s*[^\w()\[\]]*\s*[)\]]")


# The registry's own field labels, pasted into the value. CD19 carried
# "Assigned Interventions CD19/BCMA CAR T-cells" -- the heading of the column
# the sponsor was filling in, typed into the column itself.
_A_FIELD_LABEL_RE = re.compile(
    r"^\s*(assigned\s+interventions?|interventions?|arm\s+description|"
    r"experimental|active\s+comparator|placebo\s+comparator|sham\s+comparator|"
    r"drug|biological|procedure|device|radiation|genetic|dietary\s+supplement|"
    r"combination\s+product|other|behavioral|diagnostic\s+test)\s*[:\-]?\s+",
    re.IGNORECASE,
)


def tidy_name(value: str) -> str:
    """Make an intervention name readable without changing what it says."""
    text = _A_FIELD_LABEL_RE.sub("", clean_text(value)).translate(_FULLWIDTH)
    text = _TRADEMARK_RE.sub("", text)
    for _ in range(3):
        shortened = _EMPTY_BRACKET_RE.sub(" ", text)
        if shortened == text:
            break
        text = shortened
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    # "(Opdivo, / )" -> "(Opdivo)": the separators left behind when the dose
    # they separated was stripped upstream.
    text = re.sub(r"[\s,;/+-]+([)\]])", r"\1", text)
    # A bracket the sponsor opened and never closed. CD19's AUTO3 is filed as
    # "AUTO3 (CD19/22 CAR T cells" -- the registry keeps whatever was typed,
    # and the tail is the description that was going to go in the bracket.
    # Cutting at the bracket leaves the name: "AUTO3".
    text = _drop_an_unclosed_bracket(text)
    text = re.sub(r"\s{2,}", " ", text)
    # A preposition left hanging when the words it governed were stripped as
    # dosing noise: "CD19.CAR-multiVST for Group A" becomes "... for". No drug
    # name ends in one.
    text = re.sub(r"\s+(for|with|of|in|on|at|as|and|or|to|by)\s*$", "", text, flags=re.I)
    return text.strip(" -–—:,;/+")


def _drop_an_unclosed_bracket(text: str) -> str:
    depth = 0
    opened_at = -1
    for index, character in enumerate(text):
        if character in "([":
            if depth == 0:
                opened_at = index
            depth += 1
        elif character in ")]" and depth:
            depth -= 1
    if depth and opened_at > 0:
        return text[:opened_at]
    return text


# Three different kinds of statement arrive in one list from Open Targets, and
# printing them as equals is how the molecule card came to read
# "Cytosol, Predicted to be secreted, Secreted" for IL23A and
# "Nucleoli fibrillar center" for a kinase.
#
#   * where the protein is        - Cell membrane, Cytosol, Secreted
#   * how it sits in a membrane   - Single-pass type I membrane protein
#   * what a model guessed        - Predicted to be secreted
#
# The second is architecture, not a place, and it belongs on its own line. The
# third is not an observation at all: this site's rule is that an unknown
# location reads "cannot tell", so a prediction must not fill the gap and must
# never reach the modality verdict.

_TOPOLOGY_RE = re.compile(
    r"^(single|multi|type\s+i{1,3}|peripheral|lipid[- ]anchor|gpi[- ]anchor)"
    r"[\w\s-]*\b(pass|anchor|anchored)\b.*$|^.*\bmembrane protein\b.*$",
    re.IGNORECASE,
)
_PREDICTION_RE = re.compile(r"^\s*predicted\b", re.IGNORECASE)

# The Human Protein Atlas and UniProt name the same compartments differently.
# Carrying both spellings shows the reader one place twice.
_LOCATION_SYNONYMS = {
    "plasma membrane": "Cell membrane",
    "cell junctions": "Cell junction",
    "nucleoplasm": "Nucleus",
    "nuclear bodies": "Nucleus",
    "nuclear speckles": "Nucleus",
    "nucleoli": "Nucleus",
    "nucleoli fibrillar center": "Nucleus",
    "nucleoli rim": "Nucleus",
    "cytosol": "Cytoplasm",
    "vesicles": "Vesicle",
    "golgi apparatus": "Golgi apparatus",
    "mitochondria": "Mitochondrion",
    "endoplasmic reticulum": "Endoplasmic reticulum",
}


def _split_location_values(locations: list[str]) -> list[str]:
    """Open Targets returns "Cell membrane ; Single-pass type I membrane
    protein" as a single location. It is two."""
    out: list[str] = []
    for value in locations or []:
        for part in str(value or "").split(";"):
            part = clean_text(part).strip(" ;")
            if part and part not in out:
                out.append(part)
    return out


def split_locations(locations: list[str]) -> tuple[list[str], list[str]]:
    """Return (where it sits, how it sits in the membrane).

    Predictions are returned in neither: a guess is not a location, and the
    modality check is more useful saying "cannot tell" than reporting a fit
    derived from a model's opinion.
    """
    places: list[str] = []
    topology: list[str] = []
    for value in _split_location_values(locations):
        if _PREDICTION_RE.match(value):
            continue
        if _TOPOLOGY_RE.match(value):
            if value not in topology:
                topology.append(value)
            continue
        canonical = _LOCATION_SYNONYMS.get(value.lower(), value)
        if canonical not in places:
            places.append(canonical)
    # "Cell junction" and "Cell junction, tight junction" are one place named
    # at two levels of detail. Keep the specific one.
    places = [
        p for p in places
        if not any(o != p and o.lower().startswith(p.lower() + ",") for o in places)
    ]
    return places, topology


def clean_locations(locations: list[str]) -> list[str]:
    """Where the protein sits. Topology and predictions are excluded."""
    return split_locations(locations)[0]


def clean_asset_text(asset: Asset) -> None:
    """The same, for an asset. Indications feed the indication x mechanism
    matrix, so a broken character there becomes a whole unreadable row."""
    asset.name = tidy_name(asset.name)
    asset.sponsor = clean_text(asset.sponsor)
    asset.mechanism_text = clean_text(asset.mechanism_text)
    asset.indications = [i for i in (clean_text(i) for i in asset.indications or []) if i]
    asset.synonyms = [s for s in (clean_text(s) for s in asset.synonyms or []) if s]


def clean_trial_text(trial: Trial) -> None:
    """Apply :func:`clean_text` to a trial's free-text fields, in place.

    Called both when parsing a registry record and when loading a stored
    landscape: files written before this existed still carry the broken
    characters, and rebuilding them all to fix a punctuation mark is the wrong
    trade.
    """
    trial.title = clean_text(trial.title)
    trial.sponsor = clean_text(trial.sponsor)
    trial.why_stopped = clean_text(trial.why_stopped)
    trial.conditions = [c for c in (clean_text(c) for c in trial.conditions or []) if c]
    trial.interventions = [i for i in (tidy_name(i) for i in trial.interventions or []) if i]
    trial.primary_outcomes = [
        o for o in (clean_text(o) for o in trial.primary_outcomes or []) if o
    ]

# Intervention strings that are not assets.
#
# The second group is arm labels. A registry intervention field holds whatever
# the sponsor typed, and on a randomised trial that is often the name of the
# arm rather than a molecule: "Chemotherapy", "Treatment Algorithm A",
# "Targeted Systemic Therapy". CLDN18 carried three such assets and IL23A two,
# each with a phase and a sponsor, sitting in the table beside zolbetuximab as
# though they were programmes. "Matching" is the tail of "matching placebo",
# split on a comma by a sponsor who wrote a list -- it appeared on the CARD9
# page as an approved drug.
_NON_ASSETS = {
    "placebo",
    "normalsaline",
    "saline",
    "standardofcare",
    "standardcare",
    "bestsupportivecare",
    "vehicle",
    "shamcomparator",
    "nointervention",
    "control",
    "matchingplacebo",
    "placebocomparator",
    # Arm labels and category names.
    "matching",
    "matchingsolution",
    "chemotherapy",
    "immunotherapy",
    "radiotherapy",
    "radiation",
    "targetedsystemictherapy",
    "systemictherapy",
    "targetedtherapy",
    "conventionaltherapy",
    "standardtreatment",
    "standardtherapy",
    "usualcare",
    "physiciamschoice",
    "physicianschoice",
    "investigatorschoice",
    "treatmentasusual",
    "neoadjuvant",
    "neoadjuvanttreatment",
    "neoadjuvanttherapy",
    "adjuvant",
    "adjuvanttreatment",
    "adjuvanttherapy",
    "observation",
    "standardoftherapy",
    "bestavailabletherapy",
    "routine",
    "activecomparator",
    "comparator",
    "experimental",
    "intervention",
    "drug",
    "biological",
    "supportivecare",
    "observation",
    "notreatment",
    "surgery",
    "bloodsample",
    "questionnaire",
}

# Procedures, imaging and radiotherapy. The registry's intervention type field
# is supposed to separate these from drugs, and sponsors do not always set it:
# PD-1's asset table held "Computed Tomography", "Gastroscopy", "Ultrasound"
# and "Digital Gastrointestinal Radiography" as programmes against the target.
_NOT_A_MOLECULE = re.compile(
    r"\b(tomograph\w*|radiograph\w*|radiotherap\w*|radiation|gastroscop\w*|"
    r"endoscop\w*|ultrasound|ultrasonograph\w*|biopsy|imaging|scan|mri|"
    r"questionnaire|survey|exercise|counsel\w*|education|surgery|resection"
    # Procedures. An operation is not a molecule, and PDCD1 held an
    # oesophagectomy, a cryoablation and "Collecting samples from participant"
    # in the asset table beside pembrolizumab.
    r"|\w+ectomy|\w+ostomy|\w+oplasty|ablat\w*|cryo\w*|emboli\w*|"
    r"transarterial|apheres\w*|transplant\w*|collecting|specimen\w*|chemo"
    # Steps in making or giving a cell product, not the product. CD19 held
    # "CD3/CD19 depletion using cliniMACs device", a graft-manipulation step
    # on a stem-cell transplant study, and "Anti-CD19 CAR T Cells
    # Preparation", which is the background therapy on a trial of IVIG.
    r"|device|depletion|preparation|manufactur\w*|harvest\w*|conditioning"
    # Dosing prose that a sponsor typed into the intervention field.
    r"|adminstration|administration)\b"
    r"|\bevery \d+\s*(day|week|month)|\bfor \d+\s*(day|week|month)",
    re.IGNORECASE,
)

# A regimen written out in the intervention field rather than a molecule:
# "Camrelizumab Combined With Docetaxel Monotherapy", "Physician's choice
# chemotherapy", "Biological: Sintilimab Drug: Cisplatin Drug: Paclitaxel".
# Each of these entered the table beside pembrolizumab as though it were a
# separate programme.
_A_REGIMEN_NOT_A_DRUG = re.compile(
    r"(\bcombin\w*|\bplus\b|\band\b|\bor\b|\bregimen\b|\bsequential\b|"
    r"\bfollowed by\b|"
    r"\bdrug:|\bbiological:|\bphysician'?s choice\b|\binvestigator'?s choice\b|"
    r"\btherapy alone\b|\btherapy only\b|\bpreviously treated\b|"
    r"\btreated previously\b|\+/-|"
    r"\bexperimental drug\b|\bdrug protocol\b|\bstandard of care\b)",
    re.IGNORECASE,
)

# Two or more molecules typed into one intervention field: "Gemcitabine,
# Cisplatin", "HX008+Cisplatin+Gemcitabine", "Carboplatin / Cisplatin",
# "Adebrelimab，Fruquintinib". Each of these stood in the table as though it
# were one programme.
#
# Parentheses are stripped first, because what is inside them is usually the
# same molecule again -- "Azacitidine (5-Azacytidine, Ladakamycin)" is one
# drug and three names. The slash only splits when it has spaces around it:
# "PD-1/VEGF bispecific antibody" and "5-FU/LV" are single things written with
# a bare slash, and "Carboplatin / Cisplatin" is two drugs written with a
# spaced one.
_SEPARATORS_RE = re.compile(r"[,;+]| / ")


def _is_a_written_out_regimen(name: str) -> bool:
    # Dose arms are written with commas too: "anti-TL1A monoclonal antibody,
    # high dose", "BCD-261, dose 3". Stripping the dosing words first is what
    # keeps a six-arm dose-escalation from reading as a six-drug regimen.
    outside = re.sub(r"\([^)]*\)", " ", _NOISE_RE.sub(" ", name or ""))
    # A plus sign is only ever written to join two things: "PD-1+JAK1i",
    # "HX008+Cisplatin+Gemcitabine". No molecule has one in its name.
    joined = [p for p in outside.split("+") if re.search(r"[A-Za-z0-9]{2}", p)]
    if len(joined) >= 2:
        return True
    parts = [p for p in _SEPARATORS_RE.split(outside) if re.search(r"[A-Za-z]{3}", p)]
    return len(parts) >= 2

# "Treatment Algorithm A", "Regimen 2", "Arm B" -- a label with a bare letter
# or number where the molecule should be.
_ARM_LABEL_RE = re.compile(
    r"^(treatment|therapy|regimen|arm|group|cohort|schedule|strategy|algorithm|"
    r"protocol|dose\s*level)\b.{0,20}$",
    re.IGNORECASE,
)


# A measurement, not a molecule. ClinicalTrials.gov files a diagnostic under
# the same "interventions" field as a drug, so ERBB2 carried "Live Cell HER2
# signaling Transduction Analysis (CELx)" as an asset -- an assay used to pick
# who enrols in a neratinib study, counted as a programme against the target.
_A_MEASUREMENT_NOT_A_MOLECULE = re.compile(
    r"\b(analysis|assay|immunoassay|sequencing|genotyping|biopsy|cytometry|"
    r"histology|staining|questionnaire|survey|imaging|scan|scintigraphy|"
    r"screening|monitoring|measurement|profiling|test\s+kit|blood\s+draw|"
    r"sample\s+collection|specimen\s+collection)\b",
    re.IGNORECASE,
)


def _is_a_measurement(name: str) -> bool:
    return bool(_A_MEASUREMENT_NOT_A_MOLECULE.search(name or ""))


# A class, not a molecule. Sponsors register "PD-1/PD-L1 inhibitor",
# "TNF-alpha antagonists" and "EGFR-TKI (Hunan Province Tumor Hospital)" when
# the protocol allows the investigator to choose the drug. These are real
# entries in the registry and they are not assets: counting them inflates the
# table and they can never be classified, because there is no molecule to
# classify. A row is a class label when it ends in a class noun and carries no
# drug code -- "Bruton's Tyrosine Kinase Inhibitor ARQ 531" names a molecule
# and stays.
_A_CLASS_NOT_A_MOLECULE = re.compile(
    r"\b(inhibitors?|antagonists?|agonists?|blockers?|therapy|therapies|"
    r"agents?|tkis?|pathways?|regimens?|checkpoint)\s*$",
    re.IGNORECASE,
)
# Three digits, not two. Target aliases are letters plus one or two digits --
# IL-17, CD19, PD-L1 -- so a two-digit rule read "Anti-IL-17 therapy" as a
# named molecule and kept it. Drug codes run longer: ADG126, MK-1084, ARQ 531,
# BAY 80-6946.
_A_DRUG_CODE = re.compile(r"[A-Za-z]{2,}[- ]?\d{3,}|\b\d{2,}[- ]\d{3,}\b")
_A_CONSTRUCT = re.compile(
    r"\bcar\b|\bcar[- ]?(?:t|nk|m|dc)\b|chimeric antigen receptor|"
    r"\bvaccine\b|\bbispecific\b|antibody[- ]drug conjugate|\badc\b",
    re.IGNORECASE,
)
_A_COMPARATOR = re.compile(r"\bcomparator\b|\binvestigator['s]* choice\b|"
                           r"\bstandard of care\b|\bbest supportive care\b",
                           re.IGNORECASE)


def _is_a_class_label(name: str) -> bool:
    if _A_COMPARATOR.search(name or ""):
        return True
    # "Anti-CD19 CAR T cell therapy" ends in a class noun and carries no code,
    # but it is a product: a sponsor running one construct who did not give it
    # a name. The rule is for protocols that let the investigator pick any drug
    # in a class, and a named construct type is not that.
    if _A_CONSTRUCT.search(name or ""):
        return False
    bare = re.sub(r"\([^)]*\)", " ", name or "").strip()
    if not _A_CLASS_NOT_A_MOLECULE.search(bare):
        return False
    return not _A_DRUG_CODE.search(bare)


def _is_arm_label(name: str) -> bool:
    return bool(_ARM_LABEL_RE.match((name or "").strip()))


def is_not_an_asset(name: str) -> bool:
    """Is this intervention string a comparator, a category or an arm label
    rather than a molecule? Used both when discovering assets from trials and
    when loading a stored landscape that predates the check."""
    raw = tidy_name(name)
    if not raw:
        return False
    # "Matching Placebo Tablet" and "Placebo Oral Solution" never appear in the
    # exact list, because a sponsor can qualify the word any way they like.
    # Checked on the raw name: _name_key strips "placebo" as dosing noise, so
    # "Placebo Oral Solution" keys to the empty string and the exact list
    # never sees it.
    flat = re.sub(r"[^a-z]", "", raw.lower())
    if "placebo" in flat or "sham" in flat:
        return True
    if _NOT_A_MOLECULE.search(raw) or _A_REGIMEN_NOT_A_DRUG.search(raw):
        return True
    # A sentence, not a name. "of BAFFR CAR-T therapy for relapsed/refractory
    # B-cell malignancies" is a phrase from the protocol that a sponsor pasted
    # into the intervention field; the longest real drug names in the table
    # run to five words.
    # Counted outside the brackets. The rule is for a sentence pasted into the
    # intervention field; a parenthetical is a qualifier, and the sponsor this
    # table itself appends to an unnamed row -- "BCMA CAR-T cells (Chongqing
    # Precision Biotech Co.)" -- pushed such rows over the limit, so the build
    # wrote a row the next load deleted and every stored figure was one high.
    if len(re.sub(r"\([^)]*\)", " ", raw).split()) > 6:
        return True
    if _is_a_written_out_regimen(raw):
        return True
    key = _name_key(raw)
    if not key:
        # Every word was formulation or dosing noise, so there is no molecule
        # left in the name.
        return True
    return (key in _NON_ASSETS or _is_arm_label(raw) or _is_a_measurement(raw)
            or _is_a_class_label(raw))

# Strip formulation and dosing noise so "VAY736 300 mg SC" keys to "vay736".
_NOISE_RE = re.compile(
    r"\b("
    r"\d+(\.\d+)?\s*(mg|mcg|ug|g|ml|iu|kg|mg/kg)\b"          # doses
    # A cell dose. "BCMA-TGFbeta CAR-T cells (0.75 x10^6 cells/kg)" is one of
    # four arms of one Phase 1, written four ways.
    r"|\d+(\.\d+)?\s*[x×]\s*10\s*\^?\d+\s*(cells?)?(\s*/\s*kg)?"
    # An arm number, taken together with the word that makes it one. Matched
    # before the bare words below, which would strip "Dose" and leave a "1"
    # behind -- and a stray "1" is what made "CD19-BCMA Targeted CAR-T Dose 1"
    # and "Dose 2", the two dose levels of one Phase 1, into two competitors.
    # Written as a pair on purpose: a trailing number is only an arm when a
    # trial-design word says so, or "Interleukin 2" loses its 2.
    r"|(dose|cohort|group|arm|level|part|stage|step|regimen)"
    r"\s*[-#:]?\s*([0-9]{1,2}|[ivx]{1,3}|[a-h])\b"
    r"|q\d+[wdm]|qw|qd|bid|tid|qid|od|prn"                   # dosing codes
    r"|monthly|weekly|daily|yearly|once|twice|thrice"        # dosing schedule
    r"|sc|iv|po|im|it|subcutaneous|intravenous|oral"         # routes
    r"|injection|infusion|tablet|capsule|solution|syringe"   # formulations
    r"|loading|maintenance|induction"                        # regimen phases
    r"|placebo|arm|cohort|dose|dosing|group|level"           # trial-design words
    r"|high|low|mid|medium"
    r")\b",
    re.IGNORECASE,
)


def _name_key(name: str) -> str:
    return normalise_drug_name(
        relevance.strip_salt_form(_NOISE_RE.sub(" ", name or "")))


def _keys_for(asset: Asset) -> set[str]:
    keys = {_name_key(asset.name)}
    keys.update(_name_key(s) for s in asset.synonyms)
    if asset.chembl_id:
        keys.add(asset.chembl_id.lower())
    return {k for k in keys if len(k) > 2}


def enrich_from_chembl(assets: list[Asset]) -> None:
    """Overlay ChEMBL mechanism and molecule detail onto Open Targets assets."""
    ids = [a.chembl_id for a in assets if a.chembl_id]
    if not ids:
        return
    molecules = chembl_src.fetch_molecules(ids)
    for asset in assets:
        record = molecules.get(asset.chembl_id)
        if not record:
            continue
        if record.get("molecule_type"):
            asset.modality = record["molecule_type"]
        asset.first_approval = record.get("first_approval")
        asset.withdrawn = record.get("withdrawn_flag", False)
        for synonym in record.get("synonyms", []):
            if synonym not in asset.synonyms:
                asset.synonyms.append(synonym)
        asset.max_phase = max(asset.max_phase, chembl_src.phase_to_int(record.get("max_phase")))
        asset.provenance.append(chembl_src.provenance_for(asset.chembl_id))


def apply_mechanisms(assets: list[Asset], mechanisms: dict[str, dict]) -> None:
    """Attach ChEMBL action_type / mechanism_of_action by molecule ID."""
    for asset in assets:
        record = mechanisms.get(asset.chembl_id)
        if not record:
            continue
        asset.action_type = record.get("action_type") or asset.action_type
        if record.get("mechanism_of_action"):
            asset.mechanism_text = record["mechanism_of_action"]


def _industry_sponsor(trials: list[Trial]) -> tuple[str, str]:
    """Pick the sponsor to display: highest-phase industry sponsor if any."""
    if not trials:
        return "", ""
    industry = [t for t in trials if t.sponsor_class == "INDUSTRY"]
    pool = industry or trials
    best = max(pool, key=lambda t: (t.phase, t.enrollment or 0))
    return best.sponsor, best.sponsor_class


def attach_trials(assets: list[Asset], trials: list[Trial]) -> list[Trial]:
    """Link trials to assets and return the trials that matched nothing."""
    index: dict[str, Asset] = {}
    for asset in assets:
        for key in _keys_for(asset):
            index.setdefault(key, asset)

    unmatched: list[Trial] = []
    for trial in trials:
        matched = False
        # Open Targets may already have linked this NCT to a drug.
        for asset in assets:
            if trial.nct_id in asset.trials:
                matched = True
                break
        if not matched:
            for intervention in trial.interventions:
                asset = index.get(_name_key(intervention))
                if asset is not None:
                    # A trial lists a drug under several spellings, and each
                    # spelling matched: the export showed one NCT three times
                    # against one asset, and every count built on that list was
                    # inflated by the same factor.
                    if trial.nct_id not in asset.trials:
                        asset.trials.append(trial.nct_id)
                    matched = True
                    break
        if not matched:
            unmatched.append(trial)

    by_nct = {t.nct_id: t for t in trials}
    for asset in assets:
        linked = [by_nct[n] for n in asset.trials if n in by_nct]
        if not linked:
            continue
        sponsor, _ = _industry_sponsor(linked)
        if sponsor and not asset.sponsor:
            asset.sponsor = sponsor
        asset.max_phase = max([asset.max_phase] + [t.phase for t in linked])
        for trial in linked:
            for condition in trial.conditions:
                if condition not in asset.indications:
                    asset.indications.append(condition)
        asset.is_active = _is_active(asset, linked)
    return unmatched


def _is_active(asset: Asset, trials: list[Trial]) -> bool:
    if asset.max_phase == 4 and not asset.withdrawn:
        return True
    statuses = {t.status for t in trials}
    if statuses & ACTIVE_STATUSES:
        return True
    # Everything stopped and nothing running: the programme is dormant.
    if statuses and statuses <= (STOPPED_STATUSES | {"COMPLETED", "UNKNOWN"}):
        return bool(statuses & {"COMPLETED", "UNKNOWN"}) and not (
            statuses <= STOPPED_STATUSES
        )
    return True


def subject_intervention(trial) -> Optional[str]:
    """The drug a trial is about, as opposed to what it is given alongside.

    A trial is attributed to the first asset it names, and every other drug in
    it then becomes invisible. NCT07431281 is a study of sonesitatug vedotin,
    an anti-CLDN18.2 ADC, and it lists ten interventions -- among them
    zolbetuximab, as a comparator. Because zolbetuximab was already in the
    asset table the whole trial was marked matched, and AZD0901 never became
    an asset. The CLDN18 page showed one programme where the field has two.

    Registry titles follow a convention: the investigational agent is named
    first. "Sonesitatug Vedotin in Combination With Capecitabine With or
    Without Rilvegostomig" is a sonesitatug vedotin trial. So the earliest
    intervention to appear in the title is the subject, and the rest are the
    regimen around it. That is one asset per trial rather than ten, and it is
    the one the sponsor put in the title.
    """
    title = (getattr(trial, "title", "") or "").lower()
    if not title:
        return None
    best, best_at = None, len(title) + 1
    for name in getattr(trial, "interventions", None) or []:
        if not name or is_not_an_asset(name):
            continue
        at = title.find(str(name).lower())
        if at != -1 and at < best_at:
            best, best_at = name, at
    return best


def _already_known(name: str, known_keys: set[str]) -> bool:
    """Is a drug already in the table hiding inside this label?

    "PD-1 inhibitor (Tislelizumab)", "anti-PD-1 Therapy Nivolumab" and
    "JS001, an engineered anti-PD-1 antibody" are three ways of writing down a
    drug the asset table already holds. As whole strings none of them keys to
    anything, so each became a fourth, fifth and sixth programme against the
    same target.
    """
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{2,}", name or "")
    for word in words:
        key = _name_key(word)
        # A class word is not an identity. "Antibody" keys the same way in
        # "PD-1/VEGF bispecific antibody" and in CS-1003's synonym "antibody
        # CS1003", and matching on it merged a real bispecific into CS-1003.
        if len(key) < 4 or key in relevance._CLASS_WORDS or key in relevance._GENERIC:
            continue
        if key in known_keys:
            return True
        # "NIVO" for nivolumab. Long enough to be a name, and no two drugs in
        # one target's table share four opening characters.
        if any(k.startswith(key) for k in known_keys if len(k) > len(key)):
            return True
    return False


def candidate_drugs(trial: Trial, terms: list[str], words: Optional[set] = None) -> list[str]:
    """The drugs in this trial that the trial itself ties to the target.

    Two ways in. A drug whose own name carries the target -- "anti-BAFF-R
    CAR-T", "PD-1/VEGF bispecific antibody" -- is admitted from anywhere in
    the intervention list. Otherwise only the trial's subject drug is
    considered, and it has to earn its place by the title naming the target
    beside it (see ``relevance.drug_is_directed_at_target``).

    Everything else in a combination study is a partner drug. Its mechanism is
    not in this record, and inventing one is how carboplatin, omeprazole and
    an oesophagectomy came to sit in the PD-1 asset table.
    """
    pool: list[str] = []
    subject = subject_intervention(trial)
    if subject is None:
        # No intervention appears in the title. A dose-escalation study writes
        # its one drug six times -- "BCD-261, dose 1" through "dose 6" -- and
        # none of those strings is in the title, but they are all one drug.
        eligible = [i for i in (trial.interventions or []) if not is_not_an_asset(i)]
        if eligible and len({_name_key(i) for i in eligible}) == 1:
            subject = min(eligible, key=len)
    if subject:
        pool.append(subject)
    for intervention in trial.interventions or []:
        if intervention not in pool:
            pool.append(intervention)
    # Dosing words are stripped before asking whether a molecule is named:
    # "anti-TL1A monoclonal antibody, high dose" is a class label with a dose
    # attached, not a drug called high dose.
    def is_a_label(name: str) -> bool:
        return relevance.names_no_molecule(
            _NOISE_RE.sub(" ", name), terms, words or ())

    named = [
        name for name in pool
        if relevance.drug_is_directed_at_target(trial, name, terms)
        and not is_a_label(name)
    ]
    if named:
        return named
    # Nothing named, but the sponsor may still have said what the drug is.
    # BCD-261's Phase 2 lists its arms as "anti-TL1A monoclonal antibody, high
    # dose" and nothing else: a label rather than a name, and the only drug in
    # the study. That is a real anti-TL1A programme stated in the record, and
    # dropping it emptied the TL1A table. It is admitted only when the trial
    # lists no other drug -- in a combination study "PD-1 Antibody" sits
    # beside lenvatinib and says nothing about which of them acts on PD-1.
    labels = [i for i in (trial.interventions or []) if not is_not_an_asset(i)]
    class_labels = [
        i for i in labels
        if relevance.drug_is_directed_at_target(trial, i, terms) and is_a_label(i)
        # A plural label is the category, not a member of it: the protocol
        # says "PD-1 inhibitors" because the site picks one.
        and not relevance.names_a_category(i)
    ]
    if class_labels and len(class_labels) == len(labels):
        return [_named_by_the_title(trial) or min(class_labels, key=len)]
    return []


# A sponsor's development code: two to five capitals, then three or more
# digits. Narrow on purpose -- it is here only to put a name on a programme
# whose intervention field carries a class label, and the trial it came from
# is one click away on the page.
_DEVELOPMENT_CODE_RE = re.compile(r"\b([A-Z]{2,5}[- ]?\d{3,6})\b")


def _named_by_the_title(trial: Trial) -> Optional[str]:
    """The drug code a title carries when the intervention field has none."""
    for match in _DEVELOPMENT_CODE_RE.finditer(getattr(trial, "title", "") or ""):
        code = match.group(1)
        if not code.upper().startswith("NCT"):
            return code
    return None


def discover_assets_from_trials(
    unmatched: list[Trial],
    known_keys: set[str],
    *,
    subject_only: bool = False,
    terms: Optional[list[str]] = None,
    words: Optional[set] = None,
) -> list[Asset]:
    """Build assets for drugs that appear in trials but in no drug database.

    Cell therapies, academic INDs and most Chinese and Japanese programmes
    reach the clinic without a ChEMBL entry. Skipping them is how an
    automated landscape ends up quietly missing the fastest-moving part of
    the field.

    ``terms`` are the target's own names. Given them, only drugs the trial
    ties to the target are taken; without them every intervention is, which
    is what the caller wants when the trials were selected some other way.
    """
    groups: dict[str, list[Trial]] = {}
    labels: dict[str, str] = {}

    def is_unnamed(name: str) -> bool:
        return terms is not None and relevance.names_no_molecule(
            _NOISE_RE.sub(" ", name), terms, words or ())

    def group_key(trial: Trial, name: str) -> str:
        """What counts as the same programme.

        Normally the drug's name. But a programme with no name yet is written
        down differently in every record it appears in -- Mayo Clinic's
        BAFF-R CAR-T is "Autologous BAFFR-CAR T Cells" in one study,
        "Autologous BAFFR-CAR-expressing T-cells" in the next and "Autologous
        BAFFR-targeting CAR T Cells" in the third -- and keying on the string
        showed one sponsor's single programme as three competitors. When the
        label names no molecule, the sponsor is the identity.
        """
        if is_unnamed(name):
            sponsor = re.sub(r"[^a-z0-9]", "", (trial.sponsor or "").lower())
            return f"unnamed-{sponsor or _name_key(name)}"
        return _name_key(name)

    for trial in unmatched:
        # A trial already attributed to a known asset is mined for its subject
        # drug only. Taking every intervention from a combination study would
        # turn the chemotherapy backbone into a programme against the target.
        pool = trial.interventions
        if terms is not None:
            pool = candidate_drugs(trial, terms, words)
        elif subject_only:
            subject = subject_intervention(trial)
            pool = [subject] if subject else []
        for intervention in pool:
            key = group_key(trial, intervention)
            if not key or len(key) < 3 or key in _NON_ASSETS:
                continue
            if is_not_an_asset(intervention):
                continue
            # A row with no name of its own is identified by its sponsor, not
            # by its string, so the "is this drug already in the table" tests
            # do not apply to it -- and applying them made the label a
            # sponsor's group settled on depend on which of its trials had
            # been mined first.
            if not is_unnamed(intervention):
                if key in known_keys or _already_known(intervention, known_keys):
                    continue
            groups.setdefault(key, []).append(trial)
            # Keep the shortest label: "VAY736" over "VAY736 300mg monthly".
            current = labels.get(key)
            cleaned = tidy_name(_NOISE_RE.sub(" ", intervention))
            if current is None or len(cleaned) < len(current):
                labels[key] = cleaned

    out: list[Asset] = []
    for key, group in groups.items():
        sponsor, sponsor_class = _industry_sponsor(group)
        indications: list[str] = []
        for trial in group:
            for condition in trial.conditions:
                if condition not in indications:
                    indications.append(condition)
        asset = Asset(
            name=labels.get(key, key),
            sponsor=sponsor,
            modality="Other / unclassified",
            max_phase=max((t.phase for t in group), default=-1),
            indications=indications,
            trials=[t.nct_id for t in group],
            # The sponsor described the drug instead of naming it. The row is
            # kept -- the programme is real and the trial is one click away --
            # but it is not a molecule the reader can look up, and the page has
            # to say which of the two it is looking at.
            named_by_class=key.startswith("unnamed-"),
            provenance=[
                Provenance(source="ctgov", identifier=t.nct_id, url=t.url) for t in group[:5]
            ],
        )
        asset.is_active = _is_active(asset, group)
        # Academic-only programmes are kept but marked, so the crowding
        # verdict can weight them differently from a pharma programme.
        if sponsor_class and sponsor_class != "INDUSTRY":
            asset.mechanism_text = asset.mechanism_text or f"[{sponsor_class.lower()} sponsor]"
        out.append(asset)
    _qualify_repeated_class_labels(out)
    return out


# Six rows reading "CD19 CAR-T cells" is what an unnamed programme looks like
# when six sponsors each have one. The rows are right -- they are six different
# groups, and the sponsor is what tells them apart, which is why the sponsor is
# their key. Printed as six identical strings the table reads as a duplication
# bug, so the thing that distinguishes them is put in the name.
_SPONSOR_TAIL_RE = re.compile(r"\s*[,(].*$")


def _qualify_repeated_class_labels(assets: list[Asset]) -> None:
    seen: dict[str, int] = {}
    for asset in assets:
        if asset.named_by_class:
            seen[asset.name] = seen.get(asset.name, 0) + 1
    for asset in assets:
        if not asset.named_by_class or seen.get(asset.name, 0) < 2:
            continue
        sponsor = _SPONSOR_TAIL_RE.sub("", asset.sponsor or "").strip()
        if sponsor:
            asset.name = f"{asset.name} ({_shorten(sponsor, 34)})"


def _shorten(text: str, limit: int) -> str:
    """Cut at a word boundary. "Guangzhou University of Traditiona" is worse
    than "Guangzhou University", and an ellipsis inside a bracket is worse than
    both."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,-")
    cut = re.sub(r"\s+(of|for|and|the|at|in|de|du)$", "", cut, flags=re.I)
    return cut or text[:limit]


def _sponsor_key(sponsor: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (sponsor or "").lower())


def _no_database_knows(asset: Asset) -> bool:
    return not asset.chembl_id and not any(
        getattr(p, "source", "") not in ("ctgov", "manual")
        for p in asset.provenance or []
    )


def _chembl_says_they_are_different(a: Asset, b: Asset) -> bool:
    """Two ChEMBL ids, and they are not the same one.

    A synonym list is not a statement that two names are one molecule; it is
    whatever the source recorded. ChEMBL's entry for ado-trastuzumab emtansine
    (CHEMBL1743082) carries "Trastuzumab", "Herceptin" and sixteen trastuzumab
    biosimilars in its synonyms, so the plain antibody (CHEMBL1201585) keyed
    into the ADC and vanished: ERBB2 listed T-DM1, T-DXd, botidotin and
    duocarmazine, and no trastuzumab. An identifier from each side, and the two
    differ, is the one signal strong enough to overrule a shared name.

    It overrules a shared *synonym* only. When the two rows carry the same name
    once the counter-ion is off -- "NERATINIB" and "NERATINIB MALEATE", each
    with its own ChEMBL id -- the name is saying they are one molecule in two
    registered forms, and they still merge.
    """
    if _name_key(a.name) == _name_key(b.name):
        return False
    return bool(a.chembl_id and b.chembl_id and a.chembl_id != b.chembl_id)


def _release_names_owned_by_another_row(assets: list[Asset]) -> None:
    """Take a molecule's own name off every other molecule's synonym list.

    Once two rows survive as two molecules, the synonym that merged them is
    still there, and it goes on pulling that drug's trials onto the wrong row.
    A row's own name belongs to it; so do the names on a hand-entered row,
    because a person wrote them down against a citation.
    """
    owned: dict[str, Asset] = {}
    for asset in assets:
        owned.setdefault(_name_key(asset.name), asset)
        if any(getattr(p, "source", "") == "manual" for p in asset.provenance or []):
            for synonym in asset.synonyms:
                owned.setdefault(_name_key(synonym), asset)
    for asset in assets:
        asset.synonyms = [
            s for s in asset.synonyms
            if not (_chembl_says_they_are_different(owned.get(_name_key(s), asset), asset)
                    or (owned.get(_name_key(s)) is not None
                        and owned[_name_key(s)] is not asset
                        and _name_key(s) == _name_key(owned[_name_key(s)].name)))
        ]


# Words that describe an antigen or a preparation rather than name a molecule.
# NCT01922921 lists one University of Washington vaccine five times -- "HER-2
# ICD Peptide", "HER-2/neu ICD Protein", "HER-2/neu Intracellular Domain
# Protein", "HER2 ICD", "HER2 Intracellular Domain" -- and each spelling became
# a competitor. Strip these and the target's own aliases and nothing is left of
# any of them, which is the test: a row with no name of its own, in one trial,
# from one sponsor, is one programme.
_DESCRIPTOR_WORDS = {
    "icd", "intracellular", "extracellular", "domain", "protein", "peptide",
    "antigen", "epitope", "fragment", "vaccine", "vaccines", "pulsed",
    "primed", "loaded", "specific", "directed", "targeted", "targeting",
    "autologous", "allogeneic", "expanded", "ex", "vivo", "vitro", "cells",
    "cell", "lymphocytes", "dendritic", "dc", "dc1", "based", "derived",
    "recombinant", "purified", "adjuvant", "adjuvanted", "plus", "and", "the",
    "of", "a", "an", "with", "in", "anti", "human", "type", "mono", "poly",
}


def fold_unnamed_rows_in_one_trial(
        assets: list[Asset], target_tokens: Iterable[str]) -> list[Asset]:
    """One programme written five ways in one intervention list.

    Narrow on purpose. Only rows the registry sweep created, only rows from the
    same sponsor listing exactly the same trials, and only rows that carry no
    name of their own once the target's aliases and the descriptor words above
    come off. A second drug in the same trial keeps its code name, so it keeps
    its row.
    """
    drop = {t.lower() for t in target_tokens} | _DESCRIPTOR_WORDS

    def has_a_name(asset: Asset) -> bool:
        return any(t for t in re.split(r"[^a-z0-9]+", asset.name.lower())
                   if t and len(t) > 1 and t not in drop)

    groups: dict[tuple, list[Asset]] = {}
    for asset in assets:
        if not relevance.from_the_sweep_alone(asset) or has_a_name(asset):
            continue
        if not asset.trials:
            continue
        groups.setdefault(
            (_sponsor_key(asset.sponsor), frozenset(asset.trials)), []).append(asset)

    folded: set[int] = set()
    for members in groups.values():
        if len(members) < 2:
            continue
        # The fullest spelling is the one that tells a reader what it is.
        keeper = max(members, key=lambda a: (len(a.name), a.name))
        for other in members:
            if other is keeper:
                continue
            keeper.max_phase = max(keeper.max_phase, other.max_phase)
            _remember_synonym(keeper, other.name)
            for value in other.indications:
                if value not in keeper.indications:
                    keeper.indications.append(value)
            keeper.provenance.extend(other.provenance)
            folded.add(id(other))
    return [a for a in assets if id(a) not in folded]


def _remember_synonym(asset: Asset, name: str) -> None:
    name = (name or "").strip()
    if name and name not in asset.synonyms:
        asset.synonyms.append(name)


def dedupe(assets: Iterable[Asset]) -> list[Asset]:
    """Final pass: collapse assets that share a synonym key."""
    merged: dict[str, Asset] = {}
    order: list[str] = []
    for asset in assets:
        keys = _keys_for(asset)
        # Two programmes with no name of their own can key identically and
        # still be two programmes. Five companies each run something the
        # registry calls "BAFF-R CAR-T"; PeproMene's and Mayo Clinic's are not
        # the same asset, and collapsing them by string showed one competitor
        # where the field has five. A drug database's identifier still merges
        # -- that is a real assertion that two names are one molecule.
        #
        # Only rows with no name of their own. "No database knows it" used to
        # stand in for that, because there was no way to ask the question
        # directly; it also scoped every named row a person or the registry
        # contributed, so a hand-entered "Zolbetuximab" sat beside Open
        # Targets' "ZOLBETUXIMAB" as a second programme. A molecule that has a
        # name is the same molecule whoever wrote it down.
        if _no_database_knows(asset) and asset.named_by_class:
            keys = {f"{k}@{_sponsor_key(asset.sponsor)}" for k in keys}
        hit: Optional[str] = next(
            (k for k in keys
             if k in merged and not _chembl_says_they_are_different(merged[k], asset)),
            None)
        if hit is None:
            primary = sorted(keys)[0] if keys else _name_key(asset.name)
            merged[primary] = asset
            order.append(primary)
            for key in keys:
                merged.setdefault(key, asset)
            continue
        existing = merged[hit]
        # Two spellings of one molecule, and the row has to show one of them.
        # The active moiety is the name a reader looks for and the name a trial
        # writes, so "NERATINIB" wins over "NERATINIB MALEATE" -- and when only
        # the salt form was fetched, the plain name is kept as a synonym so the
        # relevance check can still match a trial that says "lapatinib".
        if relevance.strip_salt_form(existing.name) != existing.name.strip() \
                and relevance.strip_salt_form(asset.name) == asset.name.strip():
            _remember_synonym(existing, existing.name)
            existing.name = asset.name
        elif relevance.strip_salt_form(asset.name) != asset.name.strip():
            _remember_synonym(existing, asset.name)
        existing.max_phase = max(existing.max_phase, asset.max_phase)
        existing.sponsor = existing.sponsor or asset.sponsor
        existing.chembl_id = existing.chembl_id or asset.chembl_id
        existing.action_type = existing.action_type or asset.action_type
        existing.mechanism_text = existing.mechanism_text or asset.mechanism_text
        if existing.modality == "Other / unclassified":
            existing.modality = asset.modality
        # A hand-entered row wins on the fields it fills, because that is what
        # it is for. Open Targets records zolbetuximab as a "Claudin-18 binding
        # agent" at Phase 3; it is a chimeric IgG1 that kills through ADCC and
        # CDC, and the FDA approved it in October 2024. A person read the label
        # and typed that in with the citation, and deferring to the stale field
        # would leave the page saying the weaker thing.
        if any(getattr(p, "source", "") == "manual" for p in asset.provenance or []):
            existing.mechanism_text = asset.mechanism_text or existing.mechanism_text
            existing.action_type = asset.action_type or existing.action_type
            if asset.modality and asset.modality != "Other / unclassified":
                existing.modality = asset.modality
        existing.is_active = existing.is_active or asset.is_active
        for field_name in ("indications", "trials", "synonyms"):
            target_list = getattr(existing, field_name)
            for value in getattr(asset, field_name):
                if value not in target_list:
                    target_list.append(value)
        existing.provenance.extend(asset.provenance)
    out = [merged[k] for k in order]
    _release_names_owned_by_another_row(out)
    return out
