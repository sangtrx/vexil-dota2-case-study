# Independent review and delivery gates

Status: development protocol and synthetic smoke tests complete; no 500-match result exists yet. This document is a **research checklist**, not empirical evidence or a score claim.

## Priority 0 — block submission

1. **Deterministic dataset:** verify 500 eligible parsed professional matches, span at least two patches (at least 20 matches on each of two patches), freeze all 500 IDs in notebook source, and rerun once from a clean cache. Retain exclusions and source-drift caveats. A moving recent-match feed cannot support exact reproducibility. *Methodology: Bible v1.4.1 §§3.1–3.6, 14.1–14.2.*
2. **Information-time semantics:** run prefix truncation and poisoned-future checks on real matches; confirm event types and side conventions from raw objective examples; never use final totals, result or duration as a feature. OpenDota retrospective event times meet the brief's stated information convention but do not establish true historical network receive times. *Methodology: §§3.1–3.3, 13.2, 14.3.*
3. **Series-aware chronology:** ensure no match or series crosses partitions and only train fits transforms. The late holdout stays inaccessible to model selection. *Methodology: §§4.3, 5.1–5.6.*
4. **Live notebook execution:** prove one-account Kaggle CPU/private Internet reachability and then run the exact notebook with output saved. Fresh Colab and laptop Run All must also work, using only allowed API endpoints and no existing cache, keys or local data files. *Methodology: §§14.1–14.2, 14.8.*

## Priority 1 — scientific credibility and creativity

5. Gold-only logistic baseline vs three predeclared explanations of **time-value, lead fragility and objective conversion**, all fitted and chosen using training/validation only. If objectives are incomplete or side semantics uncertain, exclude M3 from candidacy and document why; do not silently derive final towers from end-game fields. *Methodology: §§1.2–1.4, 2.4, 7.7, 13.1.*
6. Report held-out log loss/Brier by phase and overall with paired 95% **whole-match** bootstrap confidence intervals and calibration plots with bin counts. Also calculate equal-match-weighted sensitivity; the primary minute-row score and CI answer different questions. *Methodology: §§4.3, 6.5, 7.2–7.5.*
7. Provide an insight about the **conditional value of an economic lead** and a predeclared descriptive comeback case, without claiming causal effects from observational data. Admit if additional features do not beat gold alone. *Methodology: §§1.4, 7.1, 12.1, 13.1.*
8. Submit a separate report of **≤4 pages**, documenting sample construction, ablations (including failures), uncertainty, which model to ship and not ship, data limitations, actual work time, and accurate disclosure of tools/public code. Never invent metrics. *Methodology: §§1.1–1.4, 14.1.*

## Priority 2 — do only if evidence demands it

- A shallow nonlinear model only if the predeclared simple family fails on validation and an explicit new candidate budget is recorded. No deep neural net, hero embedding, elaborate CV, CPCV, Sharpe/DSR, transaction-cost or Kelly framework for a 500-match **prediction-only** exercise. *Methodology: §§1.3, 7.7, 12.1.*
- No external model code unless its use can be cited and its incremental value tested independently.

## Audit results to date

- OpenDota smoke: two permitted endpoints return data. The latest pro match was unparsed; a neighboring parsed match contained gold/XP arrays and heterogeneous objective events. This demonstrates why eligibility filtering and event schema tests are mandatory.
- An offline synthetic end-to-end execution covered feature extraction, 3-way series-safe split, four predeclared models, log loss/Brier, paired cluster bootstrap and both reliability plots. **Synthetic metrics are not empirical results** and are excluded from the report.
- 14 offline contract tests pass, including pre-horn and exact-minute event boundaries, counterfactual future-data poisoning, label changes, allowed endpoints, split disjointness, baseline feature count, paired bootstrap and requirements parity.
- Remaining blockers: frozen real 500-match manifest, Kaggle in-kernel network smoke, real held-out scores, saved real outputs, fresh Colab/laptop acceptance and final report.

## References

- Assignment: *Vexil Capital - Take-Home Modelling Project*, pages 1–4.
- Private internal methodology: *Quant Research Bible* **v1.4.1**, sections cited above; *Theory Reading Paths*, `Before starting any deep dive`. No private source text, code or credentials are included here.
- Public implementation: OpenDota API documentation and scikit-learn probability calibration guide (linked from the research plan).
