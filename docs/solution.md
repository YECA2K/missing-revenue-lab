# Reference walkthrough — spoilers

## Root cause

The initial extract contains ORD-010 with update time 10:00. That becomes the checkpoint.
The later extract adds ORD-011, also updated at 10:00, worth 500,000 cents (EUR 5,000).
The strict timestamp filter excludes it. Job success measures execution, not source completeness.

The starter also inserts repeated identities rather than maintaining current order state.
A correction therefore adds another revenue row. Changing the boundary operator alone can
trade missing revenue for duplicate revenue, while still missing older late arrivals.

## Repair chosen here

The source delivers complete snapshots. The reference processes every supplied record and uses
`order_id` as a primary key. It inserts unseen orders and updates existing orders only when the
incoming version is newer. A transaction groups each delivery. Amounts remain integer cents.

This is intentionally a small full-extract upsert design, not a universal incremental ingestion
algorithm. It trades repeated scanning for correctness under the supplied contract. SQLite
`rowcount` reports actual inserted or updated rows; ignored repeats are not counted as writes.

Run the reference without editing your workspace:

```sh
python -m lab.demo --solution
python tools/verify.py
```

Both initial and repaired implementations start on fresh databases. Adding a unique constraint
to an existing database with duplicates would require a separate deduplication/migration plan.

## Why the checks matter

| Check | What it catches |
| --- | --- |
| Initial extract | Baseline arithmetic and basic load |
| Equal-timestamp arrival | Timestamp-boundary loss |
| Duplicate in delivery | Missing stable-identity protection |
| Repeated delivery | Retry inflation |
| Corrected amount | Append-versus-update errors |
| Older version | Stale overwrite |
| Older new identity | Unsafe global time cutoff |
| Empty extract | Invalid assumptions about nonempty input |

## Production limitations

- This is gross order value, not accounting revenue recognition.
- Full snapshots at large scale may be impractical. A source CDC cursor, reconciliation process,
  or explicit bounded-lateness contract may be appropriate instead. A lookback window alone
  cannot guarantee inclusion of arbitrarily late records.
- Deletes and tombstones need an explicit contract and handling.
- Same-version conflicting payloads should be detected or quarantined in a real system.
- Schema validation, malformed records, currency handling, concurrency, durable operations,
  migrations, observability and deployment are outside the reference's scope.
- These public checks are evidence for the stated examples, not a proof of general correctness.
