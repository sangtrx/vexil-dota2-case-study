# Reproducing the Dota 2 take-home

**Truong Quang Sang · Senior Data Scientist take-home**

## Read and run

1. Read [REPORT.pdf](REPORT.pdf) (four pages): model decision, test results, confidence intervals and failure cases.
2. Open [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb), the **one executable notebook**, with **16 executed code cells** and saved figures. The 14 core study/diagnostic cells (including post-TEST corrections) are followed by two reviewer QA cells. All have saved outputs except the original frozen-ID definitions cell.
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

There are **180 offline unit/contract checks**. They do **not** replace a fresh notebook Run all.

**Package:** Vexil_Dota2_Creative_Research_20261119.zip (19 November 2026). This guide is inside the extracted ZIP.

## What is included

- [Frozen 3,836 TEST forecasts](artifacts/heldout_predictions.csv), with overall and phase-wise proper-score comparisons in the notebook and report.
- [Additional experiments](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md) and the [Roshan parser correction](research/ROSHAN_CORRECTION_20261119.md): 28 adaptive screens, 81 engineered features, Q1 and fixed linear/tree models. These are post-result supplements, not another blind test.
- [Original cohort/discovery provenance](docs/DISCOVERY_PROVENANCE.md), including the unarchived raw discovery-page limitation.
- [TRAIN-only additive gold+time control](research/GOLD_INTERACTION_NULL_READOUT.md), [rejected-model register](docs/EXPERIMENT_REGISTER.md) and [independent-unit sensitivity](docs/TEAM_LEAGUE_DEPENDENCE.md).
- [Development-only timing and model-selection sensitivity](docs/REVIEWER_SCIENTIFIC_LIMITS.md), plus the reproducible [historical TEST correction receipt](docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json) from both frozen forecast CSVs.
- [Reproduction evidence](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json), including the exact-source 16-cell BigLinux local replay and an [earlier-revision Colab receipt](docs/COLAB_16CELL_RUN_RECEIPT.json), **not** a verified cloud Run All of the current notebook bytes.

**Interpretation:** M1 has lower point log loss than the required gold-only M0, but the main paired 95% interval includes zero; minute-30+ Brier is worse. Keep M0 as reference and M1 shadow-only. Corrected TEST scores were produced after the original TEST was inspected and are **not** a new blind evaluation. Raw 500-match JSON is not shipped; the notebook can refetch the public match IDs.

The [report](REPORT.pdf) includes the candidate's time estimate of approximately **10 hours of active work** and explains where AI and open-source tools were used. Research provenance is in [HISTORY.md](HISTORY.md). This ZIP and PDF can be read without access to the private GitHub repository.
