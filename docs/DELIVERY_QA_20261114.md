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
- 59/59 offline Python tests passed; notebook JSON validation passed.
- Full 26-cell notebook Run All: 14/14 code cells executed; 18,304 minute rows; 291/103/106 train/validation/held-out matches; 3,837 unchanged held-out probability rows.
- Separate model-input, outcome-label, development item, and cohort-metadata hashes added to the run receipt. The three TRAIN hashes matched an independently implemented research audit exactly.
- Eight scientific CSV outputs checked column-by-column against the original saved submission-polish execution. Maximum absolute numerical difference: 4.44e-16.
- Frozen manifest SHA-256: e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea.
- Cached source-content SHA-256: 7328f1f8df8f3925765e390f997168a084aa6bded1c1bb031da81e8e8092281b. OpenDota reparses may change this on a cold hosted run; compare the model-relevant outputs and report any material drift.

## Additional same-day reliability checks

- Independent QA checks 500 source winner labels and professional series
  identifiers directly against original cached OpenDota match payloads.
- Ten fresh, paced OpenDota match requests: 10/10 successful, 344/344
  model/item minute snapshots identical, 10/10 full raw JSON digests
  changed. This is a small source-drift canary, not full cloud acceptance.
- M1 calibration-in-the-large: mean p=0.542710 versus empirical
  minute-row win rate=0.604378; gap +0.061668, 54-series descriptive
  interval [-0.023670, +0.142116]. No model recalibration fitted.
- The latest notebook records self-reported runtime and API/cache counts,
  creates a Colab-derived artifact ZIP and has an independent offline
  verifier requiring exact saved source and numerical parity.
- A later BigLinux full replay validated this change again: 500/500
  cached match payloads, 14/14 code cells, 8 unchanged CSVs, M1 fixed.

## Saved-output and visual red-team

- The previous notebook had zero embedded PNG outputs under the local
  Matplotlib Agg backend despite calling plt.show(). The current executed
  notebook explicitly embeds four PNG figures; all were reviewed visually.
- The former fixed-gold plot showed +/-6,000 gold at minute zero without
  any training games supporting that combination. The revised chart
  displays predictions only where at least 10 distinct TRAIN matches
  are within +/-2 minutes and +/-1,000 gold; no model was refit.
- The complete 3,837-row held-out predictions remain in the output CSV.
  The notebook shows just a 16-row preview; all eight original score
  CSVs remain unchanged within 4.44e-16.
- The report is now a result-first three-page A4 PDF with two real
  figures taken from the notebook. Rendered images were reviewed,
  and the PDF contains both embedded figure objects. A local-only
  report rendering script is included.
- Offline unit/adversarial plus visible-output/report-artifact tests:
  59/59 PASS.

## V3 cold-cloud reproduction and V4 frozen-identity repair

- **Actual private Kaggle V3 CPU Run All COMPLETE**, same 500 frozen
  match IDs, **505 network calls and zero cache hits**. Pulled Kaggle
  source contained exactly 26 matching cells and 14 executed code cells.
  All eight exported CSVs matched local numeric values to max
  4.44e-16. Complete raw JSON content hashes changed; all eight
  model-relevant semantic hashes were unchanged. Immutable provider
  run URL and aggregate receipt: research/results/kaggle_v3_cold_20261114.json.
  V3 predates the V4 guards.
- **Demonstrated P0 cohort bug in V3 source:** a deliberately switched,
  valid match payload could replace one frozen requested ID while
  preserving 250/250 patch balance. New fail-closed checks validate
  actual match ID when reading caches, accepting HTTP replies, and
  assembling the frozen cohort; a wrong cached payload is discarded
  before fresh retrieval, and a wrong 200 HTTP response is rejected.
- V4 also pins the metadata-only frozen cohort SHA-256 of match IDs,
  start times and patches **before model fit**. Changing win labels
  alone cannot affect this fingerprint; start-time or patch changes
  do. The existing expected hash is
  e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea.
- Actual BigLinux **V4** full local 500-match Run All PASS, with 59/59
  offline tests, 14/14 executed code cells, four embedded plots and
  four separately exported valid PNG files. All eight science CSVs
  remain identical to within 4.44e-16; M1 and held-out forecasts unchanged.
- Kaggle notebook pull returned source and execution counts but stripped
  media payloads even for a successfully completed run. Updated cloud
  acceptance verifies the four **derived PNG files** separately for
  Kaggle and requires embedded PNGs for Colab downloads. The latest
  Colab ZIP contains eight CSVs, one receipt and four plots (13 files).
- **Private Kaggle V4 COMPLETE and strictly verified** on exact notebook
  source from 400f9fd, hash dd1d0a6ffd37f1f609451684e6d848d124dfa2fddbbc720c470513144fbf34bb.
  Provider returned COMPLETE. The fresh run made **511 HTTP requests, zero
  cache hits**; all 26 source cells and 14 executed code cells matched,
  all eight science CSVs agreed with local (max numerical delta
  4.44e-16), and all four separately downloaded PNG figures passed
  real-image validation. The source semantic fingerprints matched,
  while the full raw JSON digest drifted on unrelated upstream fields.
  Exact-source receipt:
  research/results/kaggle_v4_cold_20261114.json;
  strict verifier: research/results/kaggle_v4_strict_acceptance_20261114.json.
  This is a hosted reproduction, not a new blind outcome test or
  proof that OpenDota was a timely live feed.

## Series-level influence sensitivity

An additional independent, post-hoc leave-one-series-out analysis
is included in research/results/independent_delivery_20261114.json:
37/54 series have negative M1-minus-M0 mean log loss; 38/54 favor
M1 on Brier. Removing any single test series preserves a negative
overall log-loss difference (range -0.01483 to -0.00624 across 54
deletions) and a negative Brier difference (range -0.00424 to
-0.00319). This does **not** change the non-significant overall
series-bootstrap log-loss interval or justify model promotion.

## Exact rendered-plot parity

The new pixel-level artifact audit compares decoded RGB arrays rather
than PNG file hashes. On Kaggle V4, all four exported plots were
**pixel-identical** to BigLinux even though all four PNG file SHA-256
digests differed. The report's two illustrative source PNGs also
matched the corresponding cloud outputs pixel for pixel. The
new mutation test leaves an image visually unchanged while altering
PNG metadata (must PASS), then draws a visible overlay into a
structurally valid image (must FAIL in strict mode). The default
cross-platform gate reports pixel differences without failing on
benign font/rendering variance; strict same-renderer mode is opt-in.
Evidence: research/results/kaggle_v4_strict_pixel_acceptance_20261114.json.

## Independent development-only forward stability

- Used only the 291 frozen TRAIN games (10,683 historical minute rows);
  validation/held-out labels were not loaded for this audit. The
  independent script uses the notebook's exact feature definitions
  and independently refits M0/M1 with training-only transforms.
- Reused the **existing 3-fold TRAIN time cuts** from the notebook's
  item-sensitivity procedure: training 154/176/220 matches; later
  evaluation 22/44/49 games (115 disjoint games, 4,255 minutes).
  M1 log loss beats M0 in **one of three** windows; pooled minute-
  weighted Δ M1−M0 = **+0.00120761**, i.e. M1 worse.
- A separate post-hoc **4-fold schedule** on the same 115 games
  yields **one of four** M1-improving folds, but pooled Δ
  **−0.00115781**, marginally favoring M1. Fold ranking and
  pooled result are window-dependent.
- The sign of the standardized gold × time coefficient stays
  negative in 3/3 and 4/4 respective refits, but coefficient
  direction alone does not ensure better probability scoring.
- Every forward training cutoff excludes games with approximate
  end after the next evaluation's first start. Series do not cross
  folds. This is a post-hoc descriptive stress test, not independent
  held-out replication or a new selection protocol.
- Mutation/contract tests verify series-safe boundaries, permutation
  invariance, missing-future outcome embargo and rejection of
  non-TRAIN inputs. Total tests now **59/59 PASS**.

## Unclosed gates

- Fresh Colab-specific runtime acceptance is still unverified, though
  exact V4 source passed private Kaggle CPU cold Run All and strict
  downloadable-source/output verification.
- Model improvement remains statistically uncertain and all retrospective
  source timestamps need live-feed arrival validation before production.
- Applicant must enter their actual active hours, not elapsed API/kernel time, before submission.
- No hiring submission or model promotion has occurred.

This QA isolates source correctness from predictive evidence. The original selected M1 still lacks a statistically conclusive overall held-out advantage over M0.
