# Withdrawn inference: retrospective freshness is an endpoint-loss identity

**Status (15 November 2026): HOLD as recruiter appendix.** Retain as negative research audit / interview discussion. This post-hoc erratum follows an independent read-only Fable 5.2 XHIGH hostile review. It was written AFTER the original lag-1/2/5 results. Original model, frozen forecasts and historical commits remain unchanged.

## Critical flaw: lagged Brier statistic telescopes

Let L_t = (p_t-Y)^2 for the same game and terminal binary result Y, with contiguous minutes t=0,...,T.

For lag one, sum(t=1..T)[L_(t-1)-L_t] = L_0 - L_T.

All intermediate forecasts cancel exactly. The reported mean +0.006356 equals the aggregate starting-minus-ending loss divided by 3,730 paired minutes (106 games). It does not measure the distinct information added by each minute. Calling this an information-value signal or 3,730 independent incremental observations is misleading.

For lag k, sum(t=k..T)[L_(t-k)-L_t] = sum(t=0..k-1)L_t - sum(t=T-k+1..T)L_t.

Thus the 1/2/5-minute lag means are determined by boundary snapshots, not intervening events. Phase estimates also telescope at phase boundaries and are affected by game survival/termination. The claimed minute-20-to-29 hotspot is not established.

The **1.76x headline is withdrawn**: it compares a game-endpoint Brier decline to M1-vs-M0 matched-row predictive uplift. Those are different estimands with differing uncertainty; no CI for the ratio was presented. The corresponding log-loss ratio differs substantially. The algebra of forecast score movements is valid, but the claimed operational advantage is not.

## Additional problems

- A stale prediction uses both an old game state and an old game clock. A delayed actual packet does not remove wall-clock, survival or other context. This is not a measured network delay or causal intervention.
- The innovation-energy plus 2*(Y-p_now)*delta decomposition is a Brier identity, not a martingale calibration test. The residual outcome-alignment component accounts for about 46% of lag-1 mean and can signal model miscalibration.
- The 54-series bootstrap does not cover cross-series team/league dependence. The TEST had already been inspected repeatedly; this is post-hoc.
- Log-loss sensitivity, unequal-game/phase effects and many examined confidence intervals were not all prominent in the historical readout; the 1.76x ratio had no uncertainty. The protocol seed statement also differs from the code, which uses seed+lag.
- This mechanism was not falsified against an actual received-at-time event stream. A claim of information-filtration value needs actual event times, received times, known game time, freshness watermarks and previously untouched matched decisions.

## Correct research decision

**Do not merge this as a recruiter appendix, do not repeat 1.76x in the employer report.** Keep the experiment and correction in the research history as an honest discarded direction. If revisiting operational freshness, define a non-telescoping, latency-grounded estimand, pair comparable decisions, account for right censoring and test prospectively. The core M0/M1 package stays unchanged.

The useful senior lesson is to interrogate an attractive statistic for identities and estimand validity before treating it as a discovery. This is not a claim of a 10/10 result.
