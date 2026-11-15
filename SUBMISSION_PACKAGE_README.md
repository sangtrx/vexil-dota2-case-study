# Submission package | Live Dota 2 win probabilities

Candidate: Truong Quang Sang
Project: Vexil Capital Senior Data Scientist take-home
Deadline: Thursday, 19 November 2026 (exact submission cutoff time not confirmed)

## Contents and reproducibility

1. REPORT.pdf is the separate four-page technical report, including decisions,
   ablations, uncertainty, limitations, approximately 10 active work hours,
   and the assistance disclosure.
2. live_dota2_win_probability.ipynb is one executable notebook with 14 executed
   code cells and four embedded figures.
3. On Colab, select a CPU runtime with Internet and Run all. The notebook uses
   only the permitted OpenDota /proMatches and /matches/{match_id} endpoints,
   fetching a frozen 500-game manifest. On a local machine, install exact pins
   from requirements.txt, then run the notebook.
4. artifacts/heldout_predictions.csv exports all 3,836 held-out forecasts.
   It is a review artifact only; the notebook never loads it.
5. Four test modules under tests/ run 57 offline unit/contract checks
   (no credentials, OpenDota calls or predownloaded match data).
6. docs/EXPERIMENT_REGISTER.md lists nine historical research PRs (#3-#11),
   including the 28-model exploratory search with every negative result.
   This is an index to separate research branches, not a second report,
   and the standalone notebook does not run all those experiments.
7. Four real-data figures used in the report, including the phase error-audit chart, are included under docs/figures.
   The latest notebook has saved outputs and a 10-hour active-work estimate.
   Historical Kaggle QA covered the inclusive-terminal predecessor. A fresh Google Colab CPU Run all on 15 November fetched all 500 frozen games (514 API calls, zero cache hits), completed 14/14 cells and reproduced rounded held-out scores. The scientific code SHA matches main. The hosted notebook predates later markdown-only edits and the cloud-export CSV was not recovered for bytewise SHA comparison; see docs/COLAB_COLD_RUN_RECEIPT.json.

8. docs/ERROR_ANALYSIS.md, its frozen audit receipt, and the series-cluster sensitivity receipt expose the model's
   original-TEST late-phase Brier/ECE **descriptive point reversal** (not confirmed) and 55-row influential game.
   research/error_diagnostics.py reproduces those results without model
   fitting, and research/render_error_figure.py draws its optional chart.

PACKAGE_MANIFEST.json contains SHA-256 checksums for every entry. The package
contains no keys, private study notes, interview profile, or employer email.

## Outcome

Gold-only logistic baseline M0 was compared with validation-selected M1
(gold, elapsed minute, and their interaction). On 106 held-out games,
minute-weighted log loss changed 0.5164 to 0.5040 and Brier changed
0.1719 to 0.1684. Both paired whole-match 95% intervals for differences
include zero. On the original TEST, M1's 30+ Brier point estimate is
0.0046 worse, but its paired 95% interval [−0.0037,+0.0109] crosses zero.
A separate later 200-game development cohort favors M1 on aggregate point
scores, not as new confirmatory evidence. These historical OpenDota forecasts
neither prove true live-feed availability nor yield
a measured trading or betting profit.

**Reviewer handoff:** This is a **curated delivery repository** assembled on 15 November 2026, not a simulated chronological research log. Its main contains the reviewed notebook, report, figures, forecasts and reproducible archive. [HISTORY.md](HISTORY.md) explains that the complete original 13–15 November development commit graph and PRs are preserved in the [source repository](https://github.com/sangtrx/vexil-dota2-win-probability); the candidate can grant access separately. Historical research scores and negative findings are also reproduced within the included EXPERIMENT_REGISTER.md. Research branches are not part of notebook Run All. Candidate-only interview/study files are not included.
