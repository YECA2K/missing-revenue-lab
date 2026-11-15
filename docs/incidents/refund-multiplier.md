# INC-002 · The refund multiplier

**Question:** Why does a dashboard report EUR 410 when the ledger says EUR 130?

## What happened

The fictional shop has two orders: EUR 100 and EUR 50. The first has two items and two
distinct EUR 10 refunds. The second has one item and no refunds. Net order value should
be EUR 150 − EUR 20 = **EUR 130**. The report returns **EUR 410**.

Run `python -m lab demo --case grain`, or choose this incident in the dashboard.
Edit **`lab/refunds.py`**; run `python -m lab check --case grain` after saving.

## Source contract

| Table | Grain | Columns |
| --- | --- | --- |
| `orders` | One row per order | `order_id`, `amount_cents` |
| `order_items` | One row per order item | `item_id`, `order_id` |
| `refunds` | One row per refund | `refund_id`, `order_id`, `amount_cents` |

All monetary values are nonnegative integer EUR cents. Identifiers are unique in their own
tables. Refunds refer to known orders. An order can have zero or many items/refunds.
Different orders and refunds may have equal amounts. Inputs are already validated.
Refund status, taxes, currencies and accounting recognition are outside this exercise.

## Your deliverable

Repair `net_revenue_cents(connection)` without changing its interface or the acceptance checks.
Record the grain of every input and the joined result. Explain why your repair counts each
order once, retains orders with no refunds, and preserves distinct equal-value transactions.

## Acceptance checks

Eight checks cover the incident total, item multiplicity, multiple partial refunds, equal-value
orders, equal-value refunds, missing child rows, empty ledgers and full refunds.
The pristine starter passes four and fails four. A repaired implementation should pass all eight.

<details><summary>Reference explanation — spoilers</summary>

Joining two items and two refunds yields four rows for ORD-201. The original expression counts
EUR 100 − EUR 10 four times (EUR 360) and adds ORD-202's EUR 50, producing EUR 410.
Aggregate refunds by order ID first. Join that one-row-per-order result to orders, then sum.
The item table is not needed for this metric. `SUM(DISTINCT amount)` is unsafe because separate
orders/refunds can have the same monetary value. See `solutions/refunds.py`.

</details>
