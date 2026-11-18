# September 2026 held-out transfer check: M0 versus M1

**Research only, not included in the required Vexil 500-game submission.** November 18, 2026. Source: historical OpenDota professional-match data. Long has not yet confirmed permission to submit additional matches.

## Fixed before observing outcomes

The original March 500-game applicant dataset, notebooks, PDF and reviewer ZIP remain unchanged. Two model fits on the original 291 March TRAIN games and the original code/preprocessing were locked by Git commit **90203d7596ef4279bf4f7c16c1f20e50045d02e7**. The replay matched original 3,781 VALIDATION forecasts to within 3.4e-16 absolute difference. No March TEST or September outcomes contributed to fitting.

Exactly **200 September pro match IDs** were frozen by outcome-blind metadata selection on commit **5b9c96e3042943af56ca8eb2b2fb6e9cabf947b1**, SHA-256 of ordered selection **e1b9728d89ce59ac0711a57cc5f865d2fb422e0038c5295431c12e54dc549ab7**. They are the 200 latest completed professional matches of duration at least 600s in the predeclared September 2026 window, actually 19-30 September. No match labels or scores were used for selection. Scoring code was committed next, **fb5aadc09a5c6659155e82e358189b8b3dacd8d3**, before fetching match-specific outcomes.

## Primary results (no reselection, no refitting)

**200 of 200** selected IDs were attempted; **199 accepted** and 1 excluded. OpenDota match ID 9019333057 had misaligned player-minute clocks under the original strict feature parser. No replacement was chosen. This gives **8,740 minute forecasts** and **104 series-or-singleton groups** from **3 leagues only**.

| Metric (lower is better) | M0 gold baseline | M1 time-aware | Difference M1 - M0 |
| --- | ---: | ---: | ---: |
| Minute-weighted log loss | 0.584431 | **0.544803** | **-0.039628** |
| Brier | 0.192739 | **0.186450** | -0.006289 |
| ECE10, descriptive | 0.055346 | **0.038724** | -0.016621 |
| Brier at minute 30+ | 0.177526 | **0.162432** | -0.015094 |

The precommitted **5,000-draw series/singleton paired bootstrap** returns a 95% CI for M1-minus-M0 minute log loss of **[-0.074261, -0.010790]**. Under this particular clustering approximation, the interval excludes zero.

The internal predeclared external-support gate requires at least 150 usable games, at least 40 series groups, an improvement of at least 0.005 minute log loss, an upper CI below zero, and 30+ Brier non-regression within 0.002. Its status is **PASS**. This is a research rule, NOT Vexil grading, and does not automatically authorize production promotion or adding extra data to the employer deliverable.

## Post-hoc diagnostics, not a changed success criterion

- 123 of 199 games contributed a lower total minute log loss for M1; 76 favored M0.
- A single long/favorable game generated **24.6%** of total pooled improvement. Important influence remains.
- League-specific M1-minus-M0 log-loss deltas were **-0.090736** (30 games), **-0.057875** (63) and **-0.013813** (106).
- After deleting each league in turn, the pooled delta remained negative: **-0.030987**, **-0.030502**, **-0.067817**. These are descriptive diagnostics after opening the labels, not three independent tests.
- Equal-match weighted average log-loss delta: **-0.029196**, a different estimand than the primary minute-weighted score.
- Brier deltas by phase: 0-9 **-0.00273**; 10-19 **-0.00214**; 20-29 **-0.00108**; minute 30+ **-0.01509**.

## Scientific interpretation and limits

These retrospectively retrieved September match IDs were frozen before this study used their outcomes, and the March-trained coefficients were not changed. The September comparison supplies meaningful **out-of-time evidence** favoring M1 over M0 for this three-league sample. It does **not** restore the previously viewed March TEST to blindness, prove a globally representative cross-league result, or demonstrate live timestamp availability. Different series may share teams and league shocks, so a 104-group series bootstrap still understates some kinds of dependence. Historical OpenDota observations do not record the true data receipt time, and the one excluded clock-invalid match is disclosed.

Do not use these scores to retune M1, pick a new September cohort or replace the original 500-game split. No unqualified trading ROI, production, or causal conclusion is supported. Keep M0 as the required reference in the original submitted assignment while asking Long whether this optional extra cohort is permitted.

## Reproduce and undo

The 200 metadata-selected IDs, pre-scoring model fingerprints, pre-scoring code, output probabilities, per-match exclusions and all source-payload SHA-256 receipts are retained in the PRIVATE research branch. Raw match JSON is archived separately on the user-controlled BigLinux disk but is not included in the recruiter ZIP; a new machine would need OpenDota access and may encounter reparsed data.

Recompute all frozen cohort/denominator checks, strict preterminal minute constraints, log loss, Brier, grouped bootstrap, promotion gate and CSV checksum offline with the included script:

    python research/external_september/verify_external_results.py

If Long disallows extra matches, simply leave this branch out of the email and deliver only the canonical 500-game ZIP. No revert or reset of the reviewer branch or main is necessary; preserve scientific history.

## Additional hostile checks, performed AFTER seeing September scores (18 Nov)

These checks are **post-hoc falsifications**, not original selection criteria or a second independent TEST. The original preregistered PASS result and frozen predictions are retained without modification.

### Stronger additive logistic comparator

A two-input gold_k + minute10 L2 logistic model was fit on **the same original 291 March TRAIN games** with the same pipeline/C=1/seed. It was assessed after the September M0-versus-M1 result was already known. The original frozen M0/M1 outputs were reconstructed from the raw source with max absolute parity below 1e-10.

| Frozen-on-March comparison, September 199 games | Minute log loss |
| --- | ---: |
| M0 gold-only | 0.584431 |
| Additive gold + time | 0.586152 |
| Original M1 gold + time + gold-time interaction | **0.544803** |

Post-hoc M1-minus-additive difference **-0.041349**; paired 95% series-group bootstrap **[-0.076263,-0.012239]**. Within this retrospective sample, the M1 interaction performed better than the additive strong null. **Because the null was tested after seeing September scores, this is exploratory and must never be marketed as preregistered independent confirmation.** See posthoc_additive_null_receipt.json and posthoc_additive_null.py.

### Most-favorable matches, teams and league dependence

| Sensitivity check AFTER outcomes | Remaining games | M1 - M0 minute LL | Group bootstrap 95% CI |
| --- | ---: | ---: | --- |
| All original 199 accepted matches | 199 | -0.039628 | [-0.074261,-0.010790] |
| Drop most favorable one match | 198 | -0.030163 | [-0.059320,-0.006071] |
| Drop top 2 most favorable matches | 197 | -0.020651 | [-0.042120,-0.002775] |
| Drop top 5 most favorable matches | 194 | -0.006077 | **[-0.016201,+0.003372]** |
| Drop top 10 most favorable matches | 189 | +0.000798 | **[-0.007227,+0.008932]** |

The single most favorable match contributes **24.6%** of the total M0-M1 log-loss improvement. Removing favorable matches is **intentionally biased**, not a valid revised benchmark; the test reveals influence fragility and cannot reclassify the predeclared PASS.

All **33 distinct teams** were identifiable from raw September match metadata. A team appeared in up to **29 games**. Leaving each team out in turn preserved negative pooled M1-M0 log-loss differences (range **-0.046080 to -0.024472**), but this is a post-hoc influence check and cannot validate independence.

The match-versus-team graph has **only three connected components of sizes 20, 11 and 2**. The three leagues have 16, 11, 16 distinct participating teams; two leagues share **10 team IDs** while the third shares none. Series IDs alone therefore do **not** make 104 bootstrap groups genuinely independent; three league clusters would be **far too few** for a reliable league-cluster confidence interval. Do not interpret the reported series-bootstrap interval as a population-robust confidence bound across independent leagues/teams.

Leave-one-league-out pooled deltas remain negative (**-0.030987**, **-0.030502**, **-0.067817**) with three nonrandom and imbalanced leagues. Those are descriptive and *not* sufficient to remove the dependence concern.

**Post-hoc decision:** The precommitted September sample passes its explicitly limited internal gate, with a meaningful loss improvement for these 199 games. Broader model superiority, robustness to a few influential games, a live-serving claim and league-generalization all remain **UNVERIFIED**. Further tuning or new data mining on these consumed outcomes would harm credibility.

Reproduce: python research/external_september/posthoc_influence.py (requires author-owned raw-cache team IDs) and python research/external_september/posthoc_additive_null.py (requires author-owned raw match payload cache). Source and generated receipts are retained in this *research-only* branch. The original employer ZIP remains unchanged.
