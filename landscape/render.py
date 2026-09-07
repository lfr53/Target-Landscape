"""Memo rendering — Markdown and standalone HTML.

The output is shaped like the deliverable it imitates: a one-page landscape
memo of the sort a search-and-evaluation analyst hands a partner. Bottom line
first, then the evidence, then — not buried in an appendix — what the analysis
cannot see.

Every table carries its source. The crowding score prints its own weights.
The whitespace section is labelled a screen rather than a finding. These are
not disclaimers; they are the difference between an analysis someone can act
on and a number nobody can check.
"""

from __future__ import annotations

import html
from typing import Any

from .models import PHASE_LABELS, Landscape

_PHASE_CELL = {-1: "·", 0: "PC", 1: "1", 2: "2", 3: "3", 4: "Appr"}


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def to_markdown(landscape: Landscape, *, max_assets: int = 40) -> str:
    t = landscape.target
    c = landscape.crowding
    f = landscape.failures
    n = landscape.narrative
    lines: list[str] = []
    add = lines.append

    add(f"# {t.symbol} — competitive landscape")
    add("")
    add(f"*{t.name}*  ·  {t.ensembl_id}  ·  generated {landscape.generated}")
    add("")
    if landscape.warnings:
        add("> **Run warnings.** " + " ".join(landscape.warnings))
        add("")

    # Key facts, as a list. No verdict: on most targets the record does not
    # support one, and a template with a slot for it writes one anyway.
    header = landscape.header or {}
    if header.get("facts"):
        add("## The target")
        add("")
        for row in header["facts"]:
            line = f"- **{row['label']}** — {row['value']}"
            if row.get("note"):
                line += f"  \n  {row['note']}"
            add(line)
        add("")
        cited = sorted({p for row in header["facts"] for p in row.get("pmids", [])})
        bits = []
        if header.get("accession"):
            bits.append(f"UniProt [{header['accession']}]({header.get('url', '')}), CC BY 4.0")
        if cited:
            bits.append("cited: " + ", ".join(
                f"[PMID {p}](https://europepmc.org/article/MED/{p})" for p in cited[:6]))
        if bits:
            add("*" + ". ".join(bits) + ".*")
            add("")

    # The read comes first and is six lines long. A memo that opens with a
    # statistics table asks the reader to do the synthesis; this one does it,
    # and puts the table underneath for whoever wants to check the working.
    read = landscape.feasibility or {}
    if read.get("lines"):
        add("## What the record holds")
        add("")
        add("| | | |")
        add("|---|---|---|")
        for line in read["lines"]:
            add(f"| **{line['label']}** | {line['value']} | {line['detail']} |")
        add("")
    add(n.get("bottom_line", "—"))
    add("")

    prec = landscape.precedent or {}
    if prec.get("tier_label"):
        add("## Has anyone made a medicine out of this target")
        add("")
        add(f"**{prec['tier_label']}.** {prec.get('read', '')}")
        add("")
        for item in prec.get("evidence", []):
            add(f"- {item}")
        add("")
        approved = prec.get("approved") or []
        if approved:
            add("| Approved drug | Sponsor | Modality | First approval |")
            add("|---|---|---|---|")
            for drug in approved:
                flag = " (withdrawn)" if drug.get("withdrawn") else ""
                add(f"| {drug['name']}{flag} | {drug.get('sponsor') or '—'} | "
                    f"{drug.get('modality') or '—'} | {drug.get('first_approval') or '—'} |")
            add("")

    reads = landscape.readouts or {}
    if reads.get("verdict"):
        add("## What reads out next, and what it could prove")
        add("")
        add(reads["verdict"])
        add("")
        if reads.get("catalysts"):
            add("| Primary completion | Phase | What a result could support | Study |")
            add("|---|---|---|---|")
            for cat in reads["catalysts"][:6]:
                when = cat["date"] + (" (est.)" if cat.get("estimated") else "")
                add(f"| {when} | {cat['phase_label']} | {cat['level_label']} | "
                    f"[{cat['nct_id']}]({cat['url']}) |")
            add("")
            add("*Registered design and endpoint, read before the trial reports — a "
                "single-arm study with a pharmacodynamic endpoint cannot settle efficacy "
                "however positive it turns out.*")
            add("")

    add("| | |")
    add("|---|---|")
    add(f"| Active programmes | {c.get('n_active', 0)} ({c.get('n_dormant', 0)} dormant) |")
    add(f"| Most advanced | {c.get('lead_phase', '—')} |")
    add(f"| Mechanism classes | {c.get('n_mechanism_classes', 0)} |")
    add(f"| Named sponsors | {c.get('n_sponsors', 0)} |")
    add(f"| Phase-weighted density | **{c.get('weighted_score', 0)}** → **{c.get('verdict', '—')}** |")
    add("")

    if t.tractability:
        add("**Tractability (Open Targets):** " + "; ".join(
            f"{modality} — {', '.join(buckets)}" for modality, buckets in t.tractability.items()
        ))
        add("")

    add("## Competitive picture")
    add("")
    add(n.get("competitive", "—"))
    add("")
    for label, names in landscape.mechanism_clusters.items():
        add(f"- **{label}** ({len(names)}): {', '.join(names[:8])}"
            + (f" +{len(names) - 8} more" if len(names) > 8 else ""))
    add("")

    add("### Assets")
    add("")
    add("| Asset | Sponsor | Phase | Mechanism | Lead indications | Trials |")
    add("|---|---|---|---|---|---|")
    for a in landscape.assets[:max_assets]:
        flag = "" if a.is_active else " ⏸"
        add(
            f"| {a.name}{flag} | {a.sponsor or '—'} | {a.phase_label} | "
            f"{a.mechanism_class or '—'} | {'; '.join(a.indications[:2]) or '—'} | "
            f"{len(a.trials)} |"
        )
    if len(landscape.assets) > max_assets:
        add(f"| … +{len(landscape.assets) - max_assets} more | | | | | |")
    add("")
    add("⏸ = dormant (every linked trial stopped, nothing running)")
    add("")

    matrix = c.get("matrix", {})
    if matrix.get("rows"):
        add("### Indication × mechanism (highest phase reached)")
        add("")
        mechanisms = matrix["mechanisms"]
        add("| Indication | " + " | ".join(mechanisms) + " |")
        add("|---" * (len(mechanisms) + 1) + "|")
        for row in matrix["rows"][:15]:
            cells = [_PHASE_CELL.get(row["cells"].get(m, -1), "·") for m in mechanisms]
            add(f"| {row['indication']} | " + " | ".join(cells) + " |")
        add("")

    add("## What the stopped programmes tell us")
    add("")
    add(n.get("failures", "—"))
    add("")
    if f.get("counts"):
        add("| Reason | Trials |")
        add("|---|---|")
        for label, count in f["counts"].items():
            add(f"| {label} | {count} |")
        add("")
    cases = [c_ for c_ in f.get("cases", []) if c_.get("why_stopped")][:8]
    if cases:
        add("**Stated reasons, most decision-relevant first**")
        add("")
        for case in cases:
            phase = PHASE_LABELS.get(case["phase"], "Unknown")
            add(f"- **{case['nct_id']}** ({phase}, {case.get('sponsor') or '—'}) — "
                f"*{case['class']}* — “{case['why_stopped']}” "
                f"([record]({case['url']}))")
            if case.get("evidence"):
                add(f"  <br>*classifier: {case['evidence']}*")
        add("")

    add("## Whitespace screen")
    add("")
    add(n.get("whitespace", "—"))
    add("")
    if landscape.whitespace:
        add("| Disease | Association | Genetic evidence | Highest phase |")
        add("|---|---|---|---|")
        for row in landscape.whitespace[:10]:
            add(f"| {row['disease']} | {row['association_score']} | "
                f"{row['genetic_score']} | {row['highest_phase']} |")
        add("")

    lic = landscape.licensing or {}
    if lic.get("assets"):
        add("## Availability and licensing")
        add("")
        add(n.get("licensing", "—"))
        add("")
        add("| Programme | Holder | Scale | Phase | Status |")
        add("|---|---|---|---|---|")
        for row in lic["assets"]:
            add(f"| {row['asset']} | {row['sponsor'] or '—'} | {row['sponsor_scale']} | "
                f"{row['phase_label']} | "
                f"{'Active' if row['is_active'] else 'All trials stopped'} |")
        add("")
        flagged = [r_ for r_ in lic["assets"] if r_["signals"]]
        if flagged:
            add("**Why, in each case**")
            add("")
            for row in flagged:
                for signal in row["signals"]:
                    add(f"- **{row['asset']} — {signal['headline']}.** {signal['evidence']}")
            add("")
        add("*Signals are rules over public trial and sponsor data, not knowledge of "
            "any agreement, and nothing here is scored.*")
        add("")

        deal_summary = lic.get("deals") or {}
        by_stage = deal_summary.get("by_stage") or []
        if by_stage:
            add("**Deal comparables by stage — licences only**")
            add("")
            add("| Stage at deal | n | Median upfront ($m) | Range |")
            add("|---|---|---|---|")
            for stage in by_stage:
                add(f"| {stage['stage']} | {stage['n']} | {stage['median_upfront']} | "
                    f"{stage['min_upfront']}–{stage['max_upfront']} |")
            add("")
            n_acq = deal_summary.get("n_acquisitions") or 0
            if n_acq:
                add(f"{n_acq} acquisition{'' if n_acq == 1 else 's'} appear in the table "
                    "below but not in these medians: an acquisition price buys the "
                    "company, and averaging one against asset upfronts reports a figure "
                    "no asset was ever sold for.")
                add("")

    if landscape.deals:
        add("## Deal comparables")
        add("")
        add("| Date | Acquirer | Asset | Stage | Upfront ($m) | Total ($m) |")
        add("|---|---|---|---|---|---|")
        for d in landscape.deals:
            add(f"| {d.date} | {d.acquirer} | {d.asset} | {d.stage_at_deal} | "
                f"{d.upfront_usd_m or '—'} | {d.total_usd_m or '—'} |")
        add("")
        add("*Hand-curated. No free deal database exists; this table is only as "
            "complete as its maintainer.*")
        add("")

    add("## What this cannot see")
    add("")
    add(n.get("risks", "—"))
    add("")

    add("---")
    add("")
    weights_md = ", ".join(f"{k} {v:g}" for k, v in (c.get("weights_used") or {}).items())
    bands_md = ", ".join(f"{b['verdict']} ≥ {b['from']:g}" for b in c.get("bands_used", []))
    add(f"**Method.** Phase weights: {weights_md}. Density bands: {bands_md}. "
        f"Narrative written by: {n.get('_source', 'template')}.")
    add("")
    add("**Sources.** Open Targets Platform (CC0) · ChEMBL (CC BY-SA 3.0) · "
        "ClinicalTrials.gov (US Government public domain).")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=IBM+Plex+Mono:wght@400;500;600&"
    'family=IBM+Plex+Sans:wght@400;500;600&display=swap">'
)

_CSS = """
:root{
  /* Deep teal accent; warm-biased neutrals rather than pure grey. Semantic
     science/business colours are deliberately separate from the accent, since
     they encode a classification rather than brand the page. */
  --bg:#fcfcfa; --fg:#16191b; --muted:#70777d; --faint:#9aa1a7;
  --line:#e6e5df; --line2:#f2f1ec; --accent:#12414f; --accent-soft:#e7eef0;
  --card:#fff; --warn:#7a5200; --warnbg:#fdf6e3; --warnline:#e8d9a8;
  --sci:#9c3b34; --biz:#2f5f7a;
  --sans:"IBM Plex Sans",ui-sans-serif,-apple-system,BlinkMacSystemFont,
    "Segoe UI","Helvetica Neue",Arial,sans-serif;
  /* Registry identifiers, phases and counts are codes, not prose — they get
     the mono face, which also keeps the matrix columns aligned. */
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#101315; --fg:#e9e7e2; --muted:#98a0a6; --faint:#7a8288;
  --line:#252b2f; --line2:#1c2124; --accent:#8fc2d2; --accent-soft:#18272d;
  --card:#171b1e; --warn:#dcb463; --warnbg:#241f14; --warnline:#4a3f22;
  --sci:#dd9089; --biz:#8fbcd8;
}}
:root[data-theme="dark"]{
  --bg:#101315; --fg:#e9e7e2; --muted:#98a0a6; --faint:#7a8288;
  --line:#252b2f; --line2:#1c2124; --accent:#8fc2d2; --accent-soft:#18272d;
  --card:#171b1e; --warn:#dcb463; --warnbg:#241f14; --warnline:#4a3f22;
  --sci:#dd9089; --biz:#8fbcd8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15.5px/1.65 var(--sans);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:880px;margin:0 auto;padding:56px 28px 96px}

header{margin-bottom:34px}
h1{font-size:30px;line-height:1.15;margin:0 0 8px;letter-spacing:-.018em;
  font-weight:600;text-wrap:balance}
h1 .sym{font-family:var(--mono);font-weight:600;letter-spacing:-.03em}
.sub{color:var(--muted);font-size:13px;margin:0;font-family:var(--mono);font-weight:400}
.sub .dotsep{color:var(--faint);padding:0 7px}

h2{font-size:11px;margin:52px 0 16px;letter-spacing:.13em;text-transform:uppercase;
  font-weight:500;font-family:var(--mono);color:var(--accent);
  display:flex;align-items:center;gap:14px}
h2::after{content:"";flex:1;height:1px;background:var(--line)}
h3{font-size:10.5px;margin:32px 0 10px;color:var(--faint);text-transform:uppercase;
  letter-spacing:.13em;font-weight:500;font-family:var(--mono)}
p{margin:0 0 14px;max-width:66ch}
.lede{font-size:18px;line-height:1.55;letter-spacing:-.008em;margin-bottom:24px}
.facts{display:grid;grid-template-columns:minmax(120px,160px) 1fr;gap:8px 18px;
  margin:0 0 10px;max-width:80ch}
.facts dt{font-family:var(--mono);font-size:10.5px;text-transform:uppercase;
  letter-spacing:.09em;color:#70777d}
.facts dd{margin:0;font-size:14.5px;line-height:1.6}
.src{font-size:12px;line-height:1.6;color:var(--muted);margin-bottom:24px}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;
  overflow:hidden;margin:24px 0 18px}
.kpi{background:var(--card);padding:14px 16px 15px}
.kpi .v{font-size:21px;font-weight:600;letter-spacing:-.03em;line-height:1.2;
  font-family:var(--mono);font-variant-numeric:tabular-nums}
.kpi .l{font-size:10px;color:var(--faint);text-transform:uppercase;
  letter-spacing:.1em;margin-top:6px;line-height:1.35;font-family:var(--mono)}
.kpi.hl{background:var(--accent-soft)}
.kpi.hl .v{color:var(--accent)}

.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}
.tag{display:inline-block;font-size:11px;padding:2px 9px;border-radius:99px;
  border:1px solid var(--line);color:var(--muted);background:var(--card)}

.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:14px 0 8px;
  border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:9px 14px;border-bottom:1px solid var(--line2);vertical-align:top}
thead th{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--faint);
  font-weight:500;white-space:nowrap;border-bottom:1px solid var(--line);
  background:var(--card);font-family:var(--mono)}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:var(--line2)}
td.who{color:var(--muted)}
.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted);
  font-family:var(--mono);font-size:12.5px}
.cell{text-align:center;font-variant-numeric:tabular-nums;font-size:11.5px;
  font-weight:500;font-family:var(--mono)}
.p4{background:color-mix(in srgb,var(--accent) 34%,transparent);color:var(--fg)}
.p3{background:color-mix(in srgb,var(--accent) 24%,transparent)}
.p2{background:color-mix(in srgb,var(--accent) 14%,transparent)}
.p1{background:color-mix(in srgb,var(--accent) 7%,transparent)}
.dot{color:var(--faint);font-weight:400}
.matrix th:first-child,.matrix td:first-child{position:sticky;left:0;background:var(--card);
  z-index:1;border-right:1px solid var(--line);min-width:190px}
.matrix tbody tr:hover td:first-child{background:var(--line2)}
.legend{font-size:11px;color:var(--faint);margin:2px 0 0;line-height:1.7;
  font-family:var(--mono)}

ul.clusters{list-style:none;padding:0;margin:16px 0 0}
ul.clusters li{padding:10px 0;border-top:1px solid var(--line2);font-size:14px}
ul.clusters li:first-child{border-top:none}
ul.clusters .n{color:var(--faint);font-family:var(--mono);font-size:12px}
ul.clusters .names{color:var(--muted);font-size:13.5px}
.tag{font-family:var(--mono);font-size:10.5px}

.case{border-left:2px solid var(--line);padding:2px 0 2px 16px;margin:16px 0}
.case.sci{border-color:var(--sci)} .case.biz{border-color:var(--biz)}
.case q{quotes:none;font-size:14.5px;line-height:1.55;display:block;margin-bottom:7px}
.case .m{font-size:11.5px;color:var(--faint);font-family:var(--mono);line-height:1.7}
.case .m strong{color:var(--muted);font-weight:500}
.case .ev{color:var(--faint)}
.case a{font-family:var(--mono)}

.note{background:var(--warnbg);border:1px solid var(--warnline);color:var(--warn);
  border-radius:10px;padding:13px 16px;font-size:13px;line-height:1.55;margin:20px 0}
.method{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);
  font-size:11px;color:var(--faint);line-height:1.75;font-family:var(--mono)}
.method strong{color:var(--muted);font-weight:500}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,tr:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
table.read{width:100%;border-collapse:collapse;margin:18px 0 22px}
table.read th{text-align:left;font-family:var(--mono,ui-monospace,monospace);font-size:10.5px;
  text-transform:uppercase;letter-spacing:.1em;color:#70777d;font-weight:500;
  width:190px;vertical-align:top;padding:10px 14px 10px 12px;border-left:3px solid #e6e5df}
table.read td{padding:10px 0;vertical-align:top}
table.read tr.face-science th{border-left-color:#2e6b8a}
table.read tr.face-business th{border-left-color:#8a5a2e}
table.read .why{color:#70777d;font-size:12.5px;line-height:1.6;margin-top:5px;max-width:70ch}
figure.fig{margin:16px 0 24px}
figure.fig svg{width:100%;max-width:720px;height:auto;display:block;margin:0 auto}
figure.fig .tl-membrane{fill:#e7eef0} figure.fig .tl-cell,figure.fig .tl-nucleus{fill:#f7f6f2;stroke:#e6e5df}
figure.fig .tl-protein{fill:#12414f}
figure.fig .tl-protein-label{fill:#fff;font-size:13px;font-weight:600;text-anchor:middle;
  font-family:var(--mono,ui-monospace,monospace)}
figure.fig .tl-arrow line{stroke:#16191b;opacity:.75;stroke-linecap:round}
figure.fig .tl-arrowhead{fill:#16191b;opacity:.75}
figure.fig .tl-arrow-label{fill:#16191b;font-size:13px;font-weight:500}
figure.fig .tl-arrow-detail,figure.fig .tl-zone,figure.fig .tl-caveat{fill:#70777d;font-size:10.5px;
  font-family:var(--mono,ui-monospace,monospace)}
figure.fig .tl-empty{fill:#70777d;font-size:14px}
figure.fig figcaption{color:#70777d;font-size:12.5px;line-height:1.65;max-width:76ch;margin-top:10px}
p.fine{color:#70777d;font-size:12.5px;line-height:1.65;max-width:76ch}
@media print{body{background:#fff;font-size:11pt}.wrap{padding:0;max-width:none}
  .scroll{border:none}h2{margin-top:24px}}
@media (max-width:560px){.wrap{padding:32px 18px 64px}h1{font-size:24px}.lede{font-size:16px}}
"""

# Long mechanism labels blow the matrix out to three screens wide. The table
# gets short forms and a legend underneath; nothing is lost, and the grid
# becomes readable at a glance, which is the only reason the grid exists.
_SHORT_MECHANISM = {
    "Depleting antibody (ADCC/CDC)": "Depleting mAb",
    "Blocking antibody": "Blocking mAb",
    "Agonist antibody": "Agonist mAb",
    "Antibody — mechanism unresolved": "mAb (n/a)",
    "Ligand trap / decoy receptor": "Ligand trap",
    "Cell therapy — target-directed CAR": "CAR-T",
    "Cell therapy — bispecific CAR": "Bispecific CAR",
    "Cell therapy — ligand-based CAR": "Ligand CAR",
    "Bispecific / T-cell engager": "Bispecific",
    "ADC — payload delivery": "ADC",
    "Oligonucleotide knockdown": "Oligo",
    "Active immunisation": "Vaccine",
    "Named only by class": "Unnamed",
    "Unclassified": "n/a",
}


def _short_mechanism(label: str) -> str:
    label = (label or "Unclassified").replace(" [model]", "")
    if label in _SHORT_MECHANISM:
        return _SHORT_MECHANISM[label]
    if "—" in label:
        head, tail = label.split("—", 1)
        if "small molecule" in head.lower():
            return "SM " + tail.strip()[:14]
        return tail.strip()[:18]
    return label[:20]


def _esc(value: Any) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "—"
    return html.escape(str(value))


def _phase_cell(phase: int) -> str:
    label = _PHASE_CELL.get(phase, "·")
    if phase < 0:
        return '<td class="cell dot">·</td>'
    return f'<td class="cell p{max(phase, 1)}">{label}</td>'


def to_html(landscape: Landscape, *, max_assets: int = 60) -> str:
    t = landscape.target
    c = landscape.crowding
    f = landscape.failures
    n = landscape.narrative
    out: list[str] = []
    add = out.append

    add(f"<title>{_esc(t.symbol)} Landscape</title>")
    add(_FONTS)
    add(f"<style>{_CSS}</style>")
    add('<div class="wrap">')
    add("<header>")
    add(f'<h1><span class="sym">{_esc(t.symbol)}</span> — competitive landscape</h1>')
    add(f'<p class="sub">{_esc(t.name)}<span class="dotsep">·</span>{_esc(t.ensembl_id)}'
        f'<span class="dotsep">·</span>{_esc(landscape.generated)}</p>')
    add("</header>")

    if landscape.warnings:
        add('<div class="note"><strong>Run warnings.</strong> '
            + " ".join(_esc(w) for w in landscape.warnings) + "</div>")

    header = landscape.header or {}
    if header.get("facts"):
        add("<h2>The target</h2>")
        add('<dl class="facts">')
        for row in header["facts"]:
            add(f'<dt>{_esc(row["label"])}</dt><dd>{_esc(row["value"])}'
                + (f'<div class="why">{_esc(row["note"])}</div>' if row.get("note") else "")
                + "</dd>")
        add("</dl>")
        cited = sorted({p for row in header["facts"] for p in row.get("pmids", [])})
        bits = []
        if header.get("accession"):
            bits.append(f'UniProt <a href="{_esc(header.get("url", ""))}">'
                        f'{_esc(header["accession"])}</a>, CC BY 4.0')
        if cited:
            bits.append("cited: " + ", ".join(
                f'<a href="https://europepmc.org/article/MED/{_esc(p)}">PMID&nbsp;{_esc(p)}</a>'
                for p in cited[:6]))
        if bits:
            add('<p class="src">' + " · ".join(bits) + "</p>")

    read = landscape.feasibility or {}
    if read.get("lines"):
        add("<h2>What the record holds</h2>")
        add('<table class="read"><tbody>')
        for line in read.get("lines", []):
            add(f'<tr class="face-{_esc(line["face"])}">'
                f'<th scope="row">{_esc(line["label"])}</th>'
                f'<td><strong>{_esc(line["value"])}</strong>'
                f'<div class="why">{_esc(line["detail"])}</div></td></tr>')
        add("</tbody></table>")
        add(f"<p>{_esc(n.get('bottom_line', '—'))}</p>")
    else:
        add(f'<p class="lede">{_esc(n.get("bottom_line", "—"))}</p>')

    prec = landscape.precedent or {}
    if prec.get("tier_label"):
        add("<h2>Has anyone made a medicine out of this target</h2>")
        add(f'<p><strong>{_esc(prec["tier_label"])}.</strong> {_esc(prec.get("read", ""))}</p>')
        add("<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in prec.get("evidence", [])) + "</ul>")
        approved = prec.get("approved") or []
        if approved:
            add('<div class="scroll"><table><thead><tr><th>Approved drug</th>'
                "<th>Sponsor</th><th>Modality</th><th>First approval</th></tr></thead><tbody>")
            for drug in approved:
                flag = " <span class='tag'>withdrawn</span>" if drug.get("withdrawn") else ""
                add(f"<tr><td><strong>{_esc(drug['name'])}</strong>{flag}</td>"
                    f"<td class='who'>{_esc(drug.get('sponsor'))}</td>"
                    f"<td class='who'>{_esc(drug.get('modality'))}</td>"
                    f"<td>{_esc(drug.get('first_approval'))}</td></tr>")
            add("</tbody></table></div>")

    reads = landscape.readouts or {}
    if reads.get("verdict"):
        add("<h2>What reads out next, and what it could prove</h2>")
        add(f"<p>{_esc(reads['verdict'])}</p>")
        if reads.get("catalysts"):
            add('<div class="scroll"><table><thead><tr><th>Primary completion</th>'
                "<th>Phase</th><th>What a result could support</th><th>Study</th>"
                "</tr></thead><tbody>")
            for cat in reads["catalysts"][:6]:
                when = cat["date"] + (" (est.)" if cat.get("estimated") else "")
                add(f"<tr><td>{_esc(when)}</td><td>{_esc(cat['phase_label'])}</td>"
                    f"<td class='who'>{_esc(cat['level_label'])}</td>"
                    f"<td><a href='{_esc(cat['url'])}'>{_esc(cat['nct_id'])}</a></td></tr>")
            add("</tbody></table></div>")
            add("<p class='fine'>Registered design and endpoint, read before the trial "
                "reports — a single-arm study with a pharmacodynamic endpoint cannot "
                "settle efficacy however positive it turns out.</p>")

    add('<div class="kpis">')
    for value, label in [
        (f"{c.get('n_active', 0)}", "Active programmes"),
        (c.get("lead_phase", "—"), "Most advanced"),
        (f"{c.get('n_mechanism_classes', 0)}", "Mechanism classes"),
        (f"{c.get('n_sponsors', 0)}", "Named sponsors"),
    ]:
        add(f'<div class="kpi"><div class="v">{_esc(value)}</div>'
            f'<div class="l">{_esc(label)}</div></div>')
    add(f'<div class="kpi hl"><div class="v">{_esc(c.get("verdict", "—"))}</div>'
        f'<div class="l">Density {_esc(c.get("weighted_score", 0))}</div></div>')
    add("</div>")

    if t.tractability:
        add('<div class="tags">' + "".join(
            f"<span class='tag'>{_esc(m)}: {_esc(', '.join(b))}</span>"
            for m, b in t.tractability.items()) + "</div>")

    add("<h2>Competitive picture</h2>")
    add(f"<p>{_esc(n.get('competitive', '—'))}</p>")
    add('<ul class="clusters">')
    for label, names in landscape.mechanism_clusters.items():
        extra = f" +{len(names) - 8} more" if len(names) > 8 else ""
        add(f"<li><strong>{_esc(label)}</strong> "
            f"<span class='n'>({len(names)})</span><br>"
            f"<span class='names'>{_esc(', '.join(names[:8]))}{_esc(extra) if extra else ''}</span></li>")
    add("</ul>")

    add("<h3>Assets</h3>")
    add('<div class="scroll"><table><thead><tr>'
        "<th>Asset</th><th>Sponsor</th><th>Phase</th><th>Mechanism</th>"
        "<th>Lead indications</th><th>Trials</th></tr></thead><tbody>")
    for a in landscape.assets[:max_assets]:
        dormant = " <span class='tag'>dormant</span>" if not a.is_active else ""
        add(f"<tr><td><strong>{_esc(a.name)}</strong>{dormant}</td>"
            f"<td class='who'>{_esc(a.sponsor)}</td><td>{_esc(a.phase_label)}</td>"
            f"<td class='who'>{_esc(a.mechanism_class)}</td>"
            f"<td class='who'>{_esc('; '.join(a.indications[:2]))}</td>"
            f"<td class='num'>{len(a.trials)}</td></tr>")
    add("</tbody></table></div>")

    matrix = c.get("matrix", {})
    if matrix.get("rows"):
        add("<h3>Indication × mechanism — highest phase reached</h3>")
        mechanisms = matrix["mechanisms"]
        short = {m: _short_mechanism(m) for m in mechanisms}
        add('<div class="scroll"><table class="matrix"><thead><tr><th>Indication</th>'
            + "".join(f'<th class="cell">{_esc(short[m])}</th>' for m in mechanisms)
            + "</tr></thead><tbody>")
        for row in matrix["rows"][:18]:
            add(f"<tr><td>{_esc(row['indication'])}</td>"
                + "".join(_phase_cell(row["cells"].get(m, -1)) for m in mechanisms)
                + "</tr>")
        add("</tbody></table></div>")
        renamed = [f"<strong>{_esc(short[m])}</strong> {_esc(m)}"
                   for m in mechanisms if short[m] != m]
        legend = "PC preclinical · 1–3 phase · Appr approved · · none"
        if renamed:
            legend += "<br>" + " &nbsp;·&nbsp; ".join(renamed)
        add(f'<p class="legend">{legend}</p>')

    add("<h2>What the stopped programmes tell us</h2>")
    add(f"<p>{_esc(n.get('failures', '—'))}</p>")
    if f.get("counts"):
        add('<div class="scroll"><table><thead><tr><th>Reason</th><th>Trials</th>'
            "</tr></thead><tbody>")
        for label, count in f["counts"].items():
            add(f"<tr><td>{_esc(label)}</td><td class='cell'>{count}</td></tr>")
        add("</tbody></table></div>")
    for case in [x for x in f.get("cases", []) if x.get("why_stopped")][:8]:
        klass = "sci" if "Science" in case["class"] else ("biz" if "Business" in case["class"] else "")
        evidence = (
            f' · <span class="ev">{_esc(case["evidence"])}</span>' if case.get("evidence") else ""
        )
        add(f'<div class="case {klass}"><q>{_esc(case["why_stopped"])}</q>'
            f'<div class="m"><strong>{_esc(case["class"])}</strong> · '
            f'{_esc(PHASE_LABELS.get(case["phase"], "Unknown"))}'
            f' · {_esc(case.get("sponsor"))} · '
            f'<a href="{_esc(case["url"])}">{_esc(case["nct_id"])}</a>{evidence}</div></div>')

    add("<h2>Whitespace screen</h2>")
    add(f"<p>{_esc(n.get('whitespace', '—'))}</p>")
    if landscape.whitespace:
        add('<div class="scroll"><table><thead><tr><th>Disease</th>'
            "<th>Association</th><th>Genetic evidence</th><th>Highest phase</th>"
            "</tr></thead><tbody>")
        for row in landscape.whitespace[:12]:
            add(f"<tr><td>{_esc(row['disease'])}</td>"
                f"<td class='cell'>{_esc(row['association_score'])}</td>"
                f"<td class='cell'>{_esc(row['genetic_score'])}</td>"
                f"<td class='cell'>{_esc(row['highest_phase'])}</td></tr>")
        add("</tbody></table></div>")

    lic = landscape.licensing or {}
    if lic.get("assets"):
        add("<h2>Availability and licensing</h2>")
        add(f"<p>{_esc(n.get('licensing', '—'))}</p>")
        add('<div class="scroll"><table><thead><tr><th>Programme</th><th>Holder</th>'
            "<th>Scale</th><th>Phase</th><th>Status</th></tr></thead><tbody>")
        for row in lic["assets"]:
            add(f"<tr><td><strong>{_esc(row['asset'])}</strong></td>"
                f"<td class='who'>{_esc(row['sponsor'])}</td>"
                f"<td class='who'>{_esc(row['sponsor_scale'])}</td>"
                f"<td>{_esc(row['phase_label'])}</td>"
                f"<td>{'Active' if row['is_active'] else 'All trials stopped'}"
                "</td></tr>")
        add("</tbody></table></div>")
        for row in lic["assets"]:
            for signal in row["signals"]:
                add(f'<div class="case"><q>{_esc(row["asset"])} — '
                    f'{_esc(signal["headline"])}</q>'
                    f'<div class="m">{_esc(signal["evidence"])}</div></div>')
        add('<p class="legend">Signals are rules over public trial and sponsor data, '
            "not knowledge of any agreement, and nothing here is scored.</p>")

    if landscape.deals:
        add("<h2>Deal comparables</h2>")
        add('<div class="scroll"><table><thead><tr><th>Date</th><th>Acquirer</th>'
            "<th>Asset</th><th>Stage</th><th>Upfront $m</th><th>Total $m</th>"
            "</tr></thead><tbody>")
        for d in landscape.deals:
            add(f"<tr><td>{_esc(d.date)}</td><td>{_esc(d.acquirer)}</td>"
                f"<td>{_esc(d.asset)}</td><td>{_esc(d.stage_at_deal)}</td>"
                f"<td class='cell'>{_esc(d.upfront_usd_m)}</td>"
                f"<td class='cell'>{_esc(d.total_usd_m)}</td></tr>")
        add("</tbody></table></div>")
        add('<p class="m"><em>Hand-curated — no free deal database exists.</em></p>')

    add("<h2>What this cannot see</h2>")
    add(f"<p>{_esc(n.get('risks', '—'))}</p>")

    weights = ", ".join(f"{k} {v:g}" for k, v in (c.get("weights_used") or {}).items())
    bands = ", ".join(
        f"{b['verdict']} ≥ {b['from']:g}" for b in c.get("bands_used", [])
    )
    add('<div class="method" id="method">')
    add(f"<strong>Method.</strong> Phase weights: {_esc(weights)}. "
        f"Density bands: {_esc(bands)}. "
        f"Narrative source: {_esc(n.get('_source', 'template'))}.<br>")
    add("<strong>Data.</strong> Open Targets Platform (CC0) · ChEMBL (CC BY-SA 3.0) · "
        "ClinicalTrials.gov (US Government public domain). "
        "Phase-weighted density and the band thresholds are this tool's own convention, "
        "documented in ARCHITECTURE.md — they are a stated assumption, not a measurement.")
    add("</div></div>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Index across several targets
# ---------------------------------------------------------------------------


def to_index(entries: list[tuple[Any, str]], title: str = "Target landscapes") -> str:
    """One page comparing several targets.

    Built for two jobs. First, calibration: the density bands are only
    meaningful relative to each other, and a column of scores across a spread
    of targets is the only way to see whether the thresholds sit anywhere
    sensible. Second, demonstration: a single memo shows the output, a row of
    contrasting targets shows the judgement.

    ``entries`` is a list of (Landscape, relative link).
    """
    rows = sorted(entries, key=lambda e: -(e[0].crowding.get("weighted_score") or 0))
    out: list[str] = []
    add = out.append

    add(f"<title>{_esc(title)}</title>")
    add(_FONTS)
    add(f"<style>{_CSS}{_INDEX_CSS}</style>")
    add('<div class="wrap">')
    add("<header>")
    add(f"<h1>{_esc(title)}</h1>")
    add(f'<p class="sub">{len(rows)} targets<span class="dotsep">·</span>'
        "ranked by phase-weighted competitive density</p>")
    add("</header>")

    add("<h2>Comparison</h2>")
    add('<div class="scroll"><table><thead><tr>'
        "<th>Target</th><th>Verdict</th><th>Density</th><th>Active</th>"
        "<th>Lead</th><th>Mechanisms</th><th>Sponsors</th><th>Top whitespace</th>"
        "</tr></thead><tbody>")
    for landscape, link in rows:
        c = landscape.crowding
        whitespace = landscape.whitespace[0]["disease"] if landscape.whitespace else ""
        add(f'<tr><td><a href="{_esc(link)}"><strong>{_esc(landscape.target.symbol)}</strong></a>'
            f'<div class="who sm">{_esc(landscape.target.name)}</div></td>'
            f'<td><span class="verdict v-{_esc(str(c.get("verdict", "")).lower())}">'
            f'{_esc(c.get("verdict"))}</span></td>'
            f'<td class="num">{_esc(c.get("weighted_score"))}</td>'
            f'<td class="num">{_esc(c.get("n_active"))}</td>'
            f'<td>{_esc(c.get("lead_phase"))}</td>'
            f'<td class="num">{_esc(c.get("n_mechanism_classes"))}</td>'
            f'<td class="num">{_esc(c.get("n_sponsors"))}</td>'
            f'<td class="who">{_esc(whitespace)}</td></tr>')
    add("</tbody></table></div>")

    # A density scale only means something if you can see where each target
    # falls on it, so draw the bands rather than only listing the thresholds.
    scores = [(ls.target.symbol, ls.crowding.get("weighted_score") or 0) for ls, _ in rows]
    top = max([s for _, s in scores] + [1.0])
    bands = rows[0][0].crowding.get("bands_used", []) if rows else []
    add("<h2>Where they fall</h2>")
    add('<div class="scale">')
    for symbol, score in sorted(scores, key=lambda s: s[1]):
        width = max(1.5, 100.0 * score / (top * 1.08))
        add(f'<div class="bar"><div class="bl">{_esc(symbol)}</div>'
            f'<div class="bt"><div class="bf" style="width:{width:.1f}%"></div></div>'
            f'<div class="bv">{score:g}</div></div>')
    add("</div>")
    if bands:
        add('<p class="legend">Band thresholds: '
            + " &nbsp;·&nbsp; ".join(f"{_esc(b['verdict'])} ≥ {b['from']:g}" for b in bands)
            + "</p>")

    add('<div class="method">')
    add("<strong>Reading this.</strong> Density is a phase-weighted count of active "
        "programmes, not a measurement — the band thresholds are this tool's own "
        "convention. The comparison is the point: the score is only interpretable "
        "next to other targets, which is why this page exists.<br>")
    add("<strong>Data.</strong> Open Targets Platform (CC0) · ChEMBL (CC BY-SA 3.0) · "
        "ClinicalTrials.gov (US Government public domain).")
    add("</div></div>")
    return "\n".join(out)


_INDEX_CSS = """
.sm{font-size:11.5px;margin-top:2px}
.verdict{font-family:var(--mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.08em;padding:3px 9px;border-radius:99px;white-space:nowrap;
  border:1px solid var(--line);color:var(--muted);display:inline-block}
.v-open{background:var(--card)}
.v-emerging{background:color-mix(in srgb,var(--accent) 8%,transparent);color:var(--accent)}
.v-contested{background:color-mix(in srgb,var(--accent) 18%,transparent);color:var(--accent)}
.v-crowded{background:color-mix(in srgb,var(--accent) 30%,transparent);color:var(--fg)}
.v-saturated{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.scale{display:flex;flex-direction:column;gap:7px;margin:18px 0 6px}
.bar{display:grid;grid-template-columns:110px 1fr 52px;align-items:center;gap:12px}
.bl{font-family:var(--mono);font-size:12px;text-align:right;color:var(--muted)}
.bt{height:9px;background:var(--line2);border-radius:99px;overflow:hidden}
.bf{height:100%;background:var(--accent);border-radius:99px}
.bv{font-family:var(--mono);font-size:12px;color:var(--faint);
  font-variant-numeric:tabular-nums}
@media (max-width:560px){.bar{grid-template-columns:80px 1fr 44px;gap:8px}}
"""
