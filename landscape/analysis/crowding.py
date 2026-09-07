"""Competitive density and whitespace.

Two questions, deliberately answered with arithmetic a reader can redo by
hand rather than with a model:

**How crowded is this target?** Not "how many assets" — a flat count treats a
Phase 3 asset from a large sponsor and a dormant academic Phase 1 as equals,
which is how landscape slides mislead. Assets are weighted by phase
(``config.PHASE_WEIGHTS``), dormant programmes are excluded from the headline
and reported separately, and the verdict band is a stated convention, not a
measurement. Every component is printed alongside the score so the reader can
disagree with the weighting and recompute.

**Where is the whitespace?** A disease with strong Open Targets association
evidence — genetic evidence in particular, which is the component that
survives replication best — and no asset past preclinical. That conjunction is
the interesting one: absence of competition where the biology is well
supported, rather than absence of competition anywhere.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Optional

from ..models import Trial

# ---------------------------------------------------------------------------
# Disease name matching
# ---------------------------------------------------------------------------
#
# Open Targets speaks EFO ("Sjogren syndrome"); ClinicalTrials.gov carries
# whatever the sponsor typed ("Sjogren's Disease"). Nothing maps between them
# for free, and naive substring matching fails on exactly the pairs that
# matter — which silently reports an indication with a Phase 3 asset in it as
# untouched whitespace.
#
# So: strip punctuation and clinical filler, truncate each token to its stem
# prefix (thrombocytopenic / thrombocytopenia -> thromboc), and compare token
# sets by Jaccard overlap. Crude, deterministic, inspectable, and right on the
# cases that break substring matching.

_STOPWORDS = {
    "disease", "diseases", "syndrome", "syndromes", "disorder", "disorders",
    "primary", "secondary", "chronic", "acute", "active", "moderate", "severe",
    "refractory", "relapsed", "advanced", "adult", "adults", "paediatric",
    "pediatric", "the", "of", "and", "with", "in", "a", "an", "to", "or",
    "type", "stage", "unspecified", "other", "patients", "participants",
    # How far along and how treated. Neither changes which disease it is, and
    # each spelling of it was a separate row: "melanoma", "metastatic
    # melanoma", "advanced unresectable melanoma" and "Metastatic Melanoma"
    # were four rows in the PD-1 grid.
    "metastatic", "recurrent", "unresectable", "resectable", "locally",
    "resected", "untreated", "previously", "treated", "newly", "diagnosed",
    "progressive", "persistent", "extensive", "limited", "early", "late",
    "line", "first", "second", "third", "adjuvant", "neoadjuvant",
    # Marker status. "HER2-positive gastric cancer" and "gastric cancer" are
    # the same disease; the status is the enrolment criterion.
    "positive", "negative", "expressing", "overexpressing", "expression",
    "amplified", "amplification", "mutant", "mutated", "mutation", "mutations",
    "harboring", "harbouring", "carrying", "status", "wildtype", "wild",
}

# The words a database uses for "a cancer, unspecified which". They are
# interchangeable in every source: Open Targets writes "non-small cell lung
# carcinoma", a sponsor writes "Non-Small Cell Lung Cancer", and the grid held
# both. Folded to one token so the two are one row -- and no further, because
# "gastric cancer" and "gastric adenocarcinoma" are not the same disease and
# must not fold together.
_A_CANCER_UNSPECIFIED = {
    "cancer", "cancers", "carcinoma", "carcinomas", "neoplasm", "neoplasms",
    "neoplasia", "tumor", "tumors", "tumour", "tumours", "malignancy",
    "malignancies", "malignant",
}
_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

# One disease, several house styles. The registry carries "gastro-oesophageal
# adenocarcinoma", "gastroesophageal adenocarcinoma", "gastro-esophageal
# adenocarcinoma" and "gastrooesophageal adenocarcinoma", and the tokeniser
# saw four different diseases because a hyphen splits a word and a British
# vowel does not match an American one.
_SPELLINGS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"gastro[\s-]*o?esophag"), "gastroesophag"),
    (re.compile(r"o?esophag"), "esophag"),
    (re.compile(r"triple[\s-]*(negative|positive)"), r"triple\1"),
    (re.compile(r"\bhaemat"), "hemat"),
    (re.compile(r"\bhaemo"), "hemo"),
    (re.compile(r"aemia\b"), "emia"),
    (re.compile(r"\btumour"), "tumor"),
    (re.compile(r"\bleukaemi"), "leukemi"),
    (re.compile(r"\bcoeliac"), "celiac"),
]
# A stage is how far the disease has gone, not which disease it is. Eight rows
# of "Stage IA / IB / IIA ... Breast Cancer" are one indication.
_A_STAGE_TOKEN = re.compile(r"^(?:[iv]{1,4}[abc]?|[1-4][abc]?|v\d|ajcc|anatomic|clinical|grade)$")


def _normalise_spelling(text: str) -> str:
    out = (text or "").lower()
    for pattern, replacement in _SPELLINGS:
        out = pattern.sub(replacement, out)
    return out
_STEM_LEN = 8
_MATCH_THRESHOLD = 0.5


def disease_key(name: str, drop: frozenset[str] = frozenset()) -> frozenset[str]:
    """The tokens that say which disease this is.

    ``drop`` carries the target's own aliases. "HER2-positive breast cancer"
    and "breast cancer" are one row on an ERBB2 page -- the target's name in an
    indication says who was enrolled, not which disease they have -- and
    without dropping it the two keys never matched.
    """
    tokens: set[str] = set()
    for token in _TOKEN_SPLIT.split(_normalise_spelling(name)):
        if not token or len(token) < 2 or token in _STOPWORDS or token in drop:
            continue
        if _A_STAGE_TOKEN.match(token):
            continue
        tokens.add("\u0000cancer" if token in _A_CANCER_UNSPECIFIED else token[:_STEM_LEN])
    return frozenset(tokens)


def same_disease(a: frozenset[str], b: frozenset[str]) -> bool:
    if not a or not b:
        return False
    if a == b or a <= b or b <= a:
        return True
    return len(a & b) / len(a | b) >= _MATCH_THRESHOLD

from ..config import (
    CROWDING_BANDS,
    PHASE_WEIGHTS,
    WHITESPACE_MAX_PHASE,
    WHITESPACE_MIN_ASSOCIATION,
    WHITESPACE_MIN_GENETIC,
)
from ..models import PHASE_LABELS, Asset, DiseaseAssociation


def _band(score: float) -> str:
    verdict = CROWDING_BANDS[0][1]
    for threshold, label in CROWDING_BANDS:
        if score >= threshold:
            verdict = label
    return verdict


def score_crowding(assets: list[Asset]) -> dict[str, Any]:
    active = [a for a in assets if a.is_active]
    dormant = [a for a in assets if not a.is_active]

    weighted = sum(PHASE_WEIGHTS.get(a.max_phase, 0.25) for a in active)
    by_phase: dict[str, int] = defaultdict(int)
    for asset in active:
        by_phase[PHASE_LABELS.get(asset.max_phase, "Unknown")] += 1

    sponsors = {a.sponsor for a in active if a.sponsor}
    mechanisms = {a.mechanism_class for a in active if a.mechanism_class}
    lead_phase = max((a.max_phase for a in active), default=-1)

    return {
        "n_total": len(assets),
        "n_active": len(active),
        "n_dormant": len(dormant),
        "weighted_score": round(weighted, 1),
        "verdict": _band(weighted),
        "by_phase": dict(by_phase),
        "n_sponsors": len(sponsors),
        "n_mechanism_classes": len(mechanisms),
        "lead_phase": PHASE_LABELS.get(lead_phase, "Unknown"),
        "weights_used": {PHASE_LABELS[k]: v for k, v in PHASE_WEIGHTS.items() if k in PHASE_LABELS},
        "bands_used": [{"from": t, "verdict": v} for t, v in CROWDING_BANDS],
        "dormant_assets": [
            {"name": a.name, "phase": a.phase_label, "sponsor": a.sponsor} for a in dormant
        ],
    }


def _better_name(candidate: str, current: str) -> bool:
    """Which spelling to show. A database label is lower case and terse; a
    sponsor's is Title Case with the stage in it. Prefer the first, then the
    shorter."""
    candidate, current = candidate.strip(), current.strip()
    cheap = candidate.islower(), -len(candidate)
    have = current.islower(), -len(current)
    return cheap > have


# An indication is a disease. Three other things arrive in the same field and
# none of them is one, so ERBB2's list of 376 held "HER2 Gene Amplification"
# (who was enrolled), "central nervous system progression" (what the trial
# measured) and "cardiotoxicity" (what the drug did to them) beside breast
# cancer -- and each of those spawned three or four spellings of its own.
_A_DISEASE_NOUN = re.compile(
    r"cancer|carcinom|tumou?r|sarcom|lymphom|leuk[a]?emi|myelom|melanom|"
    r"gliom|glioblastom|blastom|neoplas|adenom|schwannom|neurom|chordom|"
    r"ependymom|meningiom|mesotheliom|myelodysplas|thymom|mycosis|"
    r"macroglobulin|malignan|disease|disorder|syndrome|deficienc|"
    r"[a-z]{3}itis\b|[a-z]{4}osis\b|[a-z]{4}pathy\b|[a-z]{4}emia\b",
    re.IGNORECASE,
)
# Who was enrolled, not what they have.
_A_BIOMARKER = re.compile(
    r"\b(amplification|amplified|overexpress\w*|expressi\w*|expressing|"
    r"mutation\w*|mutant|mutated|fusion|rearrang\w*|translocation|"
    r"wild[- ]?type|genotype|allele|exon\s*\d+|polymorph\w*|"
    r"positive|negative|status|subtype|receptor)\b",
    re.IGNORECASE,
)
# What the trial measured, not what it treated.
_AN_ENDPOINT = re.compile(
    r"\b(progression|recurrence|relapse|response|survival|remission|"
    r"resistance|refractoriness|toxicit\w*|adverse|node|nodes)\b",
    re.IGNORECASE,
)
# What the treatment did to the patient. A supportive-care or safety sub-study
# files these as its condition. The word alone does not settle it -- immune
# thrombocytopenia and warm autoimmune haemolytic anaemia are diseases people
# develop drugs for, and an earlier version of this deleted both -- so a
# symptom counts as a side effect only when the string is that symptom and
# nothing else, or when it says what caused it.
_BARE_SIDE_EFFECTS = {
    "anemia", "anaemia", "cardiotoxicity", "cardiac dysfunction",
    "cardiomyopathy", "heart failure", "neutropenia", "febrile neutropenia",
    "thrombocytopenia", "leukopenia", "nausea", "vomiting", "emesis",
    "diarrhea", "diarrhoea", "constipation", "mucositis", "stomatitis",
    "alopecia", "fatigue", "neuropathy", "peripheral neuropathy",
    "lymphedema", "lymphoedema", "hand-foot syndrome", "pain", "chronic pain",
    "insomnia", "anxiety", "depression", "weight loss", "cachexia",
    "hypertension", "kidney disorder", "renal impairment",
    "hepatic impairment", "infection", "fever", "pleural effusion",
    "healthy volunteer", "healthy volunteers", "quality of life",
}
_A_CAUSED_SIDE_EFFECT = re.compile(
    r"\b(induced|treatment[- ]emergent|therapy[- ]related|"
    r"chemotherapy[- ]related|drug[- ]related)\b", re.IGNORECASE)


_AN_ENDPOINT_ABOUT_A_DISEASE = re.compile(
    r"^(?:the\s+)?(?:tumou?r|disease|cancer|lesion)s?\s+"
    r"(progression|response|recurrence|relapse|remission|regression|control|"
    r"burden|assessment|status)$|^no evidence of disease$|^metastasis$",
    re.IGNORECASE,
)


def is_a_disease(name: str) -> bool:
    """Would a clinician call this a disease, or is it something else?

    Three things arrive in the indication field that are not diseases: who was
    enrolled ("HER2 Overexpression"), what the trial measured ("central
    nervous system progression") and what the drug did to them
    ("chemotherapy-induced anaemia"). ERBB2 carried all three, each in three
    or four spellings, inside a list of 376.
    """
    text = (name or "").strip()
    if not text:
        return False
    bare = re.sub(r"\s+", " ", text.lower()).strip(" .,")
    if bare in _BARE_SIDE_EFFECTS or _A_CAUSED_SIDE_EFFECT.search(text):
        return False
    # "tumor progression" and "tumor response" carry a disease noun and are
    # still not diseases -- they are what the trial measured happening to one.
    if _AN_ENDPOINT_ABOUT_A_DISEASE.match(bare):
        return False
    if _A_DISEASE_NOUN.search(text):
        return True
    return not (_A_BIOMARKER.search(text) or _AN_ENDPOINT.search(text))


_CANCER_TOKEN = "\u0000cancer"
# Tighter than ``same_disease``, which is right for its own job (does this
# association match any indication?) and wrong for this one. Its subset rule
# folded every cancer into the bare row "cancer", because {cancer} is a subset
# of {breast, cancer} -- ERBB2 came out with a row called "cancer" and no
# breast cancer at all. Here both sides must name something specific, and the
# bar for merging two different specific sets is higher, so that "small cell
# lung cancer" and "lung cancer" stay two rows.
_DISPLAY_THRESHOLD = 0.7


# A negation is not a detail. "non-small cell lung cancer" and "small cell
# lung carcinoma" share four tokens out of five and merged, and the shorter
# name won -- so every NSCLC programme on ERBB2 was displayed as small cell.
# The same word separates Hodgkin from non-Hodgkin lymphoma and muscle-invasive
# from non-muscle-invasive bladder cancer.
_NEGATION = "non"


def _same_row(a: frozenset[str], b: frozenset[str]) -> bool:
    if a == b:
        return True
    if (_NEGATION in a) != (_NEGATION in b):
        return False
    specific_a, specific_b = a - {_CANCER_TOKEN}, b - {_CANCER_TOKEN}
    if not specific_a or not specific_b:
        return False
    return len(a & b) / len(a | b) >= _DISPLAY_THRESHOLD


def _marker_tokens(target: Any) -> frozenset[str]:
    """The target's own short aliases, as tokens, for dropping out of a
    disease name. Descriptive names are left out: TNFSF15 is "tumor necrosis
    factor superfamily member 15", and dropping "tumor" would take the word
    out of every solid-tumour row."""
    out: set[str] = set()
    names = [getattr(target, "symbol", "") or ""]
    names += [s for s in (getattr(target, "synonyms", None) or [])]
    for name in names:
        tokens = [t for t in _TOKEN_SPLIT.split(name.lower()) if len(t) > 1]
        if not tokens or len(tokens) > 2:
            continue
        for token in tokens:
            if token in _A_CANCER_UNSPECIFIED or _A_DISEASE_NOUN.search(token):
                continue
            out.add(token)
    return frozenset(out)


def _cluster_by_disease(names: list[str], drop: frozenset[str] = frozenset()) -> dict[str, str]:
    """Map every spelling to the one name its disease will be shown under.

    Exact key equality was not enough. ``disease_key`` stems and drops filler,
    so "melanoma" and "Melanoma" collapse -- but "advanced unresectable
    melanoma" keeps its two extra tokens and stayed a separate row. The keys
    were already compared loosely everywhere else in this module by
    :func:`same_disease`; this uses the same comparison to group them, which
    is what takes PD-1 from 915 rows to a list a person can read.
    """
    keyed = [(n, disease_key(n, drop)) for n in names]
    keyed = [(n, k) for n, k in keyed if k]
    # Longest first: a specific spelling should join a general one, not the
    # other way round, and the general one is what gets displayed.
    order = sorted(keyed, key=lambda nk: (len(nk[1]), nk[0]))
    clusters: list[tuple[frozenset[str], list[str]]] = []
    for name, key in order:
        for index, (seed, members) in enumerate(clusters):
            if _same_row(key, seed):
                members.append(name)
                clusters[index] = (seed, members)
                break
        else:
            clusters.append((key, [name]))
    display: dict[str, str] = {}
    for _, members in clusters:
        best = members[0]
        for candidate in members[1:]:
            if _better_name(candidate, best):
                best = candidate
        for member in members:
            display[member] = best.strip()
    return display


def canonicalise_indications(
    assets: list[Asset], trials: Optional[list[Trial]] = None, target: Any = None
) -> int:
    """One name per disease on the assets themselves, and the phase each reached.

    The matrix below already merges spellings, but it merged them in its own
    copy. The page does not read the matrix -- it groups ``asset.indications``
    so that filtering to one modality redraws the grid -- so PD-1 was badged
    1,360 indications while the engine had resolved 915 of them, and the same
    gap sat on every target (EGFR 818/579, ERBB2 563/374, CD19 400/237). The
    number the reader saw was the raw count of spellings.

    Rather than teach the page to merge them, the merge happens once here and
    the assets carry the result, which is also what makes the counts on the
    Assets tab, the download and the matrix agree.

    ``indication_phase`` is filled at the same time and for the same reason:
    the phase an asset reached *in that indication* is resolved from the
    trials, and the page had no way to do that, so it fell back to the asset's
    overall maximum -- which is the standard way this table lies.
    """
    trials = trials or []
    by_nct = {t.nct_id: t for t in trials}

    drop = _marker_tokens(target) if target is not None else frozenset()
    every = sorted({i.strip() for a in assets for i in (a.indications or []) if i.strip()})
    display = _cluster_by_disease([n for n in every if is_a_disease(n)], drop)

    evidenced: set[str] = set()
    for asset in assets:
        reached: dict[str, int] = {}
        for nct in asset.trials or []:
            trial = by_nct.get(nct)
            if not trial:
                continue
            for condition in trial.conditions or []:
                reached[condition.strip()] = max(
                    reached.get(condition.strip(), -1), trial.phase)

        canonical: list[str] = []
        phases: dict[str, int] = {}
        from_a_trial: set[str] = set()
        for raw in asset.indications or []:
            name = display.get(raw.strip())
            if not name:
                # Not a disease, or no key to group it by. Dropped rather than
                # shown: the column is the answer to "for what", and a
                # biomarker is the answer to "in whom".
                continue
            key = disease_key(raw, drop)
            phase = reached.get(raw.strip())
            if phase is not None:
                from_a_trial.add(name)
            else:
                candidates = [p for c, p in reached.items()
                              if key and same_disease(key, disease_key(c, drop))]
                if candidates:
                    from_a_trial.add(name)
                phase = max(candidates) if candidates else asset.max_phase
            if name not in phases:
                canonical.append(name)
            phases[name] = max(phases.get(name, -1), phase)
        asset.indications = canonical
        asset.indication_phase = phases
        evidenced.update(from_a_trial)

    # The long tail. PD-1 came out of the merge with 716 diseases, 417 of them
    # carried by a single asset that never left Phase 1 -- a basket study lists
    # forty cohorts and each becomes a row. They are real, and printing them
    # buries the twenty diseases the target is actually being developed in.
    #
    # Kept: anything two or more programmes are in, and anything a trial of the
    # one programme actually names. Dropped: a lone disease carried across from
    # a drug database with no trial behind it. The page says how many were left
    # out and the download still carries every row.
    carried: dict[str, int] = {}
    for asset in assets:
        for indication in asset.indications:
            carried[indication] = carried.get(indication, 0) + 1
    # Only when the list is long enough for the tail to be the problem. The
    # grid opens on forty rows; below that every row is visible anyway and
    # dropping one loses information for nothing.
    thin: set[str] = set()
    if len(carried) > 40:
        thin = {i for i, n in carried.items() if n < 2 and i not in evidenced}
    if thin:
        for asset in assets:
            asset.indications = [i for i in asset.indications if i not in thin]
            asset.indication_phase = {k: v for k, v in asset.indication_phase.items()
                                      if k not in thin}
    return len(thin)


def indication_matrix(
    assets: list[Asset], trials: Optional[list[Trial]] = None
) -> dict[str, Any]:
    """indication -> mechanism_class -> highest phase reached *in that indication*.

    The phase is resolved per indication from the trials themselves, not from
    the asset's overall maximum. Using the asset maximum is the standard way
    this table lies: an asset in Phase 3 for one disease and a terminated
    Phase 2 for another would show Phase 3 in both rows, and a reader would
    conclude the second indication was already taken.
    """
    trials = trials or []
    by_nct = {t.nct_id: t for t in trials}

    # One row per disease, not one row per spelling of it. PD-1 came out with
    # 1,360 rows from 33 assets -- "melanoma", "Metastatic Melanoma",
    # "advanced unresectable melanoma" and "Melanoma" were four of them -- and
    # the tab was badged 1,360 while the table drew the first forty. The name
    # shown is the one a database would use: lower case, and the shortest.
    display: dict[frozenset[str], str] = {}
    for asset in assets:
        for indication in asset.indications or []:
            key = disease_key(indication)
            if not key:
                continue
            current = display.get(key)
            if current is None or _better_name(indication, current):
                display[key] = indication.strip()

    def canonical(indication: str) -> str:
        return display.get(disease_key(indication), indication.strip())

    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(lambda: -1))
    counts: dict[str, int] = defaultdict(int)
    for asset in assets:
        mechanism = asset.mechanism_class or "Unclassified"
        # What each of this asset's indications actually reached.
        per_indication: dict[str, int] = {}
        for nct in asset.trials:
            trial = by_nct.get(nct)
            if not trial:
                continue
            for condition in trial.conditions:
                key = condition.strip()
                per_indication[key] = max(per_indication.get(key, -1), trial.phase)

        # An asset that lists the same disease under three spellings is one
        # asset in that row, not three.
        seen_here: set[str] = set()
        for raw in asset.indications or ["(indication not stated)"]:
            indication = canonical(raw)
            if indication in seen_here:
                continue
            seen_here.add(indication)
            counts[indication] += 1
            phase = per_indication.get(raw.strip())
            if phase is None:
                # No trial names this indication — fall back to a fuzzy match
                # against the trial conditions before using the asset maximum.
                key = disease_key(raw)
                candidates = [
                    p for name, p in per_indication.items() if same_disease(key, disease_key(name))
                ]
                phase = max(candidates) if candidates else asset.max_phase
            if phase > matrix[indication][mechanism]:
                matrix[indication][mechanism] = phase

    ordered = sorted(
        matrix.items(),
        key=lambda kv: (-max(kv[1].values()), -counts[kv[0]], kv[0]),
    )
    mechanisms = sorted({m for row in matrix.values() for m in row})
    return {
        "mechanisms": mechanisms,
        "rows": [
            {
                "indication": indication,
                "n_assets": counts[indication],
                "cells": {m: cells.get(m, -1) for m in mechanisms},
                "max_phase": max(cells.values()),
            }
            for indication, cells in ordered
        ],
    }


# The association data is an ontology, and an ontology contains things that are
# not diseases anyone develops a drug for. KRAS's screen came back with
# "Abnormality of the cardiovascular system" and "Abnormality of the skeletal
# system": Human Phenotype Ontology terms, which describe a feature of a
# patient rather than an indication. They are not openings and they crowded out
# the rows that were.
_A_PHENOTYPE_NOT_A_DISEASE = re.compile(
    r"^(abnormality of|abnormal |decreased |increased |elevated |reduced )", re.I)


def _not_an_indication(name: str) -> bool:
    return bool(_A_PHENOTYPE_NOT_A_DISEASE.match((name or "").strip()))


# "Noonan syndrome 3" and "Noonan syndrome" are the same disease; the ontology
# numbers the subtypes by causal gene.
_A_SUBTYPE_SUFFIX = re.compile(
    r"[,\s]+(type\s+)?([0-9]{1,2}|[ivx]{1,4})\s*$", re.I)


def _family_key(name: str) -> str:
    stem = _A_SUBTYPE_SUFFIX.sub("", (name or "").strip())
    return re.sub(r"[^a-z0-9]", "", stem.lower())


def _family_name(name: str) -> str:
    """The disease without its subtype number. "cardiofaciocutaneous syndrome
    2" is a subtype of a disease with a name, and the name is what a reader
    recognises."""
    return _A_SUBTYPE_SUFFIX.sub("", (name or "").strip()).rstrip(" ,")


def find_whitespace(
    assets: list[Asset],
    associations: list[DiseaseAssociation],
    trials: Optional[list[Trial]] = None,
) -> list[dict[str, Any]]:
    """Well-evidenced diseases with nothing in the clinic.

    Two conditions, both required: the target–disease association clears a
    threshold *and* carries genetic evidence (the component that replicates
    best), and no asset has taken that disease past preclinical.
    """
    trials = trials or []

    # Everything anyone has claimed, from both the asset table and the trial
    # conditions — a trial can name an indication the asset record does not.
    claimed: list[tuple[frozenset[str], int]] = []
    for asset in assets:
        for indication in asset.indications:
            claimed.append((disease_key(indication), asset.max_phase))
    for trial in trials:
        for condition in trial.conditions:
            claimed.append((disease_key(condition), trial.phase))

    out: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    kept_keys: list[frozenset[str]] = []
    for association in associations:
        if association.score < WHITESPACE_MIN_ASSOCIATION:
            continue
        if association.genetic_score < WHITESPACE_MIN_GENETIC:
            continue
        if _not_an_indication(association.name):
            continue
        # "Noonan syndrome", "Noonan syndrome 3", "cardiofaciocutaneous
        # syndrome", "cardiofaciocutaneous syndrome 2" -- the ontology carries
        # a term per causal gene, and KRAS scores on all of them. They are one
        # disease each, listed once.
        family = _family_key(association.name)
        if family in seen_families:
            continue
        # And the same disease spelled differently: "linear nevus sebaceous
        # syndrome" beside "Linear nevus sebaceus syndrome", "Noonan syndrome"
        # beside "Noonan syndrome and Noonan-related syndrome". Compared only
        # against the rows already kept, so one loose match cannot chain a
        # whole list together.
        this_key = disease_key(association.name)
        if any(same_disease(this_key, kept) for kept in kept_keys):
            continue
        seen_families.add(family)
        kept_keys.append(this_key)
        key = disease_key(association.name)
        hits = [phase for other, phase in claimed if same_disease(key, other)]
        best = max(hits) if hits else -1
        if best > WHITESPACE_MAX_PHASE:
            continue
        association.n_assets = len(hits)
        association.highest_phase = best
        out.append(
            {
                "disease": _family_name(association.name) or association.name,
                "disease_id": association.disease_id,
                "association_score": round(association.score, 3),
                "genetic_score": round(association.genetic_score, 3),
                "highest_phase": "None in clinic" if best < 0 else PHASE_LABELS.get(best, "Unknown"),
                "n_assets": association.n_assets,
            }
        )
    return sorted(out, key=lambda r: -r["genetic_score"])[:15]
