# target-landscape

**Look up a drug target. Get six lines on whether it is worth the meeting.**

A web interface for early-stage diligence — seed and Series A — over a library
that turns a gene symbol into a judgement. Built on Open Targets, ChEMBL,
ClinicalTrials.gov and Europe PMC. No API key required.

The six lines, in the order an investor has to settle them:

| | |
|---|---|
| **Is the target real?** | Approved drug on it, tested and failed, or still a hypothesis — with the human genetic evidence behind it |
| **Did it fail before?** | The question a table of assets in development cannot answer, because failed programmes leave the table |
| **Is the window open?** | Phase-weighted competitive density, not a count |
| **Will anything be settled?** | How much of the running activity is a controlled efficacy trial, and how much only looks like one |
| **When does it get settled?** | The next readout that could change the answer, with its date |
| **What is left to do?** | A modality that could reach this protein and has not been tried, or an indication nobody has taken |

```bash
pip install -r requirements-web.txt
uvicorn web.app:app --reload          # → http://127.0.0.1:8000
```

**On Windows**, double-click `1-SETUP.bat` then `2-START-WEBSITE.bat` — no
terminal required. See [WINDOWS.md](WINDOWS.md).

The same analysis is available as a command line tool and as a document:

```bash
python -m landscape TNFRSF13C         # → out/TNFRSF13C_landscape.html
```

![The read, above the fold](docs/images/read.png)

---

## The interface

**Every target page opens with six statements, not a row of counts.** There
used to be a strip of ten summary statistics here; it was removed on purpose.
Ten numbers with no verdict attached is exactly the failure mode this page
exists to avoid — it hands you rows and leaves the judgement to you, which is
what every other target database already does.

The rule the whole interface follows: **the engine may be thick, the page must
be thin.** Each analysis module computes as much as the public record supports;
each panel shows one sentence of conclusion and at most three lines of evidence,
and puts its table behind a disclosure. Raw data is linked out to Open Targets,
ClinicalTrials.gov and Europe PMC rather than reproduced — they do tables better
than this page can, and a second-hand copy of a database is not the point.

Under the read, a generated mechanism figure: where the protein sits and every
intervention the field has actually taken, with arrow weight showing how far
each approach has come. It is drawn from the data, so it exists for all 28,000
indexed targets rather than for the handful somebody drew by hand.

Then the views. This is an explorable database, not a report with tabs:

| View | Answers |
|---|---|
| **Assets** | Whether anyone has made a medicine out of this target, then every programme, sortable, with a panel per asset showing its trials and the source of each field |
| **Mechanisms** | Grouped by what each asset *does* to the target, not by what it is — plus which modalities could physically reach this protein and have not been tried |
| **Indications** | An indication × mechanism grid: how far each approach has been taken in each disease |
| **Trials** | What reads out next and what each result could actually prove, from the registered design — a single-arm study with a pharmacodynamic endpoint cannot settle efficacy however positive it turns out |
| **Terminations** | The sponsor's own stated reason, classified and quoted |
| **Whitespace** | Well-evidenced indications with nothing in the clinic |
| **Licensing** | Which programmes show availability signals, who holds them, and what comparable assets have sold for |
| **Reading** | The most-cited reviews and recent mechanism work, from Europe PMC |

Terminations — the sponsor's own words, classified, with the matched phrase shown
so you can overrule the call:

![Termination analysis](docs/images/terminations.png)

Licensing — availability derived from the trial and sponsor data already on the
page, each signal carrying the evidence that produced it:

![Availability signals](docs/images/licensing.png)

**One filter state drives every view.** Narrow to antibodies and the mechanism
grid, the trial list and the termination notices all narrow with it. That is
what makes it explorable rather than a fixed report.

**Investor / Scientist** switches which figures lead the summary and which view
opens first. It hides nothing — a scientist needs the competitive picture and
an investor needs the mechanism, and both stay one click apart.

**Search finds targets by the names people actually use.** Nobody types
`TNFRSF13C` — they type BAFF-R. Nobody types `ERBB2` — they type HER2. Search
runs against a local index of symbols, aliases and names: instant, offline,
and alias-aware, so HER2 opens the ERBB2 landscape and the interface shows you
that it did.

The home page shows what a target page holds rather than describing it: six
tiles carrying the real figures from a real target, every one of them derived
from the same stored landscape the target page renders. Underneath, the index
doubles as a browser — filter by therapeutic area, or type to narrow it.

```bash
python scripts/seed_target_index.py     # ~200 hand-checked drug targets, ships in the repo
python scripts/build_target_index.py    # expands it to every approved human gene (HGNC)
```

The seed is what makes the box useful out of the box; the HGNC build makes it
complete. The seed's aliases survive the merge, because HGNC is authoritative
on symbols and patchy on vernacular — "PD-1" is in there, "BAFF-R" and
"TL1A" are not reliably.

**Two tiers, and the interface says which one you are reading.** Curated targets
are precomputed and committed to the repo: they open instantly and cannot fail,
because serving them touches no external API. Anything else is built live from
the three sources — 20 to 40 seconds, reported stage by stage rather than as a
spinner, then cached.

```bash
# Seed the curated tier (do this once)
python scripts/precompute.py --set calibration/targets.txt

# Export the whole site as one self-contained HTML file — no server, no cold
# start, works from a file path or any static host
python scripts/make_static_demo.py --out out/demo.html
```

### Deploying

Hugging Face Spaces, Docker SDK. Copy `SPACE_README.md` to `README.md` in the
Space, push, and it builds. The image has no build step — the frontend is plain
HTML, CSS and JavaScript served as files.

---

## Why this is not a search tool

Listing the drugs against a target is a solved problem — Open Targets does it for
free, Cortellis and Evaluate do it commercially. Listing is not the work. The work
is the five judgements a landscape has to make, and each one is a place where
a naive pipeline gets it confidently wrong:

**1. Assets are grouped by mechanism, not counted.**
Five antibodies against a receptor are one competitive situation if they all block
the ligand and a completely different one if two of them deplete the cell. The
classifier reads WHO INN stems (`-mab`, `-cept`, `-leucel`, `-siran`) alongside
ChEMBL `action_type` and mechanism text, so it places assets that have no database
record at all — which, on most targets, is where the cell therapies and the
non-Western programmes live.

**2. Terminations are split into science and business.**
A raw termination count is worse than useless: a large share of trials stop for
reasons that say nothing about the target — funding ran out, the programme was
deprioritised after a merger, COVID closed the sites. Counting those as evidence
against the biology walks a team away from a target that never failed. So
`whyStopped` — the sponsor's own one-line account, the highest-value free field in
competitive intelligence and almost never used because it is unstructured text
behind a paginated API — is classified into *science* (efficacy, safety, PK/PD),
*operational*, and *business*, with the verbatim notice quoted alongside.

The BAFF-R example is the case in point. Novartis stopped its Phase 2b in
hidradenitis suppurativa saying the study *"did not meet the target criteria for
progression despite demonstrating efficacy versus placebo… No new safety signals
were identified."* Keyword matching reads "safety" and files it as a toxicity
failure — inverting the conclusion. This tool masks negated clauses, classifies it
as a portfolio decision, and reports that it *also* matched efficacy, so the reader
can disagree with the call rather than inherit it.

**3. Density is phase-weighted, and shows its weights.**
One Phase 3 competitor is priced at four Phase 1s. Dormant programmes — every
linked trial stopped, nothing running — are reported separately rather than
inflating the count. The weights and the band thresholds are printed in the memo
footer, because a crowding score nobody can recompute is not an analysis.

**4. Availability is derived, not assumed.**
Every other target database answers "what exists". A BD or search-and-evaluation
team has assumed that already and is asking *which of these could I actually
get, and who do I call*. No licensed intelligence is needed to notice that a
Phase 2 asset whose every trial has stopped is a shelved programme with human
data — the classic in-licensing candidate — or that a sponsor running trials
only in China has probably not placed its ex-China rights. Each signal is a
rule over the asset table, each carries the evidence that fired it, and the
output is a shortlist to check rather than a recommendation. Deal comparables
sit alongside, hand-curated with a source on every row, because no free deal
database exists — and the tool says so instead of rendering an empty table.

**5. Whitespace requires evidence, not just absence.**
A disease qualifies only when the Open Targets association clears a threshold
*and* carries genetic support *and* has nothing past preclinical. Matching EFO
terms against sponsor free text is where this silently breaks — "Sjogren syndrome"
versus "Sjogren's Disease" fails a substring test — so names are compared by
stemmed token overlap, and the section is labelled a screen to check by hand
rather than a finding.

Everything above runs on rules. The optional LLM pass (`ANTHROPIC_API_KEY`) is
handed only the residue the rules could not place, is constrained to the same
controlled vocabulary, and tags every row it touched. **The tool produces a
complete memo with no model at all** — an analysis whose numbers change when a
model is swapped is not an analysis.

---

## Quickstart

Python 3.9+. The pipeline itself needs nothing beyond the standard library.

```bash
git clone https://github.com/<you>/target-landscape.git
cd target-landscape

# Check the APIs before trusting a run
python -m landscape doctor

# Live run against the public APIs
python -m landscape TNFRSF13C

# Several targets at once, plus an index comparing them
python -m landscape TNFRSF13C TNFSF13B PDCD1 --out out/

# Offline demo — no network, uses the checked-in fixture
python -m landscape --fixture fixtures/TNFRSF13C.json

# Run the reference target set and rank them on one density scale
python -m landscape --calibrate --out out/calibration

# Everything
python -m landscape TNFRSF13C \
  --out out/ \
  --format html,md,json \
  --deals deals/example.csv \
  --save-fixture fixtures/TNFRSF13C.json

python -m unittest discover -s . -p "test_*.py"
```

### `doctor`

The three public APIs rename fields between releases and nothing warns you.
The first symptom of drift is not a crash — it is a memo that renders
perfectly and says nothing: empty asset table, no warnings, plausible prose.
That quiet failure is much worse than an exception, so `doctor` probes each
source with the exact queries the pipeline uses and names the field that moved
and the function to fix:

```
Open Targets
  [  ok  ] reachable
  [  ok  ] resolves a gene symbol
  [ FAIL ] target core fields
              empty fields: tractability
              → update _TARGET_QUERY in sources/opentargets.py
```

Optional model pass:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
python -m landscape TNFRSF13C          # model resolves what the rules could not
python -m landscape TNFRSF13C --no-llm # force rules only
```

Responses are cached under `~/.cache/target-landscape`, so re-running a target is
instant and does not re-hit the APIs.

### As a library

```python
from landscape import build, to_html

ls = build("TNFRSF13C")
print(ls.crowding["verdict"], ls.crowding["weighted_score"])
for a in ls.assets[:5]:
    print(a.name, a.phase_label, a.mechanism_class, a.sponsor)
open("memo.html", "w").write(to_html(ls))
```

---

## Output

| Section | What it answers |
|---|---|
| Bottom line | The one read, with the density verdict and the lead asset |
| Competitive picture | Mechanism clusters, then the full asset table |
| Indication × mechanism | Highest phase reached *per indication* — not the asset's overall maximum, which is the standard way this table lies |
| Stopped programmes | Reason taxonomy, plus the verbatim notices most worth reading |
| Whitespace screen | Well-evidenced diseases with nothing in the clinic |
| What this cannot see | Coverage limits, stated up front rather than buried |

HTML (self-contained, prints cleanly, light and dark), Markdown, and JSON — the
JSON is the full structured record, so the tool can be a data source for something
else rather than only a document generator.

---

## Data sources

| Source | Carries | Licence |
|---|---|---|
| [Open Targets Platform](https://platform.opentargets.org/) | target identity, tractability, known drugs, disease associations with genetic evidence | CC0 |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | `action_type`, molecule type, max phase, withdrawal flags | CC BY-SA 3.0 |
| [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api) | trials, phases, sponsors, conditions, geography, `whyStopped` | US Government public domain |

Deal comparables are hand-maintained (`deals/*.csv`) because no free deal database
exists. The memo says so rather than rendering an empty section.

---

## Known limits

Stated here and in every memo the tool produces:

- **Registry coverage.** Only ClinicalTrials.gov is swept, so China- and Japan-only
  registrations are under-represented. CTIS, ChiCTR and jRCT are the obvious next
  sources.
- **Preclinical and undisclosed programmes are invisible.** The tool sees the
  clinic and the databases, not a competitor's discovery portfolio.
- **`whyStopped` is self-reported and often absent.** The memo prints the reporting
  rate so you know how much of the termination picture you are actually seeing.
- **Disease-name matching is stemmed token overlap, not ontology mapping.** Good
  enough to stop the obvious false positives; not a substitute for EFO mapping.
- **The density bands are a convention.** Hand-calibrated, documented in
  [ARCHITECTURE.md](ARCHITECTURE.md), and printed in every memo. They are a stated
  assumption, not a measurement.

## Repository

```
landscape/
  models.py            data model; every fact carries provenance
  config.py            endpoints and every constant that feeds a judgement
  http.py              cached, retrying stdlib HTTP client
  sources/             Open Targets · ChEMBL · ClinicalTrials.gov
  normalize.py         reconciliation — identity, phase, modality, sponsor
  analysis/
    mechanism.py       INN stems + mechanism vocabulary → mechanism classes
    failures.py        whyStopped → science / operational / business
    crowding.py        phase-weighted density, indication matrix, whitespace
    licensing.py       availability signals, holders, deal comparables
  llm.py               optional; residue only, vocabulary-constrained, tagged
  render.py            HTML + Markdown memo, and the multi-target index
  doctor.py            API health and schema-drift check
  store.py             curated tier + live-build cache
  targets.py           the searchable index: symbols, aliases, ranked lookup
  pipeline.py          orchestration; sources degrade, runs do not abort
web/
  app.py               FastAPI: search, lookup, build jobs, exports
  static/              the interface — no framework, no build step
data/curated/          precomputed targets, committed
data/deals/            hand-curated deal comparables, one CSV per target
data/target_index.json the searchable target index
scripts/               precompute, static export
fixtures/              offline demo + regression input
calibration/           reference target set for deriving the density bands
tests/                 198 tests — parser contracts against realistic payloads,
                       the judgement layer, and the web layer; all offline
```

The engine (`landscape/`) has no web dependencies and does not know the site
exists. Only `web/` needs FastAPI. Keeping that line clean is what lets the
same analysis serve a web request, a command line run and a CI job without
three versions of it.

Every test runs without network: the source adapters are exercised against
payloads in `tests/payloads.py` that reproduce the shapes these APIs actually
emit, malformed records included. That is what makes the retrieval layer
testable at all, given it depends on three services nobody controls.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design decisions and how the
constants were calibrated.

## Licence

MIT for the code. The data carries its own licences — see the table above.
