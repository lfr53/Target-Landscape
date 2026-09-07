"""Optional LLM layer.

The design principle here is the one that makes the tool defensible: **the
model is never the first pass and never the only record.** Rules classify
what rules can classify; the model is handed only the residue, is constrained
to the same controlled vocabulary the rules use, and every assignment it makes
is tagged in the output so a reader can see exactly which rows a model touched
and audit those rows specifically.

The tool runs, and produces a complete memo, with no API key at all. That is
deliberate. A landscape analysis whose numbers change when a model is swapped
is not an analysis.

Three jobs, in descending order of how much they matter:
  1. ``resolve_mechanisms`` — place assets the INN-stem and keyword rules left
     unclassified. Highest value: these are usually the cell therapies and the
     non-Western programmes, i.e. the interesting ones.
  2. ``classify_failures`` — classify ``whyStopped`` text the keyword rules
     missed, with the verbatim sentence quoted back as justification.
  3. ``write_narrative`` — turn the computed tables into memo prose. Prose
     only: the model is explicitly told it may not introduce a fact, a number
     or an asset that is not in the structured input it was given.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from .config import ANTHROPIC_MODEL, LLM_MAX_TOKENS
from .models import FAILURE_CLASSES, MODALITIES, Asset, Trial


class LLMUnavailable(RuntimeError):
    pass


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _client():
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise LLMUnavailable("pip install anthropic") from exc
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LLMUnavailable("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic()


def _complete(system: str, user: str, max_tokens: int = LLM_MAX_TOKENS) -> str:
    response = _client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


_JSON_RE = re.compile(r"\[.*\]|\{.*\}", re.S)


def _parse_json(text: str) -> Any:
    match = _JSON_RE.search(text or "")
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# 1. Mechanism resolution
# ---------------------------------------------------------------------------

_MECHANISM_SYSTEM = """You classify drug assets by modality and mechanism for a \
competitive landscape analysis.

Rules:
- Choose `modality` ONLY from the supplied list. No other value is valid.
- `mechanism_class` must be a short phrase describing what the asset does to \
the target (e.g. "Depleting antibody (ADCC/CDC)", "Blocking antibody", \
"Ligand trap / decoy receptor", "Cell therapy — target-directed CAR").
- Base the answer only on the name, mechanism text, sponsor and trial titles \
supplied. Do not use outside knowledge to invent a mechanism.
- If the evidence does not support a confident call, return \
modality "Other / unclassified" and mechanism_class "Unclassified". Saying \
so is correct behaviour, not failure.
- `confidence` is one of high, medium, low.
- `evidence` quotes the exact substring of the input you relied on.

Return a JSON array only. No prose."""


def resolve_mechanisms(
    assets: list[Asset], trials_by_nct: Optional[dict[str, Trial]] = None
) -> dict[str, dict[str, Any]]:
    """Return {asset.name: {modality, mechanism_class, confidence, evidence}}."""
    if not assets:
        return {}
    trials_by_nct = trials_by_nct or {}

    payload = []
    for asset in assets:
        titles = [
            trials_by_nct[n].title for n in asset.trials[:4] if n in trials_by_nct
        ]
        payload.append(
            {
                "name": asset.name,
                "synonyms": asset.synonyms[:5],
                "sponsor": asset.sponsor,
                "source_modality": asset.modality,
                "action_type": asset.action_type,
                "mechanism_text": asset.mechanism_text,
                "trial_titles": titles,
            }
        )

    user = (
        f"Allowed modality values:\n{json.dumps(MODALITIES, indent=2)}\n\n"
        f"Assets to classify:\n{json.dumps(payload, indent=2)}\n\n"
        'Return: [{"name": ..., "modality": ..., "mechanism_class": ..., '
        '"confidence": ..., "evidence": ...}]'
    )
    parsed = _parse_json(_complete(_MECHANISM_SYSTEM, user))
    if not isinstance(parsed, list):
        return {}

    out: dict[str, dict[str, Any]] = {}
    valid = set(MODALITIES)
    for row in parsed:
        if not isinstance(row, dict) or not row.get("name"):
            continue
        modality = row.get("modality")
        # Reject anything outside the vocabulary rather than passing it
        # through — an unconstrained label would silently break clustering.
        if modality not in valid:
            modality = "Other / unclassified"
        out[row["name"]] = {
            "modality": modality,
            "mechanism_class": row.get("mechanism_class") or "Unclassified",
            "confidence": row.get("confidence", "low"),
            "evidence": row.get("evidence", ""),
        }
    return out


def apply_mechanism_resolutions(
    assets: list[Asset], resolutions: dict[str, dict[str, Any]]
) -> int:
    """Write resolutions back, tagging each one as model-assigned."""
    applied = 0
    for asset in assets:
        resolution = resolutions.get(asset.name)
        if not resolution or resolution.get("confidence") == "low":
            continue
        asset.modality = resolution["modality"]
        asset.mechanism_class = f"{resolution['mechanism_class']} [model]"
        applied += 1
    return applied


# ---------------------------------------------------------------------------
# 2. Failure classification
# ---------------------------------------------------------------------------

_FAILURE_SYSTEM = """You classify why clinical trials were stopped, for a \
competitive landscape analysis.

The distinction that matters: did the programme stop because of the SCIENCE \
(efficacy, safety, PK/PD) or because of the BUSINESS (funding, strategy, \
portfolio priorities) or for OPERATIONAL reasons (recruitment, sites, supply)?

Rules:
- `class` must be one of the supplied keys exactly.
- Classify only from the sponsor's stated reason. Do not speculate about \
unstated reasons; that is what "unknown" is for.
- `evidence` quotes the exact words you relied on.

Return a JSON array only. No prose."""


def classify_failures(trials: list[Trial]) -> dict[str, dict[str, str]]:
    if not trials:
        return {}
    payload = [
        {
            "nct_id": t.nct_id,
            "why_stopped": t.why_stopped,
            "status": t.status,
            "phase": t.phase,
        }
        for t in trials
    ]
    user = (
        f"Allowed classes:\n{json.dumps(FAILURE_CLASSES, indent=2)}\n\n"
        f"Trials:\n{json.dumps(payload, indent=2)}\n\n"
        'Return: [{"nct_id": ..., "class": ..., "evidence": ...}]'
    )
    parsed = _parse_json(_complete(_FAILURE_SYSTEM, user))
    if not isinstance(parsed, list):
        return {}
    out: dict[str, dict[str, str]] = {}
    for row in parsed:
        if not isinstance(row, dict):
            continue
        label = row.get("class")
        if label not in FAILURE_CLASSES:
            continue
        out[row.get("nct_id", "")] = {
            "class": label,
            "evidence": row.get("evidence", ""),
        }
    return out


def apply_failure_classifications(
    trials: list[Trial], classifications: dict[str, dict[str, str]]
) -> int:
    applied = 0
    for trial in trials:
        result = classifications.get(trial.nct_id)
        if not result:
            continue
        trial.failure_class = result["class"]
        trial.failure_rationale = f"{result.get('evidence', '')} [model]"
        applied += 1
    return applied


# ---------------------------------------------------------------------------
# 3. Memo prose
# ---------------------------------------------------------------------------

_NARRATIVE_SYSTEM = """You write the prose sections of a competitive landscape \
memo for a pharmaceutical business development team.

Absolute constraint: every asset, number, phase, sponsor and disease you \
mention must appear in the structured input. You may not add a fact from your \
own knowledge, and you may not round, extrapolate or estimate. If the input \
does not support a claim, do not make it.

Voice: a senior search-and-evaluation analyst writing for a partner who will \
challenge every sentence. Direct, specific, no hedging filler, no marketing \
register. Where the data is thin, say it is thin.

Return a JSON object with exactly these keys, each a string of plain prose \
(no markdown headers):
- "bottom_line": 2-3 sentences. The single most decision-relevant read.
- "competitive": 3-5 sentences on who is where, by mechanism, and what the \
mechanism split implies.
- "failures": 2-4 sentences on what the stopped programmes do and do not tell \
us about the target. Name the science/business split explicitly.
- "whitespace": 2-3 sentences. Treat the whitespace screen as a hypothesis to \
check, not a finding.
- "risks": 3-4 sentences on what would change this read, and what the data \
cannot see."""


def write_narrative(summary: dict[str, Any]) -> dict[str, str]:
    user = (
        "Structured landscape data:\n"
        f"{json.dumps(summary, indent=2, default=str)[:60000]}\n\n"
        "Write the memo sections."
    )
    parsed = _parse_json(_complete(_NARRATIVE_SYSTEM, user, max_tokens=LLM_MAX_TOKENS))
    if not isinstance(parsed, dict):
        return {}
    keys = {"bottom_line", "competitive", "failures", "whitespace", "risks"}
    return {k: str(v) for k, v in parsed.items() if k in keys and v}
