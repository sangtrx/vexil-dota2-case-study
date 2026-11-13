# Vexil take-home: 14 November 2026 delivery QA

**Scope:** Preserve original M0/M1 model selection, untouched 106-game test predictions, and patch-balanced 500-match manifest. This is a correctness/reproduction patch, not another model search.

## What changed

- Source gate: require ten unique canonical player slots; verify each 60-second clock starts at zero, stays regular, and has the same length as team gold/XP and player gold/XP arrays.
- Fail closed: no forecasts on a mismatched clock rather than indexing a future gold observation by position.
- Repair synthetic corrupt-input handling for NaN/infinite/boolean event timestamps, boolean gold readings, and duplicated kill-player slots. Truncation carries only times known by the current cutoff.
- Save final notebook outputs from the fully re-executed 500-match notebook.

## BigLinux proof

- Host: epic; Python 3.12.3; the existing isolated Python environment.
- 500/500 real cached OpenDota match payloads used (0 new API calls / 500 cache hits); 250 games per patch 59/60.
- Source-clock audit: 5,000/5,000 player clocks begin at 0 and increment by 60 seconds; no gold/XP/clock length mismatch; 496 games have exactly floor(duration/60)+1 minute values and four have one extra trailing value, never needed by forecasts. The final notebook also checks 18,304/18,304 same-minute player gold and XP sums against team advantages before fitting, with exact tolerance 1e-6.
- 32/32 offline Python tests passed; notebook JSON validation passed.
- Full 26-cell notebook Run All: 14/14 code cells executed; 18,304 minute rows; 291/103/106 train/validation/held-out matches; 3,837 unchanged held-out probability rows.
- Eight scientific CSV outputs checked column-by-column against the original saved submission-polish execution. Maximum absolute numerical difference: 4.44e-16.
- Frozen manifest SHA-256: e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea.
- Cached source-content SHA-256: 7328f1f8df8f3925765e390f997168a084aa6bded1c1bb031da81e8e8092281b. OpenDota reparses may change this on a cold hosted run; compare the model-relevant outputs and report any material drift.

## Unclosed gates

- Hosted Colab fresh-runtime acceptance has not been executed on this exact branch.
- Hosted Kaggle passed an earlier version, not these latest guard edits. Do not equate cached local replay with a new cloud run.
- Applicant must enter their actual active hours, not elapsed API/kernel time, before submission.
- No hiring submission or model promotion has occurred.

This QA isolates source correctness from predictive evidence. The original selected M1 still lacks a statistically conclusive overall held-out advantage over M0.
