"""Immutable exploratory hypothesis family, independent of validation outcomes.

All 28 hypotheses fixed before any registry run. Original 394 previously
inspected development games ONLY; no consumed held-out match used for fitting
or screening. A winner needs a truly new series-disjoint future cohort.
"""
from __future__ import annotations

BASE=("gold_k","minute10","gold_x_time")
SEED=20261113
PRACTICAL_IMPROVEMENT=.005
BOOTSTRAP_REPS=5000
SPECS=[
 # id, family, title, extra features, mechanism, null mechanism, algorithm
 ("P01","time-shape","Convex lead utility",("gold_signed_square","gold_cubic"),"Gold-to-win relationship may saturate / become asymmetric in large leads.","No nonlinear gold advantage remains after gold×log(time).","logistic"),
 ("P02","time-shape","Early/late slope continuity",("gold_x_early","gold_x_late"),"The marginal worth of a lead may change smoothly around midgame.","Separate time slopes do not improve proper scores.","logistic"),
 ("P03","time-shape","Asinh gold scale",("gold_asinh",),"Log-scaling high leads reduces outlier leverage without ignoring lead sign.","A nonlinear compression is not more transportable.","logistic"),
 ("P04","time-shape","Smooth time curvature",("minute_sq","gold_x_minute_sq"),"Marginal gold utility need not be log-linear over game age.","Extra temporal curvature does not calibrate better.","logistic"),
 ("P05","economic","Relative team economy",("relative_gold",),"A fixed gold gap means less when both teams are wealthy.","Relative purchasing-power signal adds no conditional information.","logistic"),
 ("P06","economic","XP purchasing power",("relative_xp","xp_k"),"Level/resource balance complements gold spending ability.","XP is redundant conditional on gold/time.","logistic"),
 ("P07","economic","Top-two carry concentration",("top2_share_gap","carry_gold_diff_k"),"A two-player concentration may change how readily gold converts to fights.","Concentration is redundant or unstable.","logistic"),
 ("P08","economic","Support and farming topology",("bottom3_gold_diff_k","lh_diff10","gold_gini_gap"),"Low-income support weakness may affect access to objectives despite equal gold.","Distribution features do not generalize.","logistic"),
 ("P09","dynamics","Five-minute economic shock",("gold_velocity5_k","xp_velocity5_k"),"A same gold lead reached after fast recovery may carry distinct information.","Shock is fully priced by current gold/time.","logistic"),
 ("P10","dynamics","Acceleration of lead",("gold_accel10_k","gold_velocity5_k"),"Lead velocity acceleration can signal momentum reversals.","Accelerations are noise once gold/time is known.","logistic"),
 ("P11","dynamics","Short-term volatility",("gold_vol5_k","gold_vol10_k"),"Chaotic fights make an equally large lead less stable.","Past realized volatility adds no reliable signal.","logistic"),
 ("P12","dynamics","Directional persistence",("lead_persistence10","gold_drawdown10_k","lead_flip10"),"A lead maintained through repeated skirmishes may be more robust.","Persistence has no incremental probability value.","logistic"),
 ("P13","objectives","Weighted map structure",("tower_tier_delta","barracks_delta"),"Destroying later-tier towers is more valuable than the same count of outer towers.","Tier distinctions do not survive time-aware validation.","logistic"),
 ("P14","objectives","Recent tower conversion",("tower_recent10","tower_tier_delta"),"Objective conversion after economic growth may be predictive beyond current gold.","Tower event recency does not improve forecasts.","logistic"),
 ("P15","objectives","Recent lethal fights",("kills_recent5","kill_delta"),"Recent hero kills grant a temporary time advantage.","Kill momentum is reflected in gold/time.","logistic"),
 ("P16","objectives","Roshan and tower sequencing",("roshan_recent10","tower_recent10"),"Neutral objective control and map capture in short succession indicate attack windows.","Neither timing signal adds reproducible information.","logistic"),
 ("P17","option-state","Aegis claim window",("aegis_claim5",),"A short-lived pickup event differs from an irrevocable objective.","Recent Aegis claim has no value conditional on gold/time.","logistic"),
 ("P18","option-state","Buyback commitment",("buyback_commitment5",),"A dated resource commitment may signal a reversible fight state.","Buyback pressure is redundant or directionally unstable.","logistic"),
 ("P19","option-state","Economy versus structures",("unconverted_gold_k",),"A gold-leading side may already have lost durable tower/barracks control.","Economic-structural mismatch cannot improve proper loss.","logistic"),
 ("P20","items","High-impact item completions",("major_item_diff","blink_bkb_diff"),"New non-consumable purchases are discrete power-spike proxies.","Item purchases are already encoded in gold/time.","logistic"),
 ("P21","items","Recent item investment impulse",("major_recent5","purchasing_breadth5"),"Simultaneous non-consumable purchases may mark a team-wide timing window.","Item impulse is noisy and does not transport.","logistic"),
 ("P22","draft","Strong-shrinkage hero draft encoding",("draft_onehot",),"Draft counterpicks may shift initial prior beyond 50-50.","A sparse 150-dimensional draft prior cannot generalize in 291 matches.","hero_ridge"),
 ("P23","shape","Shallow nonlinear gold/time",(),"A small tree can model interactions without hand-chosen phase boundaries.","A small tree overfits and degrades calibration.","tree_base"),
 ("P24","shape","Shallow calibrated macro-state tree",("xp_k","gold_velocity5_k","tower_tier_delta","kill_delta"),"A low-capacity tree may capture multi-signal interactions.","Nonlinear multivariate interactions do not improve net loss.","tree_macro"),
 ("P25","shape","Additive B-spline gold and time",(),"Smooth learned nonlinear shape may improve gold/time probabilities without high capacity.","Low sample power does not justify spline flexibility.","spline"),
 ("P26","synthesis","Strategic conversion bundle",("relative_gold","gold_velocity5_k","tower_tier_delta","roshan_recent10"),"Economic strength, mobility and objective conversion jointly shape advantage.","Joint mechanism only adds complexity and weak priors.","logistic"),
 ("P27","synthesis","Event-state bundle",("aegis_claim5","buyback_commitment5","tower_recent10","major_recent5"),"Option windows and equipment completion may complement gold/time.","Event timing is sparse and absorbs no additional information.","logistic"),
 ("P28","shape","Strong-regularized time-value",(),"Reducing model variance may preserve the existing time interaction better out of time.","Shrinkage does not change useful conditional probability structure.","strong_ridge"),
]
assert len(SPECS)==28 and len(set(x[0] for x in SPECS))==28
FEATURE_SET = {item for s in SPECS for item in s[3] if item!="draft_onehot"}
MODELS = ("M1_time_value",)+tuple(spec[0] for spec in SPECS)
