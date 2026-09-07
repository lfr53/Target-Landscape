"""The mechanism figure, drawn from the data rather than from memory.

A target page needs a picture. Every investor memo has one, every scientist
looks for one first, and prose describing where a protein sits and how it is
being drugged is much harder to read than a diagram saying the same thing.

The obvious implementation — hand-draw a figure per target — does not survive
contact with the requirement that all 28,000 indexed targets work. So the
figure is generated, from three facts the pipeline already holds:

  * **Where the protein is.** UniProt subcellular location, reduced to the
    only distinction a drug modality cares about: outside the cell, in the
    membrane, or inside.
  * **What it is.** The Open Targets protein-family classification, which
    decides whether the glyph is a receptor spanning the membrane, a secreted
    ligand, or an intracellular enzyme.
  * **How the field is attacking it.** One arrow per mechanism class actually
    present in the asset table, labelled with how many programmes take that
    approach and how far the furthest has come.

That third element is what makes this worth drawing rather than copying from
a review. A textbook figure shows the biology. This one shows the biology
*and the competitive structure on top of it* — where the field has attacked,
how hard, and where the protein has been left alone. On a crowded target the
arrows pile onto one side; on an open one the picture is visibly empty, which
is the fastest way to communicate whitespace that this tool has.

The figure is honest about being schematic. It does not draw pathways it has
not verified, it never invents an interaction partner, and when the location
is unannotated it says so on the canvas instead of placing the protein
somewhere plausible.

Output is inline SVG with no external references, sized in a viewBox so it
scales, and coloured through CSS custom properties so it works in both
themes.
"""

from __future__ import annotations

import html
from typing import Any, Optional

from ..models import PHASE_LABELS, Landscape
from ..reference.modalities import compartment

WIDTH = 720
MIN_HEIGHT = 250
TOP_MARGIN = 58
BOTTOM_MARGIN = 58
# Room for a label above each arrow and a detail line below it, plus air.
ARROW_GAP = 72
MEMBRANE_H = 26

# The canvas is two columns: text on the left, lines on the right. They do not
# overlap, because converging lines drawn across a block of labels cross the
# text of every row below them — which looked, in the first version of this
# figure, exactly like strikethrough.
TEXT_X = 24
LINE_X = 372
TARGET_X = 596
# Longest detail string the text column can hold at the mono size used.
DETAIL_CHARS = 52

# At most this many intervention arrows; beyond it the picture stops being
# readable and the count moves into a "+n more" label.
MAX_ARROWS = 4


def _esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def _place(comp: dict[str, Any], target_class: list[str]) -> dict[str, Any]:
    """Decide the glyph and where on the canvas it goes."""
    families = " ".join(target_class).lower()
    if comp.get("surface"):
        kind = "receptor" if "receptor" in families or not families else "membrane"
        return {"kind": kind, "where": "in the plasma membrane"}
    if comp.get("secreted"):
        return {"kind": "ligand", "where": "secreted into the extracellular space"}
    if comp.get("intracellular"):
        nuclear = any("nucle" in (loc or "").lower() for loc in comp.get("locations") or [])
        if nuclear:
            return {"kind": "nuclear", "where": "in the nucleus"}
        return {"kind": "cytosolic", "where": "in the cytoplasm"}
    return {"kind": "unknown", "where": "of unannotated location"}


def _interventions(landscape: Landscape) -> list[dict[str, Any]]:
    """One row per mechanism class in the asset table, most advanced first."""
    by_class: dict[str, dict[str, Any]] = {}
    for asset in landscape.assets:
        label = asset.mechanism_class or "Unclassified"
        row = by_class.setdefault(label, {"label": label, "n": 0, "max_phase": -1, "modalities": set()})
        row["n"] += 1
        row["max_phase"] = max(row["max_phase"], asset.max_phase)
        if asset.modality:
            row["modalities"].add(asset.modality)
    rows = sorted(by_class.values(), key=lambda r: (-r["max_phase"], -r["n"], r["label"]))
    for row in rows:
        row["modalities"] = sorted(row["modalities"])
        row["phase_label"] = PHASE_LABELS.get(row["max_phase"], "Unknown")
    return rows


def _target_glyph(kind: str, symbol: str, y: int) -> str:
    """The protein itself. Shape carries the meaning, so it is not decorative."""
    label = _esc(symbol)
    if kind in {"receptor", "membrane"}:
        # Spanning the bilayer, with an extracellular head to bind.
        return (
            f'<g class="tl-target">'
            f'<rect x="{TARGET_X - 22}" y="{y - 26}" width="44" height="64" rx="11" '
            f'class="tl-protein"/>'
            f'<circle cx="{TARGET_X}" cy="{y - 40}" r="26" class="tl-protein"/>'
            f'<text x="{TARGET_X}" y="{y - 35}" class="tl-protein-label">{label}</text>'
            f"</g>"
        )
    if kind == "ligand":
        return (
            f'<g class="tl-target">'
            f'<ellipse cx="{TARGET_X}" cy="{y}" rx="40" ry="26" class="tl-protein"/>'
            f'<text x="{TARGET_X}" y="{y + 5}" class="tl-protein-label">{label}</text>'
            f"</g>"
        )
    # Intracellular: enzyme or nuclear factor.
    return (
        f'<g class="tl-target">'
        f'<rect x="{TARGET_X - 44}" y="{y - 24}" width="88" height="48" rx="14" class="tl-protein"/>'
        f'<text x="{TARGET_X}" y="{y + 5}" class="tl-protein-label">{label}</text>'
        f"</g>"
    )


def _arrows(rows: list[dict[str, Any]], target_y: int, target_x: int, height: int) -> str:
    """Intervention arrows, converging on the target from the left.

    Arrow *weight* encodes the furthest phase reached by that mechanism class,
    so a Phase 3 approach reads as heavier than a preclinical one without the
    reader parsing a number. That is the whole reason to draw this rather than
    print a table.

    The lines converge on the protein rather than running parallel into it,
    because on a contested target the convergence is the point: four arrows
    meeting at one glyph is what crowding looks like.
    """
    if not rows:
        return (
            f'<text x="{TEXT_X}" y="{target_y}" class="tl-empty">Nothing has been '
            f"recorded against this target.</text>"
        )
    shown = rows[:MAX_ARROWS]
    band = (len(shown) - 1) * ARROW_GAP
    top = max(TOP_MARGIN, min(height - BOTTOM_MARGIN - band, target_y - band // 2))
    parts: list[str] = []
    for i, row in enumerate(shown):
        y = top + i * ARROW_GAP
        weight = {4: 5, 3: 4, 2: 3, 1: 2}.get(row["max_phase"], 1.5)
        modality = row["modalities"][0] if row["modalities"] else ""
        detail = f"{row['n']} asset{'s' if row['n'] != 1 else ''} · {row['phase_label']}"
        if modality and modality != "Other / unclassified":
            detail += f" · {modality}"
        if len(detail) > DETAIL_CHARS:
            detail = detail[: DETAIL_CHARS - 1].rstrip(" ·") + "…"
        parts.append(
            f'<g class="tl-arrow">'
            f'<line x1="{LINE_X}" y1="{y}" x2="{target_x - 58}" y2="{target_y}" '
            f'stroke-width="{weight}" marker-end="url(#tl-head)"/>'
            f'<text x="{TEXT_X}" y="{y - 5}" class="tl-arrow-label">{_esc(row["label"])}</text>'
            f'<text x="{TEXT_X}" y="{y + 16}" class="tl-arrow-detail">{_esc(detail)}</text>'
            f"</g>"
        )
    if len(rows) > MAX_ARROWS:
        n = len(rows) - MAX_ARROWS
        parts.append(
            f'<text x="{TEXT_X}" y="{height - 14}" class="tl-arrow-detail">'
            f"+{n} further mechanism class{'es' if n != 1 else ''} below</text>"
        )
    return "".join(parts)


def build(landscape: Landscape, comp: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Render the figure for one target.

    The canvas height is computed from how many arrows there are rather than
    fixed, because a target with one mechanism class and a target with four
    need different amounts of room and a fixed canvas gives one of them a
    third of a page of white space.
    """
    target = landscape.target
    comp = comp or compartment(target.locations)
    placement = _place(comp, target.target_class)
    rows = _interventions(landscape)

    n_arrows = min(len(rows), MAX_ARROWS)
    height = max(
        MIN_HEIGHT,
        TOP_MARGIN + max(0, n_arrows - 1) * ARROW_GAP + BOTTOM_MARGIN
        + (24 if len(rows) > MAX_ARROWS else 0),
    )
    # The protein sits in the middle of whatever canvas that produced, except
    # on the membrane — where the band's position is the meaning, not a layout
    # choice.
    surface = placement["kind"] in {"receptor", "membrane"}
    membrane_y = int(height * 0.42)
    target_y = membrane_y if surface else int(height * 0.5)

    title = f"How {target.symbol} is being drugged"
    desc = (
        f"{target.symbol} is {placement['where']}. "
        + (
            f"{len(rows)} mechanism {'class is' if len(rows) == 1 else 'classes are'} "
            f"represented in the asset table, the most advanced reaching "
            f"{rows[0]['phase_label']}."
            if rows
            else "No programme has been recorded against it."
        )
    )

    # The membrane is drawn only when the target is actually annotated at or
    # outside it. Drawing a bilayer around a protein whose location is unknown
    # would be inventing the one fact the figure exists to show.
    zones = ""
    if surface or comp.get("secreted"):
        zones = (
            f'<rect x="0" y="{membrane_y - MEMBRANE_H // 2}" width="{WIDTH}" '
            f'height="{MEMBRANE_H}" class="tl-membrane"/>'
            f'<text x="{WIDTH - 14}" y="{membrane_y - MEMBRANE_H // 2 - 10}" '
            f'class="tl-zone" text-anchor="end">Outside the cell</text>'
            f'<text x="{WIDTH - 14}" y="{membrane_y + MEMBRANE_H // 2 + 20}" '
            f'class="tl-zone" text-anchor="end">Inside the cell</text>'
        )
    elif placement["kind"] in {"cytosolic", "nuclear"}:
        zones = (
            f'<rect x="{WIDTH * 0.3:.0f}" y="18" width="{WIDTH * 0.7:.0f}" '
            f'height="{height - 36}" rx="26" class="tl-cell"/>'
            f'<text x="{WIDTH - 14}" y="38" class="tl-zone" text-anchor="end">'
            f'{"Nucleus" if placement["kind"] == "nuclear" else "Inside the cell"}</text>'
        )

    caveat = (
        f'<text x="{WIDTH - 14}" y="{height - 14}" class="tl-caveat" text-anchor="end">'
        f"location not annotated</text>"
        if placement["kind"] == "unknown"
        else ""
    )

    svg = (
        f'<svg viewBox="0 0 {WIDTH} {height}" class="tl-diagram" role="img" '
        f'aria-labelledby="tl-diagram-title tl-diagram-desc" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<title id="tl-diagram-title">{_esc(title)}</title>'
        f'<desc id="tl-diagram-desc">{_esc(desc)}</desc>'
        f"<defs>"
        f'<marker id="tl-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" class="tl-arrowhead"/></marker>'
        f"</defs>"
        f"{zones}"
        f"{_arrows(rows, target_y, TARGET_X, height)}"
        f"{_target_glyph(placement['kind'], target.symbol, target_y)}"
        f"{caveat}"
        f"</svg>"
    )

    return {
        "svg": svg,
        "title": title,
        "caption": desc,
        "placement": placement["where"],
        "target_class": target.target_class,
        "interventions": rows,
        "note": (
            "Generated from the target's annotated location, its protein family, and the "
            "mechanism classes present in the asset table. Arrow weight is the furthest "
            "phase that approach has reached. It is a schematic of how the target is "
            "being drugged — not a pathway map, and it draws no interaction it has not "
            "read from the data."
        ),
    }
