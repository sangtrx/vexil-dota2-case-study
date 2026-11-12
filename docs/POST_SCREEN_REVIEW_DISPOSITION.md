# Independent red-team disposition after the locked 28-model screen

**13 November 2026 | Read-only Sonnet review | Original score frozen at bc134da**

The reviewer inspected the pre-results source without executing a
model or reading hidden labels. It found **no P0 future-feature
leakage in the provided candidate code**, subject to the unchanged
notebook base definitions. Its recommendation was conditional
HOLD until several pre-lock code and statistical-control weaknesses
were addressed. The complete one-shot screen **had already run**
before the review returned. We therefore did NOT pretend to repair
pre-registration retroactively or rerun the 28 experiments.

The research report is a valid **descriptive development archive**
with a real, recorded negative result; it is NOT eligible to
promote a model. Below is the disposition, with independent
read-only audits done after scoring.

## Major items

1. **Crash could consume the one-shot lock before a score exists.**
   True as an engineering weakness. This historical run did NOT
   crash: it saved 29 prediction streams, all 28 candidate
   metrics, 87 fold rows and a final receipt. A future factory
   should add preflight for every model column and train-only
   pipeline before opening labels; not relevant to the archived
   one-shot score.

2. **Train/validation series and chronology were not asserted by
   the factory runner itself.** Post-run LABEL-FREE verification
   independently established 291/103/106 game partitions, strict
   chronological ordering, zero match-ID overlap and zero
   positive-series overlap across any of train, validation and
   original test. Train had 22 games with unknown/nonpositive
   series, but all 103 validation games had a positive series ID
   (53 distinct series). The original notebook also enforced
   those split invariants.

3. **M0 gold-only was missing from the 28-model comparison
   engine despite being mentioned in the protocol.** Accepted
   as a reporting inconsistency. The mandatory M0 is already
   part of the unchanged original take-home notebook and
   its executed source validation_ablations.csv. We copied
   its original validation benchmark into THIS report as
   an external reference: log loss **0.532078517566**,
   Brier **0.180927146853**. No model was fitted after
   viewing the factory results to generate this reference.
   Factory M1 **0.519345650308** matches the original
   notebook's value BIT-FOR-BIT (absolute difference 0.0).

4. **P22 and P28 "strong shrinkage" are mislabeled.** Accepted.
   Scikit-learn's C applies to the SUM of thousands of correlated
   minute rows. P22's 160 signed hero indicators were standardized;
   rare pick indicators get very large standardized magnitude.
   With only 291 independent training games and no per-match
   sample weights, C=0.03 was NOT conservative enough.
   P22 log loss **1.581239**, much worse than M1.
   This is a failed modeling specification and a warning
   against pretending 10,683 minute rows are 10,683
   independent labels. P28 C=0.2 is not strong
   match-level regularization either. We did NOT
   retune either candidate after seeing validation.

5. **28-way multiplicity correction is not a universal
   correction for all experiments performed in earlier PRs
   #4/#5.** Correct. MAX-T adjusted only the 28 frozen
   comparisons in this factory. Many feature concepts
   were already inspected in the past; prior adaptation
   makes the reported CIs descriptive, not confirmatory.
   All 28 failed the practical/fold/FWER selection screen.

6. **Dependence may exceed professional series grouping.**
   Post-result, nonselective sensitivity was computed for
   P20 against unchanged M1, WITHOUT refitting or changing
   its rejection. Paired 5,000-draw percentile CI by:
   - 53 original series groups: [-0.013028,+0.002012]
   - 50 same-opponent-pair/day groups: [-0.012694,+0.001795]
   - 49 same-opponent-pair groups: [-0.012894,+0.002045]
   - 14 league/day groups: [-0.011024,-0.000808]

   The 14-cluster league/day percentile interval excludes zero,
   but with such few, non-independent clusters and this being
   post-hoc it does NOT constitute reliable evidence or override
   the frozen all-28 simultaneous confidence interval
   [-0.016929,+0.006434], which DOES contain zero.

## Other findings and corrections

- **PIT check coverage:** the screen passed 4,154 direct
  real-match prefix truncation and future/postgame-field poisoning
  comparisons over 394 development matches. Another
  reproducible audit across 900 already-cached games
  checked ALL 32,106 per-minute time/gold identities, and
  all 1,200 Aegis claims aligned with Roshan events.
  These prove internal parser consistency in those samples,
  NOT live packet arrival.
- **Hero IDs:** all 3,940 player hero IDs in 394 development
  matches lay in [1,155]. The factory's fixed vocabulary
  [1,160] dropped zero hero IDs. This supports numeric
  coverage, not evidence of a useful hero model.
- **Item semantics:** P20 uses timestamped reported
  purchases (major_item_diff and blink_bkb_diff), NOT
  verified persistent inventories or completed
  late-game item power. 9,051 qualifying major-item
  purchase records were observed in the development
  games. The title "High-impact item completions"
  should be read as reported item acquisition events,
  not a reconstructed item-life-cycle state.
- **P24 title:** "calibrated" is an imprecise label;
  its fixed HistGradientBoostingClassifier did not undergo
  separate calibration. Its poor validation score
  does not support its calibration.
- **Original test data:** the input match_manifest.csv
  contains match IDs, timestamps, patch, series and
  partition but NO target labels. The runner read this
  complete metadata table and filtered to 394 train/
  validation game IDs before fetching full match JSON.
  It did NOT fit, score, or load JSON for the 106
  held-out games or either 200-game forward cohort.
  The receipt field "original_test_games_accessed: 0"
  should be interpreted as **no test match detail payloads
  scored or retrieved**, not zero metadata rows touched.
- **Raw source drift:** in-play game-clock time
  comes from retrospectively parsed API payloads,
  and may not represent true live telemetry receipt time.
- **Power:** 103 validation games and 53 series groups
  are underpowered for small incremental gains,
  especially with 28 comparisons. No screen pass
  is not proof that every proposed mechanism is absent.
- **Model selection and tie breaks:** after this negative
  screen, no tie break or fresh confirmation was invoked.
- **Versions and hashes:** the original locked runner
  recorded code HEAD, registry source SHA, feature source
  SHA and split. The result archive includes exact
  byte-level SHA-256 of every saved score/prediction CSV.
  A future run should also record Python package versions
  and a combined source-payload digest before training.

## Final decision

**HOLD P01-P28. Keep M1 gold×time. No fresh holdout, no new
candidate tuning, no post-hoc retraining.**

An explanation of what was actually executed and what was
not cannot be replaced by retrospectively changing a
preregistered protocol. The research appendix is useful
for creativity/rigor but has no independently confirmed
better probabilistic model.
