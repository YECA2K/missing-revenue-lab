"""Acceptance checks. By default the intentionally broken learner code is tested."""
import importlib
import os
import sqlite3
import unittest
from lab.fixtures import snapshots

Pipeline = importlib.import_module(os.environ.get("LAB_PIPELINE_MODULE", "lab.pipeline")).Pipeline


class AcceptanceChecks(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.pipeline = Pipeline(self.db)
        self.first, self.second = snapshots()

    def test_initial_extract_matches_source(self):
        self.pipeline.ingest(self.first)
        self.assertEqual(self.pipeline.revenue_cents(), 9_500_000)

    def test_late_record_with_equal_timestamp_is_not_lost(self):
        self.pipeline.ingest(self.first)
        self.pipeline.ingest(self.second)
        self.assertEqual(self.pipeline.revenue_cents(), 10_000_000,
                         "A successful job silently missed an order.")

    def test_repeated_order_in_one_delivery_is_counted_once(self):
        self.pipeline.ingest(self.first + self.first)
        self.assertEqual(self.pipeline.revenue_cents(), 9_500_000,
                         "Source delivery duplicates must not become revenue.")

    def test_retry_does_not_change_total(self):
        self.pipeline.ingest(self.second)
        before = self.pipeline.revenue_cents()
        self.pipeline.ingest(self.second)
        self.assertEqual(self.pipeline.revenue_cents(), before)

    def test_correction_replaces_previous_order_value(self):
        self.pipeline.ingest(self.second)
        correction = {**self.second[0], "amount_cents": 1_100_000,
                      "updated_at": "2026-01-15T11:00:00Z"}
        self.pipeline.ingest(self.second + [correction])
        self.assertEqual(self.pipeline.revenue_cents(), 10_100_000,
                         "An updated order is not an additional order.")

    def test_older_delivery_cannot_overwrite_newer_value(self):
        latest = {**self.second[0], "amount_cents": 1_100_000,
                  "updated_at": "2026-01-15T11:00:00Z"}
        self.pipeline.ingest([latest])
        self.pipeline.ingest([self.second[0]])
        self.assertEqual(self.pipeline.revenue_cents(), 1_100_000)

    def test_older_timestamp_new_identity_is_still_loaded(self):
        self.pipeline.ingest(self.second)
        delayed = {"order_id": "ORD-012", "amount_cents": 20_000,
                   "updated_at": "2026-01-14T12:00:00Z"}
        self.pipeline.ingest(self.second + [delayed])
        self.assertEqual(self.pipeline.revenue_cents(), 10_020_000)

    def test_empty_delivery_is_safe(self):
        self.pipeline.ingest([])
        self.assertEqual(self.pipeline.revenue_cents(), 0)


if __name__ == "__main__":
    unittest.main()
