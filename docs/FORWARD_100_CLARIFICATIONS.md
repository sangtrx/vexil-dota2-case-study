# Post-collection methodological corrections (NOT a replacement protocol)

This note is appended after seeing the later 100-game outcomes.
The original 9d6cddf PROTOCOL.md is **preserved verbatim**. Do not claim
these clarifications were themselves precommitted.

1. **Not prospective in calendar time.** The 100 games occurred on
   11-15 Nov 2026, *before* the 15 Nov 23:36 ICT protocol commit.
   The frozen object is the match selection and scoring procedure before
   this particular detailed match retrieval, not future match outcomes.
   Correct public description: "post-original-TEST later-match frozen-
   selection robustness check". The same-day Git and file mtimes are
   operator-controlled, not independently notarized.

2. **Bounded selection and available outcome fields.** The raw
   /proMatches pages themselves may include outcomes/duration; the
   page freezer uses only match_id and start_time. The frozen listing
   contains 1,073 in-window IDs; first 100 admissible match details
   occurred in the first 101 requests (1 rejected for missing gold).
   Eligibility uses type/presence of the result and >=600 s, but
   does not use result *value* or model performance. The original
   rejected raw payload hash was **not saved**. There is one observed
   operator run, but no proof of absence of any hypothetical earlier run.

3. **Bootstrap size in the pre-commit protocol.** "Preserving total
   minute opportunities" should read: clustered resampling preserves
   intact within-cluster forecast opportunities, but the *total*
   number of minute rows varies across bootstrap draws. The
   implemented ratio estimator correctly uses
   sum(cluster loss totals) / sum(cluster forecast-row counts).
   No bootstrap scores or method changed after the result.

4. **Dependence beyond series.** Exactly 4 leagues, and 85/100
   games in the top two. League and team correlation can make
   56-series bootstrap intervals understate true uncertainty.
   Four leagues are insufficient for reliable league-bootstrap
   inference. Leave-one-league-out is a post-hoc descriptive influence
   check and NOT a model selection/exclusion rule.

5. **Calibration uncertainty.** 10-bin ECE is descriptive and
   unadjusted. Although overall ECE point estimates are 0.0520 M0
   and 0.0500 M1, minute 0-9 ECE is *worse* for M1 (0.0496 M0 to
   0.0812 M1). Overall or late-phase ECE point directions are NOT
   established population calibration gains. No recalibration was
   fitted on these 100 games.

6. **Patch semantics.** All 100 matches have OpenDota-reported
   patch ID 60. This is not a new patch test, and the ID alone is
   not proof no untracked balance hotfix or source-metadata drift
   occurred in the intervening eight months.

7. **Author-controlled replay, not independent verification.**
   TRAIN parity, original frozen TEST prediction parity and later
   100-game exact offline replay are genuine local repeatability
   evidence, but reuse the same source code/host and are not
   independently audited cloud or human reviews. The collected
   raw OpenDota JSON remains in authorized BigLinux local cache
   and is not bundled or transmitted.

8. **Null scientific decision unchanged.** M1's aggregate log-loss
   point estimate is favorable on the 100 later games, but the
   paired group CI crosses zero. Omission of one 42-game league
   flips the sign. M0 remains reference, M1 remains shadow-only.
   The exact requested 500-match assessment is not changed.

Date of corrective note: 15 November 2026, **after** outcome inspection.


9. **Source path and branch terminology corrected after retrieval.**
   The collector/protocol history remains at research/prospective in
   Git commits 9d6cddf, b49f6df and 8b8e40d. A later editorial
   rename to research/posttest_temporal was made to avoid implying
   the 11-15 Nov matches occurred *after* protocol registration.
   No data, model, score or raw payload was changed by this rename.
