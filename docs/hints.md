# Progressive hints — spoilers

<details><summary>Hint 1: find the missing identity</summary>

Compare the two extracts by `order_id`, not row position. Which record appears only in the second?
Compare its timestamp with the stored checkpoint.

</details>

<details><summary>Hint 2: test the boundary</summary>

The loader selects timestamps strictly greater than its watermark. A different record can arrive
later with a timestamp equal to that watermark. Older timestamps are also permitted by the contract.

</details>

<details><summary>Hint 3: fixing one operator is insufficient</summary>

Changing `>` to `>=` replays boundary records. The table currently has no uniqueness rule.
It can accumulate multiple rows for the same logical order, including corrections.

</details>

<details><summary>Hint 4: exploit the documented source contract</summary>

Each delivery is a complete extract. At this scale you can process the extract again and upsert
by stable identity, accepting only newer versions. This also accepts delayed new identities.
You do not need to invent an unsafe timestamp-only incremental protocol.

</details>
