# Minimal economic representation and match-balanced training: October/November

**Exploratory after previously observed outcomes, not an untouched test.** No new data, no April/October/November outcome-driven fitting, no recruiter package changes.

| Period | Model | Log loss | Brier | 30+ Brier | Equal-match LL |
| --- | --- | ---: | ---: | ---: | ---: |
| October | M0_gold | 0.499484 | 0.168514 | 0.115221 | 0.481642 |
| October | M1_interaction | 0.493602 | 0.165518 | 0.116287 | 0.470756 |
| October | Q1_path | 0.489278 | 0.164303 | 0.111409 | 0.468959 |
| October | E_SHARE1 | 0.493254 | 0.165366 | 0.115895 | 0.470411 |
| October | SAT_ASINH3 | 0.498537 | 0.165434 | 0.116869 | 0.475561 |
| October | MATCH_EQUAL | 0.491557 | 0.164981 | 0.115790 | 0.466953 |
| November | M0_gold | 0.456167 | 0.150875 | 0.091406 | 0.443868 |
| November | M1_interaction | 0.442682 | 0.144025 | 0.085197 | 0.429682 |
| November | Q1_path | 0.449371 | 0.147808 | 0.092953 | 0.435293 |
| November | E_SHARE1 | 0.441246 | 0.143342 | 0.084879 | 0.427488 |
| November | SAT_ASINH3 | 0.447740 | 0.144161 | 0.086503 | 0.433834 |
| November | MATCH_EQUAL | 0.436265 | 0.142351 | 0.082211 | 0.422656 |

## Predeclared comparisons (negative LL delta is improvement)

| Cohort | Candidate | vs | LL delta | 95% series CI | 99.5833% within-screen interval | Brier delta | Late 30+ Brier delta | Equal-match LL delta | Equal-match 95% series CI | Drop-one-series LL range |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| October | E_SHARE1 | M1_interaction | -0.000347 | [-0.001694,+0.001028] | [-0.002331,+0.001649] | -0.000153 | -0.000391 | -0.000345 | [-0.001817,+0.001178] | [-0.000543,-0.000166] |
| October | E_SHARE1 | Q1_path | +0.003976 | [-0.003849,+0.011620] | [-0.007190,+0.015197] | +0.001063 | +0.004486 | +0.001452 | [-0.005906,+0.008935] | [+0.002860,+0.005147] |
| October | SAT_ASINH3 | M1_interaction | +0.004936 | [+0.000992,+0.008788] | [-0.000946,+0.010497] | -0.000084 | +0.000582 | +0.004806 | [+0.001375,+0.008165] | [+0.004212,+0.005854] |
| October | SAT_ASINH3 | Q1_path | +0.009259 | [+0.001124,+0.017338] | [-0.002377,+0.021004] | +0.001131 | +0.005460 | +0.006603 | [-0.001086,+0.014262] | [+0.008176,+0.010601] |
| October | MATCH_EQUAL | M1_interaction | -0.002044 | [-0.005285,+0.001339] | [-0.006580,+0.002930] | -0.000537 | -0.000497 | -0.003802 | [-0.006656,-0.000881] | [-0.002836,-0.001800] |
| October | MATCH_EQUAL | Q1_path | +0.002280 | [-0.007427,+0.012097] | [-0.011378,+0.015729] | +0.000678 | +0.004381 | -0.002005 | [-0.010948,+0.007229] | [+0.000505,+0.003463] |
| November | E_SHARE1 | M1_interaction | -0.001436 | [-0.003228,+0.000539] | [-0.003937,+0.001644] | -0.000683 | -0.000318 | -0.002194 | [-0.004906,+0.000235] | [-0.002048,-0.000966] |
| November | E_SHARE1 | Q1_path | -0.008125 | [-0.023956,+0.007332] | [-0.029858,+0.012559] | -0.004466 | -0.008074 | -0.007805 | [-0.023405,+0.008038] | [-0.011810,-0.002907] |
| November | SAT_ASINH3 | M1_interaction | +0.005058 | [-0.005981,+0.015986] | [-0.011086,+0.019819] | +0.000136 | +0.001306 | +0.004152 | [-0.005735,+0.014824] | [+0.000021,+0.008499] |
| November | SAT_ASINH3 | Q1_path | -0.001631 | [-0.023454,+0.020060] | [-0.031672,+0.029535] | -0.003647 | -0.006450 | -0.001459 | [-0.022599,+0.019715] | [-0.010684,+0.005715] |
| November | MATCH_EQUAL | M1_interaction | -0.006417 | [-0.011759,-0.000695] | [-0.013660,+0.001953] | -0.001674 | -0.002986 | -0.007026 | [-0.011813,-0.001534] | [-0.009048,-0.004907] |
| November | MATCH_EQUAL | Q1_path | -0.013106 | [-0.030787,+0.005495] | [-0.036750,+0.014522] | -0.005456 | -0.010742 | -0.012637 | [-0.030411,+0.006383] | [-0.019753,-0.008605] |

## Decision, evidence and limits

- All-period gate (gain >=.005 LL vs M1 and Q1 in both periods; within-screen 99.5833% upper bound <0; no overall/late30 Brier regression): {'E_SHARE1': False, 'SAT_ASINH3': False, 'MATCH_EQUAL': False}.
- Fit uses only original 291 March TRAIN games. October and November data were already inspected for previous models; within-screen adjusted intervals do not correct cumulative feature searches.
- Source player gold_t is *cumulative earned gold*, NOT actual inventory net worth. Source as-of game clock consistency does not imply available real-time received_at.
- A match-equal TRAIN objective does not mean forecasts within the same match are independent. All intervals bootstrap whole professional series/singletons.
- The equal-match cluster-bootstrap interval was added as an explicitly POST-RESULT sensitivity after inspecting the first scoring receipt. No model, feature, hyperparameter, population, frozen comparator or approval gate was changed.
- Employer notebook, original TEST forecasts, report/PDF, ZIP, original Draft PR and main unchanged.
