# Edge V2 independent review checkpoint (2026-11-13)

All feature hypotheses and the new forward-cohort selection were committed
at 335abf1 before any S1-S4 validation results were obtained. Exact feature
source committed at c7b42da. The original notebook and Draft PR #3 remain
unchanged; this is a separate research worktree and branch.

## Why the first 76.05% headline is NOT a usable edge

- M1 and gold-only M0 make virtually the same win/lose decisions
  (76.05% vs 75.97% accuracy; only three more correct match-minute rows).
- Point-estimate log-loss improvement is more interesting: 0.5039 vs 0.5163
  on the original 106-game heldout, but the paired 95% interval for M1-M0
  spans zero (-0.0303 to +0.0014).
- These are 3,837 repeated-minute observations from only 106 matches
  and 54 positive-series groups, not 3,837 independent
  outcomes. The shared final label makes per-minute standard errors invalid.
- Earlier late-game gain is concentrated in a single match, and observed
  calibration shifts between train/validation/test.
- 'Predictive edge' means replicable improvement in properly scored
  probabilities on new match groups, not just a better headline accuracy.

## Mechanism-grounded feature engineering

S1, relative economic leverage: normalized gold lead by total team economy.
S2, resource allocation: top-two gold concentration difference and top-two
gold lead normalized by total economy. Top-two is a measurement proxy, not
a hard-coded carry hero role.
S3, gold process fragility: a normalized five-minute shock and signed lead
persistence over ten minutes.
S4, parsimonious joint state: selected S1+S2+S3 signals.

All features use per-minute player gold_t or gold advantage only up to
that minute. Player gold_t availability for the whole match: 291/291
train and 103/103 validation matches. Actual imputation is restricted
to training. Unit tests include side-swap antisymmetry, future-array and
end-of-game poison, missing player history, zero economy and invalid slots.
The combined baseline plus structural model was never given test results
for feature selection.

## Finite validation ablation (291 train / 103 validation games)

| Candidate | Validation log loss | Difference vs M1 |
|---|---:|---:|
| M1 gold + time | 0.519346 | baseline |
| S1 relative economy | 0.518253 | -0.001093 |
| S2 resource allocation | 0.517384 | -0.001962 |
| S3 lead fragility | 0.524593 | +0.005248 |
| S4 combined | 0.520049 | +0.000703 |

Differences are candidate minus M1, negative is better. The registered
acceptance gate required at least 0.005 absolute improvement AND a negative
upper bound of a whole-match 95% bootstrap interval. **NONE PASSED.**
Selection remains M1, with no new structural edge claim.

## Multiple comparisons and dependent-match correction

The apparent best S2 validation improvement is not robust:
- Per-match 4,000-draw bootstrap, unadjusted 95% difference interval
  approximately [-0.003836, +0.000014].
- Simultaneous 95% max-t interval across S1-S4, match-clustered:
  [-0.004312, +0.000388].
- Series-clustered simultaneous interval (53 positive-series clusters):
  [-0.004100, +0.000176].
All simultaneous intervals include zero. Earlier 2,000-draw S2 percentile
CI narrowly excluded zero; this instability further discourages a claim.

## Train-only chronological walk-forward checks

Three series-safe expanding evaluations from the original training period:

| Model | Fold 1 vs M1 | Fold 2 vs M1 | Fold 3 vs M1 |
|---|---:|---:|---:|
| S1 economy share | -0.00188 | -0.00184 | +0.00109 |
| S2 top-two allocation | +0.00294 | +0.00982 | +0.00261 |
| S3 fragility | -0.00321 | -0.00241 | -0.00393 |
| S4 combined | -0.00024 | +0.00786 | -0.00003 |

S2 hurts all three earlier folds even though it helps the separate
patch-60 validation. This is evidence of *lack of temporal stability*,
not proof of a particular patch mechanism. S3 improves all earlier
train-only folds then fails in validation; it illustrates why rolling
CV and one later validation are both necessary. Do not reinterpret a
sign flip as a new trading strategy.

## Decision and further hypotheses (not tested here)

**Decision: HOLD for the incremental structural model.** Keep the
original M1 and M0 baselines, do not blend these candidates after
inspecting validation. The 200-game new forward holdout remains unscored
at this checkpoint. Under the explicitly documented post-development
amendment, it may be used *once* for the already-existing M1 vs M0
replication, never for selecting S1-S4.

Future independent research questions after securing yet another
chronological holdout:
1. Economy state conditional on hero power spikes, using historical
   item purchase times and patch-specific costs; do not infer items
   from final inventories (future leakage).
2. Regime-dependent feature stability after a patch change; need more
   than two patches and enough independent series for robust inference.
3. Relative economy growth and objective conversion lead-time, with
   timestamp integrity, uncertainty-aware forecasts, and calibration.
4. Scenario and market price data would be required before assessing
   any potential actionable betting/trading edge.

Quant Research Bible v1.4.1 sections 1.2-1.4, 3.1-3.6, 4.3, 5,
6.5, 7.2-7.7, 13 and 14. This is a negative scientific result,
not a justification to try dozens more unregistered features.
