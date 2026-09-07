# Deal comparables

One CSV per target, named `<SYMBOL>.csv`. These are hand-maintained: no free,
redistributable deal database exists, and the tool says so wherever this
section appears rather than rendering an empty table and letting the reader
assume there were no deals.

Columns:

| Column | Notes |
|---|---|
| `date` | YYYY-MM or YYYY-MM-DD |
| `acquirer` | The party paying |
| `target_company` | The party being paid |
| `asset` | Asset name — matched against the asset table, so use the name the databases use |
| `mechanism` | Free text; helps when the asset itself is not in the table |
| `deal_type` | `licence` or `acquisition`. Blank means licence. **Only licences are averaged**: an acquisition price buys the company — its platform, its cash, its other programmes — and mixing one into a column of asset upfronts reports a median no asset was ever sold for. Acquisitions still appear in the table |
| `stage_at_deal` | Preclinical / Phase 1 / Phase 2 / Phase 3 / Approved — drives the by-stage medians |
| `upfront_usd_m` | Millions USD |
| `total_usd_m` | Millions USD including milestones |
| `territory` | Worldwide, ex-China, US+EU, … |
| `source_url` | **Always fill this.** A deal figure without a source is not usable in a memo |

Rows whose `asset` matches an asset in the table are shown against that
programme; rows that do not match still appear, as mechanism-level comparables.

Two files ship filled in, as worked examples: `TNFRSF13C.csv` (the BAFF/APRIL
axis — note that these price the *ligand* programmes, which is why they show as
mechanism-level comparables rather than matching a row in a BAFF-R asset table)
and `PDCD1.csv` (the PD-1/VEGF bispecific deals). Every figure on those rows was
read off the party's own press release, and the release is the `source_url`.
