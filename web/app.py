"""HTTP layer.

The engine underneath (``landscape/``) has no web dependencies and no
knowledge that this exists — it is a library that turns a gene symbol into an
analysis. This module is only plumbing: routing, a job runner so a 30-second
live build does not hold a request open, and static file serving.

The one design decision worth stating: **a live build is a job, not a
request.** Building a landscape from scratch means waiting on three external
APIs in sequence and takes 20-40 seconds. Serving that synchronously gives the
user a spinner and no information, and any proxy in front will eventually time
it out. Instead the client starts a job and polls, and the pipeline reports
which stage it is on, so the interface can say "Sweeping ClinicalTrials.gov"
rather than spinning. Same wait, entirely different experience.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from landscape import pipeline, render, store, targets as target_index
from landscape.analysis import showcase as showcase_mod
from landscape.http import HTTPError
from landscape.models import Landscape
from landscape.sources import opentargets as ot_src

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(HERE, "static")

# One live build at a time by default. These are long, API-bound jobs, and a
# public Space that fans out concurrent sweeps is a good way to get rate
# limited by the very sources the tool depends on.
MAX_CONCURRENT_BUILDS = int(os.environ.get("LANDSCAPE_MAX_BUILDS", "2"))
JOB_TTL_SECONDS = 1800

app = FastAPI(
    title="Target Landscape",
    description="Competitive landscape for a drug target, from public data.",
    version="0.2.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# A well-worked target is a big document: PDCD1's payload is 1.85 MB of JSON,
# most of it the 397 trial records and the 1814-row indication matrix that the
# tables need. It compresses to 0.20 MB, because it is repetitive text. Over a
# home connection, or a conference wifi, that is the difference between a page
# that appears and a page that is thinking about it.
app.add_middleware(GZipMiddleware, minimum_size=1024)


# ---------------------------------------------------------------------------
# Job runner
# ---------------------------------------------------------------------------


@dataclass
class Job:
    id: str
    symbol: str
    status: str = "queued"  # queued | running | done | error
    stage: str = ""
    label: str = "Queued"
    index: int = 0
    total: int = len(pipeline.STAGES)
    error: str = ""
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "status": self.status,
            "stage": self.stage,
            "label": self.label,
            "index": self.index,
            "total": self.total,
            "progress": round(self.index / self.total, 3) if self.total else 0.0,
            "error": self.error,
            "elapsed": round(time.time() - self.created, 1),
        }


_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()
_build_slots = threading.Semaphore(MAX_CONCURRENT_BUILDS)


def _reap_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    with _jobs_lock:
        for job_id in [j for j, job in _jobs.items() if job.created < cutoff]:
            _jobs.pop(job_id, None)


def _run_build(job: Job) -> None:
    def on_progress(stage: str, label: str, index: int, total: int) -> None:
        job.stage, job.label, job.index, job.total = stage, label, index, total

    with _build_slots:
        job.status = "running"
        try:
            landscape = pipeline.build(
                job.symbol,
                deals=store.load_deals(job.symbol),
                on_progress=on_progress,
            )
            store.save_cached(landscape)
            job.index = job.total
            job.label = "Done"
            job.status = "done"
        except ValueError as exc:
            job.status, job.error = "error", str(exc)
        except HTTPError as exc:
            job.status = "error"
            message = str(exc)
            # A 400 or a GraphQL error is our query being wrong for the
            # schema the service is now serving — telling the user the API is
            # down sends them to wait for a recovery that will never come.
            if "400" in message or "GraphQL error" in message:
                job.error = (
                    f"A data source rejected the query: {message} "
                    "That means the API changed its schema, not that it is down. "
                    "Run 'python -m landscape doctor' — it names the field and the "
                    "file to fix."
                )
            else:
                job.error = (
                    f"A data source could not be reached: {message} "
                    "The public APIs are occasionally down; try again shortly."
                )
        except Exception as exc:  # noqa: BLE001
            job.status, job.error = "error", f"{type(exc).__name__}: {exc}"


def _start_build(symbol: str) -> Job:
    _reap_jobs()
    with _jobs_lock:
        # Do not start a second build for a target already being built.
        for job in _jobs.values():
            if job.symbol == symbol and job.status in {"queued", "running"}:
                return job
        job = Job(id=uuid.uuid4().hex[:12], symbol=symbol)
        _jobs[job.id] = job
    threading.Thread(target=_run_build, args=(job,), daemon=True).start()
    return job


# ---------------------------------------------------------------------------
# View model
# ---------------------------------------------------------------------------


def _payload(landscape: Landscape, meta: dict[str, Any]) -> dict[str, Any]:
    data = landscape.to_dict()
    data["meta"] = meta
    # Facet values the interface needs for its filter controls. Computing them
    # here keeps the client from having to scan the asset list to discover
    # what the filters should even offer.
    assets = data["assets"]
    data["facets"] = {
        "phases": sorted({a["max_phase"] for a in assets}, reverse=True),
        "modalities": sorted({a["modality"] for a in assets if a["modality"]}),
        "mechanisms": sorted({a["mechanism_class"] for a in assets if a["mechanism_class"]}),
        "sponsors": sorted({a["sponsor"] for a in assets if a["sponsor"]}),
        "indications": sorted({i for a in assets for i in a["indications"]}),
    }
    return data


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


_SHOWCASE_CACHE: dict[str, Any] = {}


def _showcase() -> dict[str, Any]:
    """The landing page's worked example, computed once.

    A first-time visitor cannot picture a target page from a description, so
    the landing page shows the six answers for a real target with that
    target's real numbers. Cached because it means loading a full landscape,
    and the answer only changes when the curated tier is rebuilt.
    """
    symbol = showcase_mod.pick(store.curated_symbols())
    if not symbol:
        return {}
    if symbol in _SHOWCASE_CACHE:
        return _SHOWCASE_CACHE[symbol]
    loaded = store.load(symbol)
    if not loaded:
        return {}
    landscape, _meta = loaded
    result = {
        "symbol": symbol,
        "name": landscape.target.name,
        "tiles": showcase_mod.tiles(landscape),
    }
    _SHOWCASE_CACHE[symbol] = result
    return result


@app.get("/api/library")
def api_library() -> dict[str, Any]:
    """The curated tier: what is available instantly, and the worked example."""
    rows = store.index()
    # No vernacular label here. HGNC synonym lists carry truncated entries —
    # "BCM" for BCMA, "B7-H" for PD-L1, "Bp35" for CD20 — and a wrong name on
    # the front page is worse than an unglamorous one. The suggestion dropdown
    # is where aliases are taught, because there the match is checked.
    return {
        "targets": rows,
        "count": len(rows),
        "index_size": target_index.size(),
        "showcase": _showcase(),
        "empty_hint": (
            "No curated targets yet. Seed them with: "
            "python scripts/precompute.py --set calibration/targets.txt"
        )
        if not rows
        else "",
    }


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(12, ge=1, le=100),
) -> dict[str, Any]:
    """Search the local target index.

    Local first, and usually local only: it is instant, it works offline, and
    it matches the aliases people actually type. Open Targets is consulted
    only when the index has nothing, so an unindexed symbol is still findable
    without making every keystroke a round trip to a service the analysis also
    depends on.
    """
    query = q.strip()
    curated = {row["symbol"] for row in store.index()}

    results: list[dict[str, Any]] = []
    for record in target_index.search(query, limit=limit):
        results.append({
            "symbol": record["symbol"],
            "name": record.get("name", ""),
            "aliases": record.get("aliases", [])[:4],
            "areas": record.get("areas", []),
            "matched_on": record.get("matched_on", record["symbol"]),
            "tier": "curated" if record["symbol"] in curated else "index",
        })

    # Curated targets first: those open instantly, everything else is a build.
    results.sort(key=lambda r: 0 if r["tier"] == "curated" else 1)

    if not results:
        try:
            for hit in ot_src.search_targets(query, size=8):
                if hit.get("symbol"):
                    results.append({**hit, "aliases": [], "areas": [],
                                    "matched_on": hit["symbol"], "tier": "live"})
        except Exception:  # noqa: BLE001 - search must never break the page
            pass

    return {"results": results[:limit], "index_size": target_index.size()}


@app.get("/api/browse")
def api_browse(area: Optional[str] = None, limit: int = Query(300, ge=1, le=2000)) -> dict[str, Any]:
    """The index, for browsing rather than searching."""
    curated = {row["symbol"] for row in store.index()}
    rows = [
        {
            "symbol": r["symbol"],
            "name": r.get("name", ""),
            "aliases": r.get("aliases", [])[:3],
            "areas": r.get("areas", []),
            "tier": "curated" if r["symbol"] in curated else "index",
        }
        for r in target_index.browse(area, limit=limit)
    ]
    return {
        "targets": rows,
        "areas": target_index.areas(),
        "area": area,
        "index_size": target_index.size(),
        "curated_first": target_index.seeded_count(),
    }


@app.get("/api/target/{symbol}")
def api_target(symbol: str) -> dict[str, Any]:
    """Serve a stored landscape, or say how to get one."""
    try:
        symbol = store.normalise_symbol(symbol)
    except store.UnknownTarget as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # "HER2" is not a gene symbol, but it is what people type. The index maps
    # it to ERBB2 before anything else looks for a stored record.
    resolved = target_index.resolve_alias(symbol)
    if resolved and resolved != symbol:
        symbol = resolved

    found = store.load(symbol)
    if found is None:
        raise HTTPException(
            status_code=404,
            detail={
                "symbol": symbol,
                "message": "Not in the library or the cache.",
                "action": f"POST /api/build/{symbol} to build it live.",
            },
        )
    landscape, meta = found
    return _payload(landscape, meta)


@app.post("/api/build/{symbol}")
def api_build(symbol: str, force: bool = False) -> dict[str, Any]:
    try:
        symbol = store.normalise_symbol(symbol)
    except store.UnknownTarget as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resolved = target_index.resolve_alias(symbol)
    if resolved and resolved != symbol:
        symbol = resolved

    if not force and store.load(symbol) is not None:
        return {"status": "ready", "symbol": symbol}
    return {"status": "started", "job": _start_build(symbol).to_dict()}


@app.get("/api/job/{job_id}")
def api_job(job_id: str) -> dict[str, Any]:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such job — it may have expired.")
    return job.to_dict()


@app.get("/api/export/{symbol}.md", response_class=PlainTextResponse)
def api_export_md(symbol: str) -> str:
    found = store.load(store.normalise_symbol(symbol))
    if found is None:
        raise HTTPException(status_code=404, detail="Not built yet.")
    return render.to_markdown(found[0])


@app.get("/api/export/{symbol}.html", response_class=HTMLResponse)
def api_export_html(symbol: str) -> str:
    found = store.load(store.normalise_symbol(symbol))
    if found is None:
        raise HTTPException(status_code=404, detail="Not built yet.")
    # The memo renderer emits a fragment; wrap it so it stands alone as a file
    # someone can save, print or attach.
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "</head><body>" + render.to_html(found[0]) + "</body></html>"
    )


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    with _jobs_lock:
        active = sum(1 for j in _jobs.values() if j.status in {"queued", "running"})
    return {
        "ok": True,
        "curated": len(store.curated_symbols()),
        "index_size": target_index.size(),
        "active_builds": active,
        "version": app.version,
    }


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index_page() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/target/{symbol}", response_class=HTMLResponse)
def target_page(symbol: str) -> FileResponse:
    # Deep links are real URLs, not fragments: a landscape for a target is a
    # thing someone sends to a colleague.
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
