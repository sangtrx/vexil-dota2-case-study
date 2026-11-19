# Live Dota 2 Win Probability

**Vexil Capital · Senior Data Scientist take-home · Truong Quang Sang**

I tested whether match time adds useful information beyond gold lead when predicting Radiant's win probability. The study uses **500 professional OpenDota games across patches 59 and 60** and only features timestamped at or before each forecast minute. The deliverables are one executed notebook and a four-page report.

**Start with:** [Report](REPORT.pdf) · [Executed notebook](live_dota2_win_probability.ipynb) · [Run instructions](SUBMISSION_PACKAGE_README.md) · [Additional experiments](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md)

## What the evidence supports

| TEST, 106 games / 3,836 minute forecasts | Gold-only M0 | Gold + time + interaction M1 |
| --- | ---: | ---: |
| Log loss ↓ | 0.5164 | **0.5040** |
| Brier score ↓ | 0.1719 | **0.1684** |
| 30+ minute Brier ↓ | **0.1028** | 0.1074 |

M1 had lower validation loss on 103 games. On TEST, though, the paired whole-match 95% intervals for M1−M0 include zero: **log loss [−0.0304,+0.0014]** and **Brier [−0.0069,+0.0002]**. Late-game Brier is worse, the interaction helps in only **1/4** TRAIN-forward folds against additive gold + time, and one game accounts for 54.9% of the **overall** observed log-loss gain. **I recommend M0 as the reference and M1 only for future shadow evaluation.** The report shows the uncertainty by match and series.

**Reviewer ZIP:** [delivery/Vexil_Dota2_Takehome_20261119.zip](delivery/Vexil_Dota2_Takehome_20261119.zip). This concise bundle contains the one executed notebook, four-page report, dependencies, frozen VAL/TEST forecasts, a short experiment appendix and statistical receipts. The wider scripts, historical protocols and 181 offline tests remain in this private research repository rather than the email attachment.

## Run the notebook

**Google Colab:** Upload `live_dota2_win_probability.ipynb`, use a CPU runtime with Internet, and choose Runtime → Run all. The notebook requests the same **500 frozen match IDs** through `/matches/{match_id}`, rather than resampling a changing `/proMatches` feed. It needs no API key; OpenDota rate limits can make a full run slow. Colab's preinstalled scientific libraries may differ from the pinned local versions; compare saved results within reasonable numeric precision, not CSV bytes. A fresh Colab CPU Run All on **19 November 2026** used the **exact shipped notebook source**: 16/16 code cells executed without errors, 500 matches loaded and TEST scores matched to six decimals (docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json). The executed Colab export has different bytes because outputs and metadata were rewritten; scientific source code is unchanged.

**Local Python 3.12 (verified with exact pins):**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Run all notebook cells top to bottom. The **16 code cells** comprise 14 core science/diagnostic cells (some amended after initial TEST inspection) and two appended reviewer QA cells. All executable cells have saved outputs except the frozen-ID definitions cell. The notebook includes whole-match bootstrap intervals for each model and their difference, overall and by match phase.

For a quick **offline** verification of frozen forecasts, models, figures and report contracts:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

This runs **188 offline checks** without downloading raw matches. A full local fresh-kernel replay of the original 500 raw match payloads was performed on a local Linux machine, but that cache is **not bundled**. Running the notebook anew requires public OpenDota access; offline tests are not a substitute for that Run all.

## Data and interpretation boundaries

The 500-game [discovery record](docs/DISCOVERY_PROVENANCE.md) explains the original `/proMatches` pagination, the 250/250 patch cohort and the frozen IDs. Raw discovery pages were not archived. The March 2026 sample spans only 5.26 days, and **TRAIN already includes 41 games from patch 60**. VALIDATION and TEST are patch 60 as well.

The source 291/103/106 TRAIN/VALIDATION/TEST split is chronological and series-disjoint. A [point-in-time audit](docs/FULL_500_PREFIX_AUDIT_RECEIPT.json) checked 18,292 original minute snapshots against future-deleted inputs; its full rerun needs the author's raw cache. After inspecting TEST, 12 terminal rows were corrected, so the reported TEST is **not newly blind**. A [label-maturity audit](docs/DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md) refit on 286 TRAIN games whose outcomes had ended by the first validation start. This uses a match-end proxy; actual feed `received_at` remains unobserved.

Development-only lag-buffer stress and the pre/post-TEST correction history are in [Reviewer scientific limits](docs/REVIEWER_SCIENTIFIC_LIMITS.md). An optional 100-game November check is [reported separately](docs/FORWARD_100_STRESS.md). Its overall log-loss interval includes zero and **68 games overlap** a previous 120-game research set; it is not an independent replication. More extensive out-of-time October analysis is in a separate research branch, **not** silently inserted into this required 500-game notebook.

## Evidence and source history

| Question | Where to verify |
| --- | --- |
| Cohort selection and timestamp limits | [Discovery provenance](docs/DISCOVERY_PROVENANCE.md), [PIT receipt](docs/FULL_500_PREFIX_AUDIT_RECEIPT.json) |
| Why M1 was chosen, and why the interaction is unconfirmed | [Research decision trail](docs/RESEARCH_DECISION_TRAIL.md), [TRAIN additive-null check](research/GOLD_INTERACTION_NULL_READOUT.md) |
| Feature research, including the Roshan parser correction | [Research atlas](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md), [Roshan correction](research/ROSHAN_CORRECTION_20261119.md), [P01–P28 register](docs/EXPERIMENT_REGISTER.md), [research-only branch map](docs/RECORDED_RESEARCH_BRANCHES.md) |
| Error slices, dependence and calibration | [Error analysis](docs/ERROR_ANALYSIS.md), [Team/league audit](docs/TEAM_LEAGUE_DEPENDENCE.md), [Calibration](docs/CALIBRATION_BIAS_READOUT.md) |
| Reproduction evidence and environment differences | [16-cell BigLinux replay](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json), [16-cell Colab receipt](docs/COLAB_16CELL_RUN_RECEIPT.json), [historical 14-cell cloud receipt](docs/COLAB_COLD_RUN_RECEIPT.json) |
| Research and curation history | [HISTORY.md](HISTORY.md), [Branch/PR map](docs/REVIEWER_HISTORY_MAP.md), [Curation provenance](docs/CURATION_PROVENANCE.md) |

Original GitHub PR discussions remain in a separately private repo; they are not required to review the ZIP. The package contains the notebook, report, frozen TEST predictions and offline checks. The report states the **10-hour active-work estimate** and discloses AI and open-source tools.
