# Reviewer guide | Vexil Dota 2 win-probability take-home

Candidate: Truong Quang Sang

**Start here (3 minutes):** read [REPORT.pdf](REPORT.pdf), then open the [executed notebook](live_dota2_win_probability.ipynb), inspect its four saved figures and the [3,836 frozen TEST forecasts](artifacts/heldout_predictions.csv). The four-page report includes model reasoning, negative results, approximate **10 active work hours** and the AI/public-code assistance disclosure.

The notebook implements the required gold-lead logistic baseline M0 and the validation-selected gold × time challenger M1 on 500 professional OpenDota matches. Chronological, series-grouped TRAIN/VALIDATION/TEST partitions have 291/103/106 games. M1 has TEST log loss 0.5040 versus M0 0.5164; both primary whole-match confidence intervals for the difference cross zero. The original TEST minute-30+ Brier point difference is **0.00455** worse for M1, with a paired interval **[−0.0037,+0.0109]**. Keep M0 as reference and M1 shadow-only.

## How to rerun

On Google Colab: upload the notebook, select CPU runtime with Internet, and Run all. It fetches a frozen set of 500 game IDs using the public /proMatches and /matches/{match_id} endpoints; no API credentials are required. OpenDota may rate-limit requests.

On **Python 3.12 (verified)** locally:

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
~~~

The notebook has 14 executed code cells; 13 have saved outputs, while the frozen-cohort definitions cell has no output by design. The local and fresh Colab reproduction receipts are [here](docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json) and [here](docs/COLAB_COLD_RUN_RECEIPT.json). The author-controlled local replay used 500 cached raw match records **not bundled in the ZIP** and reproduced the full TEST forecast CSV byte-for-byte. A new reviewer can rerun the notebook only with live OpenDota access. Colab reproduced rounded numbers and model-code hash; cloud CSV byte parity was not verified.

For **offline** score/contract verification from the ZIP (not a fresh notebook Run all), without API keys or private research access:

~~~bash
python -m unittest discover -s tests -p "test_*.py" -q
~~~

Eleven test modules contain **111 offline unit/contract checks**. The ZIP manifest lists SHA-256 checksums for every file.

## What is supplementary

The report's original 500-game TEST is the core assessment. The [error audit](docs/ERROR_ANALYSIS.md), [VALIDATION/TEST calibration audit](docs/CALIBRATION_BIAS_READOUT.md) and [experiment register](docs/EXPERIMENT_REGISTER.md) document uncertainty, failure analysis and rejected hypotheses without refitting on TEST. The validation forecast CSV, reconstruction receipt and offline verification script are included; recreating source JSON requires OpenDota or the author's external cache.

The separate [November 100-game study](docs/FORWARD_100_STRESS.md) is **not** a blind second test: 68 games had been evaluated in a prior 120-game study and two leagues account for 85/100 games. Its probability CSV, per-match metadata, frozen candidate listing and independent source checks are included for audit, not pooled with the original TEST. Raw OpenDota match JSON is not included.

**Research history, without invented commit dates:** The included [decision trail](docs/RESEARCH_DECISION_TRAIL.md), [branch/PR map](docs/REVIEWER_HISTORY_MAP.md), [HISTORY.md](HISTORY.md) and [curation provenance](docs/CURATION_PROVENANCE.md) map the original research decisions. This GitHub repository preserves the original source main commit ancestry and selected historical branch heads. The ZIP independently contains the report, notebook, forecast files and scoring receipts; original GitHub PR discussion comments remain in the separately private source repository. No recruiter access has been granted.
