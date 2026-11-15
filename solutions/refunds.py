"""INC-002 reference: reduce each child table to the intended reporting grain."""
import sqlite3


def net_revenue_cents(db: sqlite3.Connection) -> int:
    return db.execute("""
        WITH refund_totals AS (
            SELECT order_id, SUM(amount_cents) AS amount_cents
            FROM refunds GROUP BY order_id
        )
        SELECT COALESCE(SUM(o.amount_cents - COALESCE(r.amount_cents, 0)), 0)
        FROM orders o
        LEFT JOIN refund_totals r ON r.order_id = o.order_id
    """).fetchone()[0]
