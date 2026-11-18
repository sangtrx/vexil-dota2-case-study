# External September 2026 Dota study, locked before scoring

Date: 18 Nov 2026 ICT. **Research-only: never merge into or modify the required 500-game Vexil submission without explicit scope confirmation from Long.** The canonical original applicant notebook, report and ZIP remain unmodified on their review branch.

## Question and strict evidence boundary

Do the **already-fitted M0 and M1** from the original March 2026 TRAIN cohort transfer to a separate month of pro games? This study is a retrospective, previously unexamined **external evaluation**, not actual live inference, a newly generated prospective feed, a repaired original blind TEST, or a license to retune on these results. March TEST was already inspected; its history must remain disclosed. September source data may be reparsed by OpenDota.

## Candidate selection, precommitted BEFORE reading any outcomes

- Discover pro games using OpenDota's **/proMatches** pages (read-only). Input metadata: match_id, start_time, duration, leagueid, series_id; do **not use/store outcomes or score predictors** during selection.
- Select the **200 most recent distinct IDs** with UTC start_time in **2026-09-01T00:00:00Z <= start < 2026-10-01T00:00:00Z**, and proMatches duration at least 600 seconds. Ordering: descending (start_time, match_id). This window avoids original March (500 matches), October and November historical exploratory cohorts; full prior-version history is not proof of globally unseen matches.
- Exclude IDs from the frozen original March manifest. If fewer than 200 candidates in September pages, **freeze all and mark coverage shortfall**. Never backfill from a different month based on API parsing, labels or model performance. Require at least two full pages completely earlier than 1 Sep before halting discovery; fail closed if pagination unexpectedly stops/repeats.
- Commit a SHA-256 manifest of selected IDs/metadata and the code **before** requesting match-specific endpoint /matches/{id}. This is the *selection freeze*. The metadata selection may be updated only by a new explicitly versioned study, not after scoring. No alternative September window on a poor result.

## Frozen model and evaluation

- Original March TRAIN: 291 games/10,675 minute rows, frozen train CSV SHA256. Fit only original M0 (gold_k) and M1 (gold_k, minute10, gold_x_time) L2 logistic with original median imputer, StandardScaler and C=1. SEED=20261113, scikit-learn=1.7.2, Python 3.12 environment. Test byte-level model fingerprint and stored original March predictions to ensure identical coefficients. **No recalibration or new fit on September outcomes.**
- After freezing selected IDs, fetch each /matches/{id} raw payload. Never replace failed, unparsed, short or timestamp-invalid games with new IDs. Report all failures/coverage and parse-source digest before outcome metrics. Time-safe features from **exact original notebook** helper functions; only minute t with 60*t<duration.
- Primary: paired **minute-weighted** M1−M0 log loss (negative favors M1). Secondary: paired Brier, ECE10, phase 0-9/10-19/20-29/30+ and equal-game sensitivity; each metric denominator explicit. Paired series-or-singleton bootstrap (5,000 draws, fixed seed=20261118) with group resampling for 95% log-loss difference CI. Do not bootstrap 40 minutes of one game as 40 independent observations.
- An "external support" gate needs >=150/200 successfully parsed games, >=40 independent professional-series/singleton groups, M1 log-loss improvement >=0.005, group-bootstrap 95% upper bound <0, and 30+ Brier degradation no more than +0.002. If one fails, report NO-PROMOTION with all results. Even all passing would support further validation only, **not actual live availability**, because historical event timestamps do not certify received_at.
- Do not use September outcomes to fit, tune, choose model, adjust slices/thresholds, choose a second cohort, or conceal negative results. Publication of this supplemental study waits for recruiter scope clarity.

## Versioned provenance and rollback

Branch: research/vexil-september-external-20261118, based on review/vexil-creative-atlas-20261118 commit ff24cfee89f65f425b380a4fafe760b6a13a4fec. The original 500-game artifact is unaffected. If scope disallows more than 500, omit the research branch entirely; no Git revert of review/main and no Git history deletion. The external study can remain private for applicant learning.

## No-contact and submission gate

Do not send the external research to Long, modify the existing Gmail submission draft, grant GitHub access, merge, or change the 500-game ZIP without separate applicant instruction. Recruiter reply may change **what can be submitted**, not retroactively validate a test already scored.
