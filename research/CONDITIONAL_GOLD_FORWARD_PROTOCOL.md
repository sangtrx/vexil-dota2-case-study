# Post-result hostile sensitivity: does fitted interaction survive forward TRAIN blocks?

**Authored 15 November 2026 AFTER the TRAIN conditional-gold result was
observed, BEFORE executing this separate sensitivity.** The result must
not be presented as an independent preregistered confirmatory study.
Original VAL and TEST remain prohibited in all fit and loss calculations.

## Fixed forward windows

Use the exact original, pinned 291-match, 10,675-minute TRAIN features
and the existing series-aware chronological cutpoints retained in
the previously executed calibration research: [154,176,220,252,291]
training-game index boundaries. Each of the four evaluation blocks is
predicted by a model fit to only earlier chronological TRAIN games.
Embargo training games with estimated (start_time+duration) later than
the first forward game start; this is an imperfect retrospective
maturity proxy, not actual response-receipt time.

## Frozen candidates

M0: gold_k only.
M1: gold_k, minute10, gold_x_time.
Both use median imputation, StandardScaler and fixed L2 logistic
(C=1, max_iter=1000, random_state=20261113), with no hyperparameter
or feature search. No offset calibrator and no TEST refit.

## Predetermined outcomes and analysis

1. For each fold report game and minute row counts, embargo counts,
   M0 and M1 minute-row-weighted log loss and Brier.
2. Aggregate 137 fixed OOF evaluation games / 5,081 rows in the four
   folds. Report paired M1-minus-M0 log loss and Brier.
3. Bootstrap whole OOF series or singleton matches, not minute rows,
   with replacement for 5,000 draws, seed 20261115; compute
   percentile 95% intervals for differences, with weighted minute
   rows as the primary scoring unit. No claiming independent TEST.
4. On each historical training prefix fit, compute the fixed M1
   conditional +2k-gold logit contrast at t10 versus t30. Show all
   signs, including any negative effects. This is a nested-prefix
   stability sensitivity, not independent evidence and not a
   sign-test with four independent samples.
5. If OOF log loss difference interval spans zero or the sign flips
   across prefix models, do not portray M1's time interaction as
   established predictive improvement; even positive results are
   insufficient to promote a model on reused development data.
6. No original notebook, report or employer submission modifications
   until standalone audit is reproduced and independently reviewed.

The series boundaries and embargo assumptions were selected during
previous development; this is a **post-result** research sensitivity.
