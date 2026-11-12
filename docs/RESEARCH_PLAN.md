# Research plan — Live Dota 2 win probability

**Source of truth:** the 5-page Vexil Capital take-home brief. **Start:** 2026-11-13 (ICT). **Deadline:** 2026-11-19 (timezone of submission cutoff not stated).

## Objective and acceptance criteria

Estimate P(Radiant wins | information observable at minute t), for every minute from 0 to the end of 500 usable professional matches spanning at least one patch change. Prioritize honest probability estimates and point-in-time correctness over classification accuracy.

The final repository must contain exactly one self-contained executable analysis notebook with saved outputs, a 4-page-maximum report, pinned requirements and clear local/Colab instructions. No API credentials, local data files, or unofficial Dota endpoint dependencies.

## 1. Data contract and selection

Only call:
- https://api.opendota.com/api/proMatches, with less_than_match_id pagination
- https://api.opendota.com/api/matches/{match_id}

A match is usable when radiant_gold_adv exists and match duration is at least 600 seconds. Fetch enough candidates to retain exactly 500 usable matches. Record all exclusions and API retries. Validate labels, timestamps, per-minute lengths, patch and series_id. Use patch-aware, outcome-blind cohort selection: fetch proMatches summaries while probing at most three parsed game details per page to identify a boundary between two patches; then take 250 usable matches nearest the boundary from each side. A 30-page label-blind preflight still showed patch 60 in June 2026, making a full-payload chronological scan unnecessarily expensive. This deliberately targets a patch-transition cohort, not a representative sample of all present-day pro games, and must be disclosed in the report. This balancing is our design choice, not a Vexil rule. Display the full (match_id, start_time, patch) manifest in the notebook.

Rate-limit globally to approximately 50 calls/minute without an API key, handle 429 / 5xx with bounded exponential backoff and jitter, and memoize requests in RAM or temporary runtime disk. Never commit raw match payloads. Because /proMatches is a moving recent-match feed, after the initial discovery freeze an upper-bound match-ID cursor and a deterministic match-ID manifest **inside the notebook source**. On rerun, still use the two OpenDota endpoints to verify provenance and fetch payloads; no external data file. Document potential server-side reparse/backfill drift rather than promise impossible bitwise reproducibility.

## 2. Point-in-time feature engine

Define t as integer game minute, with snapshot at 60*t seconds. At minute t:
- Per-minute arrays: indices <= t only; index 0 is 0:00.
- Event logs: event.time <= 60*t, including negative pre-horn timestamps.
- Do NOT use final net worth, final kills/tower kills, future objectives, win result as a feature, or full-match duration as a predictor.
- Use final duration only to know which minute snapshots exist; never supply it to the model.

Candidate snapshot features implemented in the notebook: gold lead (thousands), XP lead (thousands), minute, gold × log elapsed time, five-minute gold/XP changes, timestamp-filtered tower/barracks differential, Roshan differential and kill-log differential. Respect missing-field policy; never fill a missing value from future game state. Missing objectives/kill logs are represented as NaN rather than false zero, with training-only imputation. The notebook audits log coverage and short gold-array tails by patch. If objective event schema is inconsistent, exclude that feature or document a fixed time-safe fallback, not ad-hoc manual editing.

Invariants to test:
1. Truncating all series after t and filtering all events after t does not change the feature row at t.
2. Replacing future data and end-of-match totals with adversarial values does not change past features.
3. Features at t never depend on the radiant_win label.
4. Pre-horn negative event timestamps and exact boundary t*60 events are handled correctly.
5. Each match produces a single immutable label and increasing minute index.

## 3. Validation design

Use match-level, time-ordered, **series-purged** splits (target ~300 train / ~100 validation / ~100 test matches, constrained by series boundaries). Sort by match start_time, prevent a series_id from crossing splits, and use unique match_id for unmatched/missing series_id. Train only on the earliest block; tune and optionally calibrate on the middle block; report metrics once on the latest untouched held-out block.

Document actual match and row counts, unique series, win rates, duration and patch composition of each block. The balanced patch-transition sample may place much of the prior patch in training and the newer patch in validation/test; treat this as an explicit historical distribution-shift evaluation, not a reason to reshuffle until scores improve. A random row-level split is forbidden because same-match minutes share labels and histories.

## 4. Models and explicit hypothesis tests

**Required baseline:** regularized logistic regression with ONLY current gold lead as an input. Feature scaling is allowed. Do not include minute or derived features in the baseline.

**Proposed model:** small, interpretable regularized logistic regression with predeclared time-safe features and a gold-lead x game-time interaction. Favor a controlled research ladder over a large model:
- M0: gold-only baseline
- M1: gold + elapsed time and interaction (is an equal gold lead worth the same at minute 10 and minute 40?)
- M2: M1 + XP and 5-minute gold/XP momentum (does economic velocity signal fragility/comebacks?)
- M3: M2 + time-safe objectives / Roshan / kills (does converting economy into map control matter?)
- Optional capacity control: a shallow histogram gradient-boosted tree model only if simpler models plateau and data supports it.

Predefine a short candidate grid. Select a final model exclusively on validation log loss + Brier + calibration, with complexity and stability as tie breakers; **do not optimize against test**. Report all attempted ablations including hypotheses that fail. Use train-only preprocessing and, if applicable, train-only hero statistics. Avoid hero-draft encodings unless sample support and leakage-safe computation can be demonstrated.

## 5. Probability evaluation and uncertainty

On held-out matches report model and baseline:
- Log loss and Brier score overall and phases 0–9, 10–19, 20–29, >=30.
- 95% confidence intervals from 1,000–2,000 whole-match cluster bootstrap replicates.
- Paired bootstrap 95% confidence intervals for model-minus-baseline differences using the same sampled match IDs.
- Reliability diagrams/calibration curves for both models; include bin counts (small bins are noisy).
- Prediction table with match_id, minute, p_model, p_baseline, radiant_win.
- Full-match minute-weighted (per-row) primary score and an equal-match-weighted sensitivity check, because longer games contribute more rows.\n- Predeclared robustness: exclude the final two recorded minutes per match from a sensitivity score only, leaving the required all-minute primary evaluation unchanged.

Do not report last-minute accuracy. Explain the relationship between calibration, discrimination and proper scoring rules; a lower Brier score alone does not establish perfect calibration. Treat correlated minute rows as one cluster for uncertainty calculations.

## 6. Creative analysis (not data fishing)

Three predeclared falsifiable ideas:
1. **Time-dependent value of a lead.** Show estimated P(win) at equal gold leads across minute 10 / 20 / 35, with other features fixed and clearly labeled illustrative scenarios. Validate by M1 vs M0.
2. **Lead under pressure.** Quantify the fraction of large gold leads which change sign or reverse quickly. Ask whether short-horizon lead velocity improves probability quality. Validate M2 vs M1.
3. **Resource-to-objective conversion.** Does an advantage backed by recent towers/Roshan differ from an economy-only lead? Validate M3 vs M2; compare phase and confidence intervals.

Additional preregistered descriptive diagnostic: among held-out games with minute-20 absolute gold lead at least 3,000, compare eventual leader-loss fractions for deteriorating versus non-deteriorating five-minute gold momentum. One row per match, Wilson intervals with a within-series dependence caveat; not used for model selection and not causal.

Optional descriptive event study: plot gold-lead trajectory before/after observed Roshan or tower events. **Descriptive, not causal**; do not claim event causation. All figures must be generated by the notebook. No invented insights or unsupported game claims.

## 7. Runtime and packaging

GitHub is canonical. Kaggle private CPU kernel is primary execution environment; kernel-metadata must specify is_private=true, enable_internet=true, and no GPU. **First smoke test** one OpenDota GET from Kaggle. Community reports indicate CLI-pushed kernels may sometimes fail to get internet access even when the metadata flag is set; inspect actual runtime status rather than assuming the flag works. If blocked, enable via Kaggle web UI or run in Colab/local as the supported fallback while preserving the exact notebook.

Root-level notebook path: live_dota2_win_probability.ipynb. The setup cell handles Colab package installation; local prerequisites are pip install -r requirements.txt. No hidden scripts are required to reproduce results. Save executed outputs; keep caches and downloaded raw payloads out of Git.

## 8. Delivery gates and schedule (ICT)

- Nov 13: repository, brief audit, API/Kaggle smoke test, manifest, data-quality report.
- Nov 14: minute snapshots, no-leakage prefix/adversarial tests, gold-only baseline.
- Nov 15: grouped chronological split, simple ablation ladder; no test peeking.
- Nov 16: objective/momentum feature experiments, final model chosen on validation.
- Nov 17: held-out evaluation, match-bootstrap intervals, calibration figures and sensitivity.
- Nov 18: final report <=4 pages, top-to-bottom Kaggle + Colab + laptop checks, outputs committed; independent review and repairs.
- Nov 19: final freeze and delivery, invite Vexil reviewers to private GitHub repo when their GitHub IDs are known.

**GO gate:** 500 eligible match IDs across patch boundary; only permitted endpoints; no future leakage; train/tune/test disjoint by series; honest held-out intervals; seeded runnable notebook with outputs; no credentials/data dependencies; report <=4 pages and accurate AI disclosure.

**HOLD gate:** any leak test failure, unreproducible upstream selection, shared series across splits, notebook fails on Colab/local, evaluation tuned on test, or private repository inaccessible to reviewers.

## Sources for implementation decisions

- OpenDota API documentation: https://opendota.apidocumentation.com/
- OpenDota server configuration/rate limits: https://github.com/odota/core/blob/master/config.ts
- Kaggle kernels CLI: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
- Kaggle kernel metadata: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md
- Kaggle notebooks: https://www.kaggle.com/docs/notebooks
- scikit-learn calibration: https://scikit-learn.org/stable/modules/calibration

## Source-informed methodological scope (Bible v1.4.1)

This project estimates *conditional game-win probabilities*, not returns, market prices, executable fills or a betting strategy. Following Bible §§1.2–1.4 and 12.1, freeze a small null/alternative family and preserve negative ablations. Bible §§3.1–3.7 and 13.2 motivate prefix and poisoned-future invariance checks, with a caveat: retrospective OpenDota event timestamps do not prove historical network receipt times. Bible §§4.3, 5.1–5.6 and 6.5 motivate chronological, series-safe splitting and whole-match paired bootstrap. Bible §§7.2–7.7 motivate reliability curves alongside proper loss scores. Theory Reading Paths: choose the null and falsifier before the model. The private reference is used as methodology, not copied as implementation.
