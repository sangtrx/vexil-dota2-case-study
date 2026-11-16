# Review the actual research sequence

**This is a map, not a backdated experiment diary.** Original research
Git objects are preserved without rewriting their author/committer
dates. Original source main commits are in the ancestry of this
repository's main. The following historical branch heads are mirrored
as Git refs in **this repository**, and can be viewed without access
to the separate source repository once the viewer is granted access
to this one.

## Original code branches, original dates

| Research question / evidence | Original head, date (ICT) | Preserved branch in this repository |
| --- | --- | --- |
| Point-in-time notebook, baseline and grouped validation | **7b3584f**, 13 Nov | [Actual PR #3 source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr03-pit-validation) |
| Does economic topology add stable lift? | **5ff7163**, 13 Nov | [Actual PR #4 source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr04-structural-edge) |
| Aegis/buyback option state and novelty limits | **035388e**, 13 Nov | [Actual PR #5 source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr05-option-state) |
| 28 falsifiable specifications and multiple-test gate | **e544b04**, 13 Nov | [Actual PR #6 source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr06-28-hypotheses) |
| Adversarial feature/label tests and rolling TRAIN folds | **ccaac51**, 13 Nov | [Actual PR #9 source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr09-redteam) |
| Invalid freshness-ratio claim explicitly **rejected** | **5f405b5**, 15 Nov | [Actual PR #15 rejected source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr15-rejected-freshness) |
| Four-page reviewer proposal, not an accepted new model | **c377c03**, 15 Nov | [Actual PR #16 draft source](https://github.com/sangtrx/vexil-dota2-case-study/tree/history/actual-pr16-reviewer) |

The source GitHub pull requests contain additional discussion, which
is **not copied** into these mirrored branches and may be inaccessible
without separate permission to the original private repository. The
historical source code is real and inspectable here; the *PR pages*
are not fictitiously recreated with past creation dates.

## Reviewer curation created on 16 November 2026

| Actual PR in this repository | What changed | Disposition |
| --- | --- | --- |
| [PR #1: frozen original experiment](https://github.com/sangtrx/vexil-dota2-case-study/pull/1) | Immutable notebook, 3,836 TEST probabilities, 3,781 VAL predictions, TRAIN-only provenance | **Merged** |
| [PR #2: falsification](https://github.com/sangtrx/vexil-dota2-case-study/pull/2) | Rejected hypotheses, grouped CI, overlapping Nov100/120 outcomes, negative evidence | **Merged** |
| [PR #3: reviewer package](https://github.com/sangtrx/vexil-dota2-case-study/pull/3) | Four-page report, saved-output notebook, pinned setup, self-testing ZIP | **Merged** |
| [PR #4: calibration offset](https://github.com/sangtrx/vexil-dota2-case-study/pull/4) | Small reused-VAL log-loss point gain, ECE worse and CI crosses zero | **DRAFT / HOLD** |
| [PR #5: gold interaction](https://github.com/sangtrx/vexil-dota2-case-study/pull/5) | Fitted gold-time slope, but no demonstrated out-of-sample incremental skill vs strong null | **DRAFT / HOLD** |

The original experiment did **not** happen in the curation PR order
above; the curation PRs were created afterward to organize actual
evidence for a reviewer. See [research decision trail](RESEARCH_DECISION_TRAIL.md)
for the scientific "why," [curation provenance](CURATION_PROVENANCE.md)
for author-date boundaries and the [four-page report](../REPORT.pdf)
for the requested submission-length summary.

## Submission boundary

This repository is **private**. Merely creating these commits/PRs
is not delivering the assignment to Vexil or granting recruiter
permissions. Candidate identity, individual contributions, active
human hours and assistance disclosure still need applicant signoff.
No main model was changed based on exposed TEST outcomes.
