# Research history

This is the original development repository for the Vexil Capital Dota 2 take-home. Original commit timestamps, authors and PR branches have been retained. No backdated, reordered or simulated commit history was created for submission.

Read [REPORT.pdf](REPORT.pdf) and [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb) on main first. The research branches below document exploratory experiments and negative results. They are **not** all executed by the submission notebook and most were **not** selected. The original development history is a branching graph, not one artificial linear series. New handoff fixes are committed with their actual dates.

**PR disposition (15 November 2026):** #3-#10 are closed without merge as completed research archives; #11 merged the final notebook/report, #12 corrected the handoff, #13 records the fresh Colab execution, and #14 adds a post-hoc series-dependence sensitivity without changing the model. Closing a PR does not delete its branch, commits or experiment receipts. For a quick technical audit, read #3 → #6 → #9 → #11 → #12; the other PRs document separate negative experiments and QA.

## Actual research PRs

| PR | Status | Research branch | Work / conclusion |
|---|---|---|---|
| [#3](https://github.com/sangtrx/vexil-dota2-win-probability/pull/3) | Archived (not merged) | research/pit-validation-20261113 | Point-in-time notebook, 500 frozen matches, M0-M3, temporal split; M1 selected on validation |
| [#4](https://github.com/sangtrx/vexil-dota2-win-probability/pull/4) | Archived (not merged) | research/structural-edge-20261113 | S1-S4 structural economy and 200-game stage gate; no model promoted |
| [#5](https://github.com/sangtrx/vexil-dota2-win-probability/pull/5) | Archived (not merged) | research/option-value-novelty-20261113 | Aegis/buyback M4, event-clock integrity, negative results |
| [#6](https://github.com/sangtrx/vexil-dota2-win-probability/pull/6) | Archived (not merged) | research/proposal-factory-20261113 | 28 candidate specifications, familywise screening; 0/28 passed promotion gates |
| [#7](https://github.com/sangtrx/vexil-dota2-win-probability/pull/7) | Archived (not merged) | research/bible-vexil-20261113 | Stability and OOB/CSCV checks, historical Kaggle QA |
| [#8](https://github.com/sangtrx/vexil-dota2-win-probability/pull/8) | Archived (not merged) | research/vexil-submission-polish-20261113 | P20 item-timing development test; earlier portable notebook/PDF |
| [#9](https://github.com/sangtrx/vexil-dota2-win-probability/pull/9) | Archived (not merged) | research/vexil-robustness-lab-20261113 | Metamorphic tests, rolling TRAIN-only folds, malformed inputs |
| [#10](https://github.com/sangtrx/vexil-dota2-win-probability/pull/10) | Archived (not merged) | fix/vexil-delivery-audit-20261114 | Historical Kaggle/Colab evidence and delivery integrity |
| [#11](https://github.com/sangtrx/vexil-dota2-win-probability/pull/11) | Merged | review/vexil-recruiter-polish-20261114 | Final scientific notebook, strict pre-terminal repair and frozen-cache refit |
| [#12](https://github.com/sangtrx/vexil-dota2-win-probability/pull/12) | Merged | fix/vexil-hiring-review-20261115 | Terminal-boundary text, pre/post correction evidence, concise disclosure, clean Git/PR handoff |
| [#13](https://github.com/sangtrx/vexil-dota2-win-probability/pull/13) | Merged | fix/vexil-colab-receipt-20261115 | Fresh 14-cell Colab cold-run receipt, source hash and numeric parity, honest CSV limitation |
| [#14](https://github.com/sangtrx/vexil-dota2-win-probability/pull/14) | Merged post-hoc audit | research/vexil-series-ci-20261115 | 54-series grouped bootstrap from unchanged TEST forecasts; CI still crosses zero for log loss |

## Key original commits

- [e49e853](https://github.com/sangtrx/vexil-dota2-win-probability/commit/e49e853) fixed the original model-family source before initial held-out evaluation.
- [3258a762](https://github.com/sangtrx/vexil-dota2-win-probability/commit/3258a762) froze 500 selected game IDs before held-out scoring.
- [f50832ae](https://github.com/sangtrx/vexil-dota2-win-probability/commit/f50832ae) records the original 28-candidate screen.
- [4a77ae5c](https://github.com/sangtrx/vexil-dota2-win-probability/commit/4a77ae5c) repaired the terminal boundary and refitted the original selected model family.
- [dc7cabd0](https://github.com/sangtrx/vexil-dota2-win-probability/commit/dc7cabd0) reconciled scientific/report CI and historical research provenance.

## Reading historical results

The 28-model research screen used previously inspected development-validation games and predates the removal of 12 exact-at-game-end rows. It was NOT rerun as a blind test or used to promote another model. [EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) contains every recorded candidate result and the negatives. On the corrected 106-game held-out TEST, the M1-minus-M0 loss CI contains zero and M1 has worse late-game Brier/ECE. The decision was to retain M0 as a reference and shadow-test M1.

A Git author identifies a commit's recorded author, not the specific tools used to produce its contents. AI assistance is disclosed in the report. Historical Git authorship and timestamps are not altered.
