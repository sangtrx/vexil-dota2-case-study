# Conditional gold value — TRAIN-only mechanistic audit

**Disposition:** interpretable within-fit effect; NOT evidence of generalization,
calibration quality or superiority to M0. This is a post-selection analysis.

## Mechanistic question

At a game minute t, what additional *fitted log-odds of a Radiant win*
does a +2,000 gold lead carry versus zero gold at the **same minute**?

| Fixed M1 TRAIN scenario | Minute 10 | Minute 30 |
| --- | ---: | ---: |
| Predicted p(win) at zero gold | 0.50185 | 0.49528 |
| Predicted p(win) at +2k gold | 0.66499 | 0.59404 |
| Within-time probability lift (+2k vs zero) | +16.31 pp | +9.88 pp |
| Within-time log-odds lift | +0.67822 | +0.39956 |
| Within-time odds multiplier | 1.97x | 1.49x |

**Primary:** the difference in conditional *log-odds* impact at minute 10
versus minute 30 is +0.27866, cluster-bootstrap percentile 95% interval
**[+0.08937,+0.41026]**. **Secondary:** the difference in within-time
probability uplift is +6.44 percentage points, 95% interval
**[+2.16,+9.20] pp**. In 2,000 series-cluster refits, 100% yielded
positive contrasts. This is **NOT a p-value**, not fresh heldout,
not a proof that M1 outperforms M0 and not an independent review.

## Why this is the correct conditional gold question

Simply comparing p(+2k, minute 10) to p(+2k, minute 30) mixes the
game-time main effect with gold-by-time interaction. Instead subtract
same-minute zero-gold log-odds:

    G(t) = logit(p(+2k,t)) - logit(p(0,t))
    G(t) = 2 * [beta_gold + beta_interaction * log1p(t/10)]
    D = G(10)-G(30)
      = 2 * beta_interaction * [log(2)-log(4)].

The beta parameters here undo StandardScaler. The logit difference
cancels the fitted minute main coefficient and intercept exactly; an
algebraic identity check is performed on *every bootstrap fit*.

The fitted gold-by-time coefficient after undoing standardization is
about **-0.20101**. It describes a diminishing conditional log-odds
association with a 2k gold lead later in a game. M0 has no interaction
so G(t) is constant by design; this is a structural feature comparison,
**NOT an empirical proper-score improvement test**.

## Why the evidence is not a causal or out-of-time conclusion

- The original M1 was selected with reused validation, the earlier TEST
  was opened, and the conditional contrast was conceived afterward.
  The protocol and script were committed before executing this specific
  2,000-draw bootstrap, NOT before historical model selection.
- 291 original TRAIN games yield 10,675 minute forecasts in 149
  identified professional series plus 22 standalone match groups.
  Groups may share teams/league effects, and TRAIN is patch-59-heavy.
  Series bootstrap estimates instability within this sample; it does
  not establish a universal population relationship or a live effect.
- M1 already contains a gold-by-time term; a nonzero fitted coefficient
  produces this model structure by design. The new intervals do not
  establish strong out-of-sample proper score, calibrated probabilities
  or new model selection. Its original 106-game TEST paired M1-vs-M0
  intervals include zero.
- Comparing model states at fixed gold is hypothetical, **not causal**.
  No real 2k gold transfer, actual live packet latency or executable
  betting edge has been observed.
- The probability-uplift comparison also depends on the baseline p(0,t)
  and is secondary. The log-odds contrast is the predeclared target for
  this study, precisely because it removes the minute main effect.
- Multiple plausible effect shapes, new season/patch environments and
  shared roster dependence remain uncontrolled.

**Decision:** retain original notebook, TEST, model choice and public
report pending independent hostile review. This is a clearer
explanation of what selected M1 learned on TRAIN, not a justification
for promoting it to production. Its inclusion in a recruiter-facing
report needs further proofing and must explicitly preserve this scope.
A [separate post-result chronological TRAIN sensitivity](CONDITIONAL_GOLD_FORWARD_READOUT.md)
finds no reliable incremental M1 predictive skill: 137 OOF games,
log-loss M1−M0 = −0.000227 with 70-group interval
[−0.011991,+0.010104] spanning zero; M1 Brier point estimate is worse.
A stable fitted interaction must not be conflated with forecast lift.

**Reproduce:** python research/conditional_gold_value.py --check.
Sources: [locked protocol](CONDITIONAL_GOLD_VALUE_PROTOCOL.md),
[receipt](CONDITIONAL_GOLD_VALUE_RECEIPT.json),
[tests](../tests/test_conditional_gold_value.py).


## Mandatory hostile falsification added afterward

The [correct gold+minute null and patch-sensitivity study](GOLD_INTERACTION_NULL_READOUT.md)
finds negligible and inconclusive incremental forecast skill from
adding gold*time (TRAIN forward M1-minus-null log loss -0.00202,
70-group interval [-0.01480,+0.00898]) and a much smaller separate
patch-60 fitted effect (+0.029 vs +0.301 on patch 59).
The [independent local-window/survivor analysis](GOLD_LOCAL_WINDOW_SURVIVOR_READOUT.md)
finds that gold's rank discrimination AUC **INCREASES** from 0.648
at minutes 8-12 to 0.822 at 28-32 on the SAME survivor games,
with grouped early-minus-late interval [-0.250,-0.101]. The
per-2k local slope contrast CI on those games crosses zero, while
per-SD slope increases later. Therefore it is **unsupported to infer "less gold information
later" from a smaller per-2k coefficient**: these are different
estimands, and future-duration collider selection also affects the
retrospective panel. AUC increases within the observed TRAIN windows
but is not a causal or population-level claim. The per-2k coefficient
can still genuinely decline for this model; the new evidence does not
establish the opposite. Keep this post-hoc fitted conditional-gold
result outside the employer report as a qualified research artifact.
