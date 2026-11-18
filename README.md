# Live Dota 2 Win Probability

**Vexil Capital · Senior Data Scientist take-home · Truong Quang Sang**

This study estimates Radiant's win probability at a given match minute using **500 professional OpenDota games across patches 59 and 60**. The core deliverable is one executed notebook and a four-page report. Forecast features are drawn from information timestamped at or before the decision minute.

**Start here:** [Four-page report](REPORT.pdf) · [Executed notebook](live_dota2_win_probability.ipynb) · [Reviewer guide](SUBMISSION_PACKAGE_README.md) · [Full creative-feature and model-search atlas](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md)

## What the evidence supports

| TEST, 106 games / 3,836 minute forecasts | Gold-only M0 | Gold + time + interaction M1 |
| --- | ---: | ---: |
| Log loss ↓ | 0.5164 | **0.5040** |
| Brier score ↓ | 0.1719 | **0.1684** |
| 30+ minute Brier ↓ | **0.1028** | 0.1074 |

M1 was selected on 103 validation games, but its **paired whole-match 95% log-loss CI for M1−M0 is [−0.0304,+0.0014]**; the Brier interval **[−0.0069,+0.0002]** also includes zero. M1's late-game Brier score is worse. **Decision: keep M0 as reference and evaluate M1 in shadow mode.** The report details both match/series uncertainty and the stronger additive gold + time control; the interaction improved loss in only **1/4** TRAIN-forward folds. A separate TRAIN-forward M0−M1 comparison has almost zero log-loss gain and worse M1 Brier; one held-out match drives most observed late-game log-loss benefit.

**Current reviewer ZIP:** delivery/Vexil_Dota2_Creative_Research_20261119.zip (includes optional creativity atlas; no new model promoted). Earlier ZIPs remain accessible from Git history but are not in this delivery directory.

## Run the notebook

**Google Colab:** Upload `live_dota2_win_probability.ipynb`, use a CPU runtime with Internet, and choose Runtime → Run all. The notebook requests the same **500 frozen match IDs** through `/matches/{match_id}`, rather than resampling a changing `/proMatches` feed. It needs no API key; OpenDota rate limits can make a full run slow. Colab's preinstalled scientific libraries may differ from the pinned local versions; compare saved results within reasonable numeric precision, not CSV bytes. The archived 16-cell Colab receipt covers an **earlier notebook revision**, not a cloud rerun of the exact shipped file.

**Local Python 3.12 (verified with exact pins):**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Run all notebook cells top to bottom. The **16 code cells** comprise the 14 original scientific cells and two after-TEST diagnostics. All executable cells have saved outputs except the frozen-ID definitions cell. The notebook includes whole-match bootstrap intervals for each model and their difference, overall and by match phase.

For a quick **offline** verification of frozen forecasts, models, figures and report contracts:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

This runs **172 offline checks** without downloading raw matches. A full local fresh-kernel replay of the original 500 raw match payloads was performed on BigLinux, but that cache is **not bundled**. Running the notebook anew requires public OpenDota access; offline tests are not a substitute for that Run all.

## Data and interpretation boundaries

The 500-game [discovery record](docs/DISCOVERY_PROVENANCE.md) explains the original `/proMatches` pagination, the 250/250 patch cohort and the frozen IDs. Raw discovery pages were not archived. The March 2026 sample spans only 5.26 days, and **TRAIN already includes 41 games from patch 60**. VALIDATION and TEST are patch 60 as well.

The source 291/103/106 TRAIN/VALIDATION/TEST split is chronological and series-disjoint. A [point-in-time audit](docs/FULL_500_PREFIX_AUDIT_RECEIPT.json) checked 18,292 original minute snapshots against future-deleted inputs; its full rerun needs the author's raw cache. After inspecting TEST, 12 terminal rows were corrected, so the reported TEST is **not newly blind**. A [label-maturity audit](docs/DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md) refit on 286 TRAIN games whose outcomes had ended by the first validation start. This uses a match-end proxy; actual feed `received_at` remains unobserved.

An optional 100-game November check is [reported separately](docs/FORWARD_100_STRESS.md). Its overall log-loss interval includes zero and **68 games overlap** a previous 120-game research set; it is not an independent replication. More extensive out-of-time October analysis is in a separate research branch, **not** silently inserted into this required 500-game notebook.

## Evidence and source history

| Question | Where to verify |
| --- | --- |
| Cohort selection and timestamp limits | [Discovery provenance](docs/DISCOVERY_PROVENANCE.md), [PIT receipt](docs/FULL_500_PREFIX_AUDIT_RECEIPT.json) |
| Why M1 was chosen, and why the interaction is unconfirmed | [Research decision trail](docs/RESEARCH_DECISION_TRAIL.md), [TRAIN additive-null check](research/GOLD_INTERACTION_NULL_READOUT.md) |
| Full creative feature hypotheses, 28-way screen, 81-feature study and XGB/LGBM | [Creative research atlas](docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md), [original P01–P28 register](docs/EXPERIMENT_REGISTER.md) |
| Error slices, dependence and calibration | [Error analysis](docs/ERROR_ANALYSIS.md), [Team/league audit](docs/TEAM_LEAGUE_DEPENDENCE.md), [Calibration](docs/CALIBRATION_BIAS_READOUT.md) |
| Reproduction evidence and environment differences | [16-cell BigLinux replay](docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json), [16-cell Colab receipt](docs/COLAB_16CELL_RUN_RECEIPT.json), [historical 14-cell cloud receipt](docs/COLAB_COLD_RUN_RECEIPT.json) |
| Authentic research and curation history | [HISTORY.md](HISTORY.md), [Branch/PR map](docs/REVIEWER_HISTORY_MAP.md), [Curation provenance](docs/CURATION_PROVENANCE.md) |

Original GitHub PR discussions remain in a separately private repo. The notebook, report and frozen TEST predictions are included in this package; a reviewer does **not** need those private discussions to inspect the scientific results. **Repository visibility is private; without an invitation, use the attached ZIP/PDF rather than relying on GitHub links.** The report separately presents applicant-estimated active hours and the AI/public-code disclosure; neither is an independently audited work log.
