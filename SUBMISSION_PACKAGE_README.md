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

The local repository contains the offline test suite (181 at the prior checkpoint, plus new September and delivery checks). These files are **not in the concise ZIP** and do **not** replace a fresh notebook Run all.

**Reviewer package:** [delivery/Vexil_Dota2_Takehome_20261119.zip](delivery/Vexil_Dota2_Takehome_20261119.zip) (19 November 2026). Its extracted [README](delivery/REVIEWER_README.md) is intentionally short; the full source research archive and offline test suite remain available in this repository.

## What is included

- [Frozen 3,836 TEST forecasts](artifacts/heldout_predictions.csv), with overall and phase-wise proper-score comparisons in the notebook and report.
- [Additional experiments](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md), [full feature table in ZIP](delivery/FEATURE_SCREEN_AND_FAILURES.md), and the [Roshan parser correction](research/ROSHAN_CORRECTION_20261119.md): 28 adaptive screens, 81 engineered fields, Q1 and fixed linear/tree models. These are post-result supplements, not another blind test.
- [Separate September external results](research/september_external/README.md): a preregistered 199-game M1 support result outside the 500-game employer notebook, three leagues only, with frozen CSV and an offline verifier in the private repository.
- [Original cohort/discovery provenance](docs/DISCOVERY_PROVENANCE.md), including the unarchived raw discovery-page limitation.
- [TRAIN-only additive gold+time control](research/GOLD_INTERACTION_NULL_READOUT.md), [rejected-model register](docs/EXPERIMENT_REGISTER.md) and [independent-unit sensitivity](docs/TEAM_LEAGUE_DEPENDENCE.md).
- [Development-only timing and model-selection sensitivity](docs/REVIEWER_SCIENTIFIC_LIMITS.md), plus the reproducible [historical TEST correction receipt](docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json) from both frozen forecast CSVs.
- [Reproduction evidence](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json), including the exact-source local replay, historical [earlier-revision Colab receipt](docs/COLAB_16CELL_RUN_RECEIPT.json), and a [19 November fresh Colab Run All](docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json) of the current notebook's source (16/16 cells, zero errors). Colab's exported notebook bytes differ due to output metadata, not source-code edits.

**Interpretation:** M1 has lower point log loss in the original 500-game evaluation and in the separately frozen September cohort. The March paired 95% interval includes zero, and March minute-30+ Brier is worse; the September series interval excludes zero in only three leagues with dependent teams. Keep M0 as baseline, prioritize M1 for shadow testing, not production. Corrected TEST scores were produced after the original TEST was inspected and are **not** a new blind evaluation. Raw 500-match JSON is not shipped; the notebook can refetch the public match IDs.

The [report](REPORT.pdf) includes the candidate-confirmed **10 hours of active human work**, excluding unattended runs and explains where AI and open-source tools were used. Research provenance is in [HISTORY.md](HISTORY.md). This ZIP and PDF can be read without access to the private GitHub repository.
