"""Minimal HTTP layer: on-disk cache, retry, polite rate limiting.

Deliberately built on the standard library. The public bioinformatics APIs
are unauthenticated REST/GraphQL, and a dependency-light client makes the
tool trivial to run in a notebook or a locked-down corporate environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .config import CACHE_DIR, REQUEST_TIMEOUT, USER_AGENT, MAX_RETRIES, RETRY_BACKOFF


class HTTPError(RuntimeError):
    pass


def _cache_path(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return os.path.join(CACHE_DIR, f"{digest}.json")


def _read_cache(key: str, max_age_s: Optional[int]) -> Optional[Any]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    if max_age_s is not None and (time.time() - os.path.getmtime(path)) > max_age_s:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(key: str, value: Any) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_path(key), "w", encoding="utf-8") as fh:
            json.dump(value, fh)
    except OSError:
        pass  # cache is an optimisation, never a correctness requirement


def _request(
    url: str,
    data: Optional[bytes],
    headers: dict[str, str],
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Any:
    req = urllib.request.Request(url, data=data, headers=headers)
    last_error: Optional[Exception] = None
    attempts = MAX_RETRIES if retries is None else max(1, retries)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(
                req, timeout=timeout or REQUEST_TIMEOUT
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 4xx other than 429 will not succeed on retry.
            if exc.code != 429 and 400 <= exc.code < 500:
                raise HTTPError(f"{exc.code} {exc.reason} for {url}") from exc
            last_error = exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(RETRY_BACKOFF * (2**attempt))
    raise HTTPError(f"failed after {attempts} attempt(s): {url} ({last_error!r})")


def get_json(
    url: str,
    params: Optional[dict[str, Any]] = None,
    cache_ttl: Optional[int] = 86_400,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    key = f"GET {url}"
    cached = _read_cache(key, cache_ttl)
    if cached is not None:
        return cached
    result = _request(
        url,
        None,
        {"User-Agent": USER_AGENT, "Accept": "application/json"},
        retries=retries,
        timeout=timeout,
    )
    _write_cache(key, result)
    return result


def post_json(
    url: str,
    payload: dict[str, Any],
    cache_ttl: Optional[int] = 86_400,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Any:
    body = json.dumps(payload, sort_keys=True)
    key = f"POST {url} {body}"
    cached = _read_cache(key, cache_ttl)
    if cached is not None:
        return cached
    result = _request(
        url,
        body.encode("utf-8"),
        {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        retries=retries,
        timeout=timeout,
    )
    _write_cache(key, result)
    return result
