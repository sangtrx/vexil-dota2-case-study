# Early missing-data simulation on 137 TRAIN-forward games

**Post-result corrective sensitivity**, not independent confirmation or measured live latency. Old frozen receipt retained. The old function's earliest-lag source substitution was wrong.

Source: 137 games, 5081 minute forecasts, 70 professional groups. NO_DATA rows: lag1=137, lag3=411.

| Stream | Old LL | Corrected LL | Change | Old Brier | Corrected Brier | 30+ Brier check |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FRESH | 0.612086 | 0.612086 | +0.000000 | 0.212744 | 0.212744 | 0.183109 |
| CLOCK1 | 0.626112 | 0.626087 | -0.000025 | 0.218444 | 0.218432 | 0.200558 |
| HOLD1 | 0.627745 | 0.627720 | -0.000025 | 0.218889 | 0.218876 | 0.201058 |
| CLOCK3 | 0.648923 | 0.648852 | -0.000071 | 0.228006 | 0.227970 | 0.228156 |
| HOLD3 | 0.654000 | 0.653924 | -0.000075 | 0.229391 | 0.229353 | 0.230678 |

## Corrected HOLD - CLOCK (negative means holding wins)

| Lag | Corrected LL delta | Corrected 95% series CI | 97.5% two-lag CI | Corrected Brier delta | Corrected 30+ Brier delta |
| --- | ---: | --- | --- | ---: | ---: |
| 1 minute(s) | +0.001633 | [+0.000181,+0.003218] | [-0.000106,+0.003529] | +0.000445 | +0.000500 |
| 3 minute(s) | +0.005072 | [+0.000889,+0.009661] | [+0.000065,+0.010414] | +0.001383 | +0.002522 |

Old and corrected 30+ Brier is identical: all delayed states t<lag are early.
No ability to verify actual event received_at; neither retrospective simulation can establish production service latency. No original applicant change.
