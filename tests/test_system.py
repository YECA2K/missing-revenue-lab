"""Tooling regression checks, separate from intentional learner failures."""
import http.client
import json
import random
import shutil
import sqlite3
import subprocess
import sys
import threading
import tempfile
from pathlib import Path
import unittest
from contextlib import closing
from unittest.mock import patch
from lab.cases import CASES
from lab.runner import run_checks, state
from lab.server import ROOT, make_server
from solutions.pipeline import Pipeline


class ApplicationChecks(unittest.TestCase):
    def test_all_reference_acceptance_checks_pass(self):
        for slug in CASES:
            with self.subTest(case=slug):
                checks = run_checks(slug, solution=True)
                self.assertTrue(checks)
                self.assertTrue(all(check["status"] == "pass" for check in checks), checks)

    def test_workspace_state_has_no_reference_walkthrough(self):
        for slug in CASES:
            data = state(slug)
            self.assertNotIn("solution", data)
            self.assertNotIn("limitation", data)
            self.assertEqual(data["mode"], "workspace")

    def test_reference_totals_reconcile_for_all_incidents(self):
        for slug in CASES:
            data = state(slug, solution=True)
            self.assertEqual(data["actual_cents"], data["expected_cents"])
            self.assertIn("solution", data)

    def test_latest_versions_survive_shuffled_replays(self):
        rng = random.Random(761)
        records = [{"order_id": f"A{i}", "amount_cents": 1234 + i * 31 + version,
                    "updated_at": f"2026-01-{version + 1:02}T00:00:00Z"}
                   for i in range(20) for version in range(3)]
        expected = sum(1234 + i * 31 + 2 for i in range(20))
        with closing(sqlite3.connect(":memory:")) as db:
            pipeline = Pipeline(db)
            for _ in range(5):
                rng.shuffle(records)
                pipeline.ingest(records + records[:10])
                self.assertEqual(pipeline.revenue_cents(), expected)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 20)

    def test_cli_reference_check(self):
        result = subprocess.run([sys.executable, "-m", "lab", "check", "--case", "grain", "--solution"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("8/8 checks passed", result.stdout)

    def test_cli_json_export(self):
        result = subprocess.run([sys.executable, "-m", "lab", "state", "--case", "timezone", "--solution"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["actual_cents"], 30_000)


class DashboardHTTPChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=15)
        self.addCleanup(connection.close)
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_assets(self):
        for path, mime in [("/", "text/html"), ("/app.js", "text/javascript"), ("/style.css", "text/css")]:
            code, headers, body = self.request(path)
            self.assertEqual(code, 200)
            self.assertIn(mime, headers["Content-Type"])
            self.assertEqual(int(headers["Content-Length"]), len(body))
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_catalog_and_evaluated_state(self):
        code, _, body = self.request("/api/catalog")
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(body)), 3)
        code, _, body = self.request("/api/state?case=grain&solution=1")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["actual_cents"], 13_000)

    def test_unknown_case_and_private_paths(self):
        self.assertEqual(self.request("/api/state?case=unknown")[0], 400)
        self.assertEqual(self.request("/../solutions/pipeline.py")[0], 404)
        self.assertEqual(self.request("/.git/config")[0], 404)

    def test_host_and_origin(self):
        self.assertEqual(self.request("/api/catalog", {"Host": "untrusted.example"})[0], 403)
        self.assertEqual(self.request("/api/catalog", {"Origin": "https://untrusted.example"})[0], 403)

    def test_timeout_response(self):
        with patch("lab.server.subprocess.run", side_effect=subprocess.TimeoutExpired("lab", 10)):
            code, _, body = self.request("/api/state")
        self.assertEqual(code, 408)
        self.assertIn("10 seconds", json.loads(body)["error"])

    def test_syntax_error_response(self):
        with patch("lab.server.subprocess.run", return_value=subprocess.CompletedProcess("lab", 1, "", "SyntaxError: example")):
            code, _, body = self.request("/api/state")
        self.assertEqual(code, 422)
        self.assertIn("SyntaxError", json.loads(body)["detail"])

    def test_saved_workspace_repair_is_used_by_next_worker(self):
        # Work on an isolated copy: never overwrite the actual learner's solution.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for package in ("lab", "solutions", "tests"):
                shutil.copytree(ROOT / package, root / package, ignore=shutil.ignore_patterns("__pycache__"))
            repaired = (ROOT / "solutions/pipeline.py").read_text(encoding="utf-8")
            (root / "lab/pipeline.py").write_text(repaired, encoding="utf-8")
            with patch("lab.server.ROOT", root):
                code, _, body = self.request("/api/state?case=revenue")
            self.assertEqual(code, 200)
            data = json.loads(body)
            self.assertEqual(data["mode"], "workspace")
            self.assertEqual(data["passed"], 8)
            self.assertEqual(data["actual_cents"], 10_000_000)

    def test_video_range_requests_support_seeking(self):
        code, headers, body = self.request("/walkthrough.mp4", {"Range": "bytes=0-31"})
        self.assertEqual(code, 206)
        self.assertEqual(len(body), 32)
        self.assertEqual(headers["Accept-Ranges"], "bytes")
        self.assertIn(b"ftyp", body)
        code, headers, body = self.request("/walkthrough.mp4", {"Range": "bytes=-16"})
        self.assertEqual(code, 206)
        self.assertEqual(len(body), 16)
        self.assertEqual(self.request("/walkthrough.mp4", {"Range": "bytes=999999999999-"})[0], 416)


if __name__ == "__main__":
    unittest.main()
