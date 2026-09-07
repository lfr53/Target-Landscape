"""Endpoints, tunables and the scoring constants.

Every constant that feeds a judgement lives here rather than being buried in
the analysis code, so that the assumptions behind a memo can be inspected and
argued with in one place. That is the difference between a heuristic and a
black box.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

OPENTARGETS_GRAPHQL = os.environ.get(
    "OPENTARGETS_GRAPHQL", "https://api.platform.opentargets.org/api/v4/graphql"
)
CHEMBL_BASE = os.environ.get("CHEMBL_BASE", "https://www.ebi.ac.uk/chembl/api/data")
CTGOV_BASE = os.environ.get("CTGOV_BASE", "https://clinicaltrials.gov/api/v2")

# ---------------------------------------------------------------------------
# HTTP behaviour
# ---------------------------------------------------------------------------

CACHE_DIR = os.environ.get("LANDSCAPE_CACHE", os.path.expanduser("~/.cache/target-landscape"))
REQUEST_TIMEOUT = 45
MAX_RETRIES = 4
RETRY_BACKOFF = 1.5
USER_AGENT = "target-landscape/0.1 (research tool; contact: set LANDSCAPE_CONTACT)"

# ChEMBL and ClinicalTrials.gov both paginate; these bound a single run.
MAX_TRIALS = 400
MAX_KNOWN_DRUGS = 500
MAX_ASSOCIATIONS = 60

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

# Weight an asset by how far it has come. A Phase 3 competitor is not "one
# competitor" in the same sense a Phase 1 competitor is, and a flat count is
# the single most common way a landscape slide misleads its reader.
PHASE_WEIGHTS = {4: 5.0, 3: 3.0, 2: 1.5, 1: 0.75, 0: 0.25, -1: 0.25}

# Crowding verdict thresholds, applied to the phase-weighted score.
# Calibrated by hand against a reference set of targets spanning the range
# (see ARCHITECTURE.md § Calibration) — they are a convention, not a
# measurement, and the memo says so.
CROWDING_BANDS = [
    (0.0, "Open"),
    (2.0, "Emerging"),
    (8.0, "Contested"),
    (20.0, "Crowded"),
    (45.0, "Saturated"),
]

# A disease counts as whitespace when the biology is well supported but
# nobody has taken an asset into the clinic for it.
WHITESPACE_MIN_ASSOCIATION = 0.35
WHITESPACE_MIN_GENETIC = 0.05
WHITESPACE_MAX_PHASE = 0  # nothing at Phase 1 or beyond

# Trial statuses that mean the programme stopped rather than finished.
STOPPED_STATUSES = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}
ACTIVE_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
    "AVAILABLE",
}

# ---------------------------------------------------------------------------
# LLM layer (optional)
# ---------------------------------------------------------------------------

ANTHROPIC_MODEL = os.environ.get("LANDSCAPE_MODEL", "claude-sonnet-4-5")
LLM_ENABLED_DEFAULT = bool(os.environ.get("ANTHROPIC_API_KEY"))
LLM_MAX_TOKENS = 4000
