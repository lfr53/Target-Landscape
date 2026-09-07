"""Core data model.

One rule runs through this file: every fact carries its provenance. An asset
row that cannot name the source it came from is not allowed into the table,
because the whole point of the tool is that a BD analyst can be challenged on
any number in the memo and answer it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------

# Development phase, normalised to a single integer scale so that assets from
# ChEMBL (max_phase, float) and ClinicalTrials.gov (phases[], strings) can be
# compared. -1 means "we saw the asset but could not establish a phase".
PHASE_LABELS = {
    -1: "Unknown",
    0: "Preclinical",
    1: "Phase 1",
    2: "Phase 2",
    3: "Phase 3",
    4: "Approved",
}

# Modality drives almost every downstream judgement (competitive threat, IP
# position, CMC risk), so it is a first-class field rather than free text.
MODALITIES = [
    "Monoclonal antibody",
    "Bispecific antibody",
    "Antibody-drug conjugate",
    "Fc-fusion / ligand trap",
    "Cell therapy (CAR-T)",
    "Small molecule",
    "Oligonucleotide",
    "Peptide",
    "Vaccine",
    "Other / unclassified",
]

# Why a programme stopped. The split that matters commercially is
# science-driven vs business-driven: five terminated trials tell you nothing
# until you know which kind they were.
FAILURE_CLASSES = {
    "efficacy": "Science — efficacy",
    "safety": "Science — safety / tolerability",
    "pk_pd": "Science — PK/PD or biomarker",
    "cmc": "Manufacturing — supply or product quality",
    "recruitment": "Operational — recruitment",
    "operational": "Operational — other",
    "business": "Business — strategic / portfolio",
    "funding": "Business — funding / company",
    "regulatory": "Regulatory",
    "covid": "External — COVID-19",
    "unknown": "Not stated",
}

SCIENCE_CLASSES = {"efficacy", "safety", "pk_pd"}
BUSINESS_CLASSES = {"business", "funding"}
# Can the material be made at all? A separate question from the science and
# from the sponsor's appetite: a programme stopped because a batch failed
# comparability tells a buyer something specific, and it used to be filed
# under "operational" beside slow recruitment.
CMC_CLASSES = {"cmc"}


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


@dataclass
class Provenance:
    """Where a single fact came from."""

    source: str  # "opentargets" | "chembl" | "ctgov" | "manual"
    identifier: str  # ENSG…, CHEMBL…, NCT…, or a citation key
    url: Optional[str] = None
    retrieved: Optional[str] = None  # ISO date

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Target:
    ensembl_id: str
    symbol: str
    name: str = ""
    biotype: str = ""
    function: str = ""
    synonyms: list[str] = field(default_factory=list)
    # Open Targets tractability buckets, e.g. {"SM": ["Predicted tractable"],
    # "AB": ["UniProt loc high conf"]}. Kept raw because the bucket names are
    # the evidence — collapsing them to a score would hide the reasoning.
    tractability: dict[str, list[str]] = field(default_factory=dict)
    # UniProt subcellular locations and the Open Targets protein-family
    # classification. These decide which modalities are even physically
    # available against the target — an antibody cannot reach a nuclear
    # protein, a degrader cannot reach a secreted one — so they drive the
    # modality-fit read rather than being decoration.
    locations: list[str] = field(default_factory=list)
    # How the protein sits in a membrane, kept apart from where it sits. A
    # single-pass type I topology is architecture; listing it beside "Cell
    # membrane" as though it were a second address is what made the molecule
    # card read "Cell membrane, Single-pass type I membrane protein".
    topology: list[str] = field(default_factory=list)
    target_class: list[str] = field(default_factory=list)
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = [p.to_dict() for p in self.provenance]
        return d


@dataclass
class Trial:
    nct_id: str
    title: str = ""
    status: str = ""  # RECRUITING, TERMINATED, COMPLETED, …
    why_stopped: str = ""
    phase: int = -1
    sponsor: str = ""
    sponsor_class: str = ""  # INDUSTRY | NIH | OTHER
    conditions: list[str] = field(default_factory=list)
    interventions: list[str] = field(default_factory=list)
    # The sponsor's own one-paragraph description, truncated. Kept for one
    # reason: ClinicalTrials.gov's intervention search matches against text we
    # do not otherwise store, so without it a swept trial cannot be checked
    # against the target it was supposedly found for. Truncated because only
    # the opening matters -- a summary names its drug and its target in the
    # first sentence or not at all -- and 400 trials of full prose is a
    # megabyte the page never shows.
    brief_summary: str = ""
    countries: list[str] = field(default_factory=list)
    enrollment: Optional[int] = None
    start_date: str = ""
    completion_date: str = ""
    # Design fields. These are what decide whether a result, when it comes,
    # will mean anything: a single-arm open-label trial reading out a
    # biomarker cannot demonstrate efficacy however positive it is, and an
    # investor looking at a Phase 2 needs to know that before the data lands,
    # not after.
    allocation: str = ""  # RANDOMIZED | NON_RANDOMIZED | NA
    masking: str = ""  # NONE | SINGLE | DOUBLE | TRIPLE | QUADRUPLE
    intervention_model: str = ""  # PARALLEL | SINGLE_GROUP | CROSSOVER …
    primary_purpose: str = ""  # TREATMENT | PREVENTION | BASIC_SCIENCE …
    primary_outcomes: list[str] = field(default_factory=list)
    completion_date_type: str = ""  # ACTUAL | ESTIMATED
    # Filled by analysis.failures
    failure_class: str = ""
    failure_rationale: str = ""
    # Filled by analysis.readouts
    endpoint_class: str = ""
    evidence_level: str = ""
    evidence_note: str = ""

    @property
    def url(self) -> str:
        return f"https://clinicaltrials.gov/study/{self.nct_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Asset:
    """A drug programme against the target."""

    name: str
    sponsor: str = ""
    modality: str = "Other / unclassified"
    action_type: str = ""  # INHIBITOR, ANTAGONIST, AGONIST, …
    mechanism_text: str = ""  # verbatim MoA string from source
    mechanism_class: str = ""  # assigned by analysis.mechanism
    max_phase: int = -1
    indications: list[str] = field(default_factory=list)
    # The highest phase this asset reached *in* each indication, keyed by the
    # canonical indication name. Filled by analysis.crowding so that the page
    # does not have to guess: an asset in Phase 3 for one disease is not in
    # Phase 3 for all of them, and using the overall maximum is the standard
    # way an indication grid misleads.
    indication_phase: dict[str, int] = field(default_factory=dict)
    trials: list[str] = field(default_factory=list)  # NCT ids
    chembl_id: str = ""
    drug_id: str = ""  # Open Targets drug id
    synonyms: list[str] = field(default_factory=list)
    first_approval: Optional[int] = None
    withdrawn: bool = False
    is_active: bool = True  # False once every trial is terminated/withdrawn
    # The sponsor registered the trial without naming the molecule, so this row
    # is "Anti-PD-1 monoclonal antibody" or "BCMA CAR-T" rather than a name.
    # The programme is real and belongs in the table; what is missing is its
    # name, not its mechanism, and saying so is the difference between an
    # honest gap and a row that reads like a classification failure.
    named_by_class: bool = False
    provenance: list[Provenance] = field(default_factory=list)

    @property
    def phase_label(self) -> str:
        return PHASE_LABELS.get(self.max_phase, "Unknown")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = [p.to_dict() for p in self.provenance]
        d["phase_label"] = self.phase_label
        return d


@dataclass
class DiseaseAssociation:
    """Open Targets target–disease association, used for whitespace analysis."""

    disease_id: str
    name: str
    score: float
    genetic_score: float = 0.0
    n_assets: int = 0  # filled in during analysis
    highest_phase: int = -1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Deal:
    """Licensing / M&A comparable.

    There is no free, redistributable deal database, so this is populated from
    a CSV the user maintains by hand. Being explicit about that is better than
    a section that silently returns nothing.
    """

    date: str
    acquirer: str
    target_company: str
    asset: str
    mechanism: str = ""
    # licence | acquisition. The distinction decides whether a figure belongs
    # in a median: an acquisition price buys a company — its platform, its
    # cash, its other programmes — and averaging one against asset upfronts
    # produces a "typical Phase 3 upfront" that no Phase 3 asset ever cost.
    # Acquisitions are still shown; they are simply not averaged.
    deal_type: str = "licence"
    stage_at_deal: str = ""
    upfront_usd_m: Optional[float] = None
    total_usd_m: Optional[float] = None
    territory: str = ""
    source_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Landscape:
    """Everything the renderer needs."""

    target: Target
    assets: list[Asset] = field(default_factory=list)
    trials: list[Trial] = field(default_factory=list)
    associations: list[DiseaseAssociation] = field(default_factory=list)
    deals: list[Deal] = field(default_factory=list)
    # Filled by the analysis layer
    mechanism_clusters: dict[str, list[str]] = field(default_factory=dict)
    crowding: dict[str, Any] = field(default_factory=dict)
    failures: dict[str, Any] = field(default_factory=dict)
    whitespace: list[dict[str, Any]] = field(default_factory=list)
    licensing: dict[str, Any] = field(default_factory=dict)
    # Added for the investor read. These are computed in full and displayed in
    # summary — the engine is thick so that the page can be thin.
    precedent: dict[str, Any] = field(default_factory=dict)
    readouts: dict[str, Any] = field(default_factory=dict)
    modalities: list[dict[str, Any]] = field(default_factory=list)
    literature: dict[str, Any] = field(default_factory=dict)
    # UniProt/Swiss-Prot curated annotation and the paragraph assembled from
    # it. The only block on the page that says what the target *is* rather
    # than what is being done to it — curated text with its citations
    # attached, assembled by rule, never generated prose.
    annotation: dict[str, Any] = field(default_factory=dict)
    # The composed header paragraph: UniProt's curated text plus the sentence
    # saying what the target is being drugged for, which is derived from the
    # asset table and so recomputes offline. See analysis/brief.py.
    header: dict[str, Any] = field(default_factory=dict)
    diagram: dict[str, Any] = field(default_factory=dict)
    # Which cascade the target sits on, what that cascade does, and which
    # other targets on it already carry drugs. Hand-maintained in
    # data/pathways.csv with a citation per row, and attached on read like the
    # deal file: the one place the site turns biology into a neighbouring
    # commercial question rather than describing it.
    pathway: dict[str, Any] = field(default_factory=dict)
    feasibility: dict[str, Any] = field(default_factory=dict)
    narrative: dict[str, str] = field(default_factory=dict)
    generated: str = ""
    warnings: list[str] = field(default_factory=list)
    # Provenance notes: how the record was assembled. Distinct from warnings,
    # which say something went wrong. "1 trial did not name this target and
    # was left out" is the filter doing its job; in the warning box it reads
    # as a fault, and a yellow alert on every page teaches the reader to skip
    # the box that matters.
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target.to_dict(),
            "assets": [a.to_dict() for a in self.assets],
            "trials": [t.to_dict() for t in self.trials],
            "associations": [a.to_dict() for a in self.associations],
            "deals": [d.to_dict() for d in self.deals],
            "mechanism_clusters": self.mechanism_clusters,
            "crowding": self.crowding,
            "failures": self.failures,
            "whitespace": self.whitespace,
            "licensing": self.licensing,
            "precedent": self.precedent,
            "readouts": self.readouts,
            "modalities": self.modalities,
            "literature": self.literature,
            "annotation": self.annotation,
            "header": self.header,
            "diagram": self.diagram,
            "pathway": self.pathway,
            "feasibility": self.feasibility,
            "narrative": self.narrative,
            "generated": self.generated,
            "warnings": self.warnings,
            "notes": self.notes,
        }
