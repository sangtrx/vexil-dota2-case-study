# P25: Additive B-spline gold and time

**Status:** REGISTERED, UNTESTED at file-creation time. Research / exploratory only.

**Scientific mechanism.** Smooth learned nonlinear shape may improve gold/time probabilities without high capacity.

**Falsifiable null.** Low sample power does not justify spline flexibility.

**Feature definition.** New columns: none; changed model shape only. Existing fixed M1 columns: gold_k, minute10, gold_x_time. The production data contract permits only OpenDota /proMatches and /matches/{match_id}, with per-minute array entries through t and dated events at seconds <=60t.

**Algorithm.** spline; see the frozen, shared experiment runner. No candidate-specific hyperparameter tuning, external data, hero stats from validation games, or answer-dependent feature selection.

**Controls.** (i) mandatory logistic gold-only M0; (ii) currently selected M1 gold×time. Any gain must be incremental over M1; comparisons to M0 alone do not count. Equal weights for minute forecasts, with equal-match sensitivity and chronological series-safe folds.

**Falsification and decision.** A candidate must improve the already-inspected 103 validation matches over M1 by >=0.005 absolute log loss, have a non-positive Brier difference, improve in at least 2/3 original-train-only forward folds, and have upper familywise 95% series-cluster interval <0 after simultaneous correction across all 28 candidates. This is only a DEVELOPMENT SCREEN, not confirmatory evidence. A new matched/series-disjoint chronologically later cohort is necessary to claim a reproducible edge. A failure means STOP, not tune phase cutoffs or cite a lucky p-value.

**Result policy.** Keep a numerical receipt for this proposal whether better or worse; never discard or selectively report negative candidates. Do not merge an unvalidated model into original Vexil submission.
