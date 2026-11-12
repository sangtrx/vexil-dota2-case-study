# Independent review disposition: after single-shot confirmation

**Scope:** Independent read-only Sonnet statistical review of the
completed result narrative against actual phase-score and confidence
interval CSV files. The reviewer did not run models, modify code,
or evaluate a new candidate. This was a report audit AFTER the
third 200-game outcome set was consumed.

| Review risk | Disposition |
|---|---|
| "Falsified" implies stronger inference than the CI | Revised to "not confirmed" and explained failure at the prespecified effect-size/power gate |
| Direct M1-vs-M0 CI appears confirmatory | Clearly labeled post-hoc, unadjusted and hypothesis-generating |
| Commit chronology appears contradictory | Clarified b61750f = second cohort's manifest; 40d8961 = hypothesis registration; 4c11b48 = entire THIRD cohort's metadata + evaluator lock before scoring |
| Phase uncertainty and calibration missing | Exported whole-match phase sensitivity, 10-bin reliability counts and ECE by phase from existing scored predictions only; no model fitting |
| Rounding by copying a six-decimal log | Rebuilt all 30 phase loss/Brier cells from original full-precision CSV; verified both primary CIs and 15 calibration values against exported files |
| Causal wording on the gated late-game mechanism | Restricted to observational point estimates and documented sign instability across cohorts |
| Dependence/selection caveats | Explicit minute-weighted estimand, game-duration-conditioned phase populations, 97 series-or-singleton clusters and remaining tournament/team confounding |
| Inaccessible private methods source | Report is self-contained; internal research Bible only acknowledged as nonessential methodological reading |

The locked model and GO/HOLD acceptance thresholds at 4c11b48 were
unchanged after outcome inspection. The third cohort was NOT
rerun or reselected; the one-shot lock remains present. Reporting
scripts read saved prediction CSVs and never retrain.

**Audit verdict:** Report is fit for the private research archive as
a negative, well-controlled experiment. The stage gate itself remains
HOLD and MUST NOT be merged into the take-home submission.
