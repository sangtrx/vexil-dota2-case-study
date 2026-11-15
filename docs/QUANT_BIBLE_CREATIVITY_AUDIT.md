> **Research inference withdrawn (15 November 2026).** The lagged Brier freshness mean is an endpoint telescoping identity, not per-minute information value or measured latency. The 1.76x headline must not be used. Read [FRESHNESS_ERRATA.md](FRESHNESS_ERRATA.md) before interpreting the historical numbers below. This is NOT recruiter-facing appendix material.

# Vexil × Quant Research Bible | Theory-to-experiment applicability audit

**Goal:** select ideas that answer the Vexil question with the available data. **Not** to run every theorem as a model hyperparameter, claim financial alpha, or optimize on previously opened TEST. This map references [the Bible](https://github.com/sangtrx/quant-research-bible), [full 28-candidate register](EXPERIMENT_REGISTER.md) and [failure audit](ERROR_ANALYSIS.md).

## Theories genuinely exercised already

| Bible lens | Evidence in Vexil | Boundary |
| --- | --- | --- |
| §3 PIT filtration, event time | Minute-index cutoff, event-time feature constraints, source-poison/future-event tests | Parsed completed OpenDota games; actual `received_at` not available |
| §§4–5 dependence, chronological generalization | Game- and series-safe 291/103/106 split, rolling TRAIN folds, match/series cluster bootstrap | Only 5.26 days / two patches; no unseen-patch guarantee |
| §§6, 6.12–6.14 search overfitting / model confidence | 28-screen research, max-T adjustment and instability/negative results; history retained | Prior adaptive testing means no freshly valid blanket multiple-testing claim |
| §7 proper scores / calibration | M0–M3 ablation, log loss, Brier, ECE, 30+ late-game failure and 54-series sensitivity | M1 overall gain remains uncertain and late-game Brier worsens |
| §13.12 stateful win probability | Time interaction and time-conditioned forecasts; gold-flow alternatives on research branches | Not a new estimator, no online state assimilation or general martingale proof |
| §12.13 falsifiers / value of evidence | Matched-state examples, explicit negative tests and stage-gate rejection | Match examples do not imply causality or net predictive lift |

## Newly evaluated here (still not independent held-out evidence)

| Bible lens | Executed and reproducible | Does it establish a new model? |
| --- | --- | --- |
| §3, §7, §13.12 dynamic information and proper scoring | [Value of Freshness](FRESHNESS_READOUT.md): exact same-game lagged probabilities, 1/2/5 minutes, Brier/log loss, 54-series bootstrap | **No.** It quantifies retrospective value of updated inputs, not live packet latency |
| §13.12 conditional-expectation/martingale benchmark | Exact Brier innovation-energy + outcome-alignment decomposition, including censoring caveat | **No.** Algebraic diagnostic on an estimated forecast process |
| §9.12 decision-focused comparison | Same-row *fresh M0 versus stale M1* forecast-loss scenario | **No.** No measured odds, action utilities, trade fills or rollout |

## Interesting but NOT valid to promote using this used TEST

| Bible theory | What a genuinely new study would need | Why not run opportunistically now |
| --- | --- | --- |
| §7.10 forecast pooling | A frozen equal-weight or covariance pool, train-only weights and new untouched series | Selecting a mixture on TEST would launder search into hindsight |
| §§6.9–6.12 conditional forecast comparisons / MCS | Fixed complete model universe, preregistered loss and non-overlapping evaluation | 28 + prior overlapping trials already consumed development evidence |
| §13.10 domain shift / MMD | New temporal/patch/tournament cohorts with authenticated label completion | The brief's original TEST is entirely known patch 60 |
| §13.13 regime filtering and change points | Train-only causal filters, specified regime clock, untouched test | Limited 291 TRAIN games; stage and gold dynamics already extensively searched |
| §§4.7–4.8 entropy and event bars | Within-match PIT symbols, stopping-time-safe events, independent temporal cohort | Resampling alone cannot create new outcome information; likely search cost exceeds small-sample evidence |
| §7.9 nonexchangeable conformal / §6.11 e-values | Explicit online sequential coverage/null and forward evaluation | Calibration/coverage would address a different estimand, not rescue M1 after seeing TEST |
| §12.13 value-of-information experiment design | Genuine source arrival timestamps and prospective data-age intervention | Delayed saved probabilities are **not** observed network latency |

## Mechanistically inapplicable without a new task or new data

- **Market microstructure, OFI/Hawkes/Kyle, order fills, impact, quote inventory, cross-asset propagation** (§§8,10): Dota gold snapshots are not an exchange limit order book, and event timestamps are not packet arrivals.
- **Derivative pricing, Heston/BSM, term structures, VaR/ES hedge or portfolio allocation** (§§9,11): No traded instrument, position, payoff quote or PnL in this task.
- **Kelly and execution-aware return attribution** (§§7.8,8.15,9.4): Win probability alone cannot identify a profitable bet; market price, fees, latency and fills are missing.
- **Causal DML, synthetic market fidelity, off-policy RL/POMDP, financial LLM contamination** (§§9.11,13.11,13.18–13.21): No identified intervention, logged policy propensities, or relevant financial foundation-model target.

## Honest creativity decision

A genuinely creative senior-level contribution is **asking whether freshness matters more than extra model complexity**, measuring it on identical snapshots with the correct dependence unit, and identifying what must be instrumented before deployment. The new result is a *sharp operational hypothesis*, not a 10/10 self-awarded score, original theory, forecasting breakthrough or new independent holdout. A recruiter can credit its research design while still reasonably requesting actual live arrival-time and prospective evidence.

**Release boundary:** keep the 500-game notebook, 3-page employer report, frozen TEST forecasts and M1 choice unchanged. This optional audit is research appendix material; it should not replace the concise assignment deliverable.
