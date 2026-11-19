# Timing assumptions, TEST history and interpretation limits

This note supports the FOUR-PAGE REPORT.pdf. It adds no new candidate model or blind TEST. The shipped notebook and original 3,836 held-out probabilities have not changed.

## A. Label availability is not the OpenDota game clock

The historical check uses start_time + parsed duration. That is a game-duration completion proxy, not a recorded wall-clock result-arrival time. Pre-game phases, pauses, parse/replay publication and transfer delays are unmeasured. The reported 143-second estimated VAL-to-TEST gap is therefore NOT a minimum verified real-world lag margin. The five incompletely matured TRAIN outcomes are a lower bound under that proxy, not proof that all other labels were actually available.

The reproducible development-only source is research/development_asof_robustness.py; receipt: docs/DEVELOPMENT_ASOF_ROBUSTNESS_RECEIPT.json. The fixed, hypothetical extra arrival delays are 0, 3, 15, 30, 60 and 120 minutes. Each sensitivity filters TRAIN to labels hypothetically available before the first original VAL game, and evaluates on VAL games hypothetically mature before the first original TEST start. The TEST label and prediction data are not used.

| Extra assumed lag | Mature TRAIN (of 291) | Mature VAL (of 103) | Lowest loss on mature VAL |
| --- | ---: | ---: | --- |
| 0 minutes | 286 | 103 | M1 |
| 3 minutes | 285 | 102 | M1 |
| 15 minutes | 283 | 101 | M1 |
| 30 minutes | 282 | 100 | M1 |
| 60 minutes | 277 | 96 | M2 (0.517823 versus M1 0.518090) |
| 120 minutes | 272 | 90 | M1 |

At +60 minutes the unrounded log-loss margin is only 0.00026775 (about 0.000268). **It is driven by dropping seven later-finishing VAL games**, not by the TRAIN fit alone: with the same 277 mature TRAIN games but all 103 reused VAL games, M1 still leads (0.520133 versus M2 0.523409). On the restricted 96-game VAL subset M2 narrowly leads by log loss, while Brier **still favors M1 (0.175263 versus M2 0.175965)**. Filtering on completion time also changes match-duration mix and denominators (3,781 to 3,497 minute rows), so scores across different buffer levels are not directly comparable. No CI supports this tiny switch, and it is **not evidence to reselect M2** on already inspected data. The buffers are scenarios, not measured OpenDota delays; there is no live received_at log.

## B. The original held-out TEST was inspected before the terminal-boundary repair

The historical pre-correction commit 009f54d (14 November 2026, 16:16 ICT) retained 18,304 minute rows and 3,837 TEST forecasts. Historical TEST forecast CSV SHA256: e3b2c843172fdde029f5f5ec05536ea837ec023b8b860543cadedf028bb3cb32. Its M0/M1 TEST log loss was 0.516304695 / 0.503905615 and Brier was 0.171859157 / 0.168311943.

Commit 4a77ae5 (14 November 2026, 20:24 ICT) applied 60*t < duration, removing 12 terminal rows across 8 TRAIN, 3 VAL and 1 TEST games; the affected TRAIN design was refitted. The corrected frozen 3,836-forecast TEST CSV SHA256 is 03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441, with M0/M1 log loss 0.516444424 / 0.504014697 and Brier 0.171912178 / 0.168352834.

Both comparisons are descriptive, not two independent tests. **The reviewer ZIP includes only the corrected 3,836-row TEST forecast CSV.** The historical pre-correction CSV, its numeric receipt (docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json), and the standard-library verification script (research/verify_terminal_correction_history.py) remain in this public source repository. They are **not reproducible from this ZIP alone**; the original correction can be inspected in public Git history. The files named frozen_original_* refer to the **corrected 14-core-cell science snapshot**, not untouched pre-inspection code. The corrected reviewer notebook has those 14 core cells (including post-TEST corrections and diagnostics) plus two appended QA cells. It therefore does not represent an untouched pre-TEST preregistration.

## C. TRAIN-forward M0 differs from VAL and TEST for identifiable design reasons

The frozen original TRAIN-forward evaluation comprises four chronological series-separated blocks of 22, 44, 32 and 39 games. Its models use smaller, prefix-only TRAIN fits and a changed mix of patch and teams; its losses are not directly comparable as a controlled patch-effect estimate.

| Later TRAIN fold | Eval patch-60 games | M0 log loss | M1 log loss | Train-base-rate constant log loss |
| --- | ---: | ---: | ---: | ---: |
| 22 games | 0 | 0.646066 | 0.652097 | 0.688264 |
| 44 games | 0 | 0.633853 | 0.621876 | 0.696013 |
| 32 games | 2 | 0.588280 | 0.594860 | 0.698797 |
| 39 games | 39 | 0.589960 | 0.594053 | 0.695323 |
| Pooled, minute-weighted | -- | 0.612312 | 0.612086 | 0.695316 |

Original full TRAIN (291 games) fit yields M0 VALIDATION log loss 0.532490 and inspected TEST log loss 0.516444. Changes in sample, fit size, opponent/league composition and patch mix can all explain some differences, but these summaries do NOT identify which mechanism caused them. In the last TRAIN-forward fold, which evaluated 39 patch-60 games, **M0 beat M1 (0.589960 vs 0.594053)**; that is a warning about stability, not a proof that patch 60 causes the difference. These summaries do not isolate drift from the other changes.

## D. Multiple estimands, fragile uncertainty and a stop rule

The primary TEST estimand weights every admissible forecast minute equally, so longer games count more. Equal-game means constitute a different, post-result descriptive estimand. Match- and series-bootstrap percentile intervals have different cluster assumptions. The post-hoc 54-series minute-weighted 95% log-loss upper endpoint is close to zero: +0.000120 at 10,000 draws, +0.000085 at 30,000 draws (another seed), +0.000238 at 100,000 draws (third seed). Those are Monte Carlo sensitivities, not independent replications; with 54 clusters and shared league/team membership, neither a claim of robust model superiority nor a universal significance threshold follows.

The existing 28-way screen, tree models, October/November reuse and one influential TEST match are all multiple-look evidence. I did not use these post-result findings to retune or reselect a model. The defensible operational choice remains M0 reference, M1 shadow only, requiring fresh series/league data with real receipt-time instrumentation before promotion.

## Reproducibility and responsibility

From the reviewer ZIP root, use the included `live_dota2_win_probability.ipynb`, `requirements.txt` and `artifacts/heldout_predictions.csv` to reproduce and check current 500-game model results. A fresh notebook run requires OpenDota network access. The **source-repository-only** checks `research/development_asof_robustness.py --check` and `research/verify_terminal_correction_history.py --check` require development data and a historical pre-correction file not shipped in this concise ZIP.

The development receipts in this public source repository pin script/data fingerprints, versions and numeric tolerances. The linked historical comparison is not reproducible from the reviewer ZIP alone. I spent approximately 10 active hours, excluding unattended runs; this is not an audited time log. Scripts do not validate personal authorship. AI-generated code and critiques are disclosed in REPORT.pdf and do not constitute human peer review.
