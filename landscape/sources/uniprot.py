"""UniProt: the curated protein annotation behind the header brief.

Every other source in this tool describes what is being *done* to the target.
None of them says what the target *is*. Open Targets carries a one-line
function string and stops there, which is enough for a subtitle and not enough
for a reader who has never met the protein — and on an unfamiliar target that
reader is the normal case, not the edge case.

UniProt/Swiss-Prot is the right source for that gap, for four reasons:

  * **It is written by curators reading the primary literature**, not derived
    by text mining, so a statement in a FUNCTION comment is a statement
    somebody stands behind.
  * **Every statement carries its evidence.** Curated comments cite the
    PubMed records they came from, so the brief on this page can link each
    claim back the same way every other section here does.
  * **It is CC BY 4.0.** The text can be shown, quoted and redistributed with
    attribution, which is not true of the review abstracts it replaces.
  * **It needs no key and no account**, so this stays reproducible offline by
    anyone who clones the repository.

Four comment classes are read, and they answer four different questions:

  ``FUNCTION``  what the protein does
  ``SUBUNIT``   what it does it with — the complex it sits in, which is what
                decides whether there is anything for a blocking antibody to
                block
  ``DOMAIN``    (read from the ``Domain`` features) the architecture, which is
                what a small molecule or a degrader has to find a handle on
  ``DISEASE``   where human genetics has already implicated it, which is the
                strongest prior available before any clinical data exists

No model is involved anywhere in this file. The brief is assembled by rule
from curated text, so the same target produces the same paragraph on every
machine, with or without a network, forever. That is deliberate: a header that
reads differently each time it is generated is not an annotation, it is
decoration.

Licence: UniProt is CC BY 4.0. The accession is carried on the record and the
interface attributes it wherever the text appears.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from ..http import HTTPError, get_json

UNIPROT_API = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_WEB = "https://www.uniprot.org/uniprotkb"

# A field selection keeps the response small, but the names are UniProt's and
# they drift. A wrong one is rejected with 400 for the whole query, which
# would silently cost the brief on every target at once — so the selection is
# an optimisation with a fallback, never a dependency. See ``_search``.
FIELDS = (
    "accession,id,protein_name,gene_names,"
    "cc_function,cc_subunit,ft_domain,cc_disease,lit_pubmed_id"
)

# The brief is a paragraph, not a page. Segments are added in order of how
# much they tell a reader who has never met the protein, and the paragraph
# stops at the first segment that would take it past the ceiling.
#
# The floor is a target, not a guarantee, and deliberately so. Swiss-Prot
# entries vary enormously: a well-worked target carries function, subunit and
# domain annotation and fills the budget on its own, while TNFRSF13C has a
# two-sentence FUNCTION, no SUBUNIT and no Domain features at all, and lands
# nearer eighty words however the segments are ordered. The alternative to a
# short paragraph is a padded one, and padding an annotation block is how it
# stops being an annotation.
WORD_FLOOR = 100
WORD_CEILING = 200

# Curated text carries its citations inline as "(PubMed:12345678)" and marks
# statements inferred from an orthologue as "(By similarity)". Both are
# machinery: the identifiers are lifted out and re-attached as links, and the
# inference marker is kept as a flag rather than left mid-sentence.
_PUBMED_INLINE = re.compile(r"\s*\(PubMed:([0-9,\s:PubMed]+)\)")
_SIMILARITY = re.compile(r"\s*\((?:By similarity|Probable|Potential)\)")
_ECO = re.compile(r"\s*\{ECO:[^}]*\}")
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(“\"'])")


def _clean(text: str) -> tuple[str, list[str]]:
    """Strip inline evidence machinery; return the prose and the PMIDs found."""
    raw = str(text or "")
    pmids: list[str] = []
    for match in _PUBMED_INLINE.finditer(raw):
        pmids.extend(re.findall(r"\d{5,9}", match.group(1)))
    prose = _PUBMED_INLINE.sub("", raw)
    prose = _ECO.sub("", prose)
    prose = _SIMILARITY.sub("", prose)
    prose = re.sub(r"\s+", " ", prose).strip()
    return prose, pmids


def _evidence_pmids(evidences: Any) -> list[str]:
    out: list[str] = []
    for ev in evidences or []:
        if not isinstance(ev, dict):
            continue
        if (ev.get("source") or "").lower() == "pubmed" and ev.get("id"):
            out.append(str(ev["id"]))
    return out


def _texts(comment: dict[str, Any]) -> list[dict[str, Any]]:
    """A comment's texts, cleaned, each with the PubMed records behind it."""
    rows: list[dict[str, Any]] = []
    for item in comment.get("texts") or []:
        if not isinstance(item, dict):
            continue
        prose, inline = _clean(item.get("value"))
        if not prose:
            continue
        pmids = list(dict.fromkeys(_evidence_pmids(item.get("evidences")) + inline))
        rows.append({"text": prose, "pmids": pmids})
    return rows


def _protein_name(record: dict[str, Any]) -> str:
    desc = record.get("proteinDescription") or {}
    recommended = desc.get("recommendedName") or {}
    full = (recommended.get("fullName") or {}).get("value")
    if full:
        return str(full)
    for alt in desc.get("submissionNames") or desc.get("alternativeNames") or []:
        value = ((alt or {}).get("fullName") or {}).get("value")
        if value:
            return str(value)
    return ""


def _gene_names(record: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for gene in record.get("genes") or []:
        primary = (gene.get("geneName") or {}).get("value")
        if primary:
            names.append(str(primary))
        for syn in gene.get("synonyms") or []:
            value = (syn or {}).get("value")
            if value:
                names.append(str(value))
    return names


def _domains(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Domain features, collapsed to one row per distinct domain name.

    A receptor with three cysteine-rich repeats is one architectural fact, not
    three; listing the repeats separately makes a short protein look far more
    complicated than it is.
    """
    counts: dict[str, dict[str, Any]] = {}
    for feature in record.get("features") or []:
        if (feature.get("type") or "").lower() != "domain":
            continue
        name, _ = _clean(feature.get("description"))
        if not name:
            continue
        location = feature.get("location") or {}
        start = ((location.get("start") or {}).get("value"))
        end = ((location.get("end") or {}).get("value"))
        row = counts.setdefault(name, {"name": name, "count": 0, "spans": []})
        row["count"] += 1
        if start is not None and end is not None:
            row["spans"].append([start, end])
    return sorted(counts.values(), key=lambda r: (-r["count"], r["name"]))


def _diseases(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for comment in record.get("comments") or []:
        if (comment.get("commentType") or "").upper() != "DISEASE":
            continue
        disease = comment.get("disease") or {}
        name, _ = _clean(disease.get("diseaseId"))
        if not name:
            continue
        description, inline = _clean(disease.get("description"))
        xref = disease.get("diseaseCrossReference") or {}
        rows.append({
            "name": name,
            "acronym": (disease.get("acronym") or "").strip(),
            "description": description,
            "mim": str(xref.get("id") or "") if (xref.get("database") or "") == "MIM" else "",
            "pmids": list(dict.fromkeys(
                _evidence_pmids(disease.get("evidences")) + inline
            )),
        })
    return rows


def _comment_texts(record: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for comment in record.get("comments") or []:
        if (comment.get("commentType") or "").upper() == kind:
            rows.extend(_texts(comment))
    return rows


def _cited_pmids(record: dict[str, Any]) -> list[str]:
    """PubMed ids on the entry, from whichever shape the response carries.

    The field-selected response and the full entry put the citation list in
    different places. This is a count for the interface, so it reads both and
    returns nothing rather than failing if UniProt adds a third.
    """
    found: list[str] = []
    for xref in record.get("uniProtKBCrossReferences") or []:
        if (xref.get("database") or "").lower() == "pubmed" and xref.get("id"):
            found.append(str(xref["id"]))
    for reference in record.get("references") or []:
        citation = (reference or {}).get("citation") or {}
        for xref in citation.get("citationCrossReferences") or []:
            if (xref.get("database") or "").lower() == "pubmed" and xref.get("id"):
                found.append(str(xref["id"]))
    return list(dict.fromkeys(found))


def _pick(results: list[dict[str, Any]], symbol: str) -> Optional[dict[str, Any]]:
    """The entry whose gene name is the symbol, before any other match.

    ``gene:`` is not an exact-match field — a query for ``TNFRSF13C`` also
    returns family members that merely list it as a synonym. Taking the first
    hit would occasionally put a paralogue's annotation under this target's
    name, which is a worse failure than having no annotation at all.
    """
    if not results:
        return None
    wanted = symbol.strip().upper()
    for record in results:
        for gene in record.get("genes") or []:
            if str((gene.get("geneName") or {}).get("value") or "").upper() == wanted:
                return record
    for record in results:
        if wanted in {n.upper() for n in _gene_names(record)}:
            return record
    return results[0]


def _search(query: str) -> dict[str, Any]:
    """Run the query, and do not let a field name take the block down.

    UniProt rejects an unknown return field with a 400 for the entire query.
    That is a single point of failure over every target at once, and a silent
    one: the caller sees no results and cannot tell a renamed field from a
    gene with no Swiss-Prot entry. So a rejected selection is retried with no
    ``fields`` parameter at all — the full entry carries everything read here
    anyway, and a larger response is a much smaller problem than no brief.
    """
    params = {"query": query, "format": "json", "size": 5}
    try:
        return get_json(UNIPROT_API, {**params, "fields": FIELDS}) or {}
    except HTTPError:
        return get_json(UNIPROT_API, params) or {}


def fetch(symbol: str, aliases: Optional[list[str]] = None) -> dict[str, Any]:
    """Curated annotation for one human gene symbol.

    Returns ``{}`` only when the query succeeded and matched nothing reviewed
    — a real answer about the gene. A transport or query failure raises
    instead, because reporting "no reviewed UniProt entry" for a request that
    never got an answer states something about the protein that the run has no
    evidence for. The pipeline catches the raise and records it as a run
    warning, which is where a broken source belongs.
    """
    query = f"gene:{symbol} AND organism_id:9606 AND reviewed:true"
    payload = _search(query)

    record = _pick((payload or {}).get("results") or [], symbol)
    if not record:
        # A gene with no reviewed human entry is a real answer, not an error:
        # the header says so rather than falling through to an unreviewed one.
        return {}

    accession = str(record.get("primaryAccession") or "")
    citations = _cited_pmids(record)
    return {
        "accession": accession,
        "entry_name": str(record.get("uniProtkbId") or ""),
        "protein_name": _protein_name(record),
        "gene_names": _gene_names(record),
        "function": _comment_texts(record, "FUNCTION"),
        "subunit": _comment_texts(record, "SUBUNIT"),
        "domains": _domains(record),
        "disease": _diseases(record),
        "n_citations": len(citations),
        "url": f"{UNIPROT_WEB}/{accession}" if accession else "",
        "licence": "UniProt Knowledgebase (Swiss-Prot), CC BY 4.0",
    }


# ---------------------------------------------------------------------------
# The brief
# ---------------------------------------------------------------------------


def _sentences(text: str, count: int) -> str:
    """First ``count`` sentences, split at boundaries rather than by matching
    sentence bodies — a full stop inside ``0.62`` is not a sentence end."""
    parts = _SENTENCE.split(str(text or ""))
    return " ".join(parts[:count]).strip()


def _terminated(text: str) -> str:
    """End a sentence that the curator did not."""
    text = (text or "").strip()
    if text and text[-1] not in ".!?":
        return text + "."
    return text


def _words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text) if w])


def _domain_phrase(domains: list[dict[str, Any]]) -> str:
    NUMBER = {1: "a", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
    parts = []
    for row in domains[:3]:
        count = row["count"]
        word = NUMBER.get(count, str(count))
        if count == 1:
            parts.append(f"a {row['name']} domain")
        else:
            parts.append(f"{word} {row['name']} domains")
    if not parts:
        return ""
    if len(parts) == 1:
        listed = parts[0]
    else:
        listed = ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"UniProt annotates {listed}."


def _disease_phrase(symbol: str, diseases: list[dict[str, Any]]) -> str:
    named = []
    for row in diseases[:2]:
        label = row["name"]
        if row["acronym"]:
            label += f" ({row['acronym']})"
        named.append(label)
    if not named:
        return ""
    joined = named[0] if len(named) == 1 else " and ".join(named)
    # Labelled, because an unlabelled disease name in a target header reads as
    # the indication. UniProt's DISEASE comment is the Mendelian disease caused
    # by germline variants in the gene — PDCD1's is an infantile autoimmune
    # syndrome, while PD-1 is drugged in cancer. The two are not the same
    # claim, and a reader who conflates them has been misled by the page.
    #
    # The subject is "variants", which is plural whether one disease is named
    # or two: agreeing the verb with the disease count put "variants is" on
    # every single-disease target, which is most of them.
    return (
        f"Separately, germline variants in {symbol} cause {joined} — genetic "
        "validation of the target, not an indication being pursued against it."
    )


def brief(record: dict[str, Any], symbol: str) -> dict[str, Any]:
    """A 100–200 word paragraph on what this protein is, assembled by rule.

    Segments are added in descending order of what they tell a reader meeting
    the protein for the first time, and the paragraph closes at the first
    segment that would carry it past the ceiling. Nothing is paraphrased: the
    function and subunit sentences are curated text verbatim, and the two
    generated sentences state only what the annotation records.
    """
    if not record:
        return {}

    function = record.get("function") or []
    if not function:
        # Without a FUNCTION comment there is no brief worth printing. Domains
        # and disease links alone describe a protein nobody has said does
        # anything, which reads as evasion rather than as annotation.
        return {}

    segments: list[dict[str, Any]] = []
    used = 0

    def add(kind: str, text: str, pmids: list[str], required: bool = False) -> None:
        nonlocal used
        if not text:
            return
        length = _words(text)
        if not required and used + length > WORD_CEILING:
            return
        segments.append({"kind": kind, "text": text, "pmids": pmids[:4]})
        used += length

    # 1. What it does — curated, verbatim, always present.
    add("function", _sentences(function[0]["text"], 3), function[0]["pmids"], required=True)

    # 2. What it does it with. A receptor whose ligand and adaptor are named is
    #    a receptor with something for a blocking antibody to block; one with
    #    no annotated partner is not.
    subunit = record.get("subunit") or []
    if subunit and used < WORD_CEILING:
        add("subunit", _sentences(subunit[0]["text"], 2), subunit[0]["pmids"])

    # 3. Architecture, which is what a small molecule or a degrader needs a
    #    handle on. Only added while the paragraph is still short.
    if used < WORD_FLOOR + 40:
        add("domain", _domain_phrase(record.get("domains") or []), [])

    # 4. Where human genetics has already implicated it.
    diseases = record.get("disease") or []
    disease_pmids = [p for row in diseases[:2] for p in row["pmids"]][:4]
    add("disease", _disease_phrase(symbol, diseases), disease_pmids)

    # The disease's clinical description is deliberately NOT added. It reads as
    # the target's indication, and on a drug-target page it is not: a paragraph
    # of ADMIO4 symptomatology under PD-1 points a reader away from the reason
    # anyone drugs PD-1. What closes the length gap instead is the therapeutic
    # sentence, derived from the asset table in analysis/brief.py.

    # Curated text does not reliably end in a full stop — UniProt's TNFRSF13C
    # FUNCTION ends "…and the B-cell response" — so joining on a space alone
    # runs one segment into the next mid-sentence.
    text = " ".join(_terminated(s["text"]) for s in segments)
    return {
        "segments": segments,
        "text": text,
        "words": _words(text),
        "accession": record.get("accession", ""),
        "url": record.get("url", ""),
        "attribution": "UniProt/Swiss-Prot curated annotation (CC BY 4.0)",
        "note": (
            "Curated by UniProt from the primary literature, not generated. "
            "Each statement links to the records the curator cited."
        ),
    }


def fetch_brief(symbol: str, aliases: Optional[list[str]] = None) -> dict[str, Any]:
    """The record and the paragraph together — what the pipeline stores."""
    record = fetch(symbol, aliases)
    if not record:
        return {}
    return {**record, "brief": brief(record, symbol)}
