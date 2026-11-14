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
4. artifacts/heldout_predictions.csv exports all 3,837 held-out forecasts.
   It is a review artifact only; the notebook never loads it.
5. Three small test modules under tests/ run 41 offline unit/contract checks
   (no credentials, OpenDota calls or predownloaded match data).
6. Two real-data figures used in the report are included under docs/figures.
   The latest notebook has saved outputs and an 8-hour author-time disclosure.
   Earlier cold Kaggle/Colab runs verified the same scientific code; the setup
   disclosure and explanatory Markdown were corrected afterwards, then
   the whole notebook was re-executed locally against the frozen 500-game cache.

PACKAGE_MANIFEST.json contains SHA-256 checksums for every entry. The package
contains no keys, private study notes, interview profile, or employer email.

## Outcome

Gold-only logistic baseline M0 was compared with validation-selected M1
(gold, elapsed minute, and their interaction). On 106 held-out games,
minute-weighted log loss changed 0.5163 to 0.5039 and Brier changed
0.1719 to 0.1683. Both paired whole-match 95% intervals for differences
include zero. M1's Brier at minute 30+ is worse. These historical
OpenDota forecasts neither prove true live-feed availability nor yield
a measured trading or betting profit.
