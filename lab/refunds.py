"""INC-002 learner workspace: a reporting query with an intentional grain bug."""
import sqlite3


def net_revenue_cents(db: sqlite3.Connection) -> int:
    """Gross order value minus refunds, counted once per order."""
    return db.execute("""
        SELECT COALESCE(SUM(o.amount_cents - COALESCE(r.amount_cents, 0)), 0)
        FROM orders o
        LEFT JOIN order_items i ON i.order_id = o.order_id
        LEFT JOIN refunds r ON r.order_id = o.order_id
    """).fetchone()[0]
