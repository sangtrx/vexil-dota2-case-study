# Fixed March-trained rich-features on October and November reused cohorts

**Research-only transfer check.** Earlier October/November outcomes had already been scored. This is not a blind independent validation.

**19 November correction:** The ALL model used the historical 81-feature extractor with missing Roshan attribution due to the parser error. The October/November transfer experiment was **not rerun** with corrected Roshan fields. Interpret its scores as historical only; see [Roshan correction](ROSHAN_CORRECTION_20261119.md).

| Cohort | Games / rows / series | M0 log loss | M1 log loss | Q1 log loss | ALL log loss | ALL−Q1 LL (95% series bootstrap) | ALL−Q1 equal-match LL |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| October | 180 / 7346 / 107 | 0.499484 | 0.493602 | 0.489278 | 0.493651 | +0.004373 [-0.005061,+0.013042] | +0.001847 |
| November | 22 / 952 / 9 | 0.456167 | 0.442682 | 0.449371 | 0.445080 | -0.004291 [-0.024635,+0.015453] | -0.002087 |

## Comparison and generalization audit

| Cohort | ALL−M1 LL | ALL−M0 LL | ALL−Q1 Brier | ALL−Q1 Brier 30+ | Delete-one-series ALL−Q1 LL range | Frozen refutation threshold reached? |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| October | +0.000049 | -0.005834 | +0.001484 | +0.002749 | [+0.002569,+0.006403] | False |
| November | +0.002398 | -0.011087 | -0.002179 | -0.003905 | [-0.009498,+0.003702] | False |

## Predeclared league diagnostics (only leagues with >=10 games; not for model selection)

| Cohort | League ID | Games | Rows | ALL-Q1 LL | ALL-M1 LL |
| --- | --- | ---: | ---: | ---: | ---: |
| October | 18631 | 32 | 1181 | -0.002011 | +0.002920 |
| October | 19944 | 48 | 1913 | +0.015392 | +0.004278 |
| October | 20334 | 12 | 396 | -0.001752 | -0.011524 |
| October | 20395 | 81 | 3576 | +0.002123 | -0.000351 |
| November | 20486 | 15 | 681 | -0.004940 | -0.001652 |

## Reproduction and scientific limitations

- Fit all four fixed model recipes once on original March TRAIN only. The original 202 October/November metadata, previously scored rows, raw gz files and per-match hash manifests were verified; no new network downloads.
- M0/M1 predictions independently re-created against earlier saved probabilities within 1e-7; all held-out source rows exact (match_id,minute) match.
- Even an ALL improvement in both periods cannot repair prior broad March feature search or the fact these October/November outcomes were already observed for M0/M1.
- True live per-source ingress timestamps remain unverified. OpenDota post-game parser coherence does not prove fresh live availability.
- Original notebook, heldout TEST CSV, report, reviewer ZIP and Draft PR #9 unchanged.
