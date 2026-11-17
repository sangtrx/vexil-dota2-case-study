# 17 Nov 2026 external holdout — 22 genuinely new games, underpowered

**Decision: DESCRIPTIVE ONLY / DO NOT PROMOTE M1.** This optional OpenDota evaluation adds evidence on matches never used in the March 500-game notebook, prior November 100-game stress test, or the archived 120-game November research. It does **not** replace the Vexil required 500-game TEST and is not a true live-feed replay.

## Lock and provenance

- First protocol committed **before any new API discovery** as `40f36f9`; first metadata-only pilot (16 recent candidates, zero match details and zero scores) committed as `fddd70b`.
- Sample-size amendment `ae9124b` committed **before any `/matches/{id}` download or outcome-based scoring**: Nov 10 00:00 UTC to Nov 17 06:00 UTC; cap 12 `/proMatches` pages and first 300 candidates after metadata-only overlap checks. The amendment is fully disclosed; do not call this perfectly preregistered/blind.
- Amended listing commit `6b9357d` identified **22 candidates** after excluding overlap with 652 unique old match IDs and all positive old series IDs; raw page listing SHA256 `3dfab3a8d2068a01de28d7fae93e692b05f9eefdbf28c0c4b7dd61744b758294`.
- All 22 detail responses were parsed and accepted; **zero eligibility exclusions**. Raw `/matches` source payloads and exact collection receipt were committed as `19a6309` **before any M0/M1 scoring**. Original March TRAIN (291 games, 10,675 rows), gold-only M0 and gold×time M1, model fingerprints, source feature code, and original TEST scores were unchanged.
- The discovery source `/proMatches` **may contain outcomes**, though selection code only used IDs, start times and series. No human-blinding or real `received_at` logs are claimed.

## Results (22 matches; 952 minute forecasts; 9 series/singleton clusters)

| Metric, lower is better | M0 gold-only | M1 gold×time |
|---|---:|---:|
| Log loss | 0.456167 | **0.442682** |
| Brier | 0.150875 | **0.144025** |
| ECE-10 | **0.092905** | 0.104679 |

Paired M1−M0 log-loss point difference **−0.013485**; 10,000 predeclared series-bootstrap draws (seed 20261117) produced **[−0.028480, −0.000135]** (95%), but using whole **matches** yielded **[−0.028246, +0.002883]**, which includes zero. Brier difference **−0.006849**, with series CI **[−0.012602,−0.001674]** and match CI **[−0.012528,−0.000293]**. These unadjusted percentile intervals are unstable with only nine series clusters and are **not decisive inferential proof**.

**Domain concentration:** all 22 games are patch 60, from only **two leagues** (15 and 7 games). League one-at-a-time removal preserves the negative log-loss point sign, but this is not an independent league-level significance test. M1's overall calibration ECE was worse; at minute 30+, M1 ECE was **0.147316** versus M0 **0.083645**, even though Brier fell. The largest game's absolute influence equals 38.6% of the total signed log-loss improvement.

**Predeclared evidence threshold failed:** **22 games versus minimum 50**, and **9 clusters versus minimum 30**. The originally expected analysis was underpowered before scoring. Model M1 must **not** be promoted or tuned based on this result. The next valid confirmatory test would require a larger, prospectively frozen and more league-diverse cohort, preferably with true ingestion `received_at` for both features and outcomes. This optional cohort is distinct by match/series from earlier research, not necessarily independent by team/league.

## Reproduce offline without API requests

From the repo root with pinned `requirements.txt` installed, use a new scratch directory:

```bash
python -m research.prospective_nov17_holdout verify
mkdir -p /tmp/vexil-new-holdout-check
cp docs/PROSPECTIVE_NOV17_COLLECTION_RECEIPT.json /tmp/vexil-new-holdout-check/collection_receipt.json
cp -a research/prospective_nov17_accepted_raw /tmp/vexil-new-holdout-check/accepted_raw
python -m research.prospective_nov17_holdout score --out /tmp/vexil-new-holdout-check
sha256sum /tmp/vexil-new-holdout-check/score_receipt.json
```

Expected receipt SHA256 `5b2410f43bb51425faf9ec8521398b22fbf02f8f157310dcc62d985fc8861f14`. Compare `predictions.csv` to `artifacts/prospective_nov17_predictions.csv` byte-for-byte. The script refuses overwriting a previously scored directory. These scripts are optional research supplements; the required Vexil single notebook remains unchanged.

**Handoff:** Research-only private branch `research/vexil-prospective-holdout-20261117`. Do not merge into the existing Vexil reviewer ZIP or claim official employer 10/10 without an explicit separate acceptance review. No new model selection, no user personal hours or AI disclosure changes.
