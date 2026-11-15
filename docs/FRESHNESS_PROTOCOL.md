# Value of Freshness: fixed-design, post-hoc research protocol

**Evidence boundary:** This is a *read-only, post-hoc* diagnostic of the already opened 106-game/54-series held-out TEST. It is **not** a new independent test, a fresh model trial, a calibration procedure, a live-feed latency measurement, or evidence of betting alpha. No regression or feature choice may be made using these results. The recruiter notebook, report, 500-match cohort, model parameters and 3,836 forecast rows must remain byte-identical.

## Question and falsifiable mechanism

At live minute `t`, what is the *retrospective forecast-value penalty* of seeing a valid probability from `t-k` instead of the available model forecast at `t`? Under an ideal evolving conditional win probability `p_t = E[Y | F_t]`, one expects new information to improve *expected* proper score; an estimated model can violate this, and delayed observations are not the same as an authenticated feed packet delay.

Primary diagnostic, chosen before running this script: for M1 and `k=1`, evaluate `mean[Brier(p_{t-1},Y) - Brier(p_t,Y)]` on identical valid `(match_id,t)` pairs. Positive values favor freshness. Compare the baseline M0 on exactly these same pairs. Sensitivities: `k=2,5`, log loss, equal-match means, and four fixed current-minute phases (`0-9`, `10-19`, `20-29`, `30+`). No fitted lag thresholds or phase cutoffs.

## Exact information and dependence rules

Input is only frozen `artifacts/heldout_predictions.csv` and `docs/SERIES_GROUPS_TEST.json`; validate their keys, finite probabilities, terminal outcomes and forecast hash. For each game and lag, join its *existing* minute `t` with existing minute `t-k`; never carry predictions between games or use future-minute features. This is a hypothetical stale readout at minute `t`, not a re-fetch or reconstruction of what was truly received by a live system. Each game's terminal outcome is used **only in scoring**, never to calculate a forecast. Use series IDs exclusively for uncertainty; never as a predictor.

Pair-level losses are dependent across minutes and same-series games. Primary interval: paired, equal-series-probability, 10,000-draw bootstrap of 54 series, seed `20261115`, with minute-weighted mean across sampled series. As a robustness check, also report the equal-match mean (not an independent trial). Intervals are *exploratory descriptive uncertainty* after multiple prior observations of this test, not confirmatory discovery probabilities. Do not declare a new model winner, even if an interval excludes zero.

## Forecast innovation identity and limitations

For Brier score and `d = p_t - p_{t-k}`:

`(p_{t-k} - Y)^2 - (p_t - Y)^2 = d^2 + 2*(Y - p_t)*d`.

Report the two terms on paired snapshots. The second term vanishes in expectation under suitable conditional-calibration and nonanticipating sampling assumptions, but the selected set of games *surviving to minute t* can induce censoring/selection effects. Do not equate this decomposition with a formal test of martingality, an information-causal estimate, or a benchmark of actual network latency.

## Release decision

If the retrospective freshness penalty is material relative to M1-versus-M0 accuracy, recommend instrumenting `event_time`, `received_at`, feature watermark and data-age distribution before investing in additional model complexity. If not, report the null or sign-reversed finding. Actual operational value and any model promotion require a **future, untouched series/tournament** with measured feed arrival times and predeclared scoring/latency bands. Core M1 selection and held-out outputs remain untouched.
