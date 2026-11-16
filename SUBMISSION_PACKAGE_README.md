# Reviewer guide | Vexil Dota 2 win-probability take-home

Candidate: Truong Quang Sang

**Start here (3 minutes):** read [REPORT.pdf](REPORT.pdf) for the single research question, negative evidence and M0/M1 decision; then inspect the [one executed notebook](live_dota2_win_probability.ipynb) and its saved figures. For source selection, see the [dated `/proMatches` discovery provenance](docs/DISCOVERY_PROVENANCE.md); [3,836 frozen TEST forecasts](artifacts/heldout_predictions.csv) are available for offline audit. The report also includes the candidate's provisional **10 active work hours** and the required AI/public-code disclosure.

The notebook compares the required gold-only logistic baseline M0 with validation-selected gold×time M1 on 500 professional OpenDota matches (291/103/106 TRAIN/VAL/TEST, chronological and series-disjoint). **The most direct non-confirmatory TRAIN-only check** is [Figure 2 in the report](docs/figures/train_interaction_vs_additive_null.png): on four original TRAIN-forward folds, M1 beat the stricter **additive gold + time without interaction** control in only **1/4 folds**, with 70-series 95% CI **[−0.0148,+0.0090]** around the pooled log-loss difference. The separate [TRAIN-only empirical leader-win observation](docs/TRAIN_LEADER_STATE_EMPIRICAL.md) remains exploratory and is not evidence of causal time decay or added model skill. On original TEST, M1 log loss was 0.5040 versus M0 0.5164, but both primary paired intervals cross zero; minute-30+ Brier was **0.00455** worse for M1 (CI **[−0.0037,+0.0109]**). **Decision: keep M0 reference, M1 shadow-only.**

## How to rerun

On Google Colab: upload the notebook, select CPU with Internet, and Run all. Colab retains already-loaded scientific packages (latest verified Python 3.13 / NumPy 2.4.6 / scikit-learn 1.6.1) to avoid live-kernel ABI breakage; pinned local verification uses Python 3.12 / NumPy 2.2.6 / scikit-learn 1.7.2. This limits cross-runtime equality to reported metric/source parity, not CSV byte identity. The default replay fetches **500 frozen `/matches/{match_id}` payloads** to keep the original sample fixed. The notebook retains the original `/proMatches` pagination/discovery branch, documented with timestamped original commits and hash checks in [discovery provenance](docs/DISCOVERY_PROVENANCE.md); that branch is deliberately bypassed for deterministic reviewer runs. No API key is needed; rate limits may delay fetching.

On **Python 3.12 (verified)** locally:

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
~~~

The repository has **one executable main notebook**, containing **16 executed code cells**: the original 14 scientific cells plus two post-hoc QA cells that recompute point-in-time checks and report numbers **without extra files**. The historical original 14-cell source is archived as plain JSON in research/ only, not as a second notebook. The notebook's Evaluation table provides individual and paired 95% whole-match bootstrap intervals for M0/M1 log loss and Brier overall and all four phases. All have saved outputs except the original frozen-cohort definitions cell. The new [16-cell cached-source fresh-kernel receipt](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json) verifies the current notebook. Historical [14-cell source-frozen replay](docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json) and [Colab cold run](docs/COLAB_COLD_RUN_RECEIPT.json) preserve original reproducibility. Local QA used 500 original raw match JSONs **not bundled**; reviewers need live OpenDota for a new Run All. A fresh [16-cell Colab Run All receipt](docs/COLAB_16CELL_RUN_RECEIPT.json) confirms 510 API calls, 16/16 execution and six-decimal TEST-score/source parity; cloud CSV byte equality remains unverified.

For **offline** score/contract verification from the ZIP (not a fresh notebook Run all), without API keys or private research access:

~~~bash
python -m unittest discover -s tests -p "test_*.py" -q
~~~

Twenty-two test modules contain **162 offline unit/contract checks**. The ZIP manifest lists SHA-256 checksums for every file. An optional [post-hoc team/league dependence audit](docs/TEAM_LEAGUE_DEPENDENCE.md) recomputes from bundled frozen public match/group IDs and predictions, without fitting new models or changing the notebook.

## What is supplementary

The original 500-game TEST is the core assessment. The [offline label-maturity refit and interaction null](docs/DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md), [full original 500-match point-in-time audit](docs/FULL_500_PREFIX_AUDIT_RECEIPT.json) (author raw cache required), [fixed-bin grouped calibration uncertainty](docs/CALIBRATION_FIXED_BIN_GROUPED_CI.md), [error audit](docs/ERROR_ANALYSIS.md) and [experiment register](docs/EXPERIMENT_REGISTER.md) preserve negative evidence without refitting TEST. The validation forecast CSV, reconstruction receipt and offline verification script are included; recreating source JSON requires OpenDota or the author's external cache.

A [development-only as-of audit](docs/VAL_TEST_LABEL_MATURITY_RECEIPT.json) finds no unfinished VALIDATION labels by the first TEST game start under the parsed start+duration proxy, but only **143 seconds** to spare and no real received-at proof.

The separate [November 100-game study](docs/FORWARD_100_STRESS.md) is **not** a blind second test: 68 games had been evaluated in a prior 120-game study and two leagues account for 85/100 games. Its probability CSV, per-match metadata, frozen candidate listing and independent source checks are included for audit, not pooled with the original TEST. Raw OpenDota match JSON is not included.

**Research history, without invented commit dates:** The included [decision trail](docs/RESEARCH_DECISION_TRAIL.md), [branch/PR map](docs/REVIEWER_HISTORY_MAP.md), [HISTORY.md](HISTORY.md) and [curation provenance](docs/CURATION_PROVENANCE.md) map the original research decisions. This GitHub repository preserves the original source main commit ancestry and selected historical branch heads. The ZIP independently contains the report, notebook, forecast files and scoring receipts; original GitHub PR discussion comments remain in the separately private source repository. No recruiter access has been granted.
