# Gold-by-time interaction: TRAIN-only falsification

15 November 2026, authored AFTER initial conditional D>0 was seen and
AFTER read-only Sonnet HIGH hostile review. No claim of an original
blinded/registered trial. Freeze this plan before executing tests below.
Only original 291 TRAIN games, 10,675 TRAIN minute rows and frozen
500-game outcome-free split manifest are eligible. Original VAL and
TEST outcomes are not inputs to any new measure.

## A. Independent local shape / conditional survival diagnostic

Use two predefined minute windows, t=8..12 and t=28..32 inclusive.
Within each, fit a *new descriptive* gold-only LogisticRegression with
same median imputer, StandardScaler and C=1 as M0. Compute the
probability-model association of gold lead on winning as the *unscaled
log-odds coefficient per +2,000 gold*, then difference early minus late.

Do it both on (A1) all TRAIN games with snapshots in each window and
(A2) exactly the same games having all five minutes in both windows
(i.e. observations with minute 32). Conditioning the earlier window on
future duration in A2 is explicitly a **retrospective sensitivity**, not
an available-at-t10 production feature. No causal comparison.

Bootstrap series/singleton match clusters with replacement for 1000
paired draws, seed 20261115, for A1 and A2. Hold entire game/series
together (not minute rows). Report all intervals even if opposite.

Interpretation gate: do not claim the real-world gold information
*diminishes* if the balanced-panel coefficient difference CI crosses
zero or changes sign. A global M1 model fitted to all minutes imposes
one functional form; local windows can falsify that interpretation.

## B. Unit-free information

On the SAME A1/A2 windows compare AUC of gold_k for eventual Radiant
winner (higher gold predicts Radiant wins), and local gold-only logistic
slopes per one window-specific SD(gold). Compute windows' observations
and SDs; report AUC and standardized coefficients; group bootstrap
the early-minus-late AUC difference for 1000 series draws, seed 20261115.
Repeated minute rows are correlated; leave full-game clusters intact.

Interpretation gate: if AUC or standardized slope does not decline from
early to late (or their uncertainty crosses zero), *never* write
"less informative" or "diminishing predictive information" about gold.
May only say the selected M1's fitted log-odds coefficient PER fixed
2k gold declines with match time, without asserting discrimination
or independent out-of-time performance.

## C. Appropriate null, environment and influence

C1. Reproduce the same four historical TRAIN forward blocks
[154,176,220,252,291] with maturity embargo and evaluate fixed
M1 (gold,minute,interaction) against M0-prime (gold + minute, NO
interaction). This is the null for *incremental interaction skill*,
not gold-only M0. Same proper minute-row scores; 5000 series/singleton
paired bootstrap 95% CI, seed 20261115, no retune.
C2. Fit M1 on TRAIN patch 59 and patch 60 *separately* using patch
metadata in the full outcome-free manifest. Report data counts and D,
but neither subset has an independent held-out test (patch 60 only
41 TRAIN games, so any effect is imprecise).
C3. Leave out each of the 171 TRAIN series/singletons separately,
refit M1 and report min/max D and top-five influential cluster IDs.
Separately refit excluding all five at once. These share most data,
cannot be read as 171 independent replications or a CI.

## Governance

Positive D in full-TRAIN bootstrap alone is NOT a sufficient promotion
gate. No model/feature/threshold changes based on any VAL/TEST scores;
no edits to the immutable original notebook/TEST. If any of A/B/C
contradict the strong narrative, keep the entire new D study outside
the employer report, and state why in the research branch. This is a
refutation search, not a chance to pick the most favorable model.
