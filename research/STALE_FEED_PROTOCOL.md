# Synthetic gold-feed staleness stress test — fixed research protocol

**Declared before stale-feed outcomes on 18 November 2026.** This is an offline *counterfactual perturbation* of the original TRAIN series, after prior VAL/TEST had been inspected. It is not a true live-feed outage observation, not a new independent sample, and not a new Vexil model. Actual OpenDota packet received-at timestamps remain unknown.

## Falsifiable operational question

When the historical gold lead observable used by the existing M1 forecast is hypothetically delayed by a fixed 1 or 3 complete minutes, does updating the model with the current public match clock produce better future-winner probability than holding the last full M1 forecast? Choose no coefficients after observing data. Two synthetic gold-lag durations, and two policies:

- **CLOCK(lag):** at real minute t, know current minute t but receive latest gold lead at max(0,t-lag); predict using the *already fitted* original M1 logistic coefficients with [gold_old, t/10, gold_old*t/10].
- **HOLD(lag):** at minute t, emit the original fresh M1 forecast from max(0,t-lag). That previously computed forecast requires only the past gold and past minute and is causal.
- **FRESH:** original contemporaneous M1[t], an oracle reference only for measuring induced stale-data degradation, not a feasible estimate when feed is late.

At t<lag, use t=0 stored gold/forecast; all policies agree at t=0. A new match must reset all state. The model itself is fitted only once per training fold (no fallback refit), with original M1 hyperparameters and point-in-time gold lead history already checked on the 291 original TRAIN games. Resequencing raw events or imputing actual arrival times is prohibited.

## Evaluation / reject criteria

Use original TRAIN-only chronological mature-label cuts (154,176,220,252,291): 4 forward folds, 137 OOF games, 5081 minute decisions, 70 professional series/singleton groups. The original M1 fold proper scores must reproduce locked Q1 receipt at absolute 1e-10. Never read original VAL, TEST, October prospective-holdout outcomes or recruiter's ZIP for fit or tuning. Frozen applicant artifact SHA contracts.

Primary operational comparison: LL(HOLD3) − LL(CLOCK3), minute-weighted log loss; report exact 2000 paired series-bootstrap replicates with seed 20261118, descriptive 95% and a two-lag Bonferroni **97.5%** interval per lag. Negative means HOLD is better. Secondary: lag1 same comparison; LL / Brier delta of each of 4 policies relative to FRESH; late30 Brier; all four folds; t<lag edge count and evidence the values are causal and per-match restart safe. Show both scenarios even if one is bad.

**Predeclared future-only mitigation candidate gate:** HOLD3 over CLOCK3 should improve LL by >=0.003, Bonferroni upper interval below zero, >=3/4 folds improve, and late30 Brier no worse. Passing this cannot establish the presence/prevalence of actual staleness, real latency improvement, calibration or production safety; no employer model update.

No optimization over lag durations, output clipping, thresholds or additional models after outcomes. Do not relabel old results as preregistered. Negative results stay visible, applicant-owned hours / AI disclosure and main/Draft PR #9 untouched. No actual online testing/alerts without timestamped ingress data and a separately reviewed safety plan.
