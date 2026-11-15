"""Small, deterministic and entirely fictional source extracts."""
import copy

BASE = [
    {"order_id": f"ORD-{i:03}", "amount_cents": 1_000_000,
     "updated_at": "2026-01-15T09:00:00Z"} for i in range(1, 10)
] + [{"order_id": "ORD-010", "amount_cents": 500_000,
      "updated_at": "2026-01-15T10:00:00Z"}]
LATE = {"order_id": "ORD-011", "amount_cents": 500_000,
        "updated_at": "2026-01-15T10:00:00Z"}


def snapshots():
    return copy.deepcopy(BASE), copy.deepcopy(BASE + [LATE])


def refund_database(db, orders=None, items=None, refunds=None):
    """Create the independent INC-002 database; caller owns its lifetime."""
    db.executescript("""
        CREATE TABLE orders (order_id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL);
        CREATE TABLE order_items (item_id TEXT PRIMARY KEY, order_id TEXT NOT NULL);
        CREATE TABLE refunds (refund_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, amount_cents INTEGER NOT NULL);
    """)
    orders = [("ORD-201", 10_000), ("ORD-202", 5_000)] if orders is None else orders
    items = [("ITEM-1", "ORD-201"), ("ITEM-2", "ORD-201"),
             ("ITEM-3", "ORD-202")] if items is None else items
    refunds = [("REF-1", "ORD-201", 1_000),
               ("REF-2", "ORD-201", 1_000)] if refunds is None else refunds
    with db:
        db.executemany("INSERT INTO orders VALUES (?, ?)", orders)
        db.executemany("INSERT INTO order_items VALUES (?, ?)", items)
        db.executemany("INSERT INTO refunds VALUES (?, ?, ?)", refunds)


def daily_orders():
    return [
        {"order_id": "ORD-301", "amount_cents": 10_000, "created_at": "2026-06-14T22:30:00Z"},
        {"order_id": "ORD-302", "amount_cents": 20_000, "created_at": "2026-06-15T12:00:00Z"},
        {"order_id": "ORD-303", "amount_cents": 5_000, "created_at": "2026-06-15T22:15:00Z"},
    ]
