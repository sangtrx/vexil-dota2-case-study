# TRAIN-only OOF calibration: a negative promotion decision

**Question.** The assignment asks for calibrated win probabilities, but the selected M1 had only been *assessed* for calibration, not accompanied by a validated post-processing rule. Would a one-parameter correction help enough to justify changing M1?

**Design.** On 291 TRAIN games, four later-series OOF blocks (22, 44, 32, 39 games) were predicted by models trained only on earlier completed games. The second and fourth series-safe cutpoints were changed in the documented label-blind chronology amendment before any forecast score; the fourth change was unnecessary to pass the hard minimum-block gate. See the append-only errata and post-hoc sensitivity study. Of the older games, two were embargoed in fold three due to approximate completion time. A scalar log-odds intercept, b = **−0.261982**, was fitted from **5,081 OOF snapshots in 137 TRAIN games**, with slope fixed exactly to 1. No TEST payload is opened; only the original 103-game reused VALIDATION is evaluated.

| Metric on reused 103-game VALIDATION (3,781 rows) | Unchanged M1 | Fixed TRAIN-only offset | Difference (offset − M1) |
|---|---:|---:|---:|
| Log loss | 0.519714 | 0.518556 | **−0.001158** |
| Brier | 0.175902 | 0.175824 | **−0.0000779** |
| ECE, 10 equal-width bins | **0.049193** | 0.056137 | **+0.006944 (worse)** |
| Mean forecast − win fraction | +0.029950 | −0.021111 | Mean bias changes sign |
| Equal-game mean log loss difference | — | — | **−0.000272 (better)** |
| Equal-game mean Brier difference | — | — | **+0.000376 (worse)** |

A **5,000-draw paired professional-series bootstrap**, with series or standalone match as the unit (53 groups), gives uncertainty intervals for the minute-weighted differences: log loss **[−0.019380,+0.017395]**, Brier **[−0.008133,+0.008077]**. Both include zero. These intervals are **descriptive uncertainty on previously inspected validation**, not fresh confirmatory tests.

**Decision: NO EVIDENCE FOR PROMOTION.** Two minute-weighted point estimates and equal-game log loss improve slightly, but equal-game Brier and ten-bin ECE worsen, bias changes sign, and grouped intervals include zero. This 53-group design is underpowered and reused VAL is not independent. It cannot prove offsets are ineffective. Critically, the M1-vs-M0 original selection and frozen 3,836-forecast TEST remain completely unchanged. Claiming “calibrated” here would overstate the evidence. The next calibration evaluation belongs on an untouched cohort with the loss, unit and one rule predeclared.

**Hostile-review uncertainty and source repair:** Fable 5.2 XHIGH identified a non-minimal cutpoint amendment, a missing partition/series manifest pin and an overconfident rejection narrative. The append-only [errata](CALIBRATION_ERRATA.md) records these honestly. A post-hoc **1,000-draw series bootstrap on TRAIN OOF estimates offset b 95% CI [−0.7003,+0.1858]**, itself spanning zero. The result is not a stable, confirmed correction. Both the full five-column 500-game split manifest and the development-only feature CSV now have exact pinned hashes, and an executable exporter reproduces the latter without opening TEST.

**Post-hoc sensitivity on the already used 103-game VAL:** retaining the originally valid fourth cut yields b **−0.25928** (vs −0.26198), offset-vs-M1 log-loss change **−0.001214**. Adding maturity buffers of +15 and +60 minutes yields b **−0.26966** and **−0.26860**, with delta log loss **−0.000990** and **−0.001014** respectively; in both cases Brier is marginally worse with the offset. Excluding five incompletely matured TRAIN games before VAL yields delta log loss **−0.001333**; all are small descriptive effects on reused VAL and not new hypothesis tests. Fold-specific bias and patch composition are in [sensitivity receipt](CALIBRATION_SENSITIVITY_RECEIPT.json); TRAIN OOF composition changes near the patch boundary. A later, separately frozen 120-game November cohort has offset point gains but its 61-series confidence intervals still span zero, so promotion is not supported.

**Quant Bible connection.** This tests proper scoring rules, bias-in-the-large, conditional versus marginal calibration, chronological filtering and grouped uncertainty. It is a falsification and governance result, not newly discovered theory, new independent validation or a betting alpha.

**Portable reproduce:** use the bundled *derived development-only* feature CSV (no TEST outcomes):

    python research/verify_calibration_offline.py

**Raw-cache reproduce (original BigLinux cache only):**

    python research/forward_oof_calibration.py --cache /path/to/api-cache --manifest /path/to/match_manifest.csv --check

The [locked procedure](CALIBRATION_PROTOCOL.md), [full machine receipt](CALIBRATION_FORWARD_RECEIPT.json) and offline verifier include actual counts, offsets, precision and epistemic limits. No live input availability or post-game editing is presumed.
