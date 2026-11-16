# Post-hoc mechanistic audit: conditional value of +2k gold (TRAIN only)

Design committed 15 Nov 2026 **before this particular analysis is executed**.
This is not a preregistration of the whole Vexil study: M1 was selected on
previously inspected VALIDATION, and the original TEST has already been
inspected. No new model will be promoted by this analysis.

## The estimand issue

Previous report compared p(+2k, minute 10) against p(+2k, minute 30).
That combines the minute main effect with the gold-by-time interaction.
It does not isolate the question, "Does the predictive value of the same
gold lead vary with match time?" The appropriate logistic-scale estimand
subtracts the at-the-same-minute *zero-gold* prediction:

G(t) = logit[p(gold=+2k,t)] - logit[p(gold=0,t)]
D = G(10) - G(30).

This removes the minute main effect by construction. G(t) is the fitted
log odds multiplier associated with a +2k gold state **not causal
additional gold**, and D is the change in that association between
game minute 10 and 30.

For M1 with features gold_k, minute10, and gold_k * log1p(minute10),
D depends only on the fitted gold-by-time coefficient and the fixed log
time difference. Neither the model intercept nor elapsed-minute main
coefficient can change D.

## Exactly frozen procedure

- Use only the pinned 291-game TRAIN feature table and ID/series manifest
  included in the v3 research branch. Verify their SHA256 checksums and
  exact 10,675 minute-row/291-game invariants. The manifest contains no
  outcomes for VAL/TEST and no VAL/TEST feature table is opened.
- Refit the exact already-selected M1 Pipeline with fixed 3 features,
  SimpleImputer median, StandardScaler, L2 LogisticRegression(C=1,
  max_iter=1000, random_state=20261113), identical to the March notebook.
- Primary metric: D, in natural log-odds units, for gold=+2 (thousands),
  minutes 10 and 30, versus zero-gold states at matching game minute.
- Return both G(10), G(30), D, and corresponding odds multipliers
  exp(G(10)), exp(G(30)). Compare algebraically that an M0 gold-only
  model would have D=0 exactly. This is not an M0-vs-M1 performance test.
- Bootstrap 2,000 times with replacement from **171 full TRAIN series or
  singleton groups** (149 identified series, 22 standalone games),
  preserving row/match multiplicity and refitting preprocessing and M1
  each draw. Use seed 20261115, percentile 95% [2.5%,97.5%] interval
  for D, p10/p30 conditional comparisons are only supplemental.
- Planned secondary: probability-scale Δu where
  u(t)=p(+2k,t)-p(0,t), Δu=u(10)-u(30), computed from the same fixed draws.
  Note that unlike D, the probability-scale quantity also depends on
  p(0,t), so it need not have the same sign.
- Include a hand-computed identity check of the feature coefficients
  and swap-invariance of the model-time main effect. Test with synthetic
  coefficients/probabilities; verify source SHA and manifest guards.
- A primary percentile CI that includes zero means evidence for a
  changing **conditional gold log-odds effect** is weak; even if it
  excludes zero, only claim TRAIN-fit stability, not a robust out-of-time
  skill improvement, true live availability or causal inference.
- We do not change the original notebook, frozen M0/M1, historical TEST,
  original main 4-page report, v2 release, v3 PR or email.
- Follow-up reviews must not retroactively present this post-selection
  experiment as a predeclared *overall* model-selection test.

Reasoning reference: Quant Bible proper-scoring and conditional-probability
chapters; no betting alpha claim, odds feed, or latency intervention.
