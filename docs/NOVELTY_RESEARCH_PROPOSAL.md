# When Gold Is Not Control
## A point-in-time study of strategic option value and time-coherent forecasts in professional Dota 2

**Research proposal / pre-experiment design | 13 November 2026 | Draft, not a finished breakthrough**

### Abstract

At the same minute and net-gold advantage, professional Dota teams can occupy structurally different states. One team may have just acquired Aegis, created a short tactical attack window, or spent scarce resources on buybacks; the other may have converted a smaller monetary lead into towers or barracks, changes that do not simply expire. Conventional per-minute logistic models reduce these states to gold, time and sometimes cumulative objectives. We propose a parsimonious, *two-timescale state representation* separating temporary tactical option proxies from irreversible map control, plus a time-consistency audit of the resulting probability trajectories. The main scientific question is not whether a more complicated model yields a nicer accuracy number; it is whether strategic state has **incremental, reliable predictive information** after conditioning on gold and elapsed time, measured with strictly proper scoring rules and real chronological validation.

### 1. Research gap and precise novelty

Existing peer-reviewed and open-source work covers Dota in-play prediction, hero drafts, gold/XP trajectories, generic event counts, LSTMs, Transformers, phase segmentation and win-condition reasoning (Chitayat et al., ACM CHI PLAY 2024) (bibliography: `OPEN_SOURCE_PRIOR_ART.md`). Therefore this project does NOT claim first use of Dota probabilities, objectives, time dependence or neural sequence models. Its narrower, falsifiable distinction is:

**C1 — two-timescale option-state features:** An observable Aegis *claim* has an approximately five-minute upper-bound validity window, but the replay does NOT prove the item was retained after death. A buyback is a dated commitment, not simply another kill. Tower/barracks losses are persistent. Encode these with honest, timestamp-bounded event functions rather than cumulative tallies with fictitious state persistence.

**C2 — economic/structural disagreement:** A gold lead does not guarantee objective control. Introduce a single sign-equivariant measure of whether the current economic leader is simultaneously the structural laggard. Distinguish *measured discrepancy* from causal reasons for winning.

**C3 — forecast-path coherence:** This is an application of existing probability theory, NOT a newly discovered martingale theorem. Wilkinson & Ferro (arXiv:2606.31621, 2026) already study sequential probability calibration. If p_t is the true conditional probability of a fixed terminal result Y given information F_t, then {p_t} is a bounded martingale. Assess whether the forecast has *predictable conditional drift*, using series-blocked confidence intervals and game-ending absorption. This diagnoses temporal consistency; it is not a claim that all realized paths must be smooth or that p_t=p_(t+1).

The **combination and test protocol** constitute a proposed original analytical contribution in this project. They have not yet been demonstrated to outperform M1. Do not present them as a globally first-of-kind published invention.

### 2. Research questions and hypotheses

**RQ1: Do temporary tactical opportunities contain information beyond current gold/time?** Null H0: event-option features provide no incremental proper-score improvement over M1. Proposed mechanism: Roshan/Aegis and buybacks change the *feasible near-term action set*, not merely accumulated wealth. Event timestamps may help in minutes 10–35, even when gold differences are similar.

**RQ2: Does the mapping from economic advantage to durable map control matter?** Null H0: after conditioning on gold, time and transient options, irreversible structure mismatch adds no predictive information. The feature measures disagreement rather than cause; a team may trade tower damage for farm intentionally.

**RQ3: Are generated probabilities time-coherent?** Under an adequate information filtration, the *expected* future change in p_t conditional on earlier state is zero, after counting matches that end by t+h as absorbed at Y. A systematic conditional drift suggests misspecification, calibration drift or sampling bias. This is a diagnostic, not an alternative outcome score and does not automatically improve prediction.

### 3. Point-in-time state construction

Let t denote an integer game minute, T=60t and Y∈{0,1} denote the final Radiant win indicator. The only permitted raw data are `/proMatches` and `/matches/{match_id}`. At prediction time all features depend exclusively on per-minute observations with **actual time <=T** and on events logged with `event.time<=T`.

The locked M1 baseline uses gold advantage, elapsed time, and a gold×log-time interaction. The new state adds three predeclared scalar features:

1. **Aegis claim window** A_t = Σ_e s_e max(0, 1−(T−τ_e)/300), where e ranges over `CHAT_MESSAGE_AEGIS` pickup/claim events with τ_e<=T, and s_e=+1 for Radiant and −1 for Dire. This uses the five-minute Aegis duration as a bounded *recent-pickup proxy*, NOT proof of current possession: death may consume it and the exact time of pickup/use has its own uncertainty. No backwards filling and no future data.

2. **Recent buyback commitment** B_t = Σ_e s_e max(0, 1−(T−τ_e)/300), where e ranges over per-player `buyback_log` entries. The five-minute *analytical decay window* is a fixed local horizon, NOT an assertion that the game's actual buyback cooldown is five minutes. The regression coefficient is not assigned a predetermined sign: using a buyback can help survive or signal that a team is under pressure.

3. **Unconverted economic lead** U_t = g_k(t)·I[g(t)·S(t)<0], where S(t) is signed structural progress: tower kills against Dire minus tower kills against Radiant, plus a fixed 2× multiplier for barracks destruction. The 2× value is a declared heuristic, not a trained game valuation; U_t changes sign if Radiant and Dire are swapped. It is zero when structures are tied. Alternative multipliers are NOT tuned on the same test.

Temporary event streams **decay to zero**, structural control persists, and missing logs are NaN (not false zeros). Team-swap, prefix truncation and future/postgame-field poisoning must preserve or appropriately flip every feature. In particular, existing base truncation tests need to be extended to `buyback_log` and `purchase_log` before using those fields.

Use the SAME logistic-regression pipeline (train-only median imputation, train-only standardization, regularization C=1) for M1 and the single proposed M4. No LSTM, Transformer, Optuna, external embeddings, or dozens of sparsely sampled interactions on a 500-match cohort.

### 4. Falsifiable tests, validation and stopping rule

**Feasibility evidence (input-only):** Across the original 500 parsed matches, the payloads contain 795 Roshan kills, 772 Aegis claims, 1,396 buyback events and 8,121 building-kill events. These are EVENT counts, not an estimate of currently active buffs. A separate, outcome-blind audit of all three historical cohorts (500+200+200 matches) found 9,000 players' `times` arrays starting at zero and proceeding in 60-second steps; all checked per-player gold/XP/LH lengths, player clocks and team gold-advantage sums aligned. This makes the registered PIT feature construction feasible IN THESE SAMPLED MATCHES; it does not prove real-world packet arrival time.

**Development:** Original 291 train / 103 validation, chronological with intact series groups. These labels were ALREADY seen in previous projects: every newly reported M4 result on them is EXPLORATORY and subject to adaptive-selection bias. Run at most one M4 candidate with the three features as registered above, evaluated against M1 and the earlier raw-objective M3 on the same validation set. Report both positive and negative values; no threshold search and no latent coefficient edits.

**Ablation:** M1; M1+{A,B} temporary features; M1+{U} structural mismatch; single M4=M1+{A,B,U}. The ablation is DESCRIPTIVE on development; don't pick whichever looks best after seeing validation. A predeclared positive screening gate for M4: validation improvement ≥0.005 absolute log loss over M1, paired series-cluster 95% upper bound below zero, no Brier degradation, and at least two of three train-only forward folds agreeing in direction. Because n=103 validation games is small and features may be rare, this gate may fail. If it fails, STOP and document a negative result.

**New confirmatory cohort (not fetched or scored for this hypothesis):** Only after freezing code and selection, sample the first 200 new eligible parsed professional matches strictly after 2 April 2026, exclude overlapping series and match IDs, and commit the full outcome-blind manifest SHA256. Train candidate models on PREVIOUSLY DECLARED data only, then test ONCE. Use full-game minute-weighted proper log loss as primary; Brier, phase losses, calibration, equal-match sensitivity and paired series bootstrap as secondary. No use of the consumed 106+200+200 games as a blind test. Never declare a robust edge if the series-adjusted CI includes zero.

**Falsification conditions:** incomplete buyback logs; event timestamps after the game-clock cutoff; a feature changing when future logs/postgame stats are poisoned; failure under Radiant/Dire swapping; M4 losing to M1; effects confined to 1–2 series; changing sign across time; apparent gain from a single extreme match; or mismatch between saved and fresh source receipts. The absolute match outcome is not a causal label for the value of an objective.

### 5. Forecast path coherence and a game-level story

Let F_t be the observable game information. A calibrated conditional forecast p_t=E[Y|F_t] obeys E[p_(t+h)−p_t | F_t]=0. To avoid conditioning on survival, define **p_(t+h)=Y for games finished by t+h** and evaluate horizons h∈{1,5,10} fixed before analysis. Stratify the matched trajectories by earlier p_t decile or a small *predefined* event-state indicator; resample entire matches/series. This is an exploratory model diagnostic, not a replacement for strictly proper loss and not an assumption that individual win-probability paths cannot jump after events.

The visual case study should show **two ACTUAL matches at the same minute and similar gold lead but different option/structural states**, with time-aligned Roshan, Aegis and tower event markers. Any outcome difference is a comparison, not an intervention or causal effect. If there are insufficient matched examples with adequate support, show the absence of such evidence instead.

### 6. What to ship and what not to claim

Vexil values creative but CORRECT modeling, including honest negative results. The mandatory deliverable remains a single self-contained 500-match notebook, a ≤4-page report, pinned requirements, fresh-Colab Run All and assistance/public-code disclosure. The previous M1 gold×time model remains the defensible default until M4 clears a genuinely new independent gate. Do not substitute external Zenodo data, use prohibited OpenDota endpoints, add a dependency that breaks Colab, or report accuracy at the last minute as a success metric.

For the report, the actionable contribution is a concise *mechanism + falsification + visual event case*, not a PhD-length theoretical section. This proposal belongs in `docs/` as private research support, not as an unsubstantiated new result in the submitted REPORT.md.

### References

See `docs/OPEN_SOURCE_PRIOR_ART.md` for URL/DOI sources and prior-art boundaries. Mechanics: the Aegis expires within five minutes of pickup but can be consumed earlier; Liquipedia, https://liquipedia.net/dota2/Aegis_of_the_Immortal. Research methodology: registered hypotheses, point-in-time checks, match/series-blocked validation, proper log loss/Brier and uncertainty. This proposal is independent work influenced by but not copied from the cited public repositories.
