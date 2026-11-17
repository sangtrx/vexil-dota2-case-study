# All four unfinished Dota feature families — fixed 5-model historical screen

**Five complete finite candidates; original TRAIN-forward only. No fresh test, no original VAL/TEST, no main / employer / ZIP changes.**

## Primary comparison: incremental log loss (negative = candidate better)

| New family | vs M1 LL | 99.5% cluster CI vs M1 | vs Q1 LL | 99.5% cluster CI vs Q1 | Wins vs M1 / vs Q1 | Research gate |
| --- | ---: | --- | ---: | --- | ---: | --- |
| R | -0.004342 | [-0.010257,+0.000773] | +0.001781 | [-0.011550,+0.014860] | 4/4 / 1/4 | FAIL |
| O | -0.003193 | [-0.008102,+0.001351] | +0.002930 | [-0.011719,+0.017413] | 4/4 / 1/4 | FAIL |
| C | -0.002043 | [-0.004865,+0.000468] | +0.004080 | [-0.011615,+0.019915] | 4/4 / 1/4 | FAIL |
| I | -0.001426 | [-0.008796,+0.005021] | +0.004697 | [-0.010129,+0.019764] | 2/4 / 1/4 | FAIL |
| ALL | -0.007760 | [-0.018538,+0.001622] | -0.001637 | [-0.015642,+0.011463] | 4/4 / 2/4 | FAIL |

## Frozen four fold log loss

| Fold | Games | M0 | Additive | M1 | Q1 | R | O | C | I | ALL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.64607 | 0.64377 | 0.65210 | 0.63226 | 0.64440 | 0.64992 | 0.65176 | 0.65431 | 0.64488 |
| 2 | 44 | 0.63385 | 0.63952 | 0.62188 | 0.62825 | 0.62009 | 0.61953 | 0.62124 | 0.62385 | 0.62052 |
| 3 | 32 | 0.58828 | 0.58879 | 0.59486 | 0.58796 | 0.58930 | 0.59114 | 0.59087 | 0.59027 | 0.58286 |
| 4 | 39 | 0.58996 | 0.59060 | 0.59405 | 0.58159 | 0.58961 | 0.58979 | 0.59114 | 0.58946 | 0.58227 |

## Secondary: proper Brier and equal-match weighting

| New family | Δ Brier vs M1 | Δ Brier 30+ vs M1 | Equal-match Δ LL vs M1 | Patch 59 / 60 Δ LL vs M1 |
| --- | ---: | ---: | ---: | --- |
| R | -0.002050 | -0.008907 | -0.003769 | -0.00434 / -0.00434 |
| O | -0.001015 | -0.003519 | -0.002522 | -0.00278 / -0.00419 |
| C | -0.000687 | -0.001245 | -0.001739 | -0.00166 / -0.00297 |
| I | -0.000805 | -0.002381 | -0.001039 | -0.00044 / -0.00378 |
| ALL | -0.003165 | -0.010701 | -0.006588 | -0.00635 / -0.01114 |

## Audits and exclusions

- Historical raw matches = 291, TRAIN snapshot checks = 10675, swap checks = 10675, future-poison checks = 10675.
- Patches in raw TRAIN: {'59': 250, '60': 41}; OOF patch samples: {'59': 96, '60': 41}. Patch is a diagnostic, not an interaction selected post-score.
- Nonzero feature fractions: {'reg_cusum10': 0.8985, 'reg_shift3': 0.8909, 'ordinal_run_balance10': 0.8392, 'ordinal_entropy10': 0.8684, 'objective_conversion5': 0.5989, 'objective_followthrough10': 0.6919, 'item_bkb_diff': 0.2609, 'item_blink_diff': 0.4486, 'item_recent5_diff': 0.388}.
- Precise hero skill-level power-spike timestamps NOT present: BLOCKED, not silently approximated by final player level. Item BKB/Blink purchase proxy is historically reconstructed but not verified live-deliverable at the same minute.
- 2016+ OpenDota raw arrays have no trustworthy per-sample received_at; minute-index parity does not establish actual live PIT. No original TEST opened.
- All previous feature trials and the already inspected TEST create substantial researcher degrees of freedom. This one-screen 99.5% Bonferroni interval does not repair historical selection. Nothing here can be promoted.

**Decision:** Keep negative findings visible; original Vexil submission on HOLD pending applicant AI disclosure/hours and access sign-off.
