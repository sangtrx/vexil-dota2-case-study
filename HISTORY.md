# Research history

This is the original development repository for the Vexil Capital Dota 2 take-home. Original commit timestamps, authors and PR branches have been retained. No backdated, reordered or simulated commit history was created for submission.

Read [REPORT.pdf](REPORT.pdf) and [live_dota2_win_probability.ipynb](live_dota2_win_probability.ipynb) on main first. The research branches below document exploratory experiments and negative results. They are **not** all executed by the submission notebook and most were **not** selected. Before this handoff update, the original branching graph had 97 distinct reachable commits from 13-14 November 2026, not 97 commits in a single linear history.

## Actual research PRs

| PR | Research branch | Work / conclusion |
|---|---|---|
| [#3](https://github.com/sangtrx/vexil-dota2-win-probability/pull/3) | research/pit-validation-20261113 | Point-in-time notebook, 500 frozen matches, M0-M3, temporal split; M1 selected on validation |
| [#4](https://github.com/sangtrx/vexil-dota2-win-probability/pull/4) | research/structural-edge-20261113 | S1-S4 structural economy and 200-game stage gate; no model promoted |
| [#5](https://github.com/sangtrx/vexil-dota2-win-probability/pull/5) | research/option-value-novelty-20261113 | Aegis/buyback M4, event-clock integrity, negative results |
| [#6](https://github.com/sangtrx/vexil-dota2-win-probability/pull/6) | research/proposal-factory-20261113 | 28 candidate specifications, familywise screening; 0/28 passed promotion gates |
| [#7](https://github.com/sangtrx/vexil-dota2-win-probability/pull/7) | research/bible-vexil-20261113 | Stability and OOB/CSCV checks, historical Kaggle QA |
| [#8](https://github.com/sangtrx/vexil-dota2-win-probability/pull/8) | research/vexil-submission-polish-20261113 | P20 item-timing development test; earlier portable notebook/PDF |
| [#9](https://github.com/sangtrx/vexil-dota2-win-probability/pull/9) | research/vexil-robustness-lab-20261113 | Metamorphic tests, rolling TRAIN-only folds, malformed inputs |
| [#10](https://github.com/sangtrx/vexil-dota2-win-probability/pull/10) | fix/vexil-delivery-audit-20261114 | Historical Kaggle/Colab evidence and delivery integrity |
| [#11](https://github.com/sangtrx/vexil-dota2-win-probability/pull/11) | review/vexil-recruiter-polish-20261114 | Final report, strict pre-terminal repair, frozen-cache refit, final QA |

## Key original commits

- [e49e853](https://github.com/sangtrx/vexil-dota2-win-probability/commit/e49e853) fixed the original model-family source before initial held-out evaluation.
- [3258a762](https://github.com/sangtrx/vexil-dota2-win-probability/commit/3258a762) froze 500 selected game IDs before held-out scoring.
- [f50832ae](https://github.com/sangtrx/vexil-dota2-win-probability/commit/f50832ae) records the original 28-candidate screen.
- [4a77ae5c](https://github.com/sangtrx/vexil-dota2-win-probability/commit/4a77ae5c) repaired the terminal boundary and refitted the original selected model family.
- [dc7cabd0](https://github.com/sangtrx/vexil-dota2-win-probability/commit/dc7cabd0) reconciled scientific/report CI and historical research provenance.

## Reading historical results

The 28-model research screen used previously inspected development-validation games and predates the removal of 12 exact-at-game-end rows. It was NOT rerun as a blind test or used to promote another model. [EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) contains every recorded candidate result and the negatives. On the corrected 106-game held-out TEST, the M1-minus-M0 loss CI contains zero and M1 has worse late-game Brier/ECE. The decision was to retain M0 as a reference and shadow-test M1.

A Git author identifies a commit's recorded author, not the specific tools used to produce its contents. AI assistance is disclosed in the report. Historical Git authorship and timestamps are not altered.
