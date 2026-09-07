# Architecture

The design problem is not retrieval. Three public APIs will hand over everything
here in about forty lines of code. The problem is that the union of those three
APIs is *wrong* in specific, predictable ways, and a memo built on the raw union
is confidently misleading rather than merely incomplete.

So this document is mostly about the reconciliation and judgement layers, and
about which assumptions are stated rather than hidden.

The system is three layers, and the separation is load-bearing: the engine has
no web dependencies and does not know the site exists, which is what lets the
same analysis serve a web request, a CLI run and a CI job without three
versions of it.

```
  web/        FastAPI + a no-build frontend        ← plumbing only
  ────────────────────────────────────────────────
  landscape/  the engine: symbol in, analysis out  ← stdlib only
  ────────────────────────────────────────────────
  data/       curated landscapes, deals, index     ← committed
```

```
  gene symbol
      │
      ▼
┌─────────────┐   Ensembl ID · tractability · known drugs · disease associations
│ Open Targets│──────────────────────────────────────────────────┐
└─────────────┘                                                  │
┌─────────────┐   action_type · molecule_type · max_phase         │
│   ChEMBL    │──────────────────────────────────────────────────┤
└─────────────┘                                                  │
┌─────────────┐   trials · phases · sponsors · geography          │
│ CT.gov v2   │   · whyStopped                                    │
└─────────────┘──────────────────────────────────────────────────┤
                                                                 ▼
                                                        ┌──────────────┐
                                                        │  normalize   │  one asset table
                                                        └──────┬───────┘
                                        ┌───────────────┬──────┴────────┐
                                        ▼               ▼               ▼
                                   mechanism        failures        crowding
                                   (what it does)   (why it died)   (how contested)
                                        └───────────────┴───────────────┘
                                                        ▼
                                                    narrative
                                             (template, or LLM prose)
                                                        ▼
                                                 HTML · MD · JSON
```

---

## Layer 1 — Sources

Each adapter returns model objects, never raw payloads, so the analysis layer
never knows which API a fact came from. Four things are worth noting.

**Location and family are fetched in a separate query that fails soft.** Open
Targets' 26.x schema break took the whole run down once already; a field rename
in `subcellularLocations` would otherwise do it again. Fetched apart, a failure
there costs the modality-fit section and nothing else, and downstream code
treats an empty result as *unknown* — never as *not on the surface*, which is
the one wrong answer that would matter.

**UniProt answers the one question the other three cannot.** Open Targets,
ChEMBL and ClinicalTrials.gov all describe what is being *done* to the target.
None of them says what the target *is*, beyond a one-line function string. On a
target the reader has never met — the normal case, not the edge case — nothing
else on the page means anything until that gap is closed. Swiss-Prot is the
right source for it: curated by people reading the primary literature rather
than text-mined, with the PubMed records behind each statement attached, under
CC BY 4.0, and needing no key. Four comment classes are read and they answer
four different questions — `FUNCTION` what it does, `SUBUNIT` what it does it
with (which decides whether a blocking antibody has anything to block),
`DOMAIN` the architecture a small molecule or degrader needs a handle on, and
`DISEASE` where human genetics has already implicated it. `gene:` is not an
exact-match field, so the entry whose *gene name* is the symbol is preferred
before any other hit: filing a paralogue's function under this target's name
is worse than having no brief.

**Europe PMC stores metadata only.** Titles, journals, years, identifiers and
citation counts. Abstracts stay out: they are under publisher terms, and a tool
that caches them for redistribution has a licensing problem it does not need.

**Open Targets is the identity anchor.** Everything keys on the Ensembl gene ID.
The `search` endpoint is fuzzy and will return paralogues for a short gene symbol,
so `resolve_target` prefers an exact `approvedSymbol` match before falling back.

**ChEMBL is queried directly even though Open Targets already surfaces ChEMBL
drugs.** Open Targets flattens away `action_type` — INHIBITOR vs ANTAGONIST vs
AGONIST — and for a receptor target that field carries the whole competitive
argument. `find_target_ids` restricts to `SINGLE PROTEIN` human targets: protein
family and complex entries would drag in every drug against every family member
and silently inflate the count.

**ClinicalTrials.gov is swept twice.** Once for the NCT ids Open Targets already
linked to drugs, and once as a free-text sweep over the target's aliases and every
known drug name. The second pass is where a third of the real landscape usually
lives — academic INDs, cell therapies, Chinese and Japanese sponsors, none of which
reliably reach ChEMBL. Only drug-like intervention types are kept
(`DRUG`, `BIOLOGICAL`, `GENETIC`, `COMBINATION_PRODUCT`), or placebo-controlled
surgical comparators walk into the asset table.

Every source is wrapped so that failure degrades the memo instead of aborting the
run, and the degradation is recorded in `Landscape.warnings` and printed at the top
of the memo. A memo missing its tractability section is far more useful than no
memo; a memo silently missing its tractability section is worse than either.

---

## Layer 2 — Reconciliation (`normalize.py`)

The sources disagree about what a drug is called, what phase it has reached and
who owns it. Resolution rules, in order of authority:

| Field | Rule | Why |
|---|---|---|
| Identity | ChEMBL ID where both have one; otherwise a normalised key built from every synonym, with dose and formulation noise stripped (`VAY736 300 mg SC` → `vay736`) | Without this, one asset appears three times and the density score triples |
| Phase | Maximum across sources | ChEMBL's `max_phase` lags. A Phase 3 trial is evidence ChEMBL has not caught up, not a contradiction |
| Modality | ChEMBL `molecule_type` over Open Targets `drugType`, then refined by INN stem and mechanism text | Databases disagree; the text is usually right |
| Sponsor | Industry lead sponsor of the asset's highest-phase trial | An investigator-initiated Phase 1 is not a competitor in the way a pharma Phase 1 is; academic-only programmes are kept but flagged |

Assets that appear in trials but in no drug database are constructed from the trial
records (`discover_assets_from_trials`). Skipping them is how an automated
landscape quietly misses the fastest-moving part of the field.

---

## Layer 3 — Judgement

### `readouts.py` — what a trial can prove, before it reports

Counting trials is the least informative thing you can do with them. Fourteen
Phase 2s sounds like a validated, crowded mechanism; if eleven are single-arm,
open-label studies with a receptor-occupancy endpoint, the mechanism has not
been tested at all and none of that money will settle it. **That is knowable in
advance**, because design and primary endpoint are registered years before the
result — which is what makes this section worth building rather than waiting for.

Two judgements, from registered fields only. The primary endpoint is classified
(hard outcome / accepted surrogate / validated scale / biomarker / PK / safety)
against a vocabulary held in the file, with a last-resort rule that matches on
*shape* — "a change in a named score" — so that ESSDAI, SNOT-22 and every other
instrument no vocabulary will ever hold is not reported as unclassified. Then
design decides what a positive result could support: randomisation gives a
comparison, blinding protects a subjective endpoint, enrollment decides whether
an effect is separable from noise.

Three failure modes are handled explicitly, because each would print a confident
falsehood:

* *Progression-free survival* contains the word "survival". Rule order puts it
  with the surrogates; getting it backwards would inflate the evidence on every
  oncology target in the index.
* A co-primary of OS **and** adverse events is an efficacy trial. Taking the
  first endpoint, or the commonest, calls it a safety study.
* **A trial with no registered design is not an uncontrolled trial.** Reporting
  "0 of 3 controlled" turns a gap in the registry into a finding about the
  target — the same class of error as reading a missing termination reason as
  "stopped for no reason". It is reported as a gap, in those words.

The headline catalyst is the soonest *interpretable* readout, not the soonest.
A Phase 1 safety readout six months out is nearer than a Phase 3 efficacy
readout in two years and tells you far less.

### `precedent.py` — has anyone made a medicine out of this target

The tier an early investor needs first: approved, reached Phase 3, **tested and
failed**, controlled trials in flight, early clinical, or preclinical. The
third of those is the one a database of assets in development cannot show,
because failed programmes leave the asset table — a company on a target where
three Phase 3s failed for efficacy is not an early opportunity, it is a claim
that everyone before was wrong.

Genetic evidence is reported alongside, including when it is absent. Genetically
supported targets have historically succeeded at roughly twice the base rate
(Nelson 2015; Minikel 2024), which is the strongest prior available before any
clinical data exists.

### `reference/modalities.py` — what the modality demands of the target

Hand-written, versioned, and labelled as such wherever it appears. A modality
label tells a reader what the molecule is; it does not tell them that an ADC
only works if the antigen *internalises*, so a beautifully tumour-specific
surface antigen that sits still is a dead ADC target. That requirement is
stable, public, well known inside the field, and in no free database.

Only the location constraint is checked automatically, because only it is hard.
**Unknown location returns "unknown", never a pass** — asserting that an
antibody can reach a protein nobody has placed is the one failure here that
would cost somebody money. The same rule propagates upward: with no location,
every location-independent modality reports "available", which is true and no
basis for telling a reader that small molecules are an untried opening, so that
claim is withheld rather than filled with a technicality.

### `analysis/brief.py` — the header, as separable facts

The header is a list: target class, function in one sentence, subcellular
location, domains, what is in development, and — labelled, and only alongside
the development row — the Mendelian disease germline variants in the gene
cause. It was a paragraph once, and the paragraph was wrong for the site: a
narrative in that position has already decided what the facts mean, before the
reader has seen them.

Two placements are load-bearing. The **detailed biology goes to the Mechanisms
tab**, not the header: someone deciding whether to keep reading should not have
to scroll past it, and someone who wants it knows where to look. And the
**germline disease is withheld entirely when the development picture is not
loaded**, because alone it becomes the header's only disease and a reader takes
it for the indication — PDCD1's annotation is an infantile autoimmune syndrome,
while PD-1 is drugged to treat cancer.

### `sources/uniprot.py` — the curated protein text

The paragraph at the top of a target page is 100–200 words and contains no
generated prose. Segments are added in descending order of what they tell a
reader meeting the protein for the first time — function, then binding
partners, then domain architecture, then disease genetics — and the paragraph
closes at the first segment that would carry it past the ceiling. The function
and subunit sentences are curated text verbatim; the two remaining sentences
are templated and state only what the annotation records.

Three parsing decisions are load-bearing. Curated text carries its citations
inline as `(PubMed:12345678)` and marks orthologue inference as
`(By similarity)`; both are lifted out, the identifiers re-attached as links
and the inference marker dropped, so the prose reads as prose. Only PubMed
evidence becomes a citation — an `ECO:0000250` inference pointing at another
UniProtKB record is not a paper and must not be offered to a reader as one.
And repeated domains collapse to one row: a receptor with three cysteine-rich
repeats is one architectural fact, and listing them separately makes a short
protein look far more complicated than it is.

**No model is involved.** The same target produces the same paragraph on every
machine, with or without a network, forever. A header that reads differently
each time it is generated is not an annotation, it is decoration — and this is
the block a reader is most likely to quote.

### `diagram.py` — the figure, generated

Hand-drawing a figure per target does not survive the requirement that 28,000
of them work. So it is generated from three facts the pipeline already holds:
where the protein sits, what family it belongs to, and which mechanism classes
are in the asset table. A textbook figure shows the biology; this one shows the
biology *and the competitive structure on top of it*, with arrow weight encoding
the furthest phase each approach has reached. On a crowded target the arrows
pile up; on an open one the canvas is visibly empty, which is the fastest way
this tool can communicate whitespace.

It draws no interaction it has not read from the data, and when the location is
unannotated it says so on the canvas rather than placing the protein somewhere
plausible.

**It lives in the Mechanisms view, not at the top of the page.** What it draws
is the competitive structure — one arrow per approach, weighted by the phase
that approach has reached — and that is a mechanism-view fact. Under the
header it read as a pathway diagram, which it is not and never was. A figure
that invites the wrong reading is worse than no figure, and the header now
carries the thing a reader actually needed there: a paragraph saying what the
protein is.

### `feasibility.py` — six questions, answered from the record

**The engine may be thick; the page must be thin.** Every other module computes
as much as the public record supports. This one throws nearly all of it away
and returns six answers, each a count or a date, each with a note on where it
came from and a pointer to the table beneath it.

**It generates no verdict, and that is the point.** An earlier version wrote a
headline sentence saying what the six added up to — "validated in humans and
not yet crowded", "contested evidence". It read as authority the tool has not
earned. Most of the 28,000 targets someone can look up here are new or thinly
covered, and a template with a slot for a conclusion fills the slot whether or
not the record supports one. The site's job is to put the record in front of a
reader who can weigh it; a generated sentence telling them what to conclude
takes that away and adds nothing they could check.

One rule keeps the lines honest: a line appears only when it has something to
say. "0 prior failures" reads as reassurance, and on a target nobody has ever
tried it is the opposite of informative, so the history line is simply absent.


### `mechanism.py` — what the asset does

Two signals, rules first:

1. **WHO INN stems.** `-mab` antibody, `-cept` Fc-fusion trap, `-leucel` autologous
   cell therapy, `-siran` siRNA, `-vedotin` ADC. Free, deterministic, and it works
   on assets with no database record — exactly the population the trial sweep turns
   up.
2. **Mechanism text**, keyed against a vocabulary.

Explicit text beats the stem: *"bispecific BAFF-R/BCMA CAR T"* must not be filed as
a plain antibody because a name ends in `-mab`. The output label deliberately fuses
modality and pharmacology — *Depleting antibody (ADCC/CDC)* and *Blocking antibody*
are different competitive propositions even though both are `-mab` / `ANTAGONIST`
in every database.

### `failures.py` — why the programme stopped

The taxonomy exists to answer one question: *did it die of the science or of the
business?* Science-class failures are evidence about the target. Business-class
failures often mark a licensing opportunity instead.

Two mechanisms make this trustworthy:

**Negation masking.** Sponsors routinely write *"no new safety signals were
identified"* in a notice that has nothing to do with safety. Naive keyword matching
reads that as a safety failure and inverts the conclusion. Negated clauses are
blanked before the rules run.

**Multi-match reporting.** A notice that reads as both business and efficacy is
reported as both, with the matched substring quoted. `classify_reason` returns
`(primary, evidence, also_matched)` — the third element is what makes the call
auditable rather than authoritative.

**Overrides.** *"Did not meet the target criteria for progression despite
demonstrating efficacy"* is a go/no-go bar, not an efficacy failure, and the
distinction decides whether the asset is a warning or an in-licensing target.

### `licensing.py` — what is available, and who holds it

Every other target database answers "what exists". A BD team has assumed that
already and is asking which of these it could actually get. That question has
no free database behind it, but a useful part of it is derivable from data the
asset table already holds:

| Signal | Weight | Why it is evidence |
|---|---|---|
| Shelved with clinical data | +3 | Reached Phase 2+, every linked trial stopped. Human data with no active programme is the classic in-licensing candidate |
| Small or private sponsor | +2 | Not on the visible large-pharma list. Small holders partner far more often, and are reachable directly |
| Academic origin | +2 | Usually seeking a commercial partner; the contact is a tech-transfer office |
| Territory gap | +1 | Trials in some major markets and not others. Regional rights are often unplaced where a sponsor has not run trials |
| Held and active at a large sponsor | −2 | Not available except regionally, or on a later deprioritisation |

Sponsor scale is matched against a curated name list in the module rather than
hidden behind an API, and the academic list carries centres whose names contain
none of the usual words — City of Hope, Dana-Farber — because misreading a
hospital-sponsored CAR-T as a private company inverts the signal.

Two rules keep this honest. Every signal carries the evidence that fired it, so
a reader can overrule the call rather than inherit it. And the territory signal
only fires when the programme has run trials *somewhere* — a gap in every
market is the absence of data, not evidence about rights.

Deal comparables have no free source at all, so they are a hand-maintained CSV
per target with a source URL required on every row, matched to the asset table
by name and synonym and summarised as median upfront by stage. They are re-read
on every page load, so editing the CSV shows up without a rebuild, and an empty
file renders as empty rather than implying there were no deals.

**Only licences are averaged.** An acquisition price buys a company — its
platform, its cash, its other programmes — and a median that mixes one in
reports a typical Phase 3 upfront that no Phase 3 asset ever cost. On the
BAFF/APRIL axis the difference is a Phase 3 median of $125m against $1.66bn,
which is not a rounding error but a different claim about the field.
Acquisitions stay in the table, labelled and counted, because they answer a
different question: what a buyer paid for the whole programme.

### `crowding.py` — how contested, and where the gaps are

**Phase weighting.** `PHASE_WEIGHTS` in `config.py`:

| Phase | Weight |
|---|---|
| Approved | 5.0 |
| Phase 3 | 3.0 |
| Phase 2 | 1.5 |
| Phase 1 | 0.75 |
| Preclinical / unknown | 0.25 |

One Phase 3 is priced at exactly four Phase 1s — a deliberate equivalence, asserted
in the tests so that retuning the weights announces itself.

**Calibration of the bands.** `CROWDING_BANDS` (Open ≥ 0, Emerging ≥ 2, Contested
≥ 8, Crowded ≥ 20, Saturated ≥ 45) were set by hand against a spread of reference
targets — a saturated one (PD-1: dozens of approved and late-stage assets), a
crowded one, a contested one, an emerging one (BAFF-R: one Phase 3 plus a
cell-therapy tail, scoring 4.8), and targets with nothing at all. **They are a
convention, not a measurement**, and the memo footer prints them so a reader can
disagree and recompute. Anyone extending this should re-derive them over a larger
reference set — that is the honest version of this section, and it is not done.

Two of the anchors have since been checked against real builds rather than
against an estimate: PDCD1 scores 331.8 over 185 active programmes and lands in
**Saturated**, and TNFRSF13C scores 4.8 over 4 and lands in **Emerging**, which
is where each was expected to fall. Two anchors agreeing is not a calibration
— it is two points on a line drawn by hand — but it does rule out the failure
that would matter most, a scale on which everything piles into one band.

**Per-indication phase.** The indication × mechanism matrix resolves each cell from
the trials themselves, not from the asset's overall maximum. Using the maximum is
the standard way this table lies: an asset in Phase 3 for one disease and a
terminated Phase 2 for another shows Phase 3 in both rows, and a reader concludes
the second indication is taken. In the BAFF-R memo this is the difference between
reading hidradenitis suppurativa as Phase 3 (wrong) and Phase 2, terminated
(right).

**Whitespace.** Requires association score ≥ 0.35 **and** genetic evidence ≥ 0.05
**and** nothing past preclinical. The genetic component is required because it is
the association datatype that replicates best. Disease names are compared by
stemmed token overlap (Jaccard ≥ 0.5 over 8-character token prefixes, clinical
filler removed) — `Sjogren syndrome` matches `Sjogren's Disease`, `immune
thrombocytopenic purpura` matches `Immune Thrombocytopenia`, while `systemic lupus
erythematosus` correctly does **not** match `Lupus Nephritis` and `multiple
sclerosis` does not match `Multiple Myeloma`. Substring matching fails all four.

---

## Layer 4 — The model, and its limits

The LLM layer exists and is deliberately small.

- **Rules run first, always.** The model receives only rows the rules could not
  place — typically the cell therapies and the non-Western programmes.
- **Constrained to the same vocabulary.** A modality outside `MODALITIES` is
  rejected and downgraded, not passed through; an unconstrained label would break
  clustering silently.
- **Every model assignment is tagged** `[model]` in the output, so the rows a model
  touched can be audited specifically.
- **Low-confidence answers are discarded**, and the model is instructed that
  refusing to classify is correct behaviour.
- **Narrative prose only.** The narrative prompt forbids introducing any asset,
  number, phase or sponsor not present in the structured input.
- **The tool runs fully without it.** `_template_narrative` is deterministic and
  always available.

That last point is the load-bearing one. A landscape analysis whose numbers change
when a model is swapped is not an analysis.

---

## Layer 5 — Delivery

**`targets.py` — the searchable index.** Autocompleting against a remote API is
a round trip per keystroke to a service the analysis also depends on, and it
matches approved symbols only. Nobody types `TNFRSF13C`. So search runs against
a local index of symbols, aliases and names, ranked exact-symbol → exact-alias →
prefix → substring → word-boundary name match. It ships seeded with ~200
hand-checked drug targets and expands to the full HGNC set; the seed's aliases
survive the merge because HGNC is authoritative on symbols and patchy on
vernacular. Alias resolution runs on lookup too, so `/target/HER2` serves ERBB2
and the interface says that it did.

**`store.py` — two tiers.** Curated landscapes are precomputed and committed:
they open instantly and cannot fail, because serving them touches no external
API. Everything else is built live and cached. Every record carries its tier and
age, because a landscape from four months ago is a different claim from one
built this morning.

**`web/app.py` — a build is a job, not a request.** A live build waits on three
APIs in sequence for 20–40 seconds. Served synchronously that is a spinner and
an eventual proxy timeout; as a job with stage reporting it is the same wait
with the interface able to say *Sweeping ClinicalTrials.gov*. Concurrent
requests for the same target share one job rather than fanning out duplicate
sweeps against the sources.

**The target page reads top to bottom: what it is, what the record holds,
then the tables.** Key facts are the header. The six questions sit under them,
each linking down into the view that answers it. The eight views are the weight
of the page. Nothing on the page tells the reader what it all means.

**The figure was removed.** It was generated per target and it drew the
competitive structure rather than the biology, which meant readers took it for
a pathway diagram and got nothing from it either way. A figure that invites the
wrong reading is worse than no figure. `diagram.py` still builds it and its
tests still pass; nothing surfaces it.

**The language layer was removed.** The interface used to run through
`web/static/i18n.js`, an English-keyed dictionary with a Chinese translation
of everything the site said in its own voice. Drug names, sponsors,
indications, gene symbols and the curated UniProt sentences were never
translated — a reader checking an indication against a filing needs the string
the registry holds. That left a page half in one language and half in another,
maintained twice, for an audience that reads the untranslated half anyway. The
dictionary, the toggle and the two-language strings are gone; the site is
English.

**The landing page is a worked example, not a description.** A first-time
visitor cannot picture a target page from prose about one, and an essay on
methodology is the thing they skip. So the page carries two sentences of what
the site is, the search box, and then six tiles filled with the real numbers
from a real target — PD-1, chosen by `analysis/showcase.py` because a target
with two assets shows a reader six empty tiles. Every figure on a tile is
derived from the same stored landscape the target page renders, so the tiles
cannot drift away from what the reader finds when they click. Underneath sits
the index: twelve area chips with counts, and twenty-four target cards. The
earlier "how to read this" page was deleted — it was a wall of text standing
between the reader and the product, and it was explaining a page that should
not need explaining.

**`targets.py` disambiguates nicknames rather than taking the shortest
symbol.** `PD1` is an alias of PDCD1, of SNCA (the Parkinson disease 1 locus)
and of SPATA2, and shortest-symbol-wins served alpha-synuclein for the first
thing anyone types into this tool. Three signals now come first: the spelling
the reader typed, how many spellings of the nickname that gene carries, and
whether the gene is one of the hand-checked drug targets. The dropdown still
lists every gene that answers to the query, in that order, so the reader can
see and pick the one the ranking put second. HGNC records that are not single
approved symbols — readthrough fusions, cluster placeholders — are dropped at
load: they resolve to nothing downstream, so offering them is offering a
build that cannot start.

**`web/static` — one filter state, every view.** Filtering to antibodies narrows
the mechanism grid, the trial list and the termination notices together. That is
what makes it a database rather than a report with tabs. The Investor/Scientist
switch reorders what leads and which view opens first; it hides nothing, because
a scientist needs the competitive picture and an investor needs the mechanism.

**`scripts/make_static_demo.py`** exports the whole site as one self-contained
HTML file with the payloads and the index inlined — no server, no cold start,
for the demo that has to work on bad wifi.

---

## Testing

198 tests across four files, each corresponding to a failure mode found while
building the tool rather than to a line of code, and every one of them offline:
`test_analysis.py` (the judgement layer and the index), `test_sources.py`
(parser contracts against realistic payloads, including the malformed shapes
these APIs actually emit), `test_investor.py` (precedent, readouts, modality
fit and the six lines), `test_web.py` (routing, jobs, path traversal, a dead
upstream during autocomplete).

The ones that matter most:

- negated safety language is not read as a safety termination;
- a bar miss despite demonstrated efficacy classifies as business, with the
  efficacy reading preserved;
- lupus nephritis and SLE are not treated as the same disease;
- indication phases come from trials, not from the asset maximum;
- an active large-pharma Phase 3 is never reported as available, and a shelved
  Phase 2 always is;
- the territory signal does not fire on an asset with no trials at all;
- every index symbol looks like an approved gene symbol — a protein nickname
  stored as a symbol (Nav1.7, SGLT2) resolves to nothing downstream;
- `PD-1` resolves to PDCD1 and not to alpha-synuclein;
- the curated brief never carries a paralogue's function, an inline
  `(PubMed:…)` marker, or a citation that is not a paper.

`fixtures/TNFRSF13C.json` is the end-to-end input. `load_fixture(recompute=True)`
re-runs the whole analysis layer over stored raw records, so changing a weight or
a rule changes the memo with no network involved — the fixture is a regression
test, not just a demo.

---

## What would come next

In rough order of how much each would improve the output:

1. **More registries.** CTIS (EU), ChiCTR, jRCT. The single biggest coverage gap,
   and the one that most distorts the competitive read on active targets.
2. **Real EFO mapping** for disease names, replacing token overlap.
3. **Patent and publication signal** for preclinical programmes, which are
   currently invisible.
4. **Deal comparables from a real source** rather than a hand-maintained CSV.
5. **Band recalibration** over a proper reference set of targets, with the
   reference set checked into the repository. `calibration/targets.txt` holds
   the reference set; the run has not been done, and the bands in `config.py`
   are still the hand-set convention described above.
6. **Pathway neighbours.** The tool is strictly on-target: a NIK inhibitor does
   not appear on a BAFF-R page even though both sit on the non-canonical NF-κB
   pathway. "What else hits this pathway" is a real BD question and needs a
   pathway source (Reactome) the tool does not yet carry.
7. **A patient-facing view** over the same trial layer: which centres are running
   which trials, where, and against what eligibility criteria. The data pipeline is
   already there; only the presentation differs.
