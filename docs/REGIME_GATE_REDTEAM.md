# Pre-confirmation red-team and source-freeze receipt (2026-11-13)

This document was written BEFORE any scored outcomes from the third 200-match
confirmation were viewed. The stage-gate hypothesis was registered at commit
40d8961, and initial one-shot evaluation protocol code at 9043370. The
updates below fix provenance and numerical reliability, not the model family.

## Frozen outcome-blind cohort

- 200 parsed OpenDota pro matches, patch 60, March 30 to April 2, 2026.
- 200 unique match IDs, none shared with original 500+200; no positive
  series-ID overlap with either historical cohort. 97 series-or-singleton
  groups; four matches lack series IDs.
- Audited 95 cached proMatches pages / 9,500 unique candidate IDs:
  no conflicting duplicate metadata entries and all 200 selected
  match IDs appear with consistent timestamps/series IDs.
- Entire outcome-free 200-row manifest is immutable in
  research/gate_confirmation_manifest.json, with paired receipt.
- Ordered-ID SHA256:
  d521e046352ec98b8cdfef92c3e6deeb8b984a36a07263232901f1b7d9a3b2ae
- FULL metadata JSON SHA256:
  afd6c0e63d9795ef74369a025c2cb8d714f7b5ed83134db2078368e7b5ed8bca
- Selection uses timestamps, patch, parsed gold series, minimum duration,
  and exclusion of older match/series IDs. NO outcome-value-based choice.
  OpenDota parse status is retrospective; a frozen ID list prevents
  silent replacements if upstream records are later revised.

## Independent red-team fixes before confirmation

- Piecewise-linear gate accepts integer minutes only and tolerates
  only floating-point rounding error of at most 1e-12 in [0,1].
- Bootstrap raised from 2,000 to 10,000 paired whole-cluster draws
  for BOTH series and match sensitivity; two-sided simultaneous max-t
  inference is conservative for two one-sided improvements.
- One-shot evaluator requires CLEAN git HEAD and full committed
  metadata digest, original 500 ordered-ID hash, and immutable outputs.
  A consumed lock prevents rerunning after results have been seen.
- Validates all 700 gzip cache payloads before any network-capable
  API client call, and enforces 500 train +200 test unique match IDs
  with expected minute-row counts.
- PIT poison checks now include 10, 11, 15, 19, 20 and final minute,
  spanning the regime gate's transition.
- Records evaluator/source SHA256, Python library versions, git HEAD;
  writes all output files before printing scored test results.
- Confirmed original fit_model uses training-only imputation, scaling
  and C=1 logistic fit; make_minute_table uses final outcome only
  as target, and usable checks type of outcome, never the winner value.
- Series-level bootstrap remains sensitive to tournament/team
  dependence and missing series IDs.

## PRE-confirmation diagnostic on inspected earlier 200

The older, already-inspected March26–30 cohort (not third confirmation)
gave these outcomes for the FIXED gate:
- M0 log loss 0.5228517, M1 0.5180038, gated 0.5153593.
- Gate-minus-M0 -0.0074925; gate-minus-M1 -0.0026445.
- Gate Brier 0.1758475 vs M0 0.1787794 and M1 0.1768743.

The precommitted 0.005 practical-gain threshold versus BOTH prior
models was NOT met vs M1 in this older set. Do not relax it now. If
the third cohort fails, say that an edge at that size and power
was NOT demonstrated, not that stage-aware models were refuted.

## GO gate unchanged

Simultaneous series-cluster 95% upper bounds must be below zero for
both overall logloss comparisons; each improvement >=0.005 and Brier
no worse than either alternative. No model shopping, threshold changes,
or post-hoc new features on the third test.

Quant Research Bible v1.4.1 Sections 1.2-1.4, 3, 4.3, 5, 6.5,
7.2-7.7, 13 and 14.
