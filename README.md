# target-landscape

**Look up a drug target. Get six answers on whether it is worth the meeting.**

[**Open the site**](https://lfr53.github.io/Target-Landscape/) · built on Open
Targets, ChEMBL, ClinicalTrials.gov, UniProt and Europe PMC · **no API key, no
model, nothing to sign up for**.

Most databases answer either the science of a target or its commerce. A person
deciding anything has to hold both, and today that means two subscriptions and
an afternoon of moving between them. This puts them on one page, and links every
line back to the record it came from.

Six questions, in the order they have to be settled. Three are about whether the
target works, three about what can be had here, and the interface colours them
by that and by nothing else:

| | | |
|---|---|---|
| **Target characteristics** | What the protein is, where it sits, and how far anyone has got with it | science |
| **Trial design and readouts** | How much of the running activity is a controlled efficacy trial, and how much only looks like one | science |
| **Termination reasons** | Why programmes stopped — separating what that says about the target from what it says about the sponsor | science |
| **Competitive landscape** | Who is developing what, grouped by mechanism, phase-weighted rather than counted | business |
| **Licensing and deals** | What has been licensed, on whose announcement, and which programmes have never been on a deal | business |
| **Untried** | A modality that could reach this protein and has not been tried, or a disease with evidence and nothing in the clinic | business |

![The six answers, on KRAS](docs/images/read.png)

```bash
pip install -r requirements-web.txt
uvicorn web.app:app --reload          # → http://127.0.0.1:8000
```

**On Windows**, double-click `1-SETUP.bat` then `2-START-WEBSITE.bat` — no
terminal required. See [WINDOWS.md](WINDOWS.md).

The same analysis is available as a command line tool and as a document:

```bash
python -m landscape KRAS               # → out/KRAS_landscape.html
```

---

## The interface

**Every target page opens with the six answers, not a row of counts.** There used
to be a strip of ten summary statistics here; it was removed on purpose. Ten
numbers with no judgement attached is exactly the failure mode this page exists
to avoid — it hands you rows and leaves the work to you, which is what every
other target database already does.

The rule the whole interface follows: **the engine may be thick, the page must be
thin.** Each analysis module computes as much as the public record supports; each
panel shows one sentence of conclusion and at most three lines of evidence, and
puts its table behind a disclosure. Raw data is linked out to Open Targets,
ClinicalTrials.gov and Europe PMC rather than reproduced — they do tables better
than this page can, and a second-hand copy of a database is not the point.

The home page shows what a target page holds rather than describing it: six tiles
carrying the real figures from a real target, every one of them derived from the
same stored landscape the target page renders. If the tile says 13 trials
stopped, the Terminations view lists 13 trials.

![Six tiles, on a real target](docs/images/home.png)

Then the views. This is an explorable database, not a report with tabs:

| View | Answers |
|---|---|
| **Assets** | Whether anyone has made a medicine out of this target, then every programme, sortable, with a panel per asset showing its trials and the source of each field |
| **Mechanisms** | Grouped by what each asset *does* to the target, not by what it is — plus where the target sits on its pathway, which drugged neighbours share that pathway, and which modalities could physically reach this protein and have not been tried |
| **Trials** | What reads out next and what each result could actually prove, from the registered design — a single-arm study with a pharmacodynamic endpoint cannot settle efficacy however positive it turns out |
| **Terminations** | The sponsor's own stated reason, classified into five causes and quoted |
| **Licensing** | Deals already done, with the announcement each came from — then every programme on the target and whether one is on file for it |
| **Untried** | Well-evidenced diseases with nothing in the clinic, and modalities nobody has taken |
| **Reading** | The most-cited reviews and recent mechanism work, from Europe PMC |

Trials — not what is running, but what each running study could settle. A
single-arm study with a pharmacodynamic endpoint cannot answer whether the drug
works, however positive it turns out, and the registered design says so before
the result does:

![What each running trial could prove](docs/images/trials.png)

Mechanisms — what each programme does to the target, and what the target does
in the cell:

![Mechanism classes and the pathway](docs/images/mechanisms.png)

Terminations — the sponsor's own words, classified, with the matched phrase shown
so you can overrule the call:

![Termination analysis](docs/images/terminations.png)

Licensing — what has been transacted and what has not, with no score attached to
either:

![Deals on file, and where each programme stands](docs/images/licensing.png)

**One filter state drives every view.** Narrow to antibodies and the mechanism
list, the trial table and the termination notices all narrow with it. That is
what makes it explorable rather than a fixed report.

**Investor / Scientist** switches which figures lead the summary and which view
opens first. It hides nothing — a scientist needs the competitive picture and an
investor needs the mechanism, and both stay one click apart.

**Search finds targets by the names people actually use.** Nobody types
`TNFRSF13C` — they type BAFF-R. Nobody types `ERBB2` — they type HER2. Search
runs against a local index of symbols, aliases and names: instant, offline, and
alias-aware, so HER2 opens the ERBB2 landscape and the interface shows you that
it did.

```bash
python scripts/seed_target_index.py     # ~200 hand-checked drug targets, ships in the repo
python scripts/build_target_index.py    # expands it to every approved human gene (HGNC)
```

The seed is what makes the box useful out of the box; the HGNC build makes it
complete. The seed's aliases survive the merge, because HGNC is authoritative on
symbols and patchy on vernacular — "PD-1" is in there, "BAFF-R" and "TL1A" are
not reliably.

**Two tiers, and the interface says which one you are reading.** Curated targets
are precomputed and committed to the repo: they open instantly and cannot fail,
because serving them touches no external API. Anything else is built live from
the public sources — 20 to 40 seconds, reported stage by stage rather than as a
spinner, then cached.

```bash
# Seed the curated tier (do this once)
python scripts/precompute.py --set calibration/targets.txt

# Re-run the current rules over everything already built. No network, about a
# second each -- curated files are stored fully computed, so a rule change does
# not reach them until this runs.
python scripts/recompute_curated.py
```

### Deploying

The published site is static, because the site already is: every curated target
is precomputed and committed, and the server exists only to build targets outside
that set.

```bash
# One directory to serve: the shell, plus one file per target, fetched when it
# is opened. This is what the published site runs.
python scripts/make_static_demo.py --out-dir site

# One self-contained file, for sending to someone. Opens from a file path, no
# server at all.
python scripts/make_static_demo.py --out out/demo.html
```

`.github/workflows/pages.yml` rebuilds the first of those from a clean checkout
on every push and publishes it to GitHub Pages, so what is online is what the
repository can rebuild. If the export breaks, the deploy fails rather than
quietly serving a stale page. Live lookup is the one thing the published copy
cannot do, and the page says so rather than offering a search it cannot honour.

---

## Why this is not a search tool

Listing the drugs against a target is a solved problem — Open Targets does it for
free, Cortellis and Evaluate do it commercially. Listing is not the work. The work
is the judgements a landscape has to make, and each one is a place where a naive
pipeline gets it confidently wrong:

**1. An asset counts only if the record names this target.**
The obvious implementation — search the registries for the protein's name — fails
silently and spectacularly. Searching MAP3K14 by its full name returned 228
assets and 13 "approved drugs", among them hydrochlorothiazide, a diuretic with
no connection to the kinase whatsoever: the words simply co-occurred in text
somewhere. So matching runs on identifiers, never on protein full names; a trial
counts only when its own record names the drug and the target; and population
context is scored per field rather than across the concatenated string, because
"HER2-positive" thirty characters away in a condition field was poisoning the
reading of an intervention field that said "HER2/4-1BB bispecific". The same
layer folds salt forms, catches ChEMBL synonym collisions that merge two distinct
drugs, and drops rows that are not molecules at all — diagnostic assays, biomarker
cohorts, and class labels such as "PD-1/PD-L1 inhibitor", which is a protocol
letting the investigator choose, not a drug.

**2. Assets are grouped by mechanism, not counted.**
Five antibodies against a receptor are one competitive situation if they all block
the ligand and a completely different one if two of them deplete the cell. The
classifier reads WHO INN stems (`-mab`, `-cept`, `-leucel`, `-siran`) alongside
ChEMBL `action_type` and mechanism text, so it places assets that have no database
record at all — which, on most targets, is where the cell therapies and the
non-Western programmes live. Where the record states the pharmacology but not the
molecule, the label says exactly that (*inhibition, modality unresolved*) rather
than discarding the half that is known.

**3. Terminations are split into science and business.**
A raw termination count is worse than useless: a large share of trials stop for
reasons that say nothing about the target — funding ran out, the programme was
deprioritised after a merger, a supply problem, COVID closed the sites. Counting
those as evidence against the biology walks a team away from a target that never
failed. So `whyStopped` — the sponsor's own one-line account, the highest-value
free field in competitive intelligence and almost never used because it is
unstructured text behind a paginated API — is classified into five causes
(efficacy/safety/PK, business, operational, manufacturing and supply, unstated),
with the verbatim notice quoted alongside.

BAFF-R is the case in point. Novartis stopped its Phase 2b in hidradenitis
suppurativa saying the study *"did not meet the target criteria for progression
despite demonstrating efficacy versus placebo… No new safety signals were
identified."* Keyword matching reads "safety" and files it as a toxicity failure —
inverting the conclusion. This tool masks negated clauses, classifies it as a
portfolio decision, and reports that it *also* matched efficacy, so the reader can
disagree with the call rather than inherit it.

**4. Density is phase-weighted, and shows its weights.**
One Phase 3 competitor is priced at four Phase 1s. Dormant programmes — every
linked trial stopped, nothing running — are reported separately rather than
inflating the count. The weights and the band thresholds are printed on the page,
because a crowding score nobody can recompute is not an analysis.

**5. Licensing is reported, not scored.**
Every other target database answers "what exists". A BD or search-and-evaluation
team has assumed that already and is asking *which of these could I actually get,
and who do I call*. This view answers it in two lists and no score: the deals
already done, each carrying the announcement it came from; and every programme on
the target — who holds it, how far it went, what it last read out, and whether a
deal is on file for it. The programmes with no deal are the negotiable ones.

There used to be an availability score here, and a median deal value. Both were
removed. The score was a set of hand-picked weights nobody had ever checked
against an outcome, and the median was computed over a handful of hand-entered
rows — a statistic a reader should reject on sight. What is left is what can be
sourced. Deal rows are entered by hand from the parties' own announcements,
because no free database of deal terms can be redistributed; a blank section
means nobody has entered one, not that nothing has been licensed.

**6. Untried requires evidence, not just absence.**
A disease qualifies only when the Open Targets association clears a threshold
*and* carries genetic support *and* has nothing past preclinical. Matching disease
terms against sponsor free text is where this silently breaks — "Sjogren syndrome"
versus "Sjogren's Disease" fails a substring test — so names are compared by
stemmed token overlap, and the section is labelled a screen to check by hand
rather than a finding.

**No model, anywhere.** The analysis is rules over public records, so it is
reproducible offline and every line can be traced to the record that produced it.
An analysis whose numbers change when a model is swapped is not an analysis. The
place a model would genuinely help is classifying free text, and the right shape
for that is offline: let it draft candidate rows, have a person confirm them, and
commit the result as a CSV with a source on every line — so the pipeline itself
still runs on rules.

---

## Quickstart

Python 3.9+. The pipeline itself needs nothing beyond the standard library.

```bash
git clone https://github.com/lfr53/Target-Landscape.git
cd Target-Landscape

# Check the APIs before trusting a run
python -m landscape doctor

# Live run against the public APIs
python -m landscape KRAS

# Several targets at once, plus an index comparing them
python -m landscape KRAS ERBB2 PDCD1 --out out/

# Offline demo — no network, uses the checked-in fixture
python -m landscape --fixture fixtures/TNFRSF13C.json

# Run the reference target set and rank them on one density scale
python -m landscape --calibrate --out out/calibration

# Everything
python -m landscape KRAS \
  --out out/ \
  --format html,md,json \
  --deals data/deals/KRAS.csv \
  --save-fixture fixtures/KRAS.json

python -m unittest discover -s . -p "test_*.py"
```

### `doctor`

The three public APIs rename fields between releases and nothing warns you. The
first symptom of drift is not a crash — it is a memo that renders perfectly and
says nothing: empty asset table, no warnings, plausible prose. That quiet failure
is much worse than an exception, so `doctor` probes each source with the exact
queries the pipeline uses and names the field that moved and the function to fix:

```
Open Targets
  [  ok  ] reachable
  [  ok  ] resolves a gene symbol
  [ FAIL ] target core fields
              empty fields: tractability
              → update _TARGET_QUERY in sources/opentargets.py
```

Responses are cached under `~/.cache/target-landscape`, so re-running a target is
instant and does not re-hit the APIs.

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

Three layers are maintained by hand, each requiring a source URL on every row:
`data/deals/*.csv` (deal terms, from the parties' own announcements),
`data/assets/*.csv` (programmes the registries describe only by a code name), and
`data/pathways.csv` (where a target sits, cited to its UniProt entry).
Subscription databases are not used: their licences forbid redistributing what
they contain.

---

## Known limits

Stated here and on every page the tool produces:

- **The published site carries the curated set.** Everything in it is complete;
  anything else opens onto a page saying it is not built, rather than a guess.
  Running the project locally builds any human gene from the same public sources.
- **Registry coverage.** Only ClinicalTrials.gov is swept, so China- and
  Japan-only registrations are under-represented. CTIS, ChiCTR and jRCT are the
  obvious next sources.
- **Preclinical and undisclosed programmes are invisible.** The tool sees the
  clinic and the databases, not a competitor's discovery portfolio.
- **The deal layer is small and hand-entered.** It is a set of sourced rows, not
  a market sample, which is why nothing is averaged over it.
- **Some programmes cannot be classified at all.** A registry entry that gives
  only a code name states nothing about the molecule; those rows say so instead
  of being guessed at, and are resolved by hand into `data/assets/`.
- **`whyStopped` is self-reported and often absent.** The page prints the
  reporting rate so you know how much of the termination picture you are seeing.
- **Disease-name matching is stemmed token overlap, not ontology mapping.** Good
  enough to stop the obvious false positives; not a substitute for EFO mapping.
- **The density bands are a convention.** Documented in
  [ARCHITECTURE.md](ARCHITECTURE.md) and printed on the page. They are a stated
  assumption, not a measurement, and have not been calibrated against outcomes.

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

The engine (`landscape/`) has no web dependencies and does not know the site
exists. Only `web/` needs FastAPI. Keeping that line clean is what lets the same
analysis serve a web request, a command line run and a CI job without three
versions of it.

Every test runs without network: the source adapters are exercised against
payloads in `tests/payloads.py` that reproduce the shapes these APIs actually
emit, malformed records included. That is what makes the retrieval layer testable
at all, given it depends on three services nobody controls.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design decisions and how the
constants were calibrated.

## Licence

MIT for the code. The data carries its own licences — see the table above.
