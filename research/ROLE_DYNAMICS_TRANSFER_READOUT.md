# Role redistribution, gold-XP coupling and forecast consensus

**Post-result, nonblind historical research. Four fixed challengers scored without reselecting, one fitting on March TRAIN only. Negative findings retained.**

| Cohort | Model | Minute LL | Brier | 30+ Brier | Equal-game LL |
| --- | --- | ---: | ---: | ---: | ---: |
| October | M0_gold | 0.499484 | 0.168514 | 0.115221 | 0.481642 |
| October | M1_interaction | 0.493602 | 0.165518 | 0.116287 | 0.470756 |
| October | Q1_path | 0.489278 | 0.164303 | 0.111409 | 0.468959 |
| October | ALL | 0.493651 | 0.165787 | 0.114158 | 0.470806 |
| October | RANK3 | 0.493744 | 0.165539 | 0.116822 | 0.470610 |
| October | COUPLING3 | 0.494090 | 0.165935 | 0.116506 | 0.471330 |
| October | RANK_COUPLING6 | 0.494779 | 0.166237 | 0.117536 | 0.471624 |
| October | CONSENSUS | 0.489860 | 0.164189 | 0.112237 | 0.468525 |
| November | M0_gold | 0.456167 | 0.150875 | 0.091406 | 0.443868 |
| November | M1_interaction | 0.442682 | 0.144025 | 0.085197 | 0.429682 |
| November | Q1_path | 0.449371 | 0.147808 | 0.092953 | 0.435293 |
| November | ALL | 0.445080 | 0.145628 | 0.089048 | 0.433206 |
| November | RANK3 | 0.442361 | 0.143831 | 0.085774 | 0.429731 |
| November | COUPLING3 | 0.440382 | 0.143127 | 0.083881 | 0.428473 |
| November | RANK_COUPLING6 | 0.440104 | 0.142978 | 0.084906 | 0.428926 |
| November | CONSENSUS | 0.442627 | 0.144755 | 0.086230 | 0.430645 |

## Comparisons: negative logloss difference is better than comparator

| Cohort | Candidate | vs | Delta LL | 95% series CI | 99.375% series CI | Equal-game LL delta | Brier delta | 30+ Brier delta | Leave-one-series-out LL range |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| October | RANK3 | Q1_path | +0.004466 | [-0.003082,+0.011802] | [-0.005790,+0.014202] | +0.001651 | +0.001236 | +0.005413 | [+0.003508,+0.005660] |
| October | RANK3 | M1_interaction | +0.000142 | [-0.000816,+0.001159] | [-0.001211,+0.001506] | -0.000146 | +0.000020 | +0.000535 | [-0.000069,+0.000245] |
| October | COUPLING3 | Q1_path | +0.004812 | [-0.002655,+0.012169] | [-0.005067,+0.014885] | +0.002372 | +0.001632 | +0.005096 | [+0.003570,+0.005782] |
| October | COUPLING3 | M1_interaction | +0.000489 | [-0.001243,+0.002186] | [-0.001835,+0.002816] | +0.000574 | +0.000417 | +0.000219 | [+0.000166,+0.000731] |
| October | RANK_COUPLING6 | Q1_path | +0.005501 | [-0.002220,+0.012924] | [-0.004671,+0.015823] | +0.002665 | +0.001934 | +0.006127 | [+0.004213,+0.006556] |
| October | RANK_COUPLING6 | M1_interaction | +0.001178 | [-0.001063,+0.003370] | [-0.001846,+0.004244] | +0.000868 | +0.000719 | +0.001249 | [+0.000765,+0.001437] |
| October | CONSENSUS | Q1_path | +0.000582 | [-0.003201,+0.004227] | [-0.004629,+0.005625] | -0.000434 | -0.000114 | +0.000828 | [+0.000141,+0.001168] |
| October | CONSENSUS | M1_interaction | -0.003742 | [-0.007421,-0.000007] | [-0.008649,+0.001091] | -0.002231 | -0.001329 | -0.004050 | [-0.004290,-0.003191] |
| November | RANK3 | Q1_path | -0.007010 | [-0.022408,+0.008363] | [-0.027507,+0.012972] | -0.005562 | -0.003976 | -0.007179 | [-0.010932,-0.001863] |
| November | RANK3 | M1_interaction | -0.000321 | [-0.002036,+0.001426] | [-0.002569,+0.002248] | +0.000049 | -0.000194 | +0.000577 | [-0.000839,+0.000508] |
| November | COUPLING3 | Q1_path | -0.008989 | [-0.025490,+0.006517] | [-0.032061,+0.010769] | -0.006820 | -0.004680 | -0.009072 | [-0.012774,-0.002608] |
| November | COUPLING3 | M1_interaction | -0.002300 | [-0.006166,+0.002010] | [-0.007730,+0.003739] | -0.001209 | -0.000898 | -0.001316 | [-0.003675,-0.000980] |
| November | RANK_COUPLING6 | Q1_path | -0.009267 | [-0.026145,+0.007442] | [-0.032668,+0.012670] | -0.006367 | -0.004829 | -0.008047 | [-0.013810,-0.002375] |
| November | RANK_COUPLING6 | M1_interaction | -0.002578 | [-0.008273,+0.004330] | [-0.009963,+0.006717] | -0.000756 | -0.001047 | -0.000291 | [-0.004233,-0.000746] |
| November | CONSENSUS | Q1_path | -0.006744 | [-0.018763,+0.003228] | [-0.023526,+0.005682] | -0.004647 | -0.003053 | -0.006723 | [-0.009184,-0.001576] |
| November | CONSENSUS | M1_interaction | -0.000055 | [-0.006220,+0.006281] | [-0.008164,+0.008586] | +0.000964 | +0.000730 | +0.001033 | [-0.002311,+0.001521] |

## Results gating / source constraints

- Strict dual-period gate (requires >=0.005 logloss gain versus M1 and Q1, paired 99.375% series bootstrap upper<0, no Brier/30+ regression, in BOTH later cohorts): {'RANK3': False, 'COUPLING3': False, 'RANK_COUPLING6': False, 'CONSENSUS': False}.
- These are previously read October/November cohorts; per-screen Bonferroni 99.375% intervals do NOT correct earlier repeated screens and do not constitute prospective validation.
- All 291 March TRAIN matches used to fit each fixed logistic model. October and November outcomes never used in feature fitting, scaling or calibration. CONSENSUS is a fixed 0.5/0.5 probability average, no fitted gate.
- Per-player earned-gold and XP arrays must be source-aligned, as-of current minute, roster/side symmetric, group-invariant. They are NOT actual current item net worth.
- The two later cohorts and raw source manifest were previously verified; no new HTTP. True feature receipt timestamp is not available. No claims of live model reliability.
- The employer notebook, 4-page report, reviewer ZIP, original March TEST and Draft PR #9 were not changed.

**Decision:** These additional mechanisms may inform later prospective science; no changes to the employer-ready required gold-only baseline or prior model decisions.
