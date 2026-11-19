# M0 vs M1 across research cohorts

The employer notebook was fit and selected using only the original March
500-match cohort. Subsequent checks were heterogeneous retrospective studies;
some reused observed outcomes, some reused matches and several exercised an
older Roshan extractor. Their point estimates should not be pooled or treated
as independent replications.

| Evaluation sample | Games | M0 LL | M1 LL | M1 - M0 | What the comparison can support |
| --- | ---: | ---: | ---: | ---: | --- |
| March VAL | 103 | 0.5325 | 0.5197 | -0.0128 | Chose M1 on development labels |
| March corrected TEST | 106 | 0.516444 | 0.504015 | -0.012430 | 95% match CI [-0.0304,+0.0014]; TEST inspected before terminal correction |
| March TRAIN-forward (four folds) | 137 | 0.612312 | 0.612086 | -0.000226 | Weak mixed-patch training-prefix comparison; no cross-period generalization |
| 30 March–2 April stage cohort | 200 | 0.545075 | 0.533704 | -0.011371 | Separate historical nonblind gate; *blend* failed vs M1, not a confirmatory M1 test |
| September frozen external | 199/200 | 0.584431 | 0.544803 | **-0.039628** | Preregistered single-shot sample, 95% *series* CI [-0.074261,-0.010790], limited gate PASS; only 3 leagues |
| October transfer | 180 | 0.499484 | 0.493602 | -0.005882 | Outcomes reused during later candidate search |
| November early cohort | 120 | — | — | -0.01886 | 95% CI [-0.04872,+0.00379], **68 shared games** with later 100 |
| November later cohort | 100 | 0.5411 | 0.5331 | -0.0080 | 95% grouped CI [-0.0284,+0.0087]; not independent of 120 |
| November feature-transfer slice | 22 | 0.456167 | 0.442682 | -0.013485 | Small nine-group reused-outcome study |
| November fresh-date slice | 17 | 0.429328 | 0.423054 | -0.006274 | Small ten-group retrospective check, not live data |

LL is minute-weighted log loss. The 120-game row records only the published
paired difference because an aggregate M0/M1 pair was not available in that
readout; no numbers have been manufactured to fill it.

**Decision:** Across these records, M1 has a lower point-estimated log loss
than M0, with varying uncertainty, selection rules and evidence quality.
The September study is the strongest separate support and must not be hidden.
It still cannot validate production performance across leagues, especially
with repeated teams, three connected team components, influential long games
and missing live event receipt times. Keep M0 as a **required benchmark**,
retain M1 as the selected *research challenger*, and prioritize M1 for
shadow evaluation on diverse new leagues with source `received_at` logging.
Do not claim universal M1 superiority or pretend the prior 500-game TEST
became blind again.

**Evidence sources in the private research repository (not individually
bundled in the concise ZIP):** `REPORT.md`,
`docs/EXPERIMENT_REGISTER.md`,
`research/september_external/README.md` with its checksum-verified
forecast CSV, `research/OCT_NOV_FEATURE_TRANSFER_READOUT.md`,
`docs/FORWARD_100_STRESS.md` and
`research/FRESH_NOV17_EXTERNAL_READOUT.md`. The 200-game stage
protocol and raw cache live on an archival research branch, not in this
main tree.
