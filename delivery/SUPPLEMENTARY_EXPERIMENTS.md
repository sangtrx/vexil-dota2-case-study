# Supplementary experiments and negative results

**Scope:** Exploratory studies following the initial inspection of the
March 500-match TEST. These analyses were not used to revise the reported
M0/M1 fit or promote a replacement model. Unless stated otherwise, the
comparisons below are on chronological, reused TRAIN-forward folds and
**must not be compared directly with original TEST log loss**.

## What I tested

| Question / model | Recorded result | Interpretation |
| --- | --- | --- |
| 28 additional feature specifications (P01–P28) | 0/28 cleared the simultaneous-testing promotion rule on the previously reused 103-game VALIDATION set | The strongest nominal result did not survive multiplicity adjustment |
| Q1, five-input logistic model with gold-path features | TRAIN-forward LL **0.605963**, versus M1 **0.612086**; paired 95% series CI Q1−M1 **[−0.0174,+0.0047]** | Candidate improvement is uncertain; Q1 was not evaluated on original VAL/TEST |
| XGBoost / LightGBM on M1's three inputs | TRAIN-forward LL **0.615597 / 0.616196** | Neither improves on Q1; more complex learners did not earn promotion |
| Q2 sparse elastic-net, repaired 84-input features | TRAIN-forward Δ LL vs M1 **+0.017733** | Worse after fixing Roshan; no promotion |
| Q3 shallow boosted tree, repaired 84-input features | TRAIN-forward Δ LL vs M1 **+0.010129** | Worse after fixing Roshan; no promotion |
| Fixed XGB84 / LGB84 with repaired Roshan attribution | TRAIN-forward LL **0.621254 / 0.624856** | Neither earned promotion |
| M1 versus additive gold + time without interaction | Difference **−0.002020**; 95% grouped CI **[−0.0148,+0.0090]**, favourable **1/4** folds | No confirmed incremental benefit from the interaction |
| 60-second event-lag stress (ALL60) | Historical reused TRAIN-forward Δ LL vs M1 **−0.008070**; Δ vs Q1 **−0.001947** with CI crossing zero | Better than M1 in this historic sample, not confirmed against the stronger Q1 reference or live packet arrival time |
| Structural S1–S4 and Aegis/buyback M4 | Reused-VAL LL S1 **0.518253**, S2 **0.517384**, S3 **0.524593**, S4 **0.520049**, M4 **0.520596**; old M1 **0.519346** | No confirmed improvement; S1 corresponds to screened P05 |
| Separate 200-game phase blend | LL blend **0.539850**, M1 **0.533704**, M0 **0.545075** | Blend failed against M1 |
| Disagreement for wrong-side predictions | AUROC **0.51856** vs M1-confidence uncertainty **0.66576** | Worse than simpler uncertainty |
| September locked external | 199 usable of 200 preselected games; LL M0 **0.584431**, M1 **0.544803**; series CI for M1−M0 **[−0.074261,−0.010790]** | **Limited study gate PASS**, outside the required 500 matches; only 3 leagues and repeated teams |

`FEATURE_SCREEN_AND_FAILURES.md` in this ZIP lists all
**28 screened feature candidates** and all five wide-feature groups, with
the original result and failure decision. The private repository keeps
dated source branches, additional readouts and September frozen predictions.
The **positive September M1 result is preserved** without retraining or
changing the original 500-game notebook.

## A source bug was found

The first supplementary 81-feature extractor read Roshan kill ownership
from `player_slot`, but OpenDota identifies the side with `team = 2/3`.
All 486 TRAIN Roshan kill events contained the team field. The historical
extractor made two Roshan features constant zero and changed downstream
objective tempo. I corrected the parser and reran the **fixed** Q2, Q3,
XGB84 and LGB84 configurations on TRAIN-forward data without tuning or
using TEST. Their historical results were kept separately. Nested
hyperparameter studies and October/November transfer and ALL60 checks
**were not rerun** after this correction.

## Interpretation

One 55-minute held-out game accounts for **54.9%** of M1's aggregate
log-loss improvement. Removing that game from the descriptive minute-30+
influence calculation flips M1−M0 log loss from **−0.00678** to **+0.03139**.
The late-game Brier difference also worsens. This is an error diagnostic
on already inspected TEST probabilities, **not a revised model-selection
step**. Across 106 matches and 54 series/singleton groups, the primary
log-loss difference intervals include zero.

These experiments add evidence about model sensitivity and failure
modes, not proof of a new predictive edge. Full scripts, historical
receipts and additional cohort notes remain in the source repository.
