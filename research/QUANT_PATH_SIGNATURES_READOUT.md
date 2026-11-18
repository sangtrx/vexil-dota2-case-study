# Quant Bible-inspired gold/XP path geometry and durability — TRAIN-only

This is one **pre-scoring committed exploratory** candidate, not new blind validation. Data from original VAL/TEST were not used for this evaluation. Prior search multiplicity remains.

Extracted 4 new fixed-window features over 10,675 rows / 291 TRAIN matches; 10,675 mirrors and 10,675 suffix checks.

## Log loss and Brier against locked controls

| Baseline | C4−baseline log loss | Series 95% CI | Delta Brier | Late30 delta Brier | Folds C4 wins |
| --- | ---: | --- | ---: | ---: | ---: |
| M0_gold | -0.000970 | [-0.011751,+0.008190] | +0.000185 | -0.003719 | 2/4 |
| A_additive | -0.002764 | [-0.014720,+0.007256] | -0.000325 | -0.005147 | 2/4 |
| M1_interaction | -0.000743 | [-0.005335,+0.003800] | -0.000731 | -0.001832 | 2/4 |
| Q1_path | +0.005380 | [-0.004789,+0.016475] | +0.001964 | +0.006079 | 1/4 |

## Every chronological TRAIN fold

| Fold | Games | M0 LL | A LL | M1 LL | Q1 LL | C4 LL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.646066 | 0.643769 | 0.652097 | 0.632260 | 0.653662 |
| 2 | 44 | 0.633853 | 0.639518 | 0.621876 | 0.628250 | 0.628034 |
| 3 | 32 | 0.588280 | 0.588787 | 0.594860 | 0.587963 | 0.593144 |
| 4 | 39 | 0.589960 | 0.590599 | 0.594053 | 0.581592 | 0.584960 |

## Time-phase diagnostics (not selection)

| Phase | Rows | ΔLL C4−M1 | ΔLL C4−Q1 |
| --- | ---: | ---: | ---: |
| 0-9 | 1370 | +0.000383 | -0.004832 |
| 10-19 | 1370 | -0.000233 | +0.004341 |
| 20-29 | 1302 | -0.001427 | +0.009798 |
| 30+ | 1039 | -0.002045 | +0.014677 |

## Feature diversity (diagnostic, not post-hoc selection)

| Feature | Nonzero share | Most correlated fixed legacy feature | Correlation |
| --- | ---: | --- | ---: |
| sig_goldxp_loop10 | 94.5% | gold_xp_flow_gap | -0.262 |
| sig_goldxp_leadlag10 | 94.5% | gold_xp_gap | +0.330 |
| lead_occupancy10 | 96.2% | gold_xp_gap | +0.708 |
| leader_underwater_area10 | 88.4% | gold_retreat10 | -0.626 |

**Frozen gate:** FAILED; no model promotion

C4 is a small mechanistic feature hypothesis, not causal evidence that XP leads gold or a distinct live edge. With 291 historical TRAIN matches, independent evidence is limited; minute snapshots repeat the same game winner and historical source arrival times are unverified. A 2026 published OpenDota time-axis correction is a reason to request further timestamp audit, not proof this dataset is affected.

Research branch only. Original applicant TEST predictions, notebook, 4-page report, ZIP, time spent and AI disclosure remain unchanged.
