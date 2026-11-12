# Quant Research Bible v1.4.1 applied to Vexil

**Scope: retrospective research-quality audit, not a new model or a fresh unseen test.**

Canonical private reference: sangtrx/quant-research-bible at commit 8e6374c8ac8c62da6611104555ce98f1cf40a528 (main on 2026-11-13). Applicable sections 1.2–1.4, 3.1–3.7, 4.3, 5.1–5.10, 6.2, 6.4–6.7, 7.1–7.7, 12.11–12.12, 13.1–13.8, 14.1–14.5.

The Bible is a theoretical compass, not a profitability certificate or live trading contract. The Vexil model is a professional-Dota minute-level final-win forecast. Original M1 = logistic model with gold, elapsed time and gold×log(time). Original PR #3 remains the candidate; this is an optional independent private research appendix.

## Data contracts

Source = frozen 3,784 minute-level validation predictions for 29 fixed models (M1 plus 28 candidates), 103 ALREADY EXAMINED validation games. Timing metadata from the original 500-match OpenDota manifest, only IDs and start times. Development train 291, original holdout 106 and two forward cohorts 200+200 remain completely excluded from the new evaluation. No new OpenDota fetches, fitting or hyperparameter tuning. Prior 28-way test was already consumed; ALL results here are post-hoc and descriptive.

## Frozen diagnostic battery (post-hoc, no model fitting)

D1. Minute-weighted, equal-match-weighted and equal-series-weighted proper log loss and Brier difference for all 28 models versus original M1. P20, P08 and M1 details because P20/P08 looked best on previously seen data; no surprise discovery claim.

D2. Six contiguous time blocks from series-or-singleton groups sorted by earliest game start time, approximately equal group counts, no series split. Compute per-block relative proper score for each fixed model.

D3. CSCV-INSPIRED rank-reversal: all 20 combinations of 3/6 time blocks, select winner among 29 already-fitted models by minimum equal-game loss in one half, evaluate its rank and M1-relative loss in the other half. Fraction of complementary winner ranks WORSE than median is a descriptive selection-instability statistic, explicitly NOT official PBO, not a valid independent p-value and not realistic future deployment. Save all 20 selections.

D4. 3,000 series-block bootstrap draws. Select best minute-weighted loss model on drawn groups and evaluate OOB (omitted groups) relative to M1. Report which models win in-bag, fraction with positive OOB loss, group counts and all draws. Conditional on historical development data already viewed; not fresh test.

D5. P20 influence: phase, 10 worst/best influential matches, leave-one-series-out range, equal-game and minute weighted. This is an audit, not phase cutoff optimization.

D6. Complete known trial ledger, at minimum original M0-M3; prior structural S1-S4, prior M4, prior fixed stage gate and P01-P28. Rows can overlap; they are not independent trials. Earlier re-inspections invalidate naive correction for just 28 as a claim about all history.

D7. Economic boundary: two OpenDota endpoints have no executable bookmaker market, odds, spreads, settlement/cost/fills, no live receive timestamps. Proper scores do not establish PnL, edge or Kelly sizing (§7.8). No cost or trading claim.

## Kaggle execution acceptance

Three PRIVATE CPU kernels with PRIVATE input dataset, Internet OFF, seeds/hashes pinned:
K1 proper-score reconstruction and equal-game/phase sensitivity;
K2 six-block selection instability and 3,000 grouped OOB resamples;
K3 group-bootstrap/MAX-T source parity and negative-result ledger.
Every hosted kernel requires KernelWorkerStatus.COMPLETE plus downloaded numerical SHA/metric receipts before a claim of a Kaggle run. Repeated runs assess reproduction, NOT new independent evidence. If Kaggle OAuth/token is missing, build and test the notebooks locally but do NOT falsely report hosted execution.

## Unchangeable outcome

Prior factory had zero of 28 candidates pass. M1 stays selected. Do not access consumed 106+200+200 test labels to optimize. A new candidate needs a separate protocol, later series-disjoint cohort and source PIT audit. Original main notebook and report remain unchanged. Negative results remain visible.
