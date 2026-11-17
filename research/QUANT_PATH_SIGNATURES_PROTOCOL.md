# Quant Bible / 2026 path-signature ideas — bounded Dota feature trial

**Date:** 18 November 2026, before this study's four TRAIN-fold fit/scoring. Main Vexil VAL/TEST have already been used in other studies, so this is **post-result exploratory historical TRAIN research, NOT blind validation**. Do not represent it as a new Vexil employer result or as an untested, preregistered take-home.

**Scientific transfer, not borrowed result:** Private Sang Quant Research Bible v1.10.1, Git main a9e2a4f (§8.4–8.6, §13.12–13.13, §13.16); Choi (2026) Journal of Forecasting, DOI 10.1002/for.70176 (lead-lag signatures); Dota pro temporal feature work (Hodge et al., IEEE Trans Games, DOI 10.1109/TG.2019.2948469; 2025 DotA 2 Match Outcome Prediction System DOI 10.3390/bdcc9120302). Method transfer is hypothesis only.

## Mechanisms and exactly four new features

Using **as-of** Radiant gold- and XP-advantage histories g_i,x_i in thousands for i=max(0,t-10),...,t; no terminal data, labels, player final stats, optional draft priors or unseen raw data. The 291 original TRAIN matches / 10,675 rows of existing SHA-locked research/RICH_FEATURE_TRAIN_ONLY.csv.gz have gold_k and xp_level from a prior all-minute RAW projection audit.

**Economic lead-lag geometry (2).** Let G_i=g_i-g_start, X_i=x_i-x_start, dG,dX adjacent increments, V=1+sum|dG|*sum|dX|, W=tanh(g_t/5). Both features are odd under exchange of Radiant/Dire because W flips, and their raw cross-series geometry is even:
1. sig_goldxp_loop10 = W * 0.5 * sum(G_i*X_{i+1}-G_{i+1}*X_i) / V. Oriented gold–XP path area over up to 10 past intervals; it can encode **relative order** in economy growth not captured by endpoint gold/XP gaps. Not a causal estimate.
2. sig_goldxp_leadlag10 = W * sum(dX_i*dG_{i+1}-dG_i*dX_{i+1}) / V for 2+ increments, else 0. Lag-one cross-flow asymmetry on recent increments, a low-order lead/lag statistic; not fitted or a Granger causal test.

**Economic advantage durability (2).** Let s=sign(g_t), R_i=s*g_i, and running_max(R) be the cumulative maximum from the **window start**:
3. lead_occupancy10 = mean(sign(g_i)). Signed portion of recent window spent ahead; does not depend on outcome or current team-pick label.
4. leader_underwater_area10 = -s*mean(running_max(R_i)-R_i)/(1+abs(g_t)), zero when g_t=0. Signed integrated drawdown exposure / time-under-water. Unlike gold_retreat10, it records **duration and severity**, not only current retreat. The sign is odd under team swap.

**Predeclared warmup:** histories of length one give area/leadlag/underwater =0 and occupancy=sign(g0). No floor/epsilon thresholds beyond V's +1 and underwater's +1. All four values must be finite; all four must negate under side-mirroring to 1e-10. Causal prefix poison tests must pass across all 10,675 rows. No fitting when computing these transforms.

## Locked model and evaluation

Single candidate **C4 Geometry+Resilience**, exactly M1 base [gold_k,minute10,gold_x_time] plus 4 listed new features (7 total), median imputer -> StandardScaler -> LogisticRegression(C=1,max_iter=1000,random_state=20261113) as in frozen M1/Q1. No extra nonlinear model, windows, threshold tuning, additional model variants or re-fitting to VAL/TEST. Controls: M0 gold, A additive gold+minute, M1 gold×log1p(minute10), Q1 five-feature PathRisk, refit only on earlier TRAIN games.

Four historical chronological, mature-label series-disjoint folds using existing FROZEN_CUTS=(154,176,220,252,291), expected 137 out-of-fold TRAIN games / 5081 minute snapshots / 70 professional-series or singleton clusters. Ensure M0/A/M1/Q1 fold metrics exactly reproduce their existing research receipts to 1e-10, every feature row comes from that match's prefix and independent mirror/suffix-poison checks, and protected TEST CSV/notebook/ZIP hashes do not change.

Primary: minute-weighted log loss C4 minus M1 and Q1 (negative improvement). **5000 paired series-cluster bootstraps** with seed 20261115 produce descriptive 95% CIs for LL/Brier; compare M0/A too. Secondary overall Brier, 30+ Brier, fold signs, concentration of favorable improvement in a single cluster, phase slices (<10,10–19,20–29,30+) and pairwise correlations with similar existing 81 features (diagnostic ONLY). No post-hoc selection among the four features.

**Frozen future-only advancement gate**: aggregate ΔLL <=-0.0025 against both M1 and Q1, two descriptive bootstrap 95% upper bounds <0, at least 3/4 folds outperform both comparators, overall and late30 Brier not worse than both, and largest positive cluster under 50% of gain against M1. Even passing means **only** a candidate for genuinely new independent future evaluation, not employer promotion.

**Known limits and explicit stop:** 28+ previous models screened, 84-input candidates already negative; no correction across entire history, and the prior original TEST is already opened. OpenDota historical per-minute arrays are indexed by position, **not proven arrival-time aligned**: October 2026 Zenodo v3 (DOI 10.5281/zenodo.23166182) excluded 1,849 different matches for time-axis anomalies. Do not claim our raw cache is immune or that historical project-as-of proves true live observability. This experiment cannot promote the model or certify live arrival without an independent time-axis verification. Original Vexil notebook, TEST predictions, 4-page report, ZIP, Colab receipt, applicant-owned hours/AI disclosure, and Draft PR #9 must remain unchanged. Research branch only.
