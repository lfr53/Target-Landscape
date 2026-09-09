# Target Landscape

**A whole-picture view of a drug target, from biology and clinical
development to competition and transactions.**

[**Open the site**](https://lfr53.github.io/Target-Landscape/) · built on Open
Targets, ChEMBL, ClinicalTrials.gov, UniProt and Europe PMC · **no API key, no
model, nothing to sign up for**.

Target Landscape is built for people making early decisions around a drug
target: scientists asking whether a target is worth developing, or where an
opportunity may still exist; early-stage biotech investors evaluating a new
company or programme; and BD or licensing teams screening targets and assets
before deeper diligence.

The problem is rarely a lack of information. It is knowing what information
matters for the decision you are trying to make. Target data is spread across
genetics, biology, clinical trials, drug programmes, failures, competitive
pipelines and publications, and even where it is all publicly available, an
early reviewer may not know which questions need answering, which evidence is
decision-relevant, or where to find it among hundreds of records.

Target Landscape starts from the questions behind the decision, not from the
databases. For each target, it asks a structured set of six questions, three
on whether the target works and three on what can be had here:

| | | |
|---|---|---|
| **Target characteristics** | What the protein is, where it sits, and how far anyone has got with it | science |
| **Trial design and readouts** | How much of the running activity is a controlled efficacy trial, and how much only looks like one | science |
| **Termination reasons** | Why programmes stopped, and what that does and does not say about the target | science |
| **Competitive landscape** | Who is developing what, grouped by mechanism, phase-weighted rather than counted | business |
| **Licensing and deals** | What has been licensed, on whose announcement, and which programmes have never been on a deal | business |
| **Untried** | A modality that could reach this protein and has not been tried, or a disease with evidence and nothing in the clinic | business |

Each question is paired with the specific evidence needed to examine it,
rather than an undifferentiated pile of records — and wherever possible, the
underlying record, its source and its date stay visible, so the evidence can
be traced back to where it came from.

Target Landscape is designed to support judgement, not replace it. It does
not tell users whether to develop, invest in or license a target. Instead, it
helps them understand what needs to be considered, brings the relevant
evidence together, and makes that evidence easier to inspect and challenge.

![The six answers, on KRAS](docs/images/read.png)

```bash
pip install -r requirements-web.txt
uvicorn web.app:app --reload          # → http://127.0.0.1:8000
```

**On Windows**, double-click `1-SETUP.bat` then `2-START-WEBSITE.bat` — no
terminal required. See [WINDOWS.md](WINDOWS.md).

The same analysis runs as a command line tool and as a document:

```bash
python -m landscape KRAS               # → out/KRAS_landscape.html
```

---

## The interface

Each target page opens with the six answers above — one sentence of judgement
per question, at most three lines of evidence, the table behind a disclosure.
No summary strip of raw counts: a number with no verdict attached hands the
reader the work this page exists to do. Raw data is linked out to Open
Targets, ClinicalTrials.gov and Europe PMC rather than copied — they do
tables better than this page can.

The home page shows what a target page holds instead of describing it: six
tiles carrying the real figures from a real target, derived from the same
stored landscape the target page renders.

![Six tiles, on a real target](docs/images/home.png)

Then the views — one filter state drives all of them, so narrowing to
antibodies narrows the mechanism list, the trial table and the termination
notices together:

| View | Answers |
|---|---|
| **Assets** | Every programme, sortable, with a panel per asset showing its trials and the source of each field |
| **Mechanisms** | Grouped by what each asset *does* to the target — plus where the target sits on its pathway, its drugged neighbours, and which modalities could reach it and have not been tried |
| **Trials** | What reads out next and what each result could actually prove, from the registered design |
| **Terminations** | The sponsor's own stated reason, classified and quoted |
| **Licensing** | Deals already done, each with its source — then every programme on the target and whether one is on file for it |
| **Untried** | Well-evidenced diseases with nothing in the clinic, and modalities nobody has taken |
| **Reading** | The most-cited reviews and recent mechanism work, from Europe PMC |

![What each running trial could prove](docs/images/trials.png)

![Mechanism classes and the pathway](docs/images/mechanisms.png)

Terminations — the sponsor's own words, classified, with the matched phrase
shown so you can overrule the call:

![Termination analysis](docs/images/terminations.png)

Licensing — what has been transacted and what has not, no score on either:

![Deals on file, and where each programme stands](docs/images/licensing.png)

**Investor / Scientist** switches which figures lead and which view opens
first. Nothing is hidden either way — both stay one click apart.

**Search finds targets by the names people use.** Nobody types `TNFRSF13C` —
they type BAFF-R. Nobody types `ERBB2` — they type HER2. Instant, offline,
alias-aware.

```bash
python scripts/seed_target_index.py     # ~200 hand-checked drug targets, ships in the repo
python scripts/build_target_index.py    # expands it to every approved human gene (HGNC)
```

**Two tiers, and the page says which one you're reading.** Curated targets
are precomputed and committed: instant, and cannot fail, because serving one
touches no external API. Anything else is built live from the same public
sources — 20 to 40 seconds, staged rather than a spinner, then cached.

```bash
python scripts/precompute.py --set calibration/targets.txt   # seed the curated tier
python scripts/recompute_curated.py                          # re-run current rules, no network
```

### Deploying

The published site is static, because the site already is: every curated
target is precomputed and committed, and a server is only needed to build
something outside that set.

```bash
python scripts/make_static_demo.py --out-dir site      # a shell plus one file per target — what the published site runs
python scripts/make_static_demo.py --out out/demo.html # one self-contained file, for sending to someone
```

`.github/workflows/pages.yml` rebuilds the first of those from a clean
checkout on every push and publishes it to GitHub Pages, so what is online is
what the repository can rebuild. Live lookup is the one thing the published
copy cannot do, and it says so rather than offering a search it can't honour.

---

## Why this is not a search tool

Listing the drugs against a target is solved — Open Targets does it free,
Cortellis and Evaluate do it commercially. Listing is not the work. The work
is the judgements underneath a landscape, and each one exists because the
naive version of it produces a confidently wrong answer.

**1. A drug counts only if its own record names this target — not because
the target's name appears somewhere nearby.**
Search a registry for a protein's *full name* and it fails silently: MAP3K14's
full name returned 228 assets and 13 "approved drugs," among them
hydrochlorothiazide, a blood-pressure pill with no relation to the kinase —
the words had simply co-occurred in the same record. A target list built this
way looks complete and is mostly noise. So matching runs on identifiers, never
on protein names; a trial counts only when its own record names both the drug
and the target; and population context ("HER2-positive" in a *condition*
field) is scored separately from the *intervention* field, so a nearby phrase
can't poison an unrelated one. The same layer folds salt forms of the same
drug, catches ChEMBL synonym collisions that would otherwise merge two
distinct molecules, and drops rows that were never drugs — diagnostic assays,
biomarker cohorts, category labels like "PD-1/PD-L1 inhibitor" (a protocol
letting the investigator pick any drug in the class, not a molecule).

**2. Competition is measured by what a drug does to the target, not how many
drugs exist.**
Five antibodies against a receptor are one competitive situation if all five
block the same ligand, and a different one entirely if two of them instead
kill the cell that carries the receptor — same target, same modality,
opposite strategy. Counting "five antibodies" hides that. The classifier
reads WHO INN stems (`-mab`, `-cept`, `-leucel`, `-siran`) alongside ChEMBL's
`action_type` and free-text mechanism descriptions, which is what lets it
place assets with no clean database record at all — usually where the cell
therapies and non-Western programmes sit. Where a record states what the drug
does but not what kind of molecule it is, the label says exactly that
(*inhibition, modality unresolved*) instead of discarding the half that is
known.

**3. Why a trial stopped is not the same fact as whether it stopped.**
A funding round falls through, a merger reshuffles a portfolio, a supply line
fails, a site closes for COVID — none of that is evidence the biology
doesn't work, and a raw termination count treats it as if it were, which
punishes a target whose sponsor went bankrupt exactly as hard as one that
failed in the clinic. So `whyStopped` — the sponsor's own one-line account,
almost never used because it sits as unstructured text behind a paginated
API — is read and classified into five causes (efficacy/safety/PK, business,
operational, manufacturing, unstated), with the verbatim notice kept
alongside so the reader can check the call.

BAFF-R is the case that justified building this at all. Novartis stopped a
Phase 2b saying the study *"did not meet the target criteria for progression
despite demonstrating efficacy versus placebo… No new safety signals were
identified."* A keyword scan reads "safety" and files it as a toxicity
failure — the opposite of what happened. This tool masks negated clauses,
classifies the stop as a portfolio decision, and shows that it *also* matched
efficacy, so a reader can overrule the call instead of inheriting it.

**4. Crowding is weighted by how far a competitor has actually got, and the
weights are on the page.**
One Phase 3 competitor is worth more than four Phase 1s to how contested a
target is — a flat asset count says they're worth the same. Programmes whose
every linked trial has stopped are reported as dormant rather than folded
into the live count, so a target isn't read as crowded because of five
abandoned attempts nobody is still running. The weights and the band
thresholds that turn a score into "Contested" or "Open" are printed on the
page, because a number nobody can recompute from what's shown isn't an
analysis, it's an opinion with decimals.

**5. Licensing is reported as two lists, not compressed into a score.**
The reason isn't caution — it's that "how available is this target" is
actually two different questions with two different answers, and a single
score papers over which one it's giving. An investor sizing a competitive
field wants deal comparables: what has this kind of asset gone for, at what
stage. A BD analyst wants a target list: which specific programmes have never
been picked up, because those are the ones you can actually call someone
about. Averaging those into one number serves neither question and answers a
third one nobody asked. An earlier version tried anyway — a hand-weighted
"availability score" and a median deal size — and both are gone: the weights
had never been checked against a single real negotiation, and a median over
a handful of hand-typed rows is a sample size a reader should reject before
trusting the number. What replaced them: **deals already done**, each row
entered from the parties' own press release or filing, with that
announcement linked, upfront and total value kept as stated (no average
computed over them); and **every programme on the target** — holder, stage
reached, most recent or next readout, and whether it appears in the deals
list. A programme absent from that list is the one worth a call, and the
page says so instead of scoring it. The deal rows themselves are hand-entered
because no redistributable database of deal terms exists at any price —
subscription platforms cover this, but their licences forbid republishing
it — so a blank deals section here means nobody has typed one in yet, not
that the target has never been licensed.

**6. "Untried" requires positive evidence, not the absence of a listing.**
A disease qualifies only when its Open Targets association clears a
threshold *and* carries independent genetic support *and* has nothing past
preclinical — any one of the three missing, and it's dropped rather than
counted as whitespace. Matching disease names by substring fails constantly
("Sjogren syndrome" vs "Sjogren's Disease" share no substring), so names are
compared by stemmed token overlap instead, and even then the section is
labelled a screen to check by hand, not a discovery — the goal is narrowing
what a person looks at next, not replacing the look.

**No model runs any of this.** Every figure above is a rule over a public
record — reproducible offline, and traceable line by line to the record that
produced it. The one place a model would genuinely help is reading free text
at scale (classifying more `whyStopped` notices, say), and the right shape
for that is kept offline too: the model drafts candidates, a person confirms
them, and the result is committed as a sourced CSV like everything else in
the hand-maintained layers. The pipeline that actually runs never depends on
one.

---

## Quickstart

Python 3.9+. The pipeline itself needs nothing beyond the standard library.

```bash
git clone https://github.com/lfr53/Target-Landscape.git
cd Target-Landscape

python -m landscape doctor             # check the APIs before trusting a run
python -m landscape KRAS               # live run against the public APIs
python -m landscape KRAS ERBB2 PDCD1 --out out/   # several targets, plus an index comparing them
python -m landscape --fixture fixtures/TNFRSF13C.json   # offline demo, no network
python -m landscape --calibrate --out out/calibration   # reference set, one density scale

python -m landscape KRAS \
  --out out/ \
  --format html,md,json \
  --deals data/deals/KRAS.csv \
  --save-fixture fixtures/KRAS.json

python -m unittest discover -s . -p "test_*.py"
```

### `doctor`

The three public APIs rename fields between releases with no warning. The
first symptom is not a crash — it's a memo that renders perfectly and says
nothing. `doctor` probes each source with the pipeline's own queries and
names the field that moved:

```
Open Targets
  [  ok  ] reachable
  [  ok  ] resolves a gene symbol
  [ FAIL ] target core fields
              empty fields: tractability
              → update _TARGET_QUERY in sources/opentargets.py
```

Responses are cached under `~/.cache/target-landscape`, so re-running a
target is instant and doesn't re-hit the APIs.

### As a library

```python
from landscape import build, to_html

ls = build("KRAS")
print(ls.crowding["verdict"], ls.crowding["weighted_score"])
for a in ls.assets[:5]:
    print(a.name, a.phase_label, a.mechanism_class, a.sponsor)
open("memo.html", "w").write(to_html(ls))
```

---

## Data sources

| Source | Carries | Licence |
|---|---|---|
| [Open Targets Platform](https://platform.opentargets.org/) | target identity, tractability, known drugs, disease associations with genetic evidence | CC0 |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | `action_type`, molecule type, max phase, withdrawal flags | CC BY-SA 3.0 |
| [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api) | trials, phases, sponsors, conditions, geography, `whyStopped` | US Government public domain |
| [UniProt](https://www.uniprot.org/) | curated function, subcellular location, domains | CC BY 4.0 |
| [Europe PMC](https://europepmc.org/) | reviews and recent mechanism papers | per-record |

Three layers are maintained by hand, each row requiring a source URL:
`data/deals/*.csv` (deal terms, from the parties' own announcements),
`data/assets/*.csv` (programmes the registries name only by a code), and
`data/pathways.csv` (where a target sits, cited to UniProt). Subscription
databases aren't used — their licences forbid redistributing what they
contain.

---

## Known limits

Stated here and on every page the tool produces:

- **The published site carries the curated set.** Anything else opens onto a
  page saying it isn't built. Running the project locally builds any human
  gene from the same public sources.
- **Registry coverage.** Only ClinicalTrials.gov is swept — China- and
  Japan-only registrations are under-represented.
- **Preclinical and undisclosed programmes are invisible.**
- **The deal layer is small and hand-entered** — sourced rows, not a market
  sample, which is why nothing is averaged over it.
- **A registry entry with only a code name can't be classified.** Those rows
  say so instead of being guessed at, and are resolved by hand into
  `data/assets/`.
- **`whyStopped` is self-reported and often absent** — the page prints the
  reporting rate.
- **Disease-name matching is stemmed token overlap, not ontology mapping.**
- **The density bands are a convention**, printed on the page and documented
  in [ARCHITECTURE.md](ARCHITECTURE.md) — not calibrated against outcomes.

## Repository

```
landscape/
  models.py            data model; every fact carries provenance
  config.py            endpoints and every constant that feeds a judgement
  http.py              cached, retrying stdlib HTTP client
  sources/             Open Targets · ChEMBL · ClinicalTrials.gov · UniProt · Europe PMC
  relevance.py         does this record actually name this target, and this drug
  normalize.py         reconciliation — identity, phase, modality, sponsor
  consistency.py       invariants: a headline figure must equal its own table
  analysis/
    mechanism.py       INN stems + mechanism vocabulary → mechanism classes
    failures.py        whyStopped → five causes
    crowding.py        phase-weighted density, indications, untried diseases
    licensing.py       deals on file, and where each programme stands
    feasibility.py     the six questions
    showcase.py        the six tiles, from the same stored landscape
  render.py            HTML + Markdown memo, and the multi-target index
  doctor.py            API health and schema-drift check
  store.py             curated tier + live-build cache + the hand-maintained layers
  targets.py           the searchable index: symbols, aliases, ranked lookup
  pipeline.py          orchestration; sources degrade, runs do not abort
web/
  app.py               FastAPI: search, lookup, build jobs, exports
  static/              the interface — no framework, no build step
data/curated/          precomputed targets, committed
data/deals/            deal terms, hand-entered, one CSV per target
data/assets/           programmes the registries name only by a code
data/pathways.csv      where each target sits, cited to UniProt
data/target_index.json the searchable target index
scripts/               precompute, recompute, static export
fixtures/              offline demo + regression input
calibration/           reference target set for deriving the density bands
tests/                 262 tests — parser contracts against realistic payloads,
                       the judgement layer, and the web layer; all offline
```

The engine (`landscape/`) has no web dependencies and doesn't know the site
exists — only `web/` needs FastAPI. That's what lets one analysis serve a web
request, a command line run and a CI job without three versions of it.

Every test runs without network, against payloads in `tests/payloads.py`
shaped like what these APIs actually emit, malformed records included.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design decisions and how the
constants were calibrated.

## Licence

MIT for the code. The data carries its own licences — see the table above.
