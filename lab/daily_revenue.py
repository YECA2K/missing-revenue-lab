"""INC-003 learner workspace: intentional business-day boundary bug."""
from datetime import date


def daily_revenue_cents(records, business_day: str, offset_minutes: int = 120) -> int:
    """Total orders on a business date in a fixed UTC offset, default UTC+02:00."""
    target = date.fromisoformat(business_day)
    return sum(row["amount_cents"] for row in records
               if date.fromisoformat(row["created_at"][:10]) == target)
