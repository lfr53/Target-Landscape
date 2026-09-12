"""Vercel serverless entrypoint.

Vercel's Python runtime looks for an ASGI application object named ``app`` in
a file under ``api/`` and serves it directly, with no adapter needed. The
actual application lives in ``web/app.py`` exactly as it does for a normal
server (`uvicorn web.app:app`); this file exists only because Vercel
requires the entrypoint to sit under `api/`, and re-exports that same app.

Everything that differs between a normal deployment and this one -- cache
directories that must live under /tmp because the rest of the filesystem is
read-only, and a build that runs inside one request instead of a background
job -- is handled in web/app.py and landscape/config.py, keyed off the
`VERCEL` environment variable Vercel sets automatically. Nothing here is
serverless-specific beyond the import path.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from web.app import app  # noqa: E402  (import after sys.path fix, by design)

__all__ = ["app"]
