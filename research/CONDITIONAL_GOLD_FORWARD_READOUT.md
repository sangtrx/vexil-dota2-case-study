# TRAIN-only chronological check: stable fitted gold slope ≠ predictive advantage

This analysis was specified **after** the separate positive conditional-gold
bootstrap result, but **before** running this forward-fold sensitivity. It
neither draws new TEST outcomes nor retroactively confirms the M1 challenger.

## Four original chronological series-safe TRAIN blocks

The four late-TRAIN blocks have 22, 44, 32 and 39 games, respectively,
with 771, 1,649, 1,228 and 1,433 forecast minutes. The first-to-last
TRAIN boundaries are fixed at 154/176/220/252/291 games from the
previous calibration experiment. Two incomplete earlier games were
embargoed before the third block (approximate end-time proxy).

| Later-TRAIN fold | M0 log loss | M1 log loss | M1−M0 | Fitted conditional-gold log-odds Δ (10−30) |
| --- | ---: | ---: | ---: | ---: |
| 1 (22 games) | 0.646066 | 0.652097 | +0.006031 (worse) | +0.352317 |
| 2 (44 games) | 0.633853 | 0.621876 | −0.011976 (better) | +0.318348 |
| 3 (32 games) | 0.588280 | 0.594860 | +0.006580 (worse) | +0.326809 |
| 4 (39 games) | 0.589960 | 0.594053 | +0.004093 (worse) | +0.299497 |

**Aggregate OOF** on **137 unique TRAIN games and 5,081 minute rows**:
M0 log loss **0.612312**, M1 **0.612086**, difference **−0.000227**.
Paired 70-series/singleton bootstrap (5,000 draws) gives M1-minus-M0
log-loss 95% CI **[−0.011991,+0.010104]** (contains 0).

M0 Brier **0.211828**, M1 **0.212744**, M1-minus-M0 Brier difference
**+0.000916** (worse point estimate), 95% CI **[−0.002536,+0.004251]**
(contains 0). Equal-game-weight difference is −0.001623 log loss,
+0.000188 Brier, also only descriptive.

## Decision

The selected M1's *fitted structural interaction* has positive
minute-10-minus-minute-30 conditional-gold log-odds effects in all four
nested TRAIN historical prefixes. That supports a **within-fitting
interpretation** of M1; these prefixes overlap and therefore are not
four independent sign tests.

It does **not** establish improved prediction: three of four
forward blocks have worse M1 log-loss point scores, the pooled
difference is ~0 and the clustered uncertainty covers both signs.
The earlier March TEST and separate November cohort similarly
do not justify production promotion. The zero-gold conditional
reference remains hypothetical, without causal intervention.

This additional **negative skill result** must accompany any
recruiter-facing usage of the positive TRAIN-only conditional gold
effect; otherwise the effects will mislead reviewers.

**Provenance:** this post-result sensitivity follows the
[locked protocol](CONDITIONAL_GOLD_FORWARD_PROTOCOL.md); exact
[prediction receipt](CONDITIONAL_GOLD_FORWARD_RECEIPT.json) and
[source](conditional_gold_forward.py) can be replayed locally with only
TRAIN rows. This is author-controlled development evidence, not
independent human peer review, a live packet feed, or a new TEST set.
