"""Web layer tests.

Offline: the curated tier is served from disk and needs no network, which is
the whole point of having a curated tier. The one live path — building a
target that is not stored — is exercised with the pipeline mocked, so the job
runner and its progress reporting are tested without waiting on three APIs.

Skipped cleanly when FastAPI is not installed, since the engine and its test
suite must stay usable without the web dependencies.
"""

from __future__ import annotations

import datetime
import json
import glob
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient

    HAVE_FASTAPI = True
except ImportError:  # pragma: no cover
    HAVE_FASTAPI = False

from landscape import pipeline, store  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "TNFRSF13C.json")


@unittest.skipUnless(HAVE_FASTAPI, "fastapi not installed")
class WebTestCase(unittest.TestCase):
    """Point the store at a temp directory seeded from the fixture."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.curated = os.path.join(cls.tmp.name, "curated")
        cls.cache = os.path.join(cls.tmp.name, "cache")
        os.makedirs(cls.curated)
        landscape = pipeline.load_fixture(FIXTURE)
        with open(os.path.join(cls.curated, "TNFRSF13C.json"), "w", encoding="utf-8") as fh:
            json.dump(landscape.to_dict(), fh)

        cls._patchers = [
            mock.patch.object(store, "CURATED_DIR", cls.curated),
            mock.patch.object(store, "CACHE_DIR", cls.cache),
        ]
        for patcher in cls._patchers:
            patcher.start()

        from web import app as web_app

        cls.web_app = web_app
        cls.client = TestClient(web_app.app)

    @classmethod
    def tearDownClass(cls):
        for patcher in cls._patchers:
            patcher.stop()
        cls.tmp.cleanup()


class TestLibraryAndTarget(WebTestCase):
    def test_health(self):
        body = self.client.get("/api/health").json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["curated"], 1)

    def test_library_lists_the_curated_tier(self):
        body = self.client.get("/api/library").json()
        self.assertEqual(body["count"], 1)
        row = body["targets"][0]
        self.assertEqual(row["symbol"], "TNFRSF13C")
        # The index must carry the computed verdict, not just the raw record —
        # a library card with an empty verdict is the bug this guards.
        self.assertEqual(row["verdict"], "Emerging")
        self.assertEqual(row["n_active"], 4)

    def test_target_payload_carries_analysis_and_facets(self):
        body = self.client.get("/api/target/TNFRSF13C").json()
        self.assertEqual(body["target"]["symbol"], "TNFRSF13C")
        self.assertTrue(body["assets"])
        self.assertIn("crowding", body)
        self.assertIn("whitespace", body)
        self.assertIn("modalities", body["facets"])
        self.assertEqual(body["meta"]["tier"], "curated")

    def test_symbol_is_case_insensitive(self):
        self.assertEqual(self.client.get("/api/target/tnfrsf13c").status_code, 200)

    def test_unknown_target_says_how_to_build_it(self):
        response = self.client.get("/api/target/ZZZFAKE9")
        self.assertEqual(response.status_code, 404)
        self.assertIn("build", response.json()["detail"]["action"])

    def test_path_traversal_is_rejected(self):
        """Symbols become filenames, so this is a real attack surface."""
        for bad in ["../secret", "..%2Fsecret", "a/../../etc/passwd"]:
            response = self.client.get("/api/target/" + bad)
            self.assertIn(response.status_code, (400, 404), bad)

    def test_exports_render(self):
        markdown = self.client.get("/api/export/TNFRSF13C.md")
        self.assertEqual(markdown.status_code, 200)
        self.assertIn("competitive landscape", markdown.text)

        html = self.client.get("/api/export/TNFRSF13C.html")
        self.assertEqual(html.status_code, 200)
        self.assertIn("<!doctype html>", html.text.lower())

    def test_deep_link_serves_the_app_shell(self):
        response = self.client.get("/target/TNFRSF13C")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Target Landscape", response.text)


class TestSearch(WebTestCase):
    def test_curated_matches_rank_first_and_are_marked_instant(self):
        with mock.patch.object(self.web_app.ot_src, "search_targets", return_value=[]):
            body = self.client.get("/api/search?q=TNFRSF").json()
        self.assertEqual(body["results"][0]["symbol"], "TNFRSF13C")
        self.assertEqual(body["results"][0]["tier"], "curated")

    def test_live_hits_are_appended_without_duplicating_curated(self):
        live = [
            {"symbol": "TNFRSF13C", "name": "dup", "ensembl_id": "X"},
            {"symbol": "TNFRSF13B", "name": "TACI", "ensembl_id": "Y"},
        ]
        with mock.patch.object(self.web_app.ot_src, "search_targets", return_value=live):
            body = self.client.get("/api/search?q=TNFRSF").json()
        symbols = [r["symbol"] for r in body["results"]]
        self.assertEqual(symbols.count("TNFRSF13C"), 1)
        self.assertIn("TNFRSF13B", symbols)

    def test_search_survives_a_dead_upstream(self):
        """Autocomplete must never take the page down with it."""
        with mock.patch.object(self.web_app.ot_src, "search_targets", side_effect=RuntimeError):
            response = self.client.get("/api/search?q=TNFRSF")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["results"])


class TestBuildJobs(WebTestCase):
    def test_building_an_existing_target_is_a_no_op(self):
        body = self.client.post("/api/build/TNFRSF13C").json()
        self.assertEqual(body["status"], "ready")

    def test_job_reports_stages_then_completes(self):
        landscape = pipeline.load_fixture(FIXTURE)

        def fake_build(symbol, **kwargs):
            on_progress = kwargs.get("on_progress")
            for i, (stage, label) in enumerate(pipeline.STAGES):
                on_progress(stage, label, i, len(pipeline.STAGES))
                time.sleep(0.01)
            landscape.target.symbol = symbol
            return landscape

        with mock.patch.object(self.web_app.pipeline, "build", side_effect=fake_build):
            started = self.client.post("/api/build/FAKE1").json()
            self.assertEqual(started["status"], "started")
            job_id = started["job"]["id"]

            for _ in range(200):
                job = self.client.get("/api/job/" + job_id).json()
                if job["status"] in {"done", "error"}:
                    break
                time.sleep(0.02)

        self.assertEqual(job["status"], "done")
        self.assertEqual(job["progress"], 1.0)
        self.assertEqual(job["total"], len(pipeline.STAGES))

    def test_a_failed_build_surfaces_the_reason(self):
        with mock.patch.object(
            self.web_app.pipeline, "build", side_effect=ValueError("could not resolve 'NOPE'")
        ):
            started = self.client.post("/api/build/NOPE").json()
            job_id = started["job"]["id"]
            for _ in range(200):
                job = self.client.get("/api/job/" + job_id).json()
                if job["status"] in {"done", "error"}:
                    break
                time.sleep(0.02)
        self.assertEqual(job["status"], "error")
        self.assertIn("could not resolve", job["error"])

    def test_unknown_job_is_a_404(self):
        self.assertEqual(self.client.get("/api/job/deadbeef").status_code, 404)

    def test_concurrent_requests_share_one_job(self):
        """Two people asking for the same target must not start two sweeps."""
        def slow_build(symbol, **kwargs):
            time.sleep(0.3)
            return pipeline.load_fixture(FIXTURE)

        with mock.patch.object(self.web_app.pipeline, "build", side_effect=slow_build):
            first = self.client.post("/api/build/SLOW1").json()
            second = self.client.post("/api/build/SLOW1").json()
        self.assertEqual(first["job"]["id"], second["job"]["id"])


# ---------------------------------------------------------------------------
# The request path
# ---------------------------------------------------------------------------


def _path_for(symbol):
    from landscape.store import CURATED_DIR, _path

    return _path(CURATED_DIR, symbol)


class RequestPathTests(unittest.TestCase):
    """Serving a curated target must not re-derive it.

    The whole reason a curated record is stored fully computed is that the web
    layer should never do analysis on the request path. It was doing exactly
    that: ``store.load`` called ``load_fixture`` with its default
    ``recompute=True``, so every page view re-clustered the assets and rebuilt
    the indication matrix -- 4.3 seconds on PDCD1 against 0.05 for the read,
    on every single click, with no cache in front of it.
    """

    def test_loading_a_curated_target_does_not_run_the_analysis_layer(self):
        from unittest import mock
        from landscape import store as store_mod

        symbols = store_mod.curated_symbols()
        if not symbols:
            self.skipTest("no curated targets in this checkout")

        with mock.patch("landscape.pipeline.load_fixture",
                        wraps=pipeline.load_fixture) as spy:
            store_mod.load(symbols[0])
        self.assertTrue(spy.called)
        for call in spy.call_args_list:
            self.assertIs(call.kwargs.get("recompute"), False,
                          "the request path asked for a full recompute")

    def test_provenance_is_not_reported_as_a_warning(self):
        """Which sources a page rests on is provenance, not a fault. "ChEMBL
        has no entry for CARD9" in a yellow alert made an ordinary page look
        broken, and a warning box that cries wolf is the one nobody reads when
        something has actually gone wrong."""
        import json
        import tempfile as tf

        from landscape import store as store_mod

        symbols = store_mod.curated_symbols()
        if not symbols:
            self.skipTest("no curated targets in this checkout")
        source = _path_for(symbols[0])
        raw = json.load(open(source, encoding="utf-8"))
        raw["warnings"] = [
            "No single-protein human ChEMBL target matched 'X'; action types and "
            "modalities rest on Open Targets alone."
        ]
        raw["notes"] = []
        with tf.NamedTemporaryFile("w", suffix=".json", delete=False,
                                   encoding="utf-8") as fh:
            json.dump(raw, fh)
            temp = fh.name
        landscape = pipeline.load_fixture(temp, recompute=False)
        os.unlink(temp)
        self.assertEqual(landscape.warnings, [])
        self.assertEqual(len(landscape.notes), 1)

    def test_the_date_dependent_layers_are_still_refreshed(self):
        """Skipping the recompute must not serve a readout date that has
        already passed. Those two layers, and only those two, are re-run."""
        from landscape import store as store_mod

        symbols = [s for s in store_mod.curated_symbols() if s == "PDCD1"] \
            or store_mod.curated_symbols()
        if not symbols:
            self.skipTest("no curated targets in this checkout")
        found = store_mod.load(symbols[0])
        self.assertIsNotNone(found)
        landscape, _ = found
        nxt = (landscape.readouts or {}).get("next_catalyst")
        if nxt:
            self.assertGreaterEqual(nxt["date_iso"][:10],
                                    datetime.date.today().isoformat(),
                                    "the featured readout is already in the past")


# ---------------------------------------------------------------------------
# The Windows launchers
# ---------------------------------------------------------------------------


class LauncherTests(unittest.TestCase):
    """The double-click scripts, which are the only part of this project a
    non-developer ever touches.

    These exist because of a real failure. Windows PowerShell 5.1 reads a .ps1
    with no byte-order mark using the system's ANSI code page. On a Simplified
    Chinese install that is CP936, where the UTF-8 bytes of an em dash or an
    ellipsis decode as a lead byte plus a trail byte, and the trail byte
    swallows the character after it. In

        Write-Host "Creating a git repository here..."

    the swallowed character was the closing quote, so the string never ended
    and the entire file failed to parse -- reported as an unterminated string
    on the last line and a missing brace forty lines earlier. The window
    closed before any of it could be read.

    A launcher has no need for typography. Pure ASCII, and a BOM so that a
    stray character later cannot do this again.
    """

    def _launchers(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return sorted(glob.glob(os.path.join(here, "scripts", "*.ps1")))

    def test_there_are_launchers_to_check(self):
        self.assertTrue(self._launchers())

    def test_every_powershell_launcher_is_pure_ascii(self):
        for path in self._launchers():
            raw = open(path, "rb").read()
            body = raw[3:] if raw[:3] == b"\xef\xbb\xbf" else raw
            offenders = sorted({bytes([b]) for b in body if b > 127})
            self.assertEqual(
                offenders, [],
                f"{os.path.basename(path)} contains non-ASCII bytes {offenders}. "
                "Under CP936 these can eat the quote that follows them and break "
                "the whole script.")

    def test_every_powershell_launcher_carries_a_byte_order_mark(self):
        for path in self._launchers():
            self.assertEqual(
                open(path, "rb").read()[:3], b"\xef\xbb\xbf",
                f"{os.path.basename(path)} has no UTF-8 BOM, so PowerShell 5.1 "
                "will decode it with the machine's ANSI code page.")

    def test_quotes_and_braces_balance_in_every_launcher(self):
        """A crude parse check, but it is exactly the failure that shipped."""
        for path in self._launchers():
            body = open(path, "rb").read()[3:].decode("utf-8")
            name = os.path.basename(path)
            self.assertEqual(body.count("{"), body.count("}"), f"{name}: braces")
            self.assertEqual(body.count('"') % 2, 0, f"{name}: double quotes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
