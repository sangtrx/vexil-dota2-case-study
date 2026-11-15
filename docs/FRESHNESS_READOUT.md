> **Research inference withdrawn (15 November 2026).** The lagged Brier freshness mean is an endpoint telescoping identity, not per-minute information value or measured latency. The 1.76x headline must not be used. Read [FRESHNESS_ERRATA.md](FRESHNESS_ERRATA.md) before interpreting the historical numbers below. This is NOT recruiter-facing appendix material.

# Value of Freshness | A real-time forecasting question beyond model complexity

**Evidence level: post-hoc descriptive research on an already opened TEST.** Not part of the required 500-match model selection or a second independent holdout. No new fitted model, threshold, calibration, live network recording or betting return.

## The question

A model may score better offline and still be less useful in a live system if its information is old. On an **identical match/minute**, does a forecast using the latest *historically available minute snapshot* beat that same frozen model's probability from 1, 2 or 5 minutes earlier? This question has a clean counterfactual *readout*, even though it is **not** a causal test of real packet latency.

This applies three ideas from [Quant Research Bible](https://github.com/sangtrx/quant-research-bible): legal information filtrations and event/receipt clocks (section 3), strictly proper probabilistic scoring (section 7), and the evolving conditional-win-probability/martingale benchmark (section 13.12). [Protocol](FRESHNESS_PROTOCOL.md) was committed before the script's first execution, but **TEST labels had already been opened in earlier work**; the word "locked" is procedural here, not a claim of blinded confirmation.

## What was actually measured

Frozen [held-out probabilities](../artifacts/heldout_predictions.csv), 106 games, 54 professional series, 3,836 total minute forecasts. Each lag pairs minute `t` with an existing minute `t-k` **from the same game**. Scores use the identical eventual winner. No model refit or refetch. Brier value = Brier(old probability, winner) minus Brier(current probability, winner); positive means the latest snapshot scores better.

| Retrospective age | Paired minute rows | M0 Brier value | M1 Brier value | M1 95% series-bootstrap interval |
| --- | ---: | ---: | ---: | --- |
| 1 min | 3,730 | +0.006517 | **+0.006356** | [+0.005701, +0.006938] |
| 2 min | 3,624 | +0.012781 | **+0.012315** | [+0.010889, +0.013578] |
| 5 min | 3,306 | +0.029475 | **+0.028189** | [+0.024150, +0.031716] |

On **the exact same 3,730 one-minute-eligible rows**, M1's fresh Brier advantage over M0's fresh Brier is **+0.003617**. The **+0.006356** M1 one-minute freshness value is therefore about **1.76 times** that model-complexity advantage on a matched evaluation population. This is a *descriptive effect-size ratio*, not an economic ROI or a recommendation to choose a model based on exposed TEST labels.

As a more explicit same-row scenario, M1's **one-minute-old** forecast scores **0.002739 Brier worse** than M0's *current* forecast, but the descriptive 54-series interval **[-0.000412,+0.005943] crosses zero**. At two minutes, the difference is **+0.008776** (interval **[+0.005286,+0.012140]**); at five minutes it is **+0.024987** (**[+0.019754,+0.029825]**). These are *hypothetical mismatched-freshness comparisons*, not an actual choice between deployed pipelines; both models would normally experience the same upstream data delay.

### Where freshness appears to matter

For M1, the one-minute Brier value by *current* game phase is **+0.003714 (minute 0–9)**, **+0.004804 (10–19)**, **+0.009386 (20–29)** and **+0.007947 (30+)**. These bins were fixed in the protocol. The larger minute-20–29 penalty suggests a concrete question about short-lived map/economy transitions, not an identified mechanism, and the late-game conditioning is affected by game survival and duration. M1 was already known to have *worse* late-game Brier than M0; freshness does not cure that model-comparison failure.

### What the dynamic-probability theory adds

For one-minute M1 changes, the algebraic decomposition of Brier freshness value is **+0.003430 mean squared forecast innovation** plus **+0.002926 mean residual/outcome-alignment term** = **+0.006356**. For a well-specified true conditional probability process and suitable nonanticipating sampling, the latter would have zero expectation. It is **not** a formal martingale test here: estimated forecasts, correlated minute labels, and selection on surviving games violate a naive independent-increments interpretation.

**Robustness:** The equal-game-weighted one-minute M1 Brier value is **+0.006852**, positive like the minute-weighted statistic. A per-game calculation is positive in **104/106 games** and a per-series calculation in **53/54 series**. Excluding one entire series at a time leaves the minute-weighted Brier freshness value in **[+0.006291,+0.006581]**; the largest series accounts for **3.57%** of paired minute rows. This reduces the concern that one series alone drives the freshness effect, **not** the dependence, survivorship or data-reuse limitations. The 10,000-draw bootstrap resamples all games in a professional series together, rather than pretending thousands of minute labels are independent. These remain descriptive uncertainty after earlier TEST inspection and numerous past model experiments.

## Senior Data Scientist decision, not a product claim

1. Preserve the gold-only M0 benchmark and validation-selected M1; **do not** select a new model or threshold on this read-only TEST diagnostic.
2. Treat an arrival-time/data-age observability layer as a strong next operational hypothesis. Log `match_id`, `game_minute`, `event_time`, `received_at`, feature watermark, decision time and model version; score only what was genuinely available **when** an actual live decision was made.
3. Predeclare a new, previously untouched tournament/series evaluation and compare freshness bands at equal game-minute/phase and comparable source quality. Include calibration, phase-specific proper scores, source staleness, and uncertainty. No betting profitability can be inferred without contemporaneous market odds, quotes, execution and costs.

**Reproduce locally (offline, no data fetch, no GitHub Actions):**

```bash
python3 research/freshness_innovation_audit.py --check
python3 -m unittest tests.test_freshness_audit -v
```

The [machine-readable receipt](FRESHNESS_RECEIPT.json) contains the unrounded values, same-row comparisons, all phase cells and bootstrap intervals. The original [Vexil three-page report](../REPORT.pdf), selected M1, notebook, and held-out forecast CSV remain unchanged.
