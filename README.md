# Live Dota 2 Win Probability

A reproducible, minute-by-minute Radiant win-probability study using **500 parsed professional OpenDota matches** spanning patches 59 and 60 in March 2026. Prepared for the Vexil Capital Senior Data Scientist take-home.

The notebook estimates the probability that Radiant eventually wins using information available by game minute t. It compares the required **gold-lead-only logistic regression** with a validation-selected, interpretable **gold-and-time challenger**. This is a retrospective forecast study, not an authenticated live feed or a betting strategy.

## Results

| Metric | Gold-only baseline M0 | Selected challenger M1 |
| --- | ---: | ---: |
| Validation log loss (103 games) | 0.5321 | **0.5193** |
| Held-out log loss (106 games) | 0.5163 | **0.5039** |
| Held-out Brier score (106 games) | 0.1719 | **0.1683** |
| Held-out Brier, minute 30+ | **0.1028** | 0.1074 |

The paired whole-game bootstrap 95% interval for held-out **M1 minus M0** log loss is **[-0.0303, +0.0014]**; for Brier it is **[-0.0069, +0.0002]**. Both include zero. The challenger improves the overall point estimates, **not a conclusive population-level result**, and its late-game Brier score worsens.

The full results, ablations, uncertainty, calibration plots and limitations are in [REPORT.pdf](REPORT.pdf), a **four-page A4 report**.

**Full research inventory:** [Experiment register](docs/EXPERIMENT_REGISTER.md) covers all nine project/research PRs, every one of the **28 exploratory candidates** (log loss, Brier, multiplicity bounds, earlier folds and advancement decision), separate economic/strategic studies, a fixed gate on extra research matches, and negative tests. Research branches are *not* part of the notebook's Run All, and no additional model was selected by inspecting the frozen held-out test.

## Run the notebook

Use [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb). The notebook fetches its own data from the allowed OpenDota endpoints: `/api/proMatches` and `/api/matches/{match_id}`. It uses a frozen, explicit 250/250 match manifest. No credentials, uploaded datasets or other model inputs are required.

**Google Colab:** Open the notebook from this GitHub repository, choose a CPU runtime with Internet access and select **Runtime → Run all**. The setup cell checks the Python environment and installs required packages when missing. OpenDota may rate-limit requests; the collector uses bounded retry and refuses to silently substitute a different match.

**Local Python 3.11+:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Run all cells, top to bottom. `requirements.txt` pins the local Python dependencies.

**Offline verification (optional):** `python -m unittest discover -s tests -p "test_*.py" -q`. This runs 43 portable contracts for point-in-time features, report assets and frozen forecasts without calling OpenDota. The extended research/QA suite was independently run before the clean reviewer handoff.

## Files and review order

| File | Purpose |
| --- | --- |
| [REPORT.pdf](REPORT.pdf) | Four-page assessment report with real-data figures, results, limitations and required assistance disclosure |
| [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb) | Self-contained data collection, point-in-time features, M0–M3, validation, held-out scoring and saved outputs |
| [artifacts/heldout_predictions.csv](artifacts/heldout_predictions.csv) | **All 3,837** held-out predictions, one row per `(match_id, minute)`; never read as notebook input |
| [requirements.txt](requirements.txt) | Exact dependencies for local execution |
| [docs/figures/heldout_reliability.png](docs/figures/heldout_reliability.png) | Calibration view on actual held-out forecasts |
| [docs/figures/time_value_scenarios.png](docs/figures/time_value_scenarios.png) | Model's original time-value hypothesis, plotted only in training-supported states |
| [docs/EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) | All 9 project PRs and 28 exploratory hypotheses; supplemental source-linked experiment index, not a second assessment report |

Running the notebook also exports eight scientific CSV tables, four PNG figures and a JSON receipt. The included forecast CSV lets a reviewer inspect all held-out predictions without re-fetching 500 matches. The downloadable submission ZIP mirrors these files and includes SHA-256 checksums; it is not a separate model or input dataset.

## Methods and boundaries

- **Point in time:** economy arrays use only indices at or before minute `t`; logged events use timestamps no later than `60*t` seconds. Future/post-game feature-poisoning tests check the cutoff. A retrospective OpenDota replay does **not** prove that the same event was available to a production feed at that instant.
- **Validation:** chronological game-level train/validation/test split, keeping professional series together: **291 / 103 / 106 games** and **10,683 / 3,784 / 3,837 minute rows**. Training already includes 41 patch-60 games; this is not an unseen-patch test.
- **Models:** M0 is logistic regression on current gold difference. M1 adds elapsed minute and a gold-by-time interaction. M2 adds XP and five-minute velocity; M3 adds timestamped objectives and kill differential. All use the same `C=1` regularized logistic pipeline and train-only preprocessing. M1 was chosen by validation log loss.
- **Uncertainty:** paired bootstrap by whole match, rather than treating minute rows as independent labels. Same-series and league dependencies remain and can widen uncertainty. The 30+ minute phase is especially unstable.
- **Exploration:** the notebook includes a separate *development-only*, timestamped item-purchase hypothesis. Its validation score was not used to replace M1; it has no new held-out result and is not a deployed model.

The report records approximately **8 hours of active work**, excluding unattended API/cloud waiting, and discloses the coding/drafting assistance as required by the assignment. No trade execution, market prices or realised profitability are measured.
