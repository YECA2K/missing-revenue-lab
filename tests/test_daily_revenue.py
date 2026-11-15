import unittest
from lab.daily_revenue import daily_revenue_cents
from lab.fixtures import daily_orders


class AcceptanceChecks(unittest.TestCase):
    def total(self, stamp, offset=120):
        return daily_revenue_cents([{"created_at": stamp, "amount_cents": 1_234}], "2026-06-15", offset)

    def test_incident_matches_business_day(self):
        self.assertEqual(daily_revenue_cents(daily_orders(), "2026-06-15"), 30_000)

    def test_late_utc_previous_day_belongs_to_today(self):
        self.assertEqual(self.total("2026-06-14T22:30:00Z"), 1_234)

    def test_late_utc_today_belongs_to_tomorrow(self):
        self.assertEqual(self.total("2026-06-15T22:15:00Z"), 0)

    def test_exact_local_midnight_is_included(self):
        self.assertEqual(self.total("2026-06-14T22:00:00Z"), 1_234)

    def test_next_local_midnight_is_excluded(self):
        self.assertEqual(self.total("2026-06-15T22:00:00Z"), 0)

    def test_negative_offset_moves_early_utc_to_previous_day(self):
        self.assertEqual(self.total("2026-06-15T01:00:00Z", -300), 0)

    def test_input_offset_is_respected(self):
        self.assertEqual(self.total("2026-06-15T00:15:00+05:30"), 0)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.total("2026-06-15T12:00:00")

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.total("2026-06-15Tnot-a-timeZ")

    def test_midday_is_included(self):
        self.assertEqual(self.total("2026-06-15T12:00:00Z"), 1_234)

    def test_empty_input_returns_zero(self):
        self.assertEqual(daily_revenue_cents([], "2026-06-15"), 0)
