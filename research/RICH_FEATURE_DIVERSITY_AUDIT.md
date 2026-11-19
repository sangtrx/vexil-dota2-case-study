# Feature diversity and Roshan-owner availability (17 November 2026)

This is an explicit post-execution **quality audit**, not a third model variant or a new performance test. It does not change either locked model, the training input CSV, or the already reported score receipt.

## Actual 291-TRAIN cohort

- **81 engineered columns** were generated over 10,675 admissible minute snapshots from 291 original TRAIN matches.
- **2 constant-zero columns**: `o_roshan_delta`, `o_roshan10_delta`.
- **1 duplicated, nonconstant column**: `x_economy_gap` is exactly `gold_xp_gap`.
- **78 distinct, varying engineered columns** remain in the original training feature matrix. This is an *effective field count*, not evidence that these 78 statistical signals are independent.
- **486/486 timestamped `CHAT_MESSAGE_ROSHAN_KILL` events** in the 291 matches have neither `player_slot` nor `slot`. The raw source does not authorize assigning the kill to a team from this event alone. The two zero columns are correctly marked **unavailable owner-side information**, not predictive proof of no Roshan impact. Aegis event ownership is available separately for some events, but inferring Roshan-kill ownership from Aegis is not logically guaranteed (Aegis may be stolen). Do not backfill it as if observed.
- Those two zero fields and the duplicate **were included in both locked 84-input evaluations**. Their presence does not invalidate the reported scores but is a code-quality limitation and reduces effective model capacity. The locked experiment is not changed or retuned after observing the negative results.

**Evidence:** `research/RICH_FEATURE_TRAIN_ONLY.csv.gz`, `research/RICH_FEATURE_RAW_PROVENANCE.json`, `research/RICH_FEATURE_MODEL_RECEIPT.json` and the local raw-cache-only audit of all 291 selected matches. Raw payloads remain outside Git and were not added to the employer submission.

**Decision:** Historical TRAIN-wide experiments remain NO PROMOTION. Do not describe Q2/Q3 as discovering 81 independent signals. Future work could repair event attribution with a documented timestamped source and a *new locked evaluation*, but this already-viewed TRAIN result cannot establish model superiority.
