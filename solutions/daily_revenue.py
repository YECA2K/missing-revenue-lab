"""INC-003 reference: convert instants before choosing their calendar day."""
from datetime import date, datetime, timedelta, timezone


def daily_revenue_cents(records, business_day: str, offset_minutes: int = 120) -> int:
    target = date.fromisoformat(business_day)
    business_zone = timezone(timedelta(minutes=offset_minutes))
    total = 0
    for row in records:
        timestamp = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        if timestamp.utcoffset() is None:
            raise ValueError("created_at must include a timezone offset")
        if timestamp.astimezone(business_zone).date() == target:
            total += row["amount_cents"]
    return total
