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
