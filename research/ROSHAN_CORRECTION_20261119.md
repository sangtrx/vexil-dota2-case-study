# Roshan owner correction: TRAIN-only sensitivity (19 November 2026)

The historical 84-input study had a parser error. OpenDota records the side of a Roshan kill in the event's `team` field (2 = Radiant, 3 = Dire). The original `rich_feature_engineering.py` used `player_slot`/`slot` for Roshan and discarded the events. Player-slot attribution remains appropriate for Aegis and firstblood, not Roshan.

The original 500-game notebook uses `team` for Roshan already, so **none of the M0/M1/M2/M3 forecasts or the submitted TEST probabilities changed**. This repair applies only to the later 81-feature study.

## Source and feature checks

On the original 291 TRAIN matches, all **486 Roshan-kill events** had a valid `team` and none had `player_slot`/`slot`. They were not missing owner information. The corrected version was recomputed from 291 source-matched cached OpenDota JSONs: **10,675 TRAIN minute prefixes**, with side-mirroring and timestamp truncation checks.

| Engineered column | Minute rows changed | Corrected nonzero rows |
| --- | ---: | ---: |
| `o_roshan_delta` | 3,624 | 3,624 |
| `o_roshan10_delta` | 3,655 | 3,655 |
| `o_objective_tempo` | 3,655 | 9,260 |

All other columns, source labels, match IDs and forecast-minute keys were unchanged. The historical dataset had **78 distinct, varying** engineered fields; the corrected 81-column dataset has **80**, because `x_economy_gap` still duplicates `gold_xp_gap`.

## Same fixed models, same TRAIN-forward folds

The correction was discovered after previous outcomes had been inspected. This is **post-result sensitivity**, not a new confirmatory evaluation. I kept the original model classes, hyperparameters, four chronological TRAIN-only blocks, **137 evaluation games**, **5,081 minute predictions** and **70 series/singleton groups**. No original VALIDATION or TEST labels were used to select or tune a repaired model.

| Candidate | Historical log loss | Corrected log loss | Corrected Δ log loss vs M1 |
| --- | ---: | ---: | ---: |
| M1 reference | 0.612086 | 0.612086 | 0 |
| Q1 path | 0.605963 | 0.605963 | −0.006123 |
| Q2 sparse elastic-net (84 inputs) | 0.629397 | 0.629819 | +0.017733 |
| Q3 shallow boosted tree (84 inputs) | 0.621266 | 0.622214 | +0.010129 |
| XGB84 | 0.621809 | 0.621254 | +0.009169 |
| LGB84 | 0.622936 | 0.624856 | +0.012770 |

Positive Δ means a higher (worse) log loss than M1. With the repaired inputs, Q2 and Q3 still win only **1/4** forward blocks against M1. Their two-candidate-adjusted series-bootstrap intervals still include zero: Q2 **[−0.012136,+0.053563]**, Q3 **[−0.012449,+0.033904]**. The XGB84/LGB84 studies used their previously fixed 90-round configurations and were not retuned. **None of the repaired candidates is promoted.** These comparisons also do not undo the many-model search carried out before this correction.

## Reproducing the post-result correction

The ZIP contains the corrected TRAIN-only engineered feature table, raw-input hash ledger, model receipts and source. With the main pinned Python environment from `requirements.txt`:

```bash
python research/roshan_corrected_rich_models.py --check
```

To rerun the optional XGBoost/LightGBM sensitivity in a separate environment, install `xgboost==3.4.1`, `lightgbm==4.7.0` and `narwhals==2.21.2` alongside the original scientific dependencies, then run:

```bash
python research/roshan_corrected_boosted_models.py --check
```

The boosted run's exact software versions and model parameters are in its JSON receipt. The raw 291-match JSON cache is not bundled; rebuilding the engineered table from raw source requires the original match IDs and public OpenDota responses. The included frozen corrected feature table permits **offline re-evaluation of Q2/Q3 and the optional boosted models** without that raw cache. The corrected scripts verify the frozen original notebook/TEST hashes but do not fit on or score their labels.

Other model checks that used the old rich-feature parser were **not rerun** after the fix: October/November ALL transfer, ALL60 lag sensitivity and nested XGB84/LGB84. The historical readouts now carry dated errata. The three-input boosters, M0/M1 and Q1 are not affected. No new prospective model claim follows from this repair.

The historical model scores remain in `research/RICH_FEATURE_MODEL_READOUT.md` and `research/BOOSTED_TREES_DIRECT_READOUT.md`. The corrected readouts are `research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_READOUT.md` and `research/ROSHAN_CORRECTED_BOOSTED_READOUT.md`. This fix changes the interpretation of the older rich-feature studies, **not the primary 500-match result**.
