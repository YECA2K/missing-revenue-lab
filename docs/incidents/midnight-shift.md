# INC-003 · The midnight shift

**Question:** Why does a daily report show EUR 250 instead of EUR 300?

The business wants June 15, 2026 at the **fixed UTC+02:00 offset**. The original code groups
orders by the date written at the start of a UTC timestamp.

| Order | Source instant | Business clock | Amount | In June 15? |
| --- | --- | --- | --- | --- |
| ORD-301 | June 14, 22:30 UTC | June 15, 00:30 | EUR 100 | Yes |
| ORD-302 | June 15, 12:00 UTC | June 15, 14:00 | EUR 200 | Yes |
| ORD-303 | June 15, 22:15 UTC | June 16, 00:15 | EUR 50 | No |

Run `python -m lab demo --case timezone`, or select the incident in the dashboard.
Edit **`lab/daily_revenue.py`**; run `python -m lab check --case timezone` after saving.

## Source contract

- `created_at` is an ISO-8601 datetime containing `Z` or an explicit numeric timezone offset.
- Reject malformed datetimes and timestamps without an offset by raising `ValueError`.
- Every order appears once. Amounts are nonnegative integer EUR cents.
- `business_day` is a valid ISO calendar date; `offset_minutes` is a valid fixed timezone offset.
- The default is +120 minutes. Checks also use −300 minutes and non-UTC source offsets.
- The daily interval starts at local midnight, inclusive, and ends at the next midnight, exclusive.
- The offset is fixed by design. **No daylight saving or named regional timezone is modeled.**

## Your deliverable

Repair `daily_revenue_cents(records, business_day, offset_minutes=120)` without changing its
interface. Explain the difference between a written timestamp date and an instant's date in a
business timezone. Document what would need to change for a daylight-saving-aware calendar.

Eleven acceptance checks cover totals, previous/next UTC dates, midnight boundaries, negative
offsets, input offsets, naive/invalid timestamps, midday and empty input.
The pristine starter passes two and fails nine.

<details><summary>Reference explanation — spoilers</summary>

Parse each datetime with its offset, reject naive values, convert with `astimezone`, and compare
the resulting date to the business date. Summing the first two orders gives EUR 300.
See `solutions/daily_revenue.py`. Use named IANA zones and an available timezone database for
actual regional calendars; the reference deliberately requires neither.

</details>
