# Live Dota 2 Win Probability

A reproducible, minute-by-minute Radiant win-probability study using **500 parsed professional OpenDota matches** spanning patches 59 and 60 in March 2026. Prepared for the Vexil Capital Senior Data Scientist take-home.

The notebook estimates the probability that Radiant eventually wins using information available by game minute t. It compares the required **gold-lead-only logistic regression** with a validation-selected, interpretable **gold-and-time challenger**. This is a retrospective forecast study, not an authenticated live feed or a betting strategy.

## Results

| Metric | Gold-only baseline M0 | Selected challenger M1 |
| --- | ---: | ---: |
| Validation log loss (103 games) | 0.5325 | **0.5197** |
| Held-out log loss (106 games) | 0.5164 | **0.5040** |
| Held-out Brier score (106 games) | 0.1719 | **0.1684** |
| Held-out Brier, minute 30+ | **0.1028** | 0.1074 |

The paired whole-game bootstrap 95% interval for held-out **M1 minus M0** log loss is **[-0.0304, +0.0014]**; for Brier it is **[-0.0069, +0.0002]**. Both include zero. M1 improves the aggregate point estimates without conclusive primary evidence; its **30+ Brier point estimate** is worse by 0.0046, but the paired 95% interval **[−0.0037,+0.0109]** spans zero. A later 200-game development cohort also favors M1 on aggregate point scores.

The full results, ablations, uncertainty, calibration plots and limitations are in [REPORT.pdf](REPORT.pdf), a 4-page A4 report. **Read first:** [report](REPORT.pdf) → [notebook](live_dota2_win_probability.ipynb) → [research history](HISTORY.md).

**Read-only failure audit:** [Error analysis](docs/ERROR_ANALYSIS.md) explains phase calibration, the late-game Brier reversal, 54-series sensitivity and match-level influence; a small [offline verification script](research/error_diagnostics.py) recalculates held-out phase scores, ECE and influential matches from the frozen forecast CSV without model refitting. **One 55-row game explains 54.9% of the sample log-loss gain**, another reason not to treat the M1 point estimate as a confirmed improvement.

**Terminal-boundary correction:** Predictions now require the strict inequality 60t < duration. Twelve post-terminal snapshots across the original 500 games were removed (8 TRAIN, 3 VALIDATION, 1 TEST). The full corrected notebook was replayed locally from 500 cached match records with zero HTTP calls, 14/14 executed code cells and four figures. A **fresh Google Colab CPU Run all (15 November 2026)** fetched the 500 frozen games (514 API calls, zero cache hits), completed **14/14 code cells without error** and reproduced the selected model and held-out scores to 4 decimals. Its scientific-code SHA matches this repository; the uploaded notebook predates later markdown-only edits and the cloud-export CSV was not recovered for bytewise comparison. See the [Colab execution receipt](docs/COLAB_COLD_RUN_RECEIPT.json). Older Kaggle QA covered the inclusive-terminal predecessor.

**Full research history:** [Original commits and PRs](HISTORY.md) links to the authentic branches and experiments preserved in the separate development repository. The complete negative-result table is included here. [Experiment register](docs/EXPERIMENT_REGISTER.md) summarizes nine historical research workstreams and all **28 exploratory candidate scores** (log loss, Brier, multiplicity bounds, earlier folds and advancement decision), separate economic/strategic studies, a fixed gate on extra research matches, and negative tests. Research branches are not needed to run the core notebook; historical development tests were not used to promote a new model using the exposed held-out data.

## One-page decision summary

**The defensible choice is not the most expressive model.** I selected the smallest validation-winning challenger, retained negative research screens, and avoided promoting it because the original paired overall uncertainty still spans zero and actual live-feed receipt is unverified. M1's aggregate point-score advantage recurs on 200 later development games; its 30+ Brier reversal on the original TEST remains descriptive and inconclusive. A future-series evaluation with verified source timing is the next decision point.

The [three-minute reviewer path](SUBMISSION_PACKAGE_README.md) is report → executed notebook → frozen forecasts → error audit. **Figure 2** of the four-figure report shows a real held-out game trajectory, selected by gold-lead range rather than model performance.

**Provenance:** This repository presents a curated final deliverable assembled on **15 November 2026**. Its short commit history is a packaging history, **not a reconstruction of when the research experiments were performed**. The [original repository](https://github.com/sangtrx/vexil-dota2-win-probability) preserves the full authentic development history and negative research PRs; [HISTORY.md](HISTORY.md) maps them. The included report, notebook and experiment register are self-contained for assessment without relying on those external PR links.

## Run the notebook

Use [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb). The notebook fetches its own data from the allowed OpenDota endpoints: `/api/proMatches` and `/api/matches/{match_id}`. It uses a frozen, explicit 250/250 match manifest. No credentials, uploaded datasets or other model inputs are required.

**Google Colab:** With repo access, download the notebook file from GitHub and select **File → Upload notebook** in Colab, then choose a CPU runtime with Internet and **Runtime → Run all**. Direct private-GitHub import may require separately authorizing GitHub in Colab. The setup cell checks the Python environment and installs required packages when missing. OpenDota may rate-limit requests; the collector uses bounded retry and refuses to silently substitute a different match.

**Local Python 3.11+:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Run all cells, top to bottom. `requirements.txt` pins the local Python dependencies.

**Offline verification (optional):** `python -m unittest discover -s tests -p "test_*.py" -q`. This runs 56 offline checks covering point-in-time logic, frozen forecast scores and report/package contracts, without OpenDota calls. These tests are **not** a substitute for an independent hosted full notebook replay.

## Files and review order

| File | Purpose |
| --- | --- |
| [REPORT.pdf](REPORT.pdf) | Four-page assessment report with four real-data figures, results, limitations and required assistance disclosure |
| [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb) | Self-contained data collection, point-in-time features, M0–M3, validation, held-out scoring and saved outputs |
| [artifacts/heldout_predictions.csv](artifacts/heldout_predictions.csv) | **All 3,836** held-out predictions, one row per `(match_id, minute)`; never read as notebook input |
| [requirements.txt](requirements.txt) | Exact dependencies for local execution |
| [docs/figures/heldout_reliability.png](docs/figures/heldout_reliability.png) | Calibration view on actual held-out forecasts |
| [docs/figures/time_value_scenarios.png](docs/figures/time_value_scenarios.png) | Fitted time-value hypothesis, plotted only in training-supported states |
| [docs/figures/heldout_game_trajectory.png](docs/figures/heldout_game_trajectory.png) | Real held-out match: gold lead and minute-by-minute M0/M1 forecast trajectories |
| [docs/figures/phase_error_audit.png](docs/figures/phase_error_audit.png) | Error diagnosis by phase, including the late-game Brier and ECE reversal; post-hoc descriptive |
| [docs/EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) | Nine original research PRs (#3–#11) and 28 exploratory hypotheses; not a second assessment report |
| [docs/COLAB_COLD_RUN_RECEIPT.json](docs/COLAB_COLD_RUN_RECEIPT.json) | Fresh Colab 14/14 execution receipt, science-code fingerprint, runtime versions, and explicitly unverified CSV-byte parity |
| [docs/SERIES_CI_RECEIPT.json](docs/SERIES_CI_RECEIPT.json) | Post-hoc series-cluster uncertainty, 54 series and 10,000 resamples; [offline audit](research/series_cluster_sensitivity.py) |
| [docs/ERROR_ANALYSIS.md](docs/ERROR_ANALYSIS.md) | Reproducible post-hoc failure diagnosis: phase ECE/Brier, match influence and model-governance boundaries |

Running the notebook also exports eight scientific CSV tables, four PNG figures and a JSON receipt. The included forecast CSV lets a reviewer inspect all held-out predictions without re-fetching 500 matches. The downloadable submission ZIP mirrors these files and includes SHA-256 checksums; it is not a separate model or input dataset.

## Methods and boundaries

- **Point in time:** economy arrays use only indices at or before minute `t`; logged events use timestamps no later than `60*t` seconds. Future/post-game feature-poisoning tests check the cutoff. A retrospective OpenDota replay does **not** prove that the same event was available to a production feed at that instant.
- **Validation:** chronological game-level train/validation/test split, keeping professional series together: **291 / 103 / 106 games** and **10,675 / 3,781 / 3,836 minute rows**. Training already includes 41 patch-60 games; this is not an unseen-patch test.
- **Models:** M0 is logistic regression on current gold difference. M1 adds elapsed minute and a gold-by-time interaction. M2 adds XP and five-minute velocity; M3 adds timestamped objectives and kill differential. All use the same `C=1` regularized logistic pipeline and train-only preprocessing. M1 was chosen by validation log loss.
- **Uncertainty:** paired bootstrap by whole match, rather than treating minute rows as independent labels. Same-series and league dependencies remain and can widen uncertainty. The 30+ minute phase is especially unstable.
- **Exploration:** the notebook includes a separate *development-only*, timestamped item-purchase hypothesis. Its validation score was not used to replace M1; it has no new held-out result and is not a deployed model.

Approximately **10 hours of active work** were spent, excluding unattended AI/API/cloud runs. AI assistance is disclosed in REPORT.pdf. No trade execution, market prices or realised profitability are measured.
