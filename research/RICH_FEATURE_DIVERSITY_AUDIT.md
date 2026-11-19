# Feature diversity and Roshan ownership audit (17 November; corrected 19 November 2026)

**Correction history:** The 17 November version asserted that raw Roshan-kill
events did not supply an attributable team. That conclusion was **wrong**:
all 486 TRAIN Roshan-kill events had `team=2/3`, while the old parser
incorrectly searched for player slots. The unmodified 17 November text
is preserved at Git branch `research/vexil-rich-feature-lab-20261117`.
This main-branch readout is explicitly the **19 November correction**, not
a claim that the correct attribution was known on 17 November.
The original defective Q2/Q3 scores remain in the research record,
alongside corrected TRAIN-only evaluations.


This is an explicit post-execution **quality audit**, not a third model variant or a new performance test. It does not change either locked model, the training input CSV, or the already reported score receipt.

## Actual 291-TRAIN cohort

- **81 engineered columns** were generated over 10,675 admissible minute snapshots from 291 original TRAIN matches.
- **2 constant-zero columns**: `o_roshan_delta`, `o_roshan10_delta`.
- **1 duplicated, nonconstant column**: `x_economy_gap` is exactly `gold_xp_gap`.
- **78 distinct, varying engineered columns** remain in the original training feature matrix. This is an *effective field count*, not evidence that these 78 statistical signals are independent.
- **Correction (19 November):** 486/486 TRAIN Roshan-kill events have `team` 2/3, and none have `player_slot` or `slot`. The old extractor used player slots for Roshan, dropping every event. This was an implementation error, **not unavailable owner data**. The corrected parser uses `team` for Roshan and player slots for Aegis; it does not infer Roshan ownership from Aegis.
- Those two zero fields and the duplicate appeared in the **historical 84-input evaluations**. Old scores are correct only for that flawed feature matrix. The repaired model comparisons are a separate post-result TRAIN-only analysis.

**Evidence:** `research/RICH_FEATURE_TRAIN_ONLY.csv.gz`, `research/RICH_FEATURE_RAW_PROVENANCE.json`, `research/RICH_FEATURE_MODEL_RECEIPT.json` and the local raw-cache-only audit of all 291 selected matches. Raw payloads remain outside Git and were not added to the employer submission.

**Decision:** Keep the historical results with the bug disclosed. See `research/ROSHAN_CORRECTION_20261119.md` for corrected TRAIN-forward results. No model was promoted; this does not prove live received-at availability.
