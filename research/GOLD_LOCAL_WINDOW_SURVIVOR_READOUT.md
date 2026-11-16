# Gold lead: weaker logit slope per fixed 2k can coexist with higher AUC

This experiment was designed **after** the original M1-selected fixed-gold
time contrast and TRAIN-group bootstrap had been observed, in response
to a read-only hostile Sonnet review. Only 291 original TRAIN games,
the frozen manifest and 10,675 TRAIN snapshots were available.
No previously opened TEST outcomes or reused VAL labels were read.

## Two independent fixed-window local logistic models

In windows minutes 8-12 and 28-32 inclusive, fit **independent**
gold-only logistic models with the notebook's identical fixed
imputer/StandardScaler/L2 setting. This does not use the global M1
gold-by-time interaction. We compare all available games and then
a *retrospectively balanced* 186-game panel containing all five minutes
in both windows (games known AFTER the match to survive through 32).

| TRAIN association/discrimination | Early 8-12 | Late 28-32 |
| --- | ---: | ---: |
| All available games | 291 (1,454 minute rows) | 233 (1,060 rows) |
| AUC, all games | 0.72290 | **0.85783** |
| Log-odds per +2k gold, all games | **0.76520** | 0.37078 |
| Log-odds per 1 SD of gold, all games | 1.03923 | **1.87015** |
| Balanced-panel games (same matches) | 186 (930 rows) | 186 (930 rows) |
| AUC, same survivor panel | 0.64762 | **0.82197** |
| Log-odds per +2k gold, same survivors | 0.52405 | 0.33945 |
| Log-odds per 1 SD of gold, same survivors | 0.54220 | **1.51506** |

The paired cluster bootstrap resamples entire TRAIN series/singletons
(1,000 draws, seed 20261115), never individual minute labels.
Early-minus-late **AUC differences**:
- All available games: **-0.13493**, percentile 95% CI
  **[-0.19681,-0.07241]**.
- Same 186-game survivor panel: **-0.17435**, interval
  **[-0.25045,-0.10073]**.

Early-minus-late **logit slope per 2k gold**:
- All games: **+0.39442**, interval **[+0.18681,+0.64770]**.
- Same survivor panel: **+0.18460**, interval
  **[-0.10671,+0.49146]**, **includes zero**.

Early-minus-late **standardized slope per SD gold**:
- All games: **-0.83092**, interval **[-1.38835,-0.36382]**.
- Same survivor panel: **-0.97286**, interval
  **[-1.48853,-0.58459]**.

The SD of gold_k in the all-games windows rises from ~2.72 to
~10.09 (thousands), and in the balanced panel from ~2.07 to ~8.93.
A fixed 2k lead is a much larger move measured in early-game SD.
Thus a *per-2k* coefficient can fall while **rank discrimination
of gold increases** in later-game forecasts. These are different
estimands; neither should be misreported as a contradiction in data.

## Red-team decision

**Reject the unqualified inference that a smaller per-2k fitted slope
proves gold carries less predictive information later.** In these
TRAIN windows, later gold snapshots have higher descriptive AUC and
larger standardized per-SD slopes. Both quantities reflect how gold
spreads out as games evolve; the per-SD coefficient is simply the
per-2k coefficient rescaled by the window-specific SD, **not a second
independent positive test**. The point estimate for the per-2k
early-minus-late slope remains positive in both panels. Its 95%
interval crosses zero in the survivor panel, so this subset alone
cannot resolve that fixed-unit effect; a difference in which intervals
exclude zero does **not** establish a statistically significant
difference between the two panels.

**The 186-game survivor panel is collider-selected on future duration.**
The duration-to-32 rule depends on how a match unfolded; it is not an
online feature available at minute 8-12 and can change the gold/winner
relationship merely through selection. Earlier-panel AUC falls from
0.723 on all early observations to 0.648 on eventual survivors even
before comparing early with late. The AUC increase in this stratum is
descriptive, not proof of a population-level or causal late-game
information increase.

Do **not** promote M1, infer patch-generalizable skill, or call this
a betting edge. These scores repeat a game's terminal label across
minutes; resampling is series-clustered but does not account for shared
teams/leagues or all post-hoc comparisons. An untouched future
tournament cohort and real event/receipt-time records are still needed.

The earlier M1 post-selection conditional-logit effect can still
accurately be described as a **decreasing fitted slope per +2k gold**
of that particular parametric model. It does NOT mean declining
predictive information; it does not overrule the original M1-vs-M0
uncertain proper-score improvement or the gold+minute forward null
result. Keep the D=0 bootstrap-exclusion finding *outside* the
recruiter report; its standalone positive presentation is misleading.

See the [recorded hostile protocol](GOLD_INTERACTION_HOSTILE_PROTOCOL.md),
[score receipt](GOLD_LOCAL_WINDOW_SURVIVOR_RECEIPT.json) and
[reproducible script](gold_local_window_survivor.py).
