"""Does this trial have anything to do with this target?

The ClinicalTrials.gov sweep exists to catch programmes the drug databases
have not linked: an "anti-BAFF-R CAR-T" with no ChEMBL entry, a Chinese
Phase 1 that Open Targets has never heard of. It searches ``query.intr`` for
the target's names and every known drug name, and then treats what comes back
as work on the target.

That trust was misplaced, and the failure was not subtle. The search terms
included the target's full descriptive name, so MAP3K14 was searched as
"mitogen-activated protein kinase kinase kinase 14". The registry's
intervention search is stemmed rather than exact, a phrase that long matches
almost anything, and the first study it returned was:

    NCT00896389 - "Salt Loading and Thiazide Intervention Study"
    Condition: Hypertension
    Interventions: Apo-Hydro, Aquazide H, Dichlotride, Esidrex, HCTZ,
                   HydroSaluric, Hydrochlorothiazide, Hydrochlorothiazide (HCTZ)

Every one of those brand names became a separate asset. All eight were Phase
4, because hydrochlorothiazide is approved. The page then reported "13
approved drugs on this target" for a kinase that has never had a drug reach
the clinic. All 228 MAP3K14 assets came from trials that never mention
MAP3K14, NIK, NF-kappa-B or the word kinase; CARD9 acquired posaconazole
because CARD9 deficiency causes fungal disease; IL23A acquired minoxidil.

Two guards, and the second is the one that matters:

**Do not search on prose.** A protein's descriptive name is not an
intervention. Only the symbol, real aliases and known drug names go to the
registry.

**Check what comes back.** Whatever the query does, a trial earns its place
only if its own text names the target or one of its drugs. This holds even if
the registry's matching changes, which is why it is here rather than in the
query builder -- a stricter query is a guess about someone else's search
engine, and this is a fact about the record in hand.

Matching is on word boundaries over the fields that would carry the name:
title, interventions, and the sponsor's own brief summary. A trial that
mentions nothing is dropped from the asset table. It is not evidence about
the target, and counting it is worse than missing it: a missing trial makes
the picture thin, an invented one makes it wrong.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

# Words that appear in half the protein names in the genome. On their own they
# carry no identity, so a trial matching only these has matched nothing.
_GENERIC = {
    "protein", "kinase", "receptor", "factor", "member", "family", "subunit",
    "alpha", "beta", "gamma", "delta", "type", "domain", "containing",
    "associated", "related", "like", "chain", "complex", "binding", "cell",
    "human", "gene", "antigen", "channel", "transporter", "enzyme", "ligand",
    "superfamily", "activated", "regulated", "induced", "soluble", "surface",
    "nuclear", "membrane", "recruitment", "mitogen", "interleukin", "cluster",
    "differentiation", "necrosis", "tumor", "tumour", "growth", "signal",
    "transducer", "activator", "transcription", "response", "element",
}

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def is_specific(term: str) -> bool:
    """Is this term worth searching a registry for?

    A term is specific when, after dropping the filler words above, something
    is left. "mitogen-activated protein kinase kinase kinase 14" reduces to
    "14" and is rejected; "MAP3K14", "BAFF-R" and "ianalumab" survive.
    """
    term = (term or "").strip()
    if len(term) <= 3:
        return False
    remaining = [t for t in _tokens(term) if t not in _GENERIC and len(t) > 1]
    if not remaining:
        return False
    # A term that is only digits after filtering ("14") identifies nothing.
    return any(not t.isdigit() for t in remaining)


# A counter-ion or a hydration state is not a different molecule. Open Targets
# lists "NERATINIB" and "NERATINIB MALEATE" as two rows, "DACOMITINIB" and
# "DACOMITINIB ANHYDROUS" as two more, and the asset table showed both -- so
# EGFR reported five programmes it does not have and the crowding band counted
# them. Worse, the salt form is sometimes the only row: ERBB2 held "LAPATINIB
# DITOSYLATE" and no plain lapatinib, so every trial that says "lapatinib"
# failed the relevance check and was reported as unverified.
#
# Only a trailing modifier is stripped. A leading one is part of the name
# ("sodium oxybate" is not oxybate), and the word has to stand alone.
_SALT_FORMS = (
    "ditosylate|tosylate|besylate|mesylate|mesilate|maleate|malate|fumarate|"
    "succinate|tartrate|citrate|acetate|oxalate|pamoate|palmitate|stearate|"
    "lactate|gluconate|trifluoroacetate|tosilate|edisylate|napadisylate|"
    "hydrochloride|dihydrochloride|hydrobromide|bromide|chloride|iodide|"
    "sulfate|sulphate|bisulfate|phosphate|diphosphate|nitrate|"
    "sodium|potassium|calcium|magnesium|meglumine|choline|olamine|"
    "anhydrous|monohydrate|dihydrate|trihydrate|hemihydrate|hydrate"
)
_SALT_RE = re.compile(r"(?<=\w)\s+(?:" + _SALT_FORMS + r")\b", re.IGNORECASE)


def strip_salt_form(name: str) -> str:
    """"NERATINIB MALEATE" -> "NERATINIB". Unchanged when nothing is stripped."""
    out = _SALT_RE.sub("", name or "")
    out = re.sub(r"\s{2,}", " ", out).strip()
    # Never strip a name away to nothing, and never down to an initialism that
    # would collide with something else.
    return out if len(out) > 3 else (name or "").strip()


def _patterns(terms: Iterable[str]) -> list[re.Pattern[str]]:
    out: list[re.Pattern[str]] = []
    seen: set[str] = set()
    for term in terms:
        term = (term or "").strip()
        if not term or term.lower() in seen or not is_specific(term):
            continue
        seen.add(term.lower())
        # Word boundaries, and the separators inside a name are interchangeable
        # so that "BAFF R", "BAFF-R" and "BAFFR" all match one another.
        parts = [re.escape(t) for t in _tokens(term)]
        if not parts:
            continue
        out.append(re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]{0,2}".join(parts)
                              + r"(?![a-z0-9])", re.I))
    return out


def _haystack(trial: Any) -> str:
    """The fields that would carry a target or drug name if the trial were
    about it. Conditions are deliberately excluded: a disease name is not a
    target name, and including them is how CARD9 collected antifungals."""
    parts: list[str] = [
        str(getattr(trial, "title", "") or ""),
        str(getattr(trial, "brief_summary", "") or ""),
    ]
    parts.extend(str(i or "") for i in (getattr(trial, "interventions", None) or []))
    return " ".join(parts)


def trial_is_on_target(trial: Any, terms: Iterable[str]) -> bool:
    """True when the trial's own text names the target or one of its drugs."""
    text = _haystack(trial)
    if not text.strip():
        # No title, no interventions, no summary: nothing to judge it on. Keep
        # it rather than delete a record for being sparse -- it contributes no
        # asset either way, and the trial tables are honest about empty fields.
        return True
    return any(p.search(text) for p in _patterns(terms))


# A gene named as a way of choosing patients, not as a thing a drug acts on.
# CARD9's only trial is "Pilot Study of Posaconazole in Crohn's Disease", whose
# conditions are "Crohn Disease" and "CARD9 S12N Risk Allele": the allele
# selects who enrols, and posaconazole is an antifungal acting on fungal
# CYP51. The trial belongs in the trial list -- it is real work on people
# defined by this gene -- but its interventions are not programmes against the
# target, and posaconazole was being reported as an approved CARD9 drug.
_POPULATION_CONTEXT = re.compile(
    # A protein-variant notation is a population all by itself: G12C, V600E,
    # S12N, T790M. "JAB-21822 Combined With Chemotherapy and Bevacizumab in
    # Second-line KRAS G12C CRC" names no mutation word at all, and
    # bevacizumab sat in the KRAS asset table because of it.
    r"(\b[A-Z]\d{1,4}[A-Z]\b|"
    # The receptor-status shorthand, written with a sign instead of a word:
    # "Luminal-like(HER2-,ER+)", "advanced ER+/HER2- breast cancer". The words
    # below catch "HER2-negative"; nothing caught the sign, and "Niraparib Plus
    # Aromatase Inhibitors for Luminal-like(HER2-,ER+) ... Breast Cancer" put
    # aromatase inhibitors in the ERBB2 asset table -- off a trial that
    # enrolled patients whose tumours do not express it.
    r"[A-Za-z0-9][+-](?=[\s,;)\]/]|$)|"
    r"risk\s+allele|allele|deficien\w*|mutat\w+|variant\w*|polymorph\w*|"
    r"genotype\w*|carrier\w*|haplotype\w*|snp|wild[-\s]?type|"
    r"knockout|null|loss[-\s]of[-\s]function|gain[-\s]of[-\s]function|"
    r"positive|negative|expressing|expression|status|mutant)",
    re.IGNORECASE,
)


def target_is_in_the_drug_name(name: str, terms: Iterable[str]) -> bool:
    """Does the molecule's own name carry the target? "HER2/41BB Bispecific"."""
    text = str(name or "")
    return bool(text.strip()) and any(p.search(text) for p in _patterns(terms))


def names_target_as_a_drug_target(trial: Any, terms: Iterable[str]) -> bool:
    """Is the target named as something a drug acts on, or as a genotype?

    Every mention is inspected with a little text either side. If all of them
    sit in genotype language, the trial is about a population defined by this
    gene rather than about drugging it, and nothing in its intervention list
    should enter the asset table.
    """
    # Field by field, not one concatenated string. The window is 40 characters
    # either side, and on a joined string it reached out of the field it was
    # reading: PRS-343 is filed with the intervention "HER2/41BB Bispecific"
    # and the condition "HER2-positive Breast Cancer", and the word "positive"
    # from the second landed inside the window taken around the first. A
    # bispecific whose own name states the target was read as a genotype.
    segments: list[str] = [
        str(getattr(trial, "title", "") or ""),
        str(getattr(trial, "brief_summary", "") or ""),
    ]
    segments.extend(str(i or "") for i in (getattr(trial, "interventions", None) or []))
    segments.extend(str(c or "") for c in (getattr(trial, "conditions", None) or []))
    patterns = _patterns(terms)
    if not patterns:
        return False
    saw_any = False
    for text in segments:
        for pattern in patterns:
            for match in pattern.finditer(text):
                saw_any = True
                window = text[max(0, match.start() - 40):match.end() + 40]
                if not _POPULATION_CONTEXT.search(window):
                    return True
    # No mention at all is handled by filter_trials; here it means every
    # mention was a genotype.
    return not saw_any


def filter_trials(trials: list, terms: Iterable[str]) -> tuple[list, list]:
    """Split a sweep into (on target, not on target)."""
    patterns = _patterns(terms)
    if not patterns:
        return list(trials), []
    keep, drop = [], []
    for trial in trials:
        text = _haystack(trial)
        if not text.strip() or any(p.search(text) for p in patterns):
            keep.append(trial)
        else:
            drop.append(trial)
    return keep, drop


def _vouched_by_a_database(asset: Any) -> bool:
    """Did a drug database say this molecule acts on this target?

    Open Targets and ChEMBL assert a drug-target link; the registry sweep does
    not -- it only found a string in a trial record. The distinction decides
    which names are allowed to speak for the target.

    A hand-entered row counts. The rule this enforces is that a name may only
    speak for the target if something outside the sweep put it there, so that
    a trial the sweep invented cannot then vouch for itself; a row in
    data/assets/<SYMBOL>.csv is outside the sweep and carries a citation, and
    rows without a source_url never load at all. Excluding them cost ERBB2
    thirteen trials: Open Targets lists the trastuzumab conjugates and not the
    parent antibody, the hand row supplies it with the FDA label attached, and
    every trial that says "trastuzumab" was still being reported as a trial
    that never names the target.
    """
    return any(getattr(p, "source", "") != "ctgov"
               for p in getattr(asset, "provenance", None) or [])


def from_the_sweep_alone(asset: Any) -> bool:
    """Did nothing but the registry sweep put this asset in the table?

    Different question from :func:`_vouched_by_a_database`, which decides
    which names are allowed to build a search query and so excludes a
    hand-entered one too. This one asks who created the row, and a row a
    person entered by hand is not the sweep's to overwrite.
    """
    sources = [getattr(p, "source", "") for p in getattr(asset, "provenance", None) or []]
    return bool(sources) and all(s == "ctgov" for s in sources)


def terms_for(target: Any, assets: Optional[list] = None) -> list[str]:
    """Every name that identifies this target or a drug known to act on it.

    Used both to build the registry query and to check what it returns, so the
    two can never drift apart.

    Only database-vouched drugs are included, and that restriction is the
    whole point. The first version added every asset name, including the ones
    the sweep had itself invented -- so the hypertension trial that created
    "Hydrochlorothiazide" was then kept *because* it mentioned
    hydrochlorothiazide. The bogus asset and the bogus trial vouched for each
    other and the filter passed everything. Evidence has to come from outside
    the thing it is judging.
    """
    terms: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        value = (value or "").strip()
        key = value.lower()
        if value and key not in seen and is_specific(value):
            seen.add(key)
            terms.append(value)

    add(getattr(target, "symbol", "") or "")
    for synonym in getattr(target, "synonyms", None) or []:
        add(synonym)
    # target.name is NOT added. It is a description, not an identifier, and
    # searching a registry for it is what produced the diuretics.
    for asset in assets or []:
        if not _vouched_by_a_database(asset):
            continue
        name = getattr(asset, "name", "") or ""
        add(name)
        # A registry row is often the salt: Open Targets gave ERBB2 "LAPATINIB
        # DITOSYLATE" and no plain lapatinib, and the whole multi-word phrase
        # has to appear for the pattern to match. Seventeen ERBB2 trials that
        # say "lapatinib" or "Tykerb" were therefore reported as trials that
        # never name the target. The counter-ion is not part of what a sponsor
        # writes, so the active moiety is searched for as well.
        add(strip_salt_form(name))
        for synonym in (getattr(asset, "synonyms", None) or [])[:3]:
            add(synonym)
            # The synonyms carry the salt too: osimertinib's first three are
            # "AZD-9291 MESYLATE", "AZD9291 mesylate", "Mereletinib mesilate",
            # and the code name a trial actually writes -- AZD9291 -- is in
            # none of them until the counter-ion comes off.
            add(strip_salt_form(synonym))
    return terms


# ---------------------------------------------------------------------------
# Which drug in a trial is a programme against the target?
#
# The sweep answers "is this trial about the target". It does not answer "which
# of this trial's drugs acts on the target", and on a busy target the second
# question is where the table goes wrong. PDCD1 stored 197 assets. Twenty-six
# came from a drug database. The other 171 were interventions lifted out of
# combination studies: carboplatin, cisplatin, gemcitabine and paclitaxel, but
# also omeprazole, loperamide and smectite powder from the supportive-care arms,
# trastuzumab (HER2), bevacizumab (VEGF), ipilimumab (CTLA-4), evolocumab
# (PCSK9), an oesophagectomy, a cryoablation, and "Collecting samples from
# participant".
#
# Each of those trials really is a PD-1 trial. None of those drugs is a PD-1
# drug. Being given alongside pembrolizumab is not a mechanism.
#
# There is no offline way to look up what a molecule binds, so the rule is not
# "decide what it binds" -- it is "does this record say?". A drug joins the
# asset table when the trial's own words tie it to the target:
#
#   route 1  the drug's name says so
#            "Anti-BAFF-R CAR-T", "PD-1/VEGF bispecific antibody"
#   route 2  the title puts the target beside the drug, with nothing
#            combinatorial in between
#            "Efficacy and Safety of BCD-100 (Anti-PD-1) in Combination With..."
#                             ^^^^^^^^^^^^^^^^^^ adjacent -> BCD-100 is kept
#            "Lenvatinib Plus PD-1 Antibody vs TACE"
#                       ^^^^^^ "Plus" -> lenvatinib is a partner, not a
#                              PD-1 drug, and it is not kept
#
# Anything else is a partner drug whose mechanism this record does not state.
# The trial still counts as a trial. Its partner drugs are not counted as
# programmes against the target, and the page says how many were set aside.

# Words that turn "X <word> Y" into two separate drugs given together. If one
# of these sits between the drug and the target's name, the sentence is naming
# a combination, not explaining what the drug is.
_COMBINATION = re.compile(
    r"\b(plus|and|or|with|without|versus|vs|combin\w*|following|followed|"
    r"after|before|added|add[- ]on|adjuvant|neoadjuvant|sequential|alone|"
    r"monotherapy|compared|comparing|arm|group|then|switch\w*|prior|"
    r"maintenance|induction|consolidation|salvage|backbone|regimen)\b"
    # The comma is not here. It joins a list -- "Camrelizumab, Fluzoparib,
    # Nab-paclitaxel" -- but it also introduces the appositive that says what a
    # drug is: "MK-7240, an anti-TL1A antibody". Rejecting every comma cost
    # five real BCMA CAR-T programmes, a BeiGene pan-KRAS degrader and four
    # CD19 assets, all of them written in that form. Which of the two a comma
    # is doing is settled below, by whether the words after it describe the
    # drug.
    r"|[+/;]",
    re.IGNORECASE,
)

# Route 2 asks whether the title names the target beside the drug. Beside is
# not enough. Three rows got in on proximity alone and none of them acts on
# the target it was filed under:
#
#   "Zolbetuximab With mFOLFOX6 or CAPOX in Claudin 18.2 Overexpressed ..."
#        CAPOX is capecitabine and oxaliplatin, four characters from CLDN18
#   "Apatinib ... Harboring Wild-type Epidermal Growth Factor Receptor"
#        apatinib is a VEGFR2 inhibitor, filed under EGFR
#   "MS-20 has also been shown to be anti-PD-1 booster ..."
#        a fermented soybean adjuvant, filed under PD-1
#
# So the words in between have to *describe the drug*. These are the ones a
# sponsor writes when saying what a molecule is.
_SAYS_WHAT_THE_DRUG_IS = re.compile(
    r"\b(anti|against|directed|target(?:ing|ed)?|specific|selective|"
    r"block(?:ade|ing|s)?|inhibit(?:or|ors|ing|s)?|antagoni\w*|agoni\w*|"
    r"degrad\w*|bind(?:er|ers|ing)?|engager|trap|decoy|"
    r"car|cart|chimeric antigen receptor|adc|conjugate|bispecific|"
    r"monoclonal|antibody|is an?|as an?)\b",
    re.IGNORECASE,
)

# ... and it has to be a description rather than a claim. The MS-20 sentence
# passes every other test: eight words, no combination word, and "anti-PD-1"
# right there in it. What it says is that a gut-microbiome adjuvant makes
# someone else's PD-1 antibody work better, which is the opposite of the drug
# acting on PD-1. A drug defined by what it was given after, or what it failed
# on, is not defined by what it binds either.
_A_CLAIM_NOT_A_DESCRIPTION = re.compile(
    r"\b(shown|shows?|demonstrat\w*|report\w*|known|believ\w*|suggest\w*|"
    r"appears?|seems?|been|has|have|had|was|were|may|might|can|could|will|"
    r"boost\w*|potentiat\w*|enhanc\w*|sensiti[sz]\w*|synerg\w*|augment\w*|"
    r"resistan\w*|refractor\w*|relapsed|progress\w*|fail\w*|intoleran\w*|"
    r"na[iï]ve|pretreated|experienced|eligible|ineligible)\b",
    re.IGNORECASE,
)

# A plural class label is a category of marketed drugs, not one programme.
# "PD-1 inhibitors" is what an investigator writes when the protocol lets each
# site use whichever checkpoint antibody it stocks -- NCT05535998 pairs it with
# "Targeted therapy" and names no sponsor but the investigator. It sat in the
# table beside pembrolizumab with a phase of its own.
#
# The singular is a different statement. "Anti-PD-1 monoclonal antibody" is one
# unnamed drug in one Phase 2, and that programme is real.
_A_CATEGORY_NOT_A_PROGRAMME = re.compile(
    r"\b(inhibitors|antibodies|agents|drugs|blockers|antagonists|agonists|"
    r"therapies|immunotherapies|medications|products|molecules|treatments|"
    r"regimens|compounds|inhibitor\(s\)|antibody\(s\))\b",
    re.IGNORECASE,
)


def names_a_category(name: str) -> bool:
    """Is this label a class of drugs rather than one of them?"""
    return bool(_A_CATEGORY_NOT_A_PROGRAMME.search(name or ""))


# A full stop, question mark or newline with whitespace after it. Abbreviations
# are not excluded, and do not need to be: a gap holding "et al. " is prose
# either way.
_SENTENCE_END = re.compile(r"[.!?](?=\s)|\n")


def _closes_someone_elses_bracket(gap: str) -> bool:
    """Did the target's name sit inside a parenthesis belonging to another drug?

    "Camrelizumab (Immunotherapy, PD-1 inhibitor), Fluzoparib (PARP inhibitor)"
    puts "PD-1 inhibitor" thirteen characters from fluzoparib, with a comma and
    a class word in between -- every mark of an appositive. The bracket says
    otherwise: the description closes before fluzoparib is reached, so it
    describes camrelizumab. Fluzoparib is a PARP inhibitor, and the sentence
    says so.
    """
    depth = 0
    for character in gap:
        if character in "([":
            depth += 1
        elif character in ")]":
            if depth == 0:
                return True
            depth -= 1
    return False

# Words that describe a kind of drug rather than name one. "PD-1 inhibitor",
# "Immune checkpoint inhibitor" and "Anti-PD-1 monoclonal antibody" were three
# separate rows in the PDCD1 table, none of them a molecule.
_CLASS_WORDS = {
    "anti", "antibody", "antibodies", "monoclonal", "mab", "moab", "inhibitor",
    "inhibitors", "blocker", "blockers", "blockade", "agonist", "antagonist",
    "agent", "agents", "therapy", "therapies", "therapeutic", "treatment",
    "drug", "drugs", "medication", "targeting", "targeted", "directed",
    "checkpoint", "immune", "immunotherapy", "ici", "icis", "bispecific",
    # "EGFR-TKI" sat in the EGFR table at Phase 4, because erlotinib is
    # approved and the class inherits the phase of its best member. The
    # trial it came from is "Cryotherapy Combine Icotinib for Advanced
    # NSCLC" -- a real study of a real EGFR inhibitor, whose intervention
    # field names the class rather than the molecule. An approved drug that
    # is not a drug is the MAP3K14 failure again, one class word later.
    "tki", "tkis", "generation", "first", "second", "third", "fourth", "next",
    "inhibitors", "line",
    "conjugate", "adc", "car", "cart", "vaccine", "molecule", "small",
    "inhibition", "axis", "pathway", "based", "class", "standard", "care",
    "of", "the", "a", "an", "and", "or", "with", "for", "in", "on", "to",
    "single", "dual", "novel", "new", "any", "other", "plus", "combination",
    "full", "fully", "recombinant", "humanized", "humanised", "chimeric",
    "biosimilar", "autologous", "allogeneic", "engineered", "modified",
    "injection", "named", "generic", "originator", "reference",
    "cells", "cart", "expressing", "targeting", "vivo", "vitro", "product",
    "construct", "infusion", "transduced", "redirected", "armored",
}


def names_no_molecule(
    name: str, target_terms: Iterable[str], target_words: Iterable[str] = ()
) -> bool:
    """Is this intervention a category rather than a named drug?

    The target's own names are struck out, then the words that describe a class
    of drug. If nothing is left, the sponsor wrote down what kind of thing the
    arm gets rather than which molecule -- "PD-1 antibody", "Immune checkpoint
    inhibitor", "Standard of therapy". Those are not programmes and cannot be
    counted as ones.

    ``target_words`` carries the loose words of the target's descriptive name
    as well, so "Anti-PD-1 (Anti-Programmed-Death-1)" reduces to nothing in the
    same way "PD-1 antibody" does. The description is useless as a search term
    -- that is what put diuretics on MAP3K14 -- but it is exactly right for
    recognising a reader-facing paraphrase of the target's own name.
    """
    text = name or ""
    for pattern in _patterns(target_terms):
        text = pattern.sub(" ", text)
    loose = {w.lower() for w in target_words}
    # A single character never names a drug. "Autologous BAFFR-CAR T Cells"
    # leaves only the "T" of "T cells" behind, and that lone letter was enough
    # to make Mayo Clinic's one CAR-T look like three separate programmes.
    left = [t for t in _tokens(text)
            if len(t) > 1 and t not in _CLASS_WORDS and t not in _GENERIC
            and t not in loose and not t.isdigit()]
    return not left


def target_words(target: Any) -> set[str]:
    """Every loose word of the target's own names, description included."""
    out: set[str] = set()
    for value in ([getattr(target, "symbol", "") or "", getattr(target, "name", "") or ""]
                  + list(getattr(target, "synonyms", None) or [])):
        out.update(_tokens(value))
    return out


def _spans(text: str, needle: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    low, want = text.lower(), (needle or "").lower()
    if not want:
        return out
    at = low.find(want)
    while at != -1:
        out.append((at, at + len(want)))
        at = low.find(want, at + 1)
    return out


def drug_is_directed_at_target(trial: Any, name: str, target_terms: Iterable[str]) -> bool:
    """Does this trial's own text say this drug acts on this target?

    Route 1, the drug's name carries the target's name. Route 2, the title
    names the target within a short reach of the drug and puts no combination
    word in between. Neither is a guess about pharmacology; both are readings
    of the record in hand.
    """
    patterns = _patterns(target_terms)
    if not patterns or not (name or "").strip():
        return False
    if any(_a_drug_target_here(name, m) for p in patterns for m in p.finditer(name)):
        return True
    # The title first, then the sponsor's own summary -- "BCD-100 (Anti-PD-1)"
    # is as likely to be written in one as the other. Joined with a full stop,
    # because the two are separate sentences and running them together made
    # one: NCT02332512 ends its title "...Harboring Wild-type Epidermal Growth
    # Factor Receptor (EGFR)" and opens its summary "Apatinib is a new kind of
    # selective VEGFR-2 inhibitor". Concatenated, that reads as "(EGFR)
    # Apatinib is a", and a VEGFR2 inhibitor entered the EGFR table on the
    # strength of a sentence that says it is not one.
    title = ". ".join(filter(None, [getattr(trial, "title", "") or "",
                                    getattr(trial, "brief_summary", "") or ""]))
    drug_at = _spans(title, name)
    if not drug_at:
        return False
    for pattern in patterns:
        for match in pattern.finditer(title):
            # The gene named as a way of choosing patients rather than as a
            # thing a drug acts on. This is what oncology titles do most:
            # "Bortezomib in KRAS-Mutant Non-Small Cell Lung Cancer" reads
            # exactly like "JDQ443 for KRAS G12C NSCLC", and only one of those
            # drugs is aimed at KRAS. The record does not say which, so
            # neither is taken -- bortezomib is a proteasome inhibitor, and
            # counting it as a KRAS programme is the mistake posaconazole made
            # on CARD9.
            if not _a_drug_target_here(title, match):
                continue
            for start, end in drug_at:
                if match.start() >= end:
                    gap = title[end:match.start()]
                    # The describing word can sit after the target's name as
                    # easily as before it -- "ALLO-715 BCMA CAR T Cells" puts
                    # the whole description on the far side of "BCMA" -- so the
                    # span read for it runs from the drug through a few words
                    # past the target.
                    described = title[start:match.end() + 25]
                else:
                    gap = title[match.end():start]
                    described = title[match.start():end + 25]
                # Far enough apart and the sentence has moved on to something
                # else; a combination word means they are two drugs, not one
                # drug and its description.
                if len(gap) > 40 or _COMBINATION.search(gap):
                    continue
                # Apposition does not survive a full stop, or a bracket that
                # closes around the other drug. Two names either side of one of
                # those are two statements.
                if _SENTENCE_END.search(gap) or _closes_someone_elses_bracket(gap):
                    continue
                # A mention is not a statement. The record has to say what the
                # drug is, and say it rather than claim something about it.
                if _A_CLAIM_NOT_A_DESCRIPTION.search(gap):
                    continue
                if not _SAYS_WHAT_THE_DRUG_IS.search(described):
                    continue
                return True
    return False


# A ligand and its receptor are two molecules whose names differ by one
# letter, and the shorter one matches inside the longer: "BAFF" is found in
# every "BAFF-R". Five BAFF-R CAR-T programmes and Novartis's anti-BAFF-R
# antibody sat in the BAFF table because of it -- while Open Targets files
# ianalumab under TNFRSF13C, correctly, one page away.
#
# No list of receptors is needed to see this. A target whose own name is the
# receptor carries "BAFF-R", "BAFF receptor" and "BAFFR" among its synonyms,
# so its pattern consumes the suffix and there is nothing left after the match
# to trip on. Only the ligand's shorter pattern stops in the middle of a word
# it does not own.
_A_RECEPTOR_NOT_THIS = re.compile(r"^[-‐-―\s]?(?:R\b|Rs\b|receptors?\b)")


def _a_drug_target_here(text: str, match: "re.Match[str]") -> bool:
    """Is this one mention of the target naming a drug target or a genotype?"""
    if _A_RECEPTOR_NOT_THIS.match(text[match.end():match.end() + 12]):
        return False
    window = text[max(0, match.start() - 40):match.end() + 40]
    return not _POPULATION_CONTEXT.search(window)


def target_terms(target: Any) -> list[str]:
    """The target's own names, without any drug names.

    ``terms_for`` mixes in every known drug because the registry query needs
    both. The two questions above are about the *target* appearing beside a
    drug, so a list that also contains drug names would let one drug vouch for
    another standing next to it.
    """
    out: list[str] = []
    seen: set[str] = set()
    for value in [getattr(target, "symbol", "") or ""] + list(
            getattr(target, "synonyms", None) or []):
        value = (value or "").strip()
        if value and value.lower() not in seen and is_specific(value):
            seen.add(value.lower())
            out.append(value)
    return out
