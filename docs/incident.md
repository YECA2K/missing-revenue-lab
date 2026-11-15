# Incident INC-001: missing revenue

## Timeline

All dates and timestamps are fictional. All timestamps use UTC.

| Time | Event |
| --- | --- |
| 10:05 | First extract arrives: 10 orders totaling EUR 95,000.00 |
| 10:06 | Loader succeeds and stores its latest source timestamp |
| 10:15 | Second extract arrives: 11 orders totaling EUR 100,000.00 |
| 10:16 | Loader succeeds but warehouse remains at EUR 95,000.00 |

The second extract includes an order not present in the first. It has the same source update
timestamp as another order in the first delivery. Delivery time is not a field in the records.

## Source contract

- Every delivery is a **complete extract** of all orders known to the source.
- `order_id` is the stable identity of an order. Revenue counts each identity once.
- `amount_cents` is a nonnegative integer representing the current gross order amount in EUR.
- `updated_at` is normalized UTC in fixed-width `YYYY-MM-DDTHH:MM:SSZ` format.
- An order correction has a strictly newer `updated_at` than its prior version.
- Two different orders may share an update timestamp.
- Records can arrive late, including timestamps older than the warehouse maximum.
- Deliveries may repeat records or include multiple versions. Identical identity/timestamp pairs
  have identical payloads; conflicting same-version payloads are outside this exercise.
- Orders are not deleted. Refunds, taxes, discounts, currencies and recognized revenue are not modeled.
- Ingestion is single-process; one delivery fits in memory. A timestamp comparison as a string
  is valid only because the fixed-format UTC contract is explicit.

## Acceptance criteria

The initial delivery should reconcile, the late order must be included, duplicates must not inflate
the total, corrections must replace old values, retries must preserve totals, older versions must
not overwrite newer versions, delayed new identities must load, and empty input must be safe.

Keep `Pipeline(connection)`, `ingest(records)` and `revenue_cents()` available.
Each test starts with a fresh SQLite database. The demo also uses a fresh in-memory database.
No migration of an existing broken database is required.

## Investigation notes to write

1. What source assumption did the original loader make?
2. Which records prove that assumption is unsafe?
3. What happens if you change only the comparison operator?
4. Which checks show that your repair handles both missing and excess revenue?
5. Would your approach still work for a billion-row change-data-capture feed?
