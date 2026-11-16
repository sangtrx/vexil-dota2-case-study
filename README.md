# Live Dota 2 Win Probability

**Vexil Capital · Senior Data Scientist take-home · Truong Quang Sang**

A reproducible study of **500 parsed professional OpenDota matches** (patches 59 and 60, 21–26 March 2026). At each admissible game minute, the notebook estimates Radiant's probability of winning using information timestamped no later than that minute. This is a historical point-in-time exercise, not a live-feed latency or betting-profitability claim.

**Review in this order:** [four-page report](REPORT.pdf) → [notebook with saved outputs](live_dota2_win_probability.ipynb) → [research decision trail](docs/RESEARCH_DECISION_TRAIL.md) → [frozen TEST predictions](artifacts/heldout_predictions.csv). The original research Git ancestry is preserved in this repository, with exploratory branch heads mirrored for review; no separate source access is needed to audit the main numerical results.

## Results on the held-out TEST

| Proper score (lower is better) | Gold-only logistic M0 | Gold + time logistic M1 |
| --- | ---: | ---: |
| Validation log loss, 103 games | 0.5325 | **0.5197** |
| TEST log loss, 106 games | 0.5164 | **0.5040** |
| TEST Brier, 106 games | 0.1719 | **0.1684** |
| TEST minute-30+ Brier | **0.1028** | 0.1074 |

**Evaluation boundary:** The 12 terminal-minute corrections were made after the original TEST had been inspected. These are corrected results on the same games, **not a new blind TEST**.

The gold-only logistic model is the required baseline. I selected M1 on validation log loss; M1 adds elapsed minute and gold × time interaction to that baseline. A constant **TRAIN-only** Radiant-win prior (149/291 games) has TEST log loss **0.6884** and Brier **0.2476**, so both fitted models outperform this no-skill reference.

The primary **whole-match paired** 95% bootstrap intervals for M1 minus M0 are **[-0.0304, +0.0014]** (log loss) and **[-0.0069, +0.0002]** (Brier): both cross zero. M1's minute-30+ Brier point estimate is **0.00455 worse**, paired interval **[−0.0037,+0.0109]**. One 55-row game accounts for 54.9% of the observed gain; five embargoed TRAIN-only rolling-origin folds favored M1 in only **2/5**. **Decision: M0 remains the reference; M1 is shadow-only, not proven superior.**

The fixed-gold forecast contrast is not the same as a claim that gold becomes less discriminative late in a match. M1 maps +2,000 Radiant gold to 66.5% at minute 10 and 59.4% at minute 30, but a TRAIN-only series-bootstrap interval for this difference crosses zero. The report separates this fitted scenario from the held-out test.

## Where the assignment requirements are addressed

| Requirement | Evidence in this package |
| --- | --- |
| 500 professional OpenDota matches | Notebook collection and frozen 250/250 match IDs; setup needs no API key |
| Gold-lead logistic baseline **and** own model | M0–M3 model comparison in notebook and [report](REPORT.pdf); M1 selected by validation |
| Information available at the forecast time | Minute-prefix features, timestamped events, negative-time/future-feature poisoning tests; strict pre-terminal 60*t < duration |
| Chronological split, label timing and probability evaluation | Series-disjoint **291 TRAIN / 103 VALIDATION / 106 TEST**; 5 TRAIN games may finish after first VAL start (embargo sensitivity keeps M1 selected); proper scores, grouped uncertainty and calibration diagnostics |
| Executable notebook with visible outputs | [Executed notebook](live_dota2_win_probability.ipynb): 14 code cells, four embedded figures; source-frozen 500-game local and fresh Colab replay receipts |
| Setup and reproducibility | [Pinned dependencies](requirements.txt), commands below, [3-minute review guide](SUBMISSION_PACKAGE_README.md), frozen forecast CSV |
| Separate report, at most four pages, with assistance disclosure | [REPORT.pdf](REPORT.pdf): four A4 pages, results, limitations, active-time estimate, AI/public-code disclosure |

## Reproduce

**Google Colab:** Upload the notebook to a CPU runtime with Internet and choose Runtime → Run all. It requests only two public OpenDota endpoints: /proMatches and /matches/{match_id}. The 500 IDs are fixed; network rate limits are retried but never silently replaced with different matches. Saved outputs and figures are already included for review without rerunning.

**Local Python 3.12 (verified with exact pins):**

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
~~~

Run the notebook top to bottom. For a fast no-network contract check:

~~~bash
python -m unittest discover -s tests -p "test_*.py" -q
~~~

This runs **111 offline checks** on immutable forecasts, point-in-time logic, numerical audits and delivery integrity. From the ZIP, reviewers can rerun the notebook **with OpenDota Internet access** or recompute/check the supplied TEST forecasts **offline**. Raw OpenDota JSON is not bundled; the cached-source full replay is an author-controlled receipt, not a locally runnable ZIP-only replay. The cached-source [local full-replay receipt](docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json) confirms all 14 cells and the 3,836 original TEST forecasts; a [fresh Colab receipt](docs/COLAB_COLD_RUN_RECEIPT.json) confirms source-code and rounded numerical parity, **not** cloud-export CSV byte parity.

## Evidence boundaries and research history

The training split already contains 41 patch-60 games; VALIDATION and TEST are both patch 60, **not an unseen-patch generalization result**. The notebook uses API event timestamps, which do not establish when a live consumer actually received each event. Calibration-in-the-large and ECE intervals are post-hoc, not calibration fits. The original **VALIDATION** M1 forecast-minus-outcome bias is **+0.0300** (53-series CI [−0.0436,+0.1001]); on inspected **TEST** it is **−0.0617** (54-series CI [−0.1410,+0.0250]). Neither establishes drift; the [frozen validation/TEST calibration audit](docs/CALIBRATION_BIAS_READOUT.md) is reproducible from bundled CSVs without model changes.

An optional [100-game November check](docs/FORWARD_100_STRESS.md) uses the original frozen M0/M1 and has confidence intervals crossing zero; **68 of those games overlap an earlier 120-game research cohort**, so the results are not independent replications. [Frozen calibration audit](docs/CALIBRATION_BIAS_READOUT.md), [error analysis](docs/ERROR_ANALYSIS.md) and [experiment register](docs/EXPERIMENT_REGISTER.md) preserve negative results without model promotion.

**Git provenance:** [HISTORY.md](HISTORY.md), the [clickable branch/PR map](docs/REVIEWER_HISTORY_MAP.md) and [curation provenance](docs/CURATION_PROVENANCE.md) distinguish authentic 13–15 November research from the 16 November reviewer curation PRs. The [decision trail](docs/RESEARCH_DECISION_TRAIL.md) links hypotheses, rejected alternatives and the deployment gate to source evidence. Original GitHub PR discussions remain in a separately private repo, but original code ancestry and selected branch heads are included here. Historical 200-game raw payloads are not bundled.

The report states the candidate's **approximately 10 hours of active work** estimate and details extensive AI assistance. No third-party Dota predictor was copied; no measured betting returns or verified live latency are claimed.
