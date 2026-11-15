"""Learner workspace. The bugs in this file are intentional.

Amounts are integer euro cents. Timestamps are UTC ISO-8601 strings.
"""
import sqlite3


class Pipeline:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT, amount_cents INTEGER, updated_at TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoint (watermark TEXT)")
        self.db.commit()

    def ingest(self, records):
        """Load a complete source extract. Return number of rows written."""
        checkpoint = self.db.execute("SELECT watermark FROM checkpoint").fetchone()
        watermark = checkpoint[0] if checkpoint else ""
        selected = [row for row in records if row["updated_at"] > watermark]
        with self.db:
            for row in selected:
                self.db.execute("INSERT INTO orders VALUES (?, ?, ?)",
                                (row["order_id"], row["amount_cents"], row["updated_at"]))
            if selected:
                self.db.execute("DELETE FROM checkpoint")
                self.db.execute("INSERT INTO checkpoint VALUES (?)",
                                (max(row["updated_at"] for row in selected),))
        return len(selected)

    def revenue_cents(self):
        return self.db.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM orders").fetchone()[0]
