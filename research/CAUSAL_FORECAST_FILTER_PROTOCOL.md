# Post-result TRAIN-only live probability revision study — locked protocol

**Declared:** 18 November 2026, before executing S1/S2 outcomes below. This is exploratory research after multiple previous model screens and an already-open original TEST; it is **not** original take-home preregistration or blind confirmation. Source: db401e4 rich lab, original 291 TRAIN games only. VAL, TEST, 180-game holdout and employer ZIP are out of scope.

## Question and mechanism

Minute-by-minute forecasts are a **sequence**, not just isolated rows. Can a simple causal filter reduce prediction revision churn while keeping the proper-scoring penalty acceptably small? Filtering cannot add information. It may hide true swings and harm calibration; a calm but wrong forecast is failure.

Use frozen M1 gold-by-time logistic as input stream. Fit M0, M1 and Q1 only on mature, prior TRAIN games within each locked forward fold; no transforms or outcomes from current block enter fitting. Reproduce existing Q1 benchmark fold scores to 1e-10. Order each game's minute predictions from t=0; initialize q_0=p_0. For later minutes, with z(p)=log(p/(1-p)), q_t = logistic(alpha_t*z(p_t)+(1-alpha_t)*z(q_(t-1))). Use **no labels or future events** to choose alpha. Two fixed policies:

- **S1, fixed logit filter:** alpha_t=0.65 every minute after t=0.
- **S2, observable-event reset:** alpha_t=1.00 if any signed cumulative difference in o_tower_delta, o_rax_delta or o_kills_delta changed since minute t-1; alpha_t=0.65 otherwise. This is an incomplete event proxy: equal simultaneous opposing events can cancel. No Roshan attribution guesses. At reset q_t=p_t, zero current-minute lag relative to M1.

S1/S2 are postprocessing **policies**, not fitted predictive models. Each new match restarts state. No cross-game or cross-series contamination. Reuse prefix-only and side-mirror-audited features. Do not add third policy, change alpha, alter event definition, or pick a time window after viewing scores.

## Exact evaluation

Use existing FROZEN_CUTS=(154,176,220,252,291), four TRAIN-forward folds, expected 137 games / 5,081 minute forecasts / 70 series/singletons. At first evaluation start, training labels must mature under existing end-time proxy, and professional series must not straddle boundaries.

**Forecast safeguard:** paired minute-weighted log loss (S1/S2 minus M1), Brier overall and minute >=30; 5,000 series/singleton cluster-bootstrap draws for descriptive 95% LL/Brier intervals and 97.5% Bonferroni two-policy LL intervals; per-fold sign and comparison with M0/Q1. A CI crossing zero is not evidence of noninferiority.

**Operational proxy:** within-game absolute probability revision |q_t-q_(t-1)|, average variation, total variation per game, >5 percentage-point revisions per game, all compared with unfiltered M1. Exclude minute zero from revision denominators. Count event-reset minutes and check exact event reset to M1. Do not equate smoother forecasts with better usability.

**Frozen exploratory advancement gate:** candidate only for future independent study (never submission replacement) if overall delta LL <= +0.002 vs M1, Bonferroni upper interval <=+0.005, overall and late30 delta Brier <=+0.001, >=3/4 fold deltas LL <=+0.002, >=20% reduction in mean absolute revision AND >5pp revision count. Compare M0 and Q1 regardless. Passing this cannot prove formal noninferiority or production benefit.

Guardrails: frozen source SHA parity, no lookahead or future operations, no change to scored original TEST CSV / notebook / report / ZIP / applicant-owned time and disclosure, no model tuning post-results. Dedicated research branch only.
