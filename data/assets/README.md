# Hand-entered programmes

One CSV per target, named `<SYMBOL>.csv`. Rows here are merged into the asset
table before anything is counted, so the asset count, the phase histogram, the
crowding band and the mechanism clusters all see them.

## Why the file exists

The discovery rules only take a drug from a trial when the trial's own words
tie it to the target. That is deliberate — it is what keeps posaconazole off
CARD9 and hydrochlorothiazide off MAP3K14 — and it has a cost. CLDN18 is the
clearest case:

    NCT07431281 — "Sonesitatug Vedotin in Combination With Capecitabine ...
    in Participants With Advanced or Metastatic Gastric ... Adenocarcinoma
    Expressing Claudin18.2"

Claudin18.2 appears three times in that record. All three are `Expressing` or
`-positive`: the enrolment criterion, not a statement about what the drug
binds. The rule cannot tell that record apart from a chemotherapy trial in the
same population, and it should not guess. A person can, and the citation is
what makes the difference between a judgement and a guess.

Use this file for that. Not for programmes you remember — for programmes you
can point at.

## Columns

| Column | Notes |
|---|---|
| `name` | The name to show. Matched against the rest of the table, so a row that is already there merges rather than duplicating |
| `sponsor` | The company or institution running it |
| `modality` | One of: Monoclonal antibody, Bispecific antibody, Antibody-drug conjugate, Fc-fusion / ligand trap, Cell therapy (CAR-T), Small molecule, Oligonucleotide, Peptide, Vaccine. Blank is fine — the rules will classify from `mechanism` |
| `mechanism` | What it does to the target, in a sentence. This is what the mechanism clusters read, so write the action: "kills through ADCC and CDC", "cleavable linker to MMAE" |
| `max_phase` | Preclinical / Phase 1 / Phase 2 / Phase 3 / Approved. Anything else reads as Unknown |
| `indications` | Semicolon-separated |
| `trials` | Semicolon-separated NCT ids. Optional — trials also attach by name |
| `synonyms` | Semicolon-separated. Code names and brand names go here, and they are what lets the row merge with a database row |
| `chembl_id` | Optional. Fill it when a database row already carries this molecule's name as one of *its* synonyms and would swallow the row. ChEMBL lists "Trastuzumab" and "Herceptin" among the synonyms of ado-trastuzumab emtansine, so trastuzumab merged into the ADC and ERBB2 showed four conjugates and no parent antibody. Two different ChEMBL ids keep the two rows apart |
| `source_url` | **Required. A row without one is skipped**, silently and on purpose: the rest of the table is checkable, and an unsourced row would borrow that credibility |
| `note` | Shown on the row's provenance line. Say what the source establishes and when |

## Two things to know

**A row wins on the fields it fills.** Open Targets records zolbetuximab as a
"Claudin-18 binding agent" at Phase 3. It is a chimeric IgG1 that kills through
ADCC and CDC, and the FDA approved it in October 2024. The hand row carries the
later reading and the citation, so it takes precedence — which is the whole
reason to type one in.

**Edits land on the next refresh, not the next page load.** A programme changes
every figure above it on the page. Deal rows are attached when the page is
read; these are not, because a row the crowding band has never seen would make
the arithmetic wrong. Run `6-REFRESH-LIBRARY.bat` after editing. Until you do,
the consistency check says the file and the record disagree, and names the rows.

`CLDN18.csv` ships filled in as the worked example.
