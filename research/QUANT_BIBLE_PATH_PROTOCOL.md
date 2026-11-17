# TRAIN-only Quant Bible path dependence experiment

**Declared 17 November 2026, AFTER original Vexil TEST and many prior experiments were inspected. NOT a fresh blind TEST, not preregistration of original take-home, and no authorization to replace M0/M1.**

## Hypothesis
At equal current gold lead and game minute, a lead that *retreated from its local high* or moved more erratically could be less predictive of the winning side than a stable lead. Predictive association only; no causal interpretation. Adapt path-dependent drawdown, realized volatility and trend efficiency from [Quant Bible §8.4–8.6](https://github.com/sangtrx/quant-research-bible/blob/main/QUANT_RESEARCH_BIBLE.md); use its §5 walk-forward and sample-dependence principles. Prior Vexil register already screened acceleration P10, volatility P11 and persistence P12, so this is **one bounded further hypothesis**, NOT a search over variants.

For integer minute t, let g[j] be Radiant's gold lead (in thousands) at minute j, and W = g[max(0,t-10):t+1], d = diff(W), s = sign(g[t]) (s=0 for tied):
- `adverse_excursion10_k = s * max(0, max(s*W)-abs(g[t]))` — local leading-side peak-to-current loss (odd under swapping Radiant and Dire).
- `signed_realized_vol10_k = s * sqrt(mean(d**2))` (0 if no increment) — realized gold-lead motion, **not** market returns.
- `directional_efficiency10 = (g[t]-W[0])/(sum(abs(d))+1e-6)` (0 without increment), between -1 and 1.

All three require only prefix through t. Verify against truncated prefixes and sign inversion **on all 10,675 TRAIN minute rows**.

## Fixed benchmark and single model
Inputs: exactly hashed `research/frozen_original_train_features.csv.gz` (291 TRAIN games, 10,675 rows). NEVER read original VALIDATION or TEST outcomes for model selection.
- M0: gold_k.
- A (stronger null): gold_k, minute10.
- M1: gold_k, minute10, gold_x_time.
- **Q1_PathRisk**: gold_k, minute10, adverse_excursion10_k, signed_realized_vol10_k, directional_efficiency10.
For each: median imputation, StandardScaler, LogisticRegression(C=1,max_iter=1000,random_state=20261113). No fitted transforms outside folds.

Use frozen original TRAIN forward cutpoints **(154,176,220,252,291)**; fit only prior games with `start_time + duration <= first evaluation start` (match-end proxy, NOT actual receipt timestamp); preserve intact series groups. Expect **4 folds, 137 evaluated games, 5,081 minute forecasts, 70 series/singleton clusters**. Compare Q1 vs A and M1, **minute-weighted log loss** primary, Brier overall and 30+ secondary; **5,000 paired series-bootstrap draws**; show fold differences and all guardrails. All four blocks are retrospectively viewed TRAIN, NOT new prospective evidence.

**Predeclared gate before computing results:** promote to *future* validation candidate only if Q1 improves log loss **>=0.0025 against BOTH A and M1**, each 95% series-bootstrap CI upper bound <0; wins **>=3/4 folds** against each; overall and 30+ Brier no worse against both; no individual series/singleton supplies >=50% of total positive Q1–A log-loss gain. Even if all pass, current applicant's already-open TEST remains unchanged; new independent chronological evidence would still be needed for superiority claims.

No alternative windows, polynomial degree, new model family, alternate hyperparameters or P-hacking on repeated fold results. If Q1 fails, **do not insert it in the employer notebook**. Keep negative finding as evidence that an explicit creative hypothesis was tested and rejected, if it is relevant enough to summarize.
