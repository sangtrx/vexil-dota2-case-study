# Reviewer guide · Vexil Dota 2

**Truong Quang Sang · Senior Data Scientist take-home**

## Read and run

1. Read [REPORT.pdf](REPORT.pdf) (four pages): model decision, test results, confidence intervals and failure cases.
2. Open [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb), the **one executable notebook**, with **16 executed code cells** and saved figures. The 14 original scientific cells are followed by two post-TEST audit cells; All have saved outputs except the original frozen-ID definitions cell.
3. To reproduce from public OpenDota, choose **CPU → Runtime → Run all** in Google Colab. No API key or extra local files are required. The notebook refetches the same 500 frozen match IDs; OpenDota rate limits can delay the run.

For exact local dependency pins, use **Python 3.12 (verified)**:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

For offline contract checks against the supplied predictions and figures:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

There are **172 offline unit/contract checks**. They do **not** replace a fresh notebook Run all.

**Submission archive:** delivery/Vexil_Dota2_Creative_Research_20261119.zip (scientific repair 19 November; outdated archives are preserved in Git history, not here).

## What is included

- [Frozen 3,836 TEST forecasts](artifacts/heldout_predictions.csv), with overall and phase-wise proper-score comparisons in the notebook and report.
- [Complete creative-feature and model-search atlas](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md): all P01–P28, S1–S4/M4, all 81 engineered column names, Q1, 84-input elastic-net/trees, direct XGBoost/LightGBM, nested tuning, transfer and stale-feed tests. The research readouts are **optional, post-result supplements** and not a second mandatory notebook or a new blind test.
- [Original cohort/discovery provenance](docs/DISCOVERY_PROVENANCE.md), including the unarchived raw discovery-page limitation.
- [TRAIN-only additive gold+time control](research/GOLD_INTERACTION_NULL_READOUT.md), [rejected-model register](docs/EXPERIMENT_REGISTER.md) and [independent-unit sensitivity](docs/TEAM_LEAGUE_DEPENDENCE.md).
- [Reproduction evidence](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json), including the original 16-cell BigLinux replay and the [Colab receipt](docs/COLAB_16CELL_RUN_RECEIPT.json).

**Interpretation:** M1 has lower point log loss than the required gold-only M0, but the main paired 95% interval includes zero; minute-30+ Brier is worse. Keep M0 as reference and M1 shadow-only. Corrected TEST scores were produced after the original TEST was inspected and are **not** a new blind evaluation. Raw 500-match JSON is not shipped; the notebook can refetch the public match IDs.

The [report](REPORT.pdf) contains the candidate's time estimate (approximately 10 active hours) and AI/public-code assistance disclosure, including separate XGBoost/LightGBM/Narwhals tooling. The estimate and applicant's own contribution still require **candidate confirmation before sending**. Original research history is in [HISTORY.md](HISTORY.md). The GitHub repo is private: **provide this ZIP/PDF directly unless reviewer access has actually been confirmed**; private PR discussions are not needed.
