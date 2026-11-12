# When Gold Is Not Control
## A time-aware, point-in-time study of temporary strategic opportunities in professional Dota 2

### The question

Two teams can have the same gold advantage at minute 25 while having
different options for what happens next. One may have just acquired
Aegis, a temporary opportunity to force a fight; the other may be
ahead in gold but behind in towers. A model using only gold and time
does not represent that distinction. I wanted to test whether these
strategic states improve the *quality of win probabilities*, rather
than simply asking whether a larger model could classify the winner.

### The hypothesis

I separated short-lived and persistent information using exactly
three point-in-time features: an aged recent Aegis-claim proxy,
an aged recent buyback-use proxy, and a signed measure of economic
lead without matching tower/barracks control. These are observables,
not direct measurements of causal advantage. The same regularized
logistic family is used as in the gold×time baseline, allowing a
controlled comparison without architecture or hyperparameter search.

### Evidence and a real counterexample to one-dimensional state

On a frozen sample of 900 matches, I audited 9,000 player time
series and verified the timestamp and exact gold-balance identity
at **32,106 minute positions**. I separately checked the event clock:
1,200 Aegis claims followed a Roshan kill by at most 13 seconds,
and 876 first-blood event timestamps agreed with the independent
match summary to within one second. Event clocks share the
OpenDota parser, so none of this establishes network receive-time
availability.

At minute 25, two independently selected patch-59 professional
matches had Radiant gold leads of **1,901 versus 1,929** and
XP leads of **6,964 versus 6,862**, but different strategic
states. One had a recent Radiant Aegis claim; the other had gold
without matching structural control. The selection did not use
game outcomes, and both Radiant teams ultimately won. This is
a demonstration of *state information the baseline omits*,
not evidence that a feature causes victory or predicts better.

### Falsification and what happened

I registered the feature set and screening criterion before
running the new ablation. On the 291-game training and 103-game
previously inspected validation sample, the combined candidate
was **worse**, not better: log loss 0.520596 versus
**0.519346** for gold×time; delta +0.001251; paired
53-series 95% interval [−0.004386,+0.006336].
One earlier training-only fold deteriorated sharply while two
improved. The screen failed, so I did not use the consumed
held-out games to rescue the candidate.

The key result is therefore a **negative predictive experiment**
and a **positive measurement finding**, with a reproducible
case study and testable next hypothesis. It would be
misleading to ship the new model or claim a trading edge.

### Next scientific step

The unresolved question is whether *actual remaining Aegis
possession*, item-completion power spikes and objective conversion
have information beyond gold when their timestamps and item
lifecycle are observed more accurately. A new study would
pre-register those observables and effect-size thresholds and
evaluate ONCE on genuinely later professional series. The present
take-home's limited two-endpoint sample cannot identify a
causal benefit or establish a globally novel win-condition model.

This is the research distinction I would defend: **a
mechanism-specific representation, a strict availability
contract, an ablation against a much simpler model, and a
decision that follows the evidence even when the proposed
mechanism does not improve the score.**
