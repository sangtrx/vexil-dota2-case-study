# Evidence boundaries and development-only falsification

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

At +60 minutes the margin is only 0.000267 log-loss units. It is a post-result sensitivity, not evidence to reselect M2 or recalibrate on an already inspected TEST. The buffers are scenarios, not measured OpenDota delays; there is no live received_at log.

## B. The original held-out TEST was inspected before the terminal-boundary repair

The original source commit 009f54d (14 November 2026, 16:16 ICT) retained 18,304 minute rows and 3,837 TEST forecasts. Historical TEST forecast CSV SHA256: e3b2c843172fdde029f5f5ec05536ea837ec023b8b860543cadedf028bb3cb32. Its M0/M1 TEST log loss was 0.516304695 / 0.503905615 and Brier was 0.171859157 / 0.168311943.

Commit 4a77ae5 (14 November 2026, 20:24 ICT) applied 60*t < duration, removing 12 terminal rows across 8 TRAIN, 3 VAL and 1 TEST games; the affected TRAIN design was refitted. The corrected frozen 3,836-forecast TEST CSV SHA256 is 03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441, with M0/M1 log loss 0.516444424 / 0.504014697 and Brier 0.171912178 / 0.168352834.

Both comparisons are descriptive, not two independent tests. The original commit can be inspected from Git history but the historical pre-correction CSV is not included in the recruiter ZIP. The corrected notebook has 14 core code cells (including post-TEST corrections and diagnostics) plus two appended QA cells. The 14 core cells must NOT be described as an untouched pre-TEST preregistration.

## C. TRAIN-forward M0 differs from VAL and TEST for identifiable design reasons

The frozen original TRAIN-forward evaluation comprises four chronological series-separated blocks of 22, 44, 32 and 39 games. Its models use smaller, prefix-only TRAIN fits and a changed mix of patch and teams; its losses are not directly comparable as a controlled patch-effect estimate.

| Later TRAIN fold | Eval patch-60 games | M0 log loss | M1 log loss | Train-base-rate constant log loss |
| --- | ---: | ---: | ---: | ---: |
| 22 games | 0 | 0.646066 | 0.652097 | 0.688264 |
| 44 games | 0 | 0.633853 | 0.621876 | 0.696013 |
| 32 games | 2 | 0.588280 | 0.594860 | 0.698797 |
| 39 games | 39 | 0.589960 | 0.594053 | 0.695323 |
| Pooled, minute-weighted | -- | 0.612312 | 0.612086 | 0.695316 |

Original full TRAIN (291 games) fit yields M0 VALIDATION log loss 0.532490 and inspected TEST log loss 0.516444. Changes in sample, fit size, opponent/league composition and patch mix can all explain some differences, but these summaries do NOT identify which mechanism caused them. This is the correct explanation boundary, not a claim of confirmed drift.

## D. Multiple estimands, fragile uncertainty and a stop rule

The primary TEST estimand weights every admissible forecast minute equally, so longer games count more. Equal-game means constitute a different, post-result descriptive estimand. Match- and series-bootstrap percentile intervals have different cluster assumptions. The post-hoc 54-series minute-weighted 95% log-loss upper endpoint is close to zero: +0.000120 at 10,000 draws, +0.000085 at 30,000 draws (another seed), +0.000238 at 100,000 draws (third seed). Those are Monte Carlo sensitivities, not independent replications; with 54 clusters and shared league/team membership, neither a claim of robust model superiority nor a universal significance threshold follows.

The existing 28-way screen, tree models, October/November reuse and one influential TEST match are all multiple-look evidence. Do not tune/reselect models or presentation claims to force significance. The defensible operational choice remains M0 reference, M1 shadow only, requiring fresh series/league data with real receipt-time instrumentation before promotion.

## Reproducibility and responsibility

From the ZIP root with pinned dependencies, run:

    python research/development_asof_robustness.py --check

This fails if the frozen source hashes, computed scores or timing outcomes differ. The archived historical 009f54d prior-TEST comparison requires Git history and is not recreated from the ZIP. An applicant must personally check the reported active-time estimate and be prepared to explain which research decisions were theirs. AI-written code/reviews are not independent human peer review.
