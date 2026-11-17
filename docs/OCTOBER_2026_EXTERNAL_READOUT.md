# October 2026 out-of-time holdout — evidence, not a model promotion

**Decision:** M1's point estimates improve overall log loss and Brier on 180 newly selected October games, but the **primary paired series-bootstrap log-loss interval crosses zero**. M1 performs worse after minute 30. Keep **M0 as reference / M1 shadow-only**, and do not advertise a verified live production advantage.

## Provenance, locked before outcomes

- This is a separate historical sample, NOT part of the required 500-game notebook and NOT a genuinely live feed-time holdout. The fixed October-1-to-November-1 protocol and M0/M1 model fingerprints were committed at `736ec0c`, before any October /proMatches or /matches detail access.
- The 12 `/proMatches` source pages, their content hashes and the **first 180 metadata-selected candidates** were committed at `09ba545`, **before detailed outcomes**. Full October API coverage contained more candidates; the fixed cap selects the most recent 180 (actual October 20–31). The 180 accepted raw matches and audit receipt were then committed at `d975e33`, **before inference**. No candidate excluded, no invalid clocks. Original 500 + previous November 100 + archived November 120 reduce to 652 distinct historical IDs; **zero overlap by match ID or positive series ID** with this October sample.
- Frozen models extracted from the exact March TRAIN 291-game notebook; same scaler/imputer and logistic coefficients, verified against precommitted fingerprints. No October refit, recalibration, feature selection or alternative model selected. Only permitted OpenDota endpoints `/proMatches` and `/matches/{match_id}` used.
- Raw samples and scores are in this private research branch. Notebook/report/ZIP in Vexil Draft PR #9 and source `main` remain unchanged. The separately assessed 22-game November 16–17 cohort is NOT pooled with this one.

## Results

| Sample / metric | M0 gold-only | M1 gold+time+interaction |
|---|---:|---:|
| Eligible games | 180 | 180 |
| Minute forecasts | 7,346 | 7,346 |
| Log loss ↓ | 0.499484 | **0.493602** |
| Brier ↓ | 0.168514 | **0.165518** |
| ECE-10 ↓ | 0.049255 | **0.043797** |

**Predeclared primary Δ = M1−M0, negative favors M1:** minute-weighted log loss **−0.005883**, 10,000 paired series/singleton-bootstrap 95% CI **[−0.013481,+0.001528]**; match-bootstrap **[−0.013658,+0.001669]**. Neither excludes zero. Brier Δ **−0.002996**, series bootstrap **[−0.005634,−0.000358]**, match bootstrap **[−0.005634,−0.000345]** (unadjusted). An independent 25,000-resample audit reproduced the uncertainty direction and recomputed scores without the repository scoring function.

| Phase | Δ log loss (M1−M0) | Δ Brier (M1−M0) |
|---|---:|---:|
| 0–9 | −0.011172 | −0.005329 |
| 10–19 | −0.018166 | −0.006893 |
| 20–29 | −0.005769 | −0.001328 |
| 30+ | **+0.009328 (M1 worse)** | **+0.001065 (M1 worse)** |

These four phase slices are exploratory, unadjusted for multiple comparisons and conditioned on match survival. The 30+ deterioration is consistent in direction with the original TEST late-game Brier concern; it cannot establish a mechanism or independent live-latency validity.

## Generalization and uncertainty limitations

- **107 series/singleton clusters** and 43 distinct known team IDs, but only **7 leagues**. The two largest leagues account for **129/180 games (71.7%)**. Every game was recorded on **patch 60**, so this new cohort cannot establish across-patch robustness. These league/team dependencies are not removed by a series-level bootstrap; with only seven leagues, a league-cluster CI would be too fragile to treat as confirmatory.
- The most influential individual game accounts for **24.9% of the observed aggregate log-loss difference**. Leaving out each league preserves the sign of the descriptive aggregate difference, but those leave-one-out calculations are post-hoc diagnostics, not model selection or multiple independent replications.
- Label outcomes and minute snapshots are from **historical parsed OpenDota payloads**. True in-game `received_at`, delivery lag and completeness watermarks remain unknown. The historical March TEST was inspected before its terminal-row repair; this October test does not retroactively make that March TEST blind.
- A smaller log-loss difference with a CI crossing zero does not prove equivalence, nor does a favorable unadjusted Brier CI alone establish stable deployment skill. No model promotion is authorized. Source raw page outcomes could exist in the API response, but **selection code used only metadata**; do not label this human-blinded.

**Source files:** `docs/OCTOBER_2026_EXTERNAL_HOLDOUT_PROTOCOL.md`, `docs/OCTOBER_2026_EXTERNAL_LISTING.json`, `docs/OCTOBER_2026_COLLECTION_RECEIPT.json`, `docs/OCTOBER_2026_EXTERNAL_SCORE_RECEIPT.json`, `artifacts/OCTOBER_2026_EXTERNAL_PREDICTIONS.csv`, `artifacts/OCTOBER_2026_EXTERNAL_METADATA.csv`, `research/october2026_accepted_raw/` and the original frozen scoring helper. `score_receipt.json` contains exact numbers, all four phases, original model fingerprints and fixed bootstrap settings.
