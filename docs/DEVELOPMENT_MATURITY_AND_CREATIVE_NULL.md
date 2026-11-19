# Label maturity and the value of the time interaction

**Audit dated 16 November 2026. Retrospective analysis of reused
development data, not an unseen TEST.** The original 500-game notebook and
all 3,836 held-out predictions remain byte-frozen. The question is
whether a production-time label restriction affects model selection.

## 1. Correctness: a training label must be known at fit time

The original chronological series-disjoint partition is **291 TRAIN /
103 VALIDATION / 106 TEST**. Five TRAIN games ended after the earliest
VALIDATION game started, under the approximate completion proxy
(start_time + parsed duration), by at most 1,606 seconds.
A model fitted at that first validation start could not know
their final winners.

**Future as-of label guardrail:**
[`research/label_maturity_policy.py`](../research/label_maturity_policy.py) checks whether a winner label could have been known when the model was fitted. It requires observed `received_at` by default and fails closed without it. The historical sensitivity below explicitly sets `require_received_at=False` because original OpenDota payloads have no such timestamp; this enforces only estimated match completion. The original 291-game fit and already inspected TEST remain unchanged.

The same **four fixed notebook specifications** were refitted using only
the **286 TRAIN games with mature outcomes** at that cutoff. Predictions
were evaluated **only on the originally used 103 VALIDATION games**.

| Original development validation score | Gold-only M0 | Gold × time M1 | Fragility M2 | Objectives M3 |
| --- | ---: | ---: | ---: | ---: |
| 291-game TRAIN fit: log loss | 0.532490 | **0.519714** | 0.522386 | 0.528205 |
| Mature 286-game TRAIN fit: log loss | 0.532940 | **0.520209** | 0.522953 | 0.528550 |
| Mature 286-game TRAIN fit: Brier | 0.181236 | **0.176074** | 0.178012 | 0.180768 |

**M1 remains the model selected by reused VALIDATION.** The mature-only
fit has slightly worse point scores than the original. This sensitivity
quantifies risk but **does not repair the original training fit**, create
a new TEST or prove live feed readiness. Actual received-at time is
unverified; the maturity rule uses only estimated match completion.

The **full internal research archive**, not the concise reviewer ZIP, includes **14,456 minute rows for the original 394 development
games**, all four model families' at-minute inputs, and the frozen
split/series metadata. This derived archive excludes all **106 TEST** rows and outcomes; the reviewer ZIP contains only the corrected frozen TEST forecast CSV required by Vexil.
The internal verifier refits the four original candidates, checks the original
M0/M1 VALIDATION probabilities, reproduces the mature-label embargo,
and fails closed on checksum or score changes.

Run from the ZIP root, offline:

    python research/mature_label_validation_audit.py --verify

Re-export from the author's historical 394 raw OpenDota response cache:

    python research/mature_label_validation_audit.py \
      --export-from-cache /path/to/original/api-cache

The exporter refuses to overwrite already published evidence.
Raw API payloads are **not** in the ZIP; OpenDota can reparse games.
See the [machine receipt](MATURE_LABEL_VALIDATION_RECEIPT.json)
for exact excluded IDs, original/purged scores and source hashes.

## 2. Creativity: compare interaction to the right simple null

A fitted model with a gold-by-time interaction can assign different
win probabilities to identical gold at different game clocks. That is
**not itself evidence of predictive advantage from the interaction**.

The proper nested null for the interaction is **gold + elapsed time
without the interaction**, not only the compulsory gold-only M0.
The [TRAIN-only Draft PR #5](https://github.com/sangtrx/vexil-dota2-case-study/pull/5)
used four chronological later-TRAIN folds: **137 distinct games and
5,081 forecast minutes**. M1-minus-additive-null log loss was
**−0.002020**; the 70-series/singleton clustered 95% interval
**[−0.014801,+0.008984]** contains zero. Brier difference was
**+0.000405**, CI **[−0.003059,+0.003857]**. An incremental
out-of-sample benefit of gold-by-time interaction was **not**
established. These are post-result TRAIN-only sensitivity analyses,
not independent blind samples. The **original unmerged-Draft source and
receipt are now bundled in this reviewer ZIP**:
[interaction-null receipt](../research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json),
[model-check source](../research/gold_interaction_null_influence.py) and
[readout](../research/GOLD_INTERACTION_NULL_READOUT.md). Reproduce on the
original frozen TRAIN-only features without Internet:

    python research/gold_interaction_null_influence.py --check


The separate two-game TRAIN example with similar minute-25 gold/XP
but different Roshan/Aegis and tower control explains why gold
does not represent the full Dota state. Yet M3 objective-event inputs
made VALIDATION log loss **0.528205**, worse than M1 **0.519714**.
This is an attractive idea that failed its predictive gate,
not a claimed achievement.

## 3. Calibration is a model-release gate

The separate [TRAIN-only OOF calibration Draft PR #4](https://github.com/sangtrx/vexil-dota2-case-study/pull/4)
trained an intercept offset using only 137 TRAIN games. On already
reused VALIDATION, it slightly improved M1 log loss
**0.519714 → 0.518556**, but worsened ECE10
**0.049193 → 0.056137**. The 53-series grouped 95% interval
for the log-loss gain **[−0.019380,+0.017395]** contains zero.
The honest decision is **HOLD**, not to silently recalibrate on TEST.
Original unmerged-Draft sources are bundled:
[TRAIN-OOF calibration receipt](../research/CALIBRATION_FORWARD_RECEIPT.json),
[readout](../research/CALIBRATION_FINDINGS.md),
[replay script](../research/verify_calibration_offline.py) and the
source-frozen 394-game development archive (without TEST rows).
Reproduce offline:

    python research/verify_calibration_offline.py


A new unopened, predeclared, multi-league series cohort with an
explicit label-maturity embargo, proper-score, calibration,
event-received-at and feature-completeness gates is required before
promoting M1. These analyses show how a Senior Data Scientist
**rejects unsupported improvements**, not that a larger model won.
