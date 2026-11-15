import sqlite3
import unittest
from contextlib import closing
from lab.fixtures import refund_database
from lab.refunds import net_revenue_cents


class AcceptanceChecks(unittest.TestCase):
    def report(self, orders=None, items=None, refunds=None):
        with closing(sqlite3.connect(":memory:")) as db:
            refund_database(db, orders, items, refunds)
            return net_revenue_cents(db)

    def test_incident_total_matches_order_ledger(self):
        self.assertEqual(self.report(), 13_000, "Expected EUR 150 gross minus EUR 20 refunds.")

    def test_extra_items_do_not_create_extra_revenue(self):
        self.assertEqual(self.report([("A", 10_000)], [("I1", "A"), ("I2", "A")], []), 10_000)

    def test_multiple_refunds_reduce_one_order_once(self):
        self.assertEqual(self.report([("A", 10_000)], [("I1", "A")],
                                     [("R1", "A", 1_000), ("R2", "A", 2_000)]), 7_000)

    def test_equal_value_orders_are_distinct_sales(self):
        self.assertEqual(self.report([("A", 10_000), ("B", 10_000)], [], []), 20_000,
                         "SUM(DISTINCT amount) would silently merge two legitimate orders.")

    def test_equal_value_refunds_are_distinct_refunds(self):
        self.assertEqual(self.report([("A", 10_000)], [],
                                     [("R1", "A", 1_000), ("R2", "A", 1_000)]), 8_000)

    def test_order_without_items_or_refunds_is_retained(self):
        self.assertEqual(self.report([("A", 1_234)], [], []), 1_234)

    def test_empty_ledger_returns_zero(self):
        self.assertEqual(self.report([], [], []), 0)

    def test_full_refund_returns_zero(self):
        self.assertEqual(self.report([("A", 10_000)], [("I1", "A")], [("R1", "A", 10_000)]), 0)
