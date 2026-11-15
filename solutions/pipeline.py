"""Reference solution for the documented full-snapshot source contract."""
import sqlite3


class Pipeline:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), updated_at TEXT NOT NULL)")
        self.db.commit()

    def ingest(self, records):
        # Each delivery is a complete extract, so replaying all records is safe.
        # A timestamp alone cannot establish which records have already arrived.
        written = 0
        with self.db:
            for row in records:
                cursor = self.db.execute("""
                    INSERT INTO orders VALUES (?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        amount_cents=excluded.amount_cents, updated_at=excluded.updated_at
                    WHERE excluded.updated_at > orders.updated_at
                """, (row["order_id"], row["amount_cents"], row["updated_at"]))
                written += cursor.rowcount
        return written

    def revenue_cents(self):
        return self.db.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM orders").fetchone()[0]
