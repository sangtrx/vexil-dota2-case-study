# Vexil: 28-hypothesis research factory (13 November 2026)

## Why this exists

The Vexil take-home values creativity as much as technical correctness.
However, creating and testing many ideas and showing only the best
validation score is multiple-hypothesis overfitting. This repository
makes the exploratory search *auditable and finite*, and it keeps the
required one-notebook take-home untouched.

The proposed 28 directions are grouped into distinct economic
questions: time-value curvature; economy size and player allocation;
lead persistence and realized volatility; objective conversion
and team-fight histories; Aegis/buyback/item/event windows;
draft-side priors; and restricted-capacity nonlinear alternatives.
These are NOT 28 claims of algorithmic originality.

## Scope, cutoff and rules

- **Allowed data:** only the two OpenDota endpoints named in the
  take-home, using already-cached original match payloads.
- **Development:** the original **291 train + 103 validation**
  games, with 500-game split and patch boundary untouched.
  Earlier work has already inspected those 103 validation labels,
  so this is **exploratory and not blinded**.
- **Exclusions:** original 106 test and first and second forward
  200-game cohorts have been consumed. They are NOT accessed for
  the 28-model screening. New models may not be retro-tested on
  these and described as independent validation.
- **Comparator:** mandatory M0 gold-only AND proposed M1
  gold+time+gold×log(time), unchanged from original take-home.
  Original run reported M1 validation log loss 0.519346.
- **Stage A:** use three preselected, chronological series-safe
  validation blocks drawn only from the 291-game original TRAIN
  cohort. They are small, so use direction agreement as a guard,
  not a significance guarantee.
- **Stage B:** fit each registered fixed pipeline once on all
  291 train games; score all 28 on the 103 previously inspected
  validation games. Report all log losses, Brier, and per-match
  sensitivity scores.
- **Selection correction:** one paired, simultaneous familywise
  95% max-|t| confidence interval from 5,000 fixed-seed
  series-or-singleton cluster bootstrap replications for all
  28 comparisons against M1. This is descriptive because validation
  was already inspected, and normal bootstrap validity depends on
  the number/independence of clusters.
- **GO-for-fresh-test gate:** candidate must have log-loss
  improvement over M1 ≥0.005, Brier non-worse, favorable direction
  on at least 2 of 3 train-only folds, and adjusted series-cluster
  confidence upper bound <0. The gate is locked BEFORE testing.
  Choose at most ONE top eligible candidate, breaking ties
  by simpler model/feature count, then ID. In case of no eligible
  candidate: STOP, keep M1.
- **Fresh confirmation:** only after a positive screen, freeze
  all code and a new later cohort after 2 April 2026, with no
  overlapping match/series and no outcome-based selection. Train
  only on predeclared earlier data; test once. Do not use a
  fourth cohort merely because none of the 28 ideas worked.
- **Deployment:** even a fresh positive one-shot experiment is
  a finite cohort result, not causal proof, market alpha, or
  evidence of real-time network packet availability.

## Architecture and compute

Research implementations are pure functions. No external GitHub
code is copied, and no external match dataset enters evaluation.
No PyTorch dependency, GPU, Optuna search, learned hero embeddings,
stock price feeds or payout data are needed. Models use
scikit-learn pipelines and fixed choices; even nonlinear tests
are deliberately low-capacity because the independent unit is
a professional match/series, not 18,000 independent minute rows.

The factory writes every candidate's prediction, log loss, Brier,
three walk-forward fold results, reliability detail and
bootstrap bounds. It preserves negative results. Its output
does not modify REPORT.md or the original notebook and is
never silently promoted into the take-home PR.

## Academic and open-source references

- https://github.com/amarcu/dota-predictor: LSTM, 20 features,
  phase isotonic calibration and hero embeddings; uses a
  random split, not the Vexil series-safe chronological test.
- https://github.com/Shel2123/Dota2-Win-Prediction:
  GPU out-of-time CV, chat/hero/economy feature groups and Optuna;
  source datasets/metric differ from this task.
- https://github.com/Ukroyur/Dota2-BigData-Match-Prediction:
  pregame hero matchup and first-ten-minute prediction on a
  historical 123k-match dataset; not comparable per-minute scoring.
- https://github.com/Hisokaqq/Dota-2-Match-Outcome-Prediction:
  leakage-safe training-only hero draft stats and shrinkage;
  its public match and draft task is different.
- https://github.com/interpretml/interpret:
  Explainable Boosting Machine, GAMs and local explanations.
- https://github.com/amarcu/dota-predictor/blob/main/docs/features.md:
  directly inspected 20-feature specification.
- IEEE Transactions on Games, Hodge et al. 2021,
  DOI 10.1109/TG.2019.2948469: live professional-game win prediction.
- CHI PLAY 2024, Chitayat et al.,
  DOI 10.1145/3677079: win-condition reasoning.

Any exact new feature remains a hypothesis within this private
project, not a verified global literature-first invention.
