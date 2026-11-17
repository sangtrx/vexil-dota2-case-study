# Pre-outcome metadata-only sample-size amendment — 17 November 2026

This amendment is visible and dated, **not a claim that the first locked protocol was followed without modification**.

The original protocol was committed as `40f36f9` **before** any prospective `/proMatches` discovery. Its two-page, no-detail metadata pilot was committed as `fddd70b`: 200 rows but only **16** IDs started during [Nov16 00:00 UTC, Nov17 09:00 UTC). **No `/matches/{id}` was downloaded and no outcome score or M0/M1 probability was computed.** Those raw pages may themselves contain winner fields; selection used only IDs, timestamps and series. This is **metadata-guided feasibility amendment, not an independently blinded experiment**.

## Exactly one amended population, before detail requests

- Extended start-time window: **[2026-11-10T00:00:00Z, 2026-11-17T06:00:00Z)**. The 3-hour delay between the newest allowed start and metadata discovery reduces, but does not eliminate, ongoing-game selection bias.
- Maximum **12** pages of `/proMatches` in descending ID pagination. Use first **up to 300 candidates** after metadata-only exclusion. Do not use match outcome, patch, league, gold or team to select. Download every frozen candidate and report all exclusions.
- Exclude match IDs and positive series IDs from the original 500, previous forward 100, and distinct old 120-game November cohort from private original repository `sangtrx/dota2-live-win-probability` Draft PR #3. Copied metadata-only manifest at `research/november_120_candidate_manifest.csv`, SHA256 `7f0d24c94fc899935b9d05a1c56444ae4a3aba1530ee2857cc7ccb8dbe70a825`. Historical unique match IDs **652** (=500+100+120-68).
- Original strict parse eligibility, frozen feature functions, fitted M0/M1 coefficients, 10,000 paired bootstrap draws with seed 20261117, whole-series primary and whole-match sensitivity, 4 game phases, and **minimum 50 games plus 30 independent series/singletons** remain unchanged.
- Source baseline Draft PR #9 `4eb95765567cd4216001fac46aacc4b3a53afebd`. New games are an **extra out-of-time descriptive/stress cohort**, NOT a pristine blind TEST, live feed timing proof, or permission to promote a model.
- The initial tiny-window pilot listing and raw page hashes remain preserved in Git, and must NOT be scored separately. Do not shift the window again after new detail outcomes are opened.

**Audit:** amendment justified only by metadata count before opening any `/matches/{id}` or model scores. Original outcome availability in raw `/proMatches` pages means this is not human-blinded adjudication. Report negative and inconclusive results.
