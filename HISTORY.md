# Research history and submission curation

The original research commits date from 13–15 November 2026, including main at SHA 5bff687 before reviewer curation. All fourteen original PR #3–#16 head branches are [linked in the branch/PR map](docs/REVIEWER_HISTORY_MAP.md), under history/actual-* refs, so a reader can inspect original code, diffs and recorded dates. The original [private source repository](https://github.com/sangtrx/vexil-dota2-win-probability) holds GitHub PR discussions; access to its private comments is separate from this repository.

**The curation/01, curation/02 and curation/03 PRs are new work dated 16 November 2026**, arranging frozen results and reviewer QA. They are not backdated experiments. Begin with [REPORT.pdf](REPORT.pdf), [the executed notebook](live_dota2_win_probability.ipynb) and the concise [research decision trail](docs/RESEARCH_DECISION_TRAIL.md). The [provenance contract](docs/CURATION_PROVENANCE.md) distinguishes archival work from new integration commits.

**PR disposition (15 November 2026):** #3-#10 are closed without merge as completed research archives; #11 merged the final notebook/report, #12 corrected the handoff, #13 records the fresh Colab execution, and #14 adds a post-hoc series-dependence sensitivity without changing the model. Closing a PR does not delete its branch, commits or experiment receipts. For a quick technical audit, read #3 → #6 → #9 → #11 → #12; the other PRs document separate negative experiments and QA.

## Reviewer package updates (17–19 November 2026)

- **17 November:** Reviewed the notebook, provenance and saved evaluation results. The original TEST forecast CSV was not changed.
- **18 November:** Recorded additional feature and model comparisons as exploratory, post-result work; none replaced the selected model.
- **19 November:** Fixed Roshan team attribution in the separate 81-feature study, reran the same fixed Q2/Q3 and XGBoost/LightGBM models on TRAIN-forward only, and rebuilt the report and ZIP. The original 500-game notebook and 3,836 TEST forecasts stayed unchanged. [Correction and limits](research/ROSHAN_CORRECTION_20261119.md).

Original GitHub PR discussions are in a **different private repository**. They may return 404 without separate access. This repository preserves mirrored source branches, the principal readouts and the original commit timestamps. Git author metadata records commits, not individual manual authorship; AI assistance is disclosed in the report.

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
| [#13](https://github.com/sangtrx/vexil-dota2-win-probability/pull/13) | Merged | fix/vexil-colab-receipt-20261115 | Fresh 14-cell Colab cold-run receipt, source hash, numeric parity and unverified cloud-export CSV parity |
| [#14](https://github.com/sangtrx/vexil-dota2-win-probability/pull/14) | Merged post-hoc audit | research/vexil-series-ci-20261115 | 54-series grouped bootstrap from unchanged TEST forecasts; CI still crosses zero for log loss |
| [#15](https://github.com/sangtrx/vexil-dota2-win-probability/pull/15) | Rejected/closed | research/vexil-quant-bible-freshness-20261115 | Proposed freshness headline telescoped; explicitly withdrawn |
| [#16](https://github.com/sangtrx/vexil-dota2-win-probability/pull/16) | Draft/unmerged | review/vexil-senior-submission-20261115 | Separate historical four-page reviewer proposal, not merged into the original research main |

## Key original commits

- [e49e853](https://github.com/sangtrx/vexil-dota2-win-probability/commit/e49e853) fixed the original model-family source before initial held-out evaluation.
- [3258a762](https://github.com/sangtrx/vexil-dota2-win-probability/commit/3258a762) froze 500 selected game IDs before held-out scoring.
- [f50832ae](https://github.com/sangtrx/vexil-dota2-win-probability/commit/f50832ae) records the original 28-candidate screen.
- [4a77ae5c](https://github.com/sangtrx/vexil-dota2-win-probability/commit/4a77ae5c) repaired the terminal boundary and refitted the original selected model family.
- [dc7cabd0](https://github.com/sangtrx/vexil-dota2-win-probability/commit/dc7cabd0) reconciled scientific/report CI and historical research provenance.

## Post-selection TRAIN-only uncertainty study

The optional TRAIN-only fitted-time uncertainty study was developed after
the original 500-game M1 selection and after TEST scores were exposed.
Its [fixed protocol](research/TRAIN_CONTRAST_PROTOCOL.md) was committed
as **07ddc6a**, and the frozen TRAIN features, manifest checksums and
resampling implementation as **476a841**, both before the new bootstrap
receipt was written. The **original TEST and M1 remain unchanged**. This
study has 291 TRAIN games, 149 identified series and 22 standalone games;
the +2k-gold minute-10 minus minute-30 point contrast is +7.1 percentage
points with a 2,000-draw percentile 95% interval [−1.1,+13.8] pp that
crosses zero. These protocol commit IDs are from the separate earlier reviewer
repository, not dates fabricated into this new curation ancestry;
the saved frozen receipts are copied here. They do not prove
true feed arrival time. The original raw match
payloads are not included with the derived TRAIN features.

The archived 200-game development study is documented in the
[experiment register](docs/EXPERIMENT_REGISTER.md). It belongs to the
original private research history, not the optional TRAIN-only contrast.
Its raw payloads and separate replay code are not part of this ZIP.
The original PR discussion links may require separate access.
Original research code and selected branch heads are mirrored into
this repository for reviewers of this repository alone; read access to this
repository is managed separately.

## Separate Nov 2026 post-TEST temporal check

After the original 500-game TEST was opened, I locked a separate
100-match selection and scoring procedure. The matches themselves
had already been played; Git and filesystem timing evidence for
the order of operations is self-attested, not external notarization.
There are 4,355 minute rows, 56 series/singleton clusters, and just
four represented leagues (85 games in two). Both paired confidence
intervals include zero, and omitting one large league reverses the
log-loss point advantage. A separate 120-game November
study has its [frozen match manifest](docs/NOVEMBER_120_RESEARCH_MANIFEST.csv)
and [68-game overlap receipt](docs/NOVEMBER_COHORT_OVERLAP_RECEIPT.json)
included in this ZIP. These checks are not independent replications;
no pooled test or model promotion is claimed. The original 500-game
notebook, TEST rows, historical research and model weights remain unchanged. This is
optional evidence in docs/FORWARD_100_STRESS.md and the frozen
artifacts/forward_100_predictions.csv, not a replacement assessment.

## Reading historical results

The 28-model research screen used previously inspected development-validation games and predates the removal of 12 exact-at-game-end rows. It was NOT rerun as a blind test or used to promote another model. [EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) contains every recorded candidate result and the negatives. On the corrected 106-game TEST, the original M1-minus-M0 primary intervals include zero. M1's late-game Brier/ECE are worse as **descriptive point estimates** (30+ Brier difference +0.0046, paired 95% interval [−0.0037,+0.0109] crosses zero). The separate later 200-game development cohort favors M1 on **aggregate point scores**, not a confirmatory 30+ effect. M0 remains the recommended reference. M1 could be evaluated alongside it in a future shadow study after live data-arrival timing is verified.

A Git author identifies a commit's recorded author, not the specific tools used to produce its contents. AI assistance is disclosed in the report. Historical Git authorship and timestamps are not altered.

## Dated reviewer curation (16 November 2026)

- [Curation PR #1](https://github.com/sangtrx/vexil-dota2-case-study/pull/1): preserve the selected 500-game experiment, corrected 3,836 TEST forecasts, TRAIN-only model and VALIDATION evidence.
- [Curation PR #2](https://github.com/sangtrx/vexil-dota2-case-study/pull/2): retain real rejected hypotheses, 68/100 overlapping games, uncertainty and decision gates.
- [Curation PR #3](https://github.com/sangtrx/vexil-dota2-case-study/pull/3): assemble the four-page report, honest assistance disclosure, deterministic self-testing reviewer archive and transparent history.
- Unmerged research drafts deliberately remain DRAFT/HOLD; they do not strengthen the original TEST or add independent confirmation.

These PRs were opened here on 16 November; original commits and their timestamps were preserved.
