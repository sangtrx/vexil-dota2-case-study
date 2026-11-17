# Model-disagreement reliability: fixed TRAIN-only falsification

**Declared 18 November 2026 before scoring this new study.** Development is post-result and post-28+ exploration: this **is not a preregistered original take-home, new blind holdout, validated alerting product or independent confirmation**. The full original 500-match TEST, 103-match VAL, all external holdout labels, employer report and ZIP are excluded from research fitting/evaluation. Base source HEAD: 282530f. Branch: research/vexil-disagreement-reliability-20261118.

## Decision question

Can disagreement among three small Dota win-probability models detect **wrong-sided M1 decisions** more effectively than the obvious control, M1's own predicted uncertainty? A warning signal must be available at the current minute; final winner is allowed **only in offline evaluation**, never in the risk score.

**Outcome:** per-minute binary error E(t) = 1 if final Radiant winner is inconsistent with M1's >=0.5 predicted side at t, else zero. This judges the quality of a hypothetical side selection, **not** M1 probability calibration, downstream utility, or a real trade.

**Exactly one proposed score:** D(t) = max(|p_M1(t)-p_M0(t)|, |p_M1(t)-p_Q1(t)|). No fitted risk meta-model, no tuning, no blending, no prediction correction. All three probabilities must be fit on mature **prior TRAIN games** in exactly the fixed prior four forward folds, using the prior hyperparameters. Match labels, future per-minute states or cross-match future stats must not contribute to p or D.

**Strong null:** U(t) = min(p_M1(t), 1-p_M1(t)), the M1 probability of getting its own chosen side wrong *under its calibration claim*. The null is hard to beat because confidence directly estimates risk if calibrated. No re-fitting to the error label.

## Locked design, metrics and failure gates

Frozen cutpoints (154,176,220,252,291) on only the 291 original TRAIN games; 4 chronological folds, 137 OOF games, 5,081 historical per-minute forecasts, 70 professional series/singleton clusters. No shared series across train/eval and exclude non-mature fit labels per original match-end proxy; model-parity log loss/Brier at 1e-10 with existing Q1 receipt.

- **Primary:** minute-weighted AUROC of E from D vs U, paired difference (D-U). Compare 2,000 paired *whole-series/singleton* bootstrap replicates with seed 20261118 for a descriptive 95% interval. Do not treat minute rows as independent. Full interval is descriptive within this single screen and does not account for all prior screens.
- **Secondary:** wrong-side precision within the highest 20% alerts, and fraction of errors captured, each for D and U. This is a **retrospective OOF ranking** (quantile determined on scored outcomes' probability distributions without labels), not a valid online-alert threshold nor a claimed operational deployment. Report total wrong-side prevalence, denominators and four individual fold AUROCs. Report high-confidence (max(p,1-p)>=0.75) errors only as a fixed subgroup diagnostic with explicit denominator; no subgroup promotion.
- **Confounding check:** partition into uncertainty intervals U in [0,0.1),[0.1,0.2),[0.2,0.3),[0.3,0.4),[0.4,0.5] and phases minute <10, 10-19,20-29,30+. In each cell of >=20 forecasts with both error classes, split D by within-cell median (ties counted as low); report weighted (high-D minus low-D) wrong-side risk difference, individual cell counts, eligible/excluded rows. Median is assessed offline and not claimed to be a deployable threshold. A positive difference alone is descriptive and need not survive independent confirmation.
- **Diagnostics, not selection:** fixed components |M1-M0| and |M1-Q1| AUROC reported transparently. Do not select whichever wins after observing data. No new model candidate, parameters or threshold.

**Frozen exploratory future-study gate** requires D-U AUROC >=+0.03, series-bootstrap 95% lower bound >0, D outperforms U in >=3/4 folds, >=+0.03 wrong-side precision improvement at top20% over U, AND positive within-confidence/time descriptive risk gradient. Even if passed, it merits only **prospective independent evaluation**, not alteration to the original Vexil submission.

**Fail if:** insufficient unique clusters, invalid probability, incorrect baseline receipt, any use of validation/test outcomes, mismatch in 137 games/5081 forecasts, series leak, error label enters D or U, tampered original TEST/notebook/report/ZIP, or prior protocol/results edited after peeking. Negative results are kept. Actual event received-at is unknown; historical replay cannot certify real time. Applicant-owned hours, contributions, AI disclosure and employer access are untouched.
