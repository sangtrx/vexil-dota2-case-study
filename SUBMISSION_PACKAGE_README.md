# Submission package | Live Dota 2 win probabilities

Candidate: Truong Quang Sang
Project: Vexil Capital Senior Data Scientist take-home
Deadline: Thursday, 19 November 2026 (submission cutoff time zone not specified)

## Contents and reproducibility

1. REPORT.pdf is the separate three-page technical report, including decisions,
   ablations, uncertainty, limitations, approximately eight active work hours,
   and the assistance disclosure.
2. live_dota2_win_probability.ipynb is one executable notebook with 14 executed
   code cells and four embedded figures.
3. On Colab, select a CPU runtime with Internet and Run all. The notebook uses
   only the permitted OpenDota /proMatches and /matches/{match_id} endpoints,
   fetching a frozen 500-game manifest. On a local machine, install exact pins
   from requirements.txt, then run the notebook.
4. artifacts/heldout_predictions.csv exports all 3,836 held-out forecasts.
   It is a review artifact only; the notebook never loads it.
5. Four small test modules under tests/ run 51 offline unit/contract checks
   (no credentials, OpenDota calls or predownloaded match data).
6. docs/EXPERIMENT_REGISTER.md lists all nine project/research PRs,
   including the 28-model exploratory search with every negative result.
   This is an index to separate research branches, not a second report,
   and the standalone notebook does not run all those experiments.
7. Three real-data figures used in the report, including the phase error-audit chart, are included under docs/figures.
   The latest notebook has saved outputs and an 8-hour author-time disclosure.
   Earlier cold Kaggle/Colab runs verified the PREVIOUS inclusive-terminal scientific code. The corrected notebook was then executed locally against the frozen 500-game cache.
   The corrected source now excludes 12 terminal-boundary minute rows, so the exact current notebook has not yet had a new cold hosted run.

8. docs/ERROR_ANALYSIS.md and its frozen audit receipt expose the model's
   late-game calibration/Brier reversal and 55-row influential game.
   research/error_diagnostics.py reproduces those results without model
   fitting, and research/render_error_figure.py draws its optional chart.

PACKAGE_MANIFEST.json contains SHA-256 checksums for every entry. The package
contains no keys, private study notes, interview profile, or employer email.

## Outcome

Gold-only logistic baseline M0 was compared with validation-selected M1
(gold, elapsed minute, and their interaction). On 106 held-out games,
minute-weighted log loss changed 0.5164 to 0.5040 and Brier changed
0.1719 to 0.1684. Both paired whole-match 95% intervals for differences
include zero. M1's Brier at minute 30+ is worse. These historical
OpenDota forecasts neither prove true live-feed availability nor yield
a measured trading or betting profit.

**Reviewer handoff:** This is the original development repository, not a single-commit snapshot. Its main branch contains the final notebook, report and forecasts. [HISTORY.md](HISTORY.md) links to unchanged research branches and PR #3-#11. Historical experiments are not part of notebook Run All. Candidate-only interview/study files are not included.
