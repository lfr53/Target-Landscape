"""The header: key facts about the target, and nothing more.

This block used to be a paragraph, and the paragraph was wrong for the site.
A target page is read by someone who does not yet know the protein, and what
they need first is a handful of separable facts — what kind of target it is,
what it does, where it sits, what is being developed against it — not a
narrative that has already decided what those facts mean.

Two rules follow from that:

**No conclusions.** Every value here is a count, a name, a location or a
curated sentence. Nothing says which of them matters, because on a new or
thinly covered target — most of the 28,000 — there is no honest answer to
that, and a template with a slot for one will fill it anyway.

**Short.** The detailed mechanism belongs on the Mechanisms tab, where a
reader goes when they want it. It is returned separately here for exactly
that reason.

The curated half comes from UniProt (``sources/uniprot.py``); the development
half is derived from this tool's own asset table, so it recomputes offline.
No model is involved.

One placement decision is load-bearing. UniProt's ``DISEASE`` comment records
the **Mendelian disease caused by germline variants in the gene** — PDCD1's is
an infantile autoimmune syndrome, while PD-1 is drugged to treat cancer. It is
carried as its own labelled fact, never mixed into what the target is being
developed for, and it is withheld entirely when the development picture is not
loaded, because on its own a reader takes it for the indication.
"""

from __future__ import annotations

import re
from typing import Any, Optional


def _words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text or "") if w])


def _terminated(text: str) -> str:
    """End a sentence the curator did not. UniProt's TNFRSF13C FUNCTION ends
    "…and the B-cell response", with no full stop."""
    text = (text or "").strip()
    if text and text[-1] not in ".!?":
        return text + "."
    return text


def _join(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _sentences(text: str, count: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\u201c\"\'])", str(text or ""))
    return " ".join(parts[:count]).strip()


def _display_name(name: str) -> str:
    """INN names arrive shouted from some sources. CEMIPLIMAB mid-sentence
    reads as an error. Single all-capital alphabetic tokens only, so BNT327,
    LM-299 and "BAFFR CAR-T" are left alone."""
    name = (name or "").strip()
    if re.fullmatch(r"[A-Z]{5,}", name):
        return name.capitalize()
    return name


def _trial_count(landscape: Any, indication: str) -> int:
    """How many registered trials name this indication.

    The tie-break that makes the list mean something. On BAFF-R every Phase 3
    row carries the same single asset, so phase and asset count tie and
    alphabetical order decides — which put autoimmune hepatitis ahead of
    Sjogren's disease, the indication the Phase 3 programme is built around.
    """
    key = _normalise(indication)
    if not key:
        return 0
    return sum(
        1 for trial in landscape.trials or []
        if any(key == _normalise(c) for c in trial.conditions or [])
    )


def _top_indications(landscape: Any, limit: int = 3) -> tuple[list[str], int]:
    """The indications with work in them, most advanced first, and how many
    more sit at that same phase."""
    rows = ((landscape.crowding or {}).get("matrix") or {}).get("rows") or []
    if not rows:
        return [], 0
    ranked = sorted(
        rows,
        key=lambda r: (
            -(r.get("max_phase") or -1),
            -_trial_count(landscape, r.get("indication") or ""),
            -(r.get("n_assets") or 0),
            r.get("indication") or "",
        ),
    )
    lead_phase = ranked[0].get("max_phase")
    at_lead = sum(1 for r in ranked if r.get("max_phase") == lead_phase)

    out: list[str] = []
    for row in ranked:
        name = (row.get("indication") or "").strip()
        if name and name not in out:
            out.append(name)
        if len(out) == limit:
            break
    return out, max(0, at_lead - len(out))


def _lead_asset(assets: list) -> Any:
    """The programme a reader would name, not the one that sorts first.

    Assets order by phase then alphabetically, which put cemiplimab ahead of
    nivolumab on the letter C. Among assets at the top phase, the one carrying
    the most registered trials is the one the field is built around.
    """
    top = max((a.max_phase for a in assets), default=-1)
    at_top = [a for a in assets if a.max_phase == top] or list(assets)
    return max(at_top, key=lambda a: (len(a.trials or []), len(a.indications or []),
                                      -len(a.name)))


def _fact(key: str, label: str, value: str, note: str = "",
          pmids: Optional[list[str]] = None) -> dict[str, Any]:
    return {"key": key, "label": label, "value": value, "note": note,
            "pmids": (pmids or [])[:3]}


def _development_fact(landscape: Any) -> Optional[dict[str, Any]]:
    """What is being developed against the target. Counts and names only."""
    assets = landscape.assets or []
    if not assets:
        return _fact(
            "development", "In development",
            "Nothing in the public record",
            "No asset against this target was found in Open Targets, ChEMBL or "
            "ClinicalTrials.gov. Preclinical and undisclosed work is invisible to all "
            "three.",
        )

    lead = _lead_asset(assets)
    indications, remainder = _top_indications(landscape)

    value = ""
    if indications:
        value = _join(indications)
        if remainder > 12:
            value += f" — 3 of {remainder + len(indications)} indications at that phase"
        elif remainder:
            value += f", and {remainder} more at that phase"
    else:
        value = f"{len(assets)} asset{'s' if len(assets) != 1 else ''}, indications not registered"

    note = f"Furthest programme: {_display_name(lead.name)}"
    if lead.sponsor:
        note += f" ({lead.sponsor})"
    note += ", approved" if lead.max_phase >= 4 else f", {lead.phase_label}"
    if lead.mechanism_class:
        # Direction is a fact about the molecule, not a judgement: blocking a
        # receptor and depleting the cells carrying it are different medicines.
        note += f", {lead.mechanism_class}"
    note += "."
    n_classes = len(landscape.mechanism_clusters or {})
    if n_classes > 1:
        note += f" {n_classes} mechanism classes in the table."
    return _fact("development", "In development", value, note)


def facts(landscape: Any, annotation: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """The header list. Each entry stands alone and none ranks the others."""
    annotation = annotation or {}
    curated = (annotation.get("brief") or {}).get("segments") or []
    by_kind = {segment["kind"]: segment for segment in curated}
    target = getattr(landscape, "target", None)

    rows: list[dict[str, Any]] = []

    classes = [c for c in (getattr(target, "target_class", None) or []) if c]
    if classes:
        rows.append(_fact("class", "Target class", _join(classes[:2])))

    if "function" in by_kind:
        # One sentence. The rest of the curated text goes to Mechanisms.
        seg = by_kind["function"]
        rows.append(_fact("function", "Function", _terminated(_sentences(seg["text"], 1)),
                          "", seg.get("pmids")))
    elif getattr(target, "function", ""):
        rows.append(_fact("function", "Function",
                          _terminated(_sentences(target.function, 1)),
                          "Open Targets function line; no reviewed UniProt entry."))

    locations = [l for l in (getattr(target, "locations", None) or []) if l]
    if locations:
        rows.append(_fact("location", "Where it sits", ", ".join(locations[:3]),
                          "Subcellular location, which decides which modalities can "
                          "physically reach it."))

    # Architecture, on its own line. It used to sit inside the location list,
    # where "Cell membrane, Single-pass type I membrane protein" read as two
    # addresses rather than a place and a shape.
    # "Single-pass type I membrane protein" under a row already labelled about
    # membrane architecture repeats itself, and at 320px the card broke the
    # line after the hyphen -- "Single- pass". The label carries the context.
    topology = [
        re.sub(r"\s*membrane protein$", "", t).strip()
        for t in (getattr(target, "topology", None) or []) if t
    ]
    topology = [t for t in topology if t]
    if topology:
        rows.append(_fact("topology", "How it sits", ", ".join(topology[:2]),
                          "Membrane architecture. It constrains where an antibody can "
                          "bind, not where the protein is."))

    domains = (annotation.get("domains") or [])
    if domains:
        listed = ", ".join(
            f"{d['name']}" + (f" ×{d['count']}" if d.get("count", 1) > 1 else "")
            for d in domains[:3]
        )
        rows.append(_fact("domain", "Domains", listed))

    development = _development_fact(landscape) if landscape is not None else None
    if development:
        rows.append(development)

    # Germline disease, on its own line and labelled. Only when the development
    # picture is loaded — alone it reads as the indication.
    if development and "disease" in by_kind:
        diseases = annotation.get("disease") or []
        named = []
        for row in diseases[:2]:
            label = row["name"]
            if row.get("acronym"):
                label += f" ({row['acronym']})"
            named.append(label)
        if named:
            rows.append(_fact(
                "genetics", "Germline variants cause", _join(named),
                "A Mendelian disease caused by variants in this gene. It is not an "
                "indication anyone is developing against the target.",
                [p for d in diseases[:2] for p in d.get("pmids") or []],
            ))
    return rows


def mechanism_note(annotation: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """The full curated description, for the Mechanisms tab.

    Everything the header trims: the rest of the FUNCTION comment, the complex
    the protein sits in, the architecture. A reader who wants the biology goes
    looking for it; a reader deciding whether to keep reading should not have
    to scroll past it.
    """
    annotation = annotation or {}
    curated = (annotation.get("brief") or {}).get("segments") or []
    by_kind = {segment["kind"]: segment for segment in curated}

    parts, pmids = [], []
    for kind in ("function", "subunit"):
        seg = by_kind.get(kind)
        if seg:
            parts.append(_terminated(seg["text"]))
            pmids += seg.get("pmids") or []
    if not parts:
        return {}
    return {
        "text": " ".join(parts),
        "pmids": list(dict.fromkeys(pmids))[:6],
        "accession": annotation.get("accession", ""),
        "url": annotation.get("url", ""),
        "attribution": "UniProt/Swiss-Prot curated annotation (CC BY 4.0)",
    }


def compose(landscape: Any, annotation: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Everything the header and the Mechanisms tab need."""
    annotation = annotation or {}
    rows = facts(landscape, annotation)
    if not rows:
        return {}
    return {
        "facts": rows,
        "mechanism": mechanism_note(annotation),
        "accession": annotation.get("accession", ""),
        "url": annotation.get("url", ""),
        "curated_source": bool((annotation.get("brief") or {}).get("segments")),
        "development_unknown": landscape is None,
        "attribution": "UniProt/Swiss-Prot curated annotation (CC BY 4.0)",
    }
