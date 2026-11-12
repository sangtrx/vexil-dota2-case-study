# Independent PhD / quant red-team and response (13 Nov 2026)

Read-only Sonnet reviewer inspected the registered proposal, public
prior-art table and pure feature code after development ablation.
The review did not change model specifications or execute a fourth
confirmatory cohort.

**Verdict:** Conditional GO as an exploratory, scientifically
falsifiable research appendix; NO-GO for model M4; M1 remains
the take-home candidate. The existing 103-game validation set
was previously inspected, so interval estimates are descriptive,
not new confirmatory significance.

| Raised concern | Evidence / disposition |
|---|---|
| Array clocks were checked, event clocks were not | Fixed via new event_clock_audit.py on all 900 cache-only games: 1,200 Aegis claims always followed a Roshan event within 13s; 876 firstblood timestamp summaries within 1s; no missing/nonfinite or out-of-window event times. Because parser fields share an origin, no live network timing guarantee is asserted |
| Sparse mostly-zero event features may disguise missing values | All 9,000 player logs contained explicit (possibly empty) list fields; option features were 100% observed in 291 train and 103 validation games, so this experiment performed no actual imputation. Future missingness MUST be modeled or fail closed; deployment is HOLD |
| n=103/53 validation groups and power not enough | Disclosed 53 series clusters and CI spanning 0; practical screen needs at least 0.005 improvement and bootstrap upper<0. A smaller effect is not ruled out. No new test run or threshold adjustment |
| Fixed 300s proxies are arbitrary rather than exact gameplay state | Clearly distinguished Aegis *recent pickup*, which may be consumed, from possession; buyback 300s is ANALYTICAL decay, not a cooldown; structure multiplier 2 is a declared, uncalibrated heuristic |
| Conditional martingale property comes from existing theory | Credited Wilkinson & Ferro (2026) and restricted cohort diagnostic to descriptive; gold/time-only regressors need not be calibrated to full-history filtration |
| Claim of novel theorem / win conditions is unwarranted | Added CHI PLAY (2024) and direct LSTM/feature definitions from open source. Report now says independently formulated local research question; global algorithm novelty is NOT established |
| Two-match case is anecdotal and selection can be adaptive | The matching source and fixed deterministic tolerance rule were committed before viewing the selected outcomes. The minute-25 narrative was explored after phase-support review. Both games won for Radiant, so illustration ONLY, no intervention or performance claim. Figure and labels are reproducible |
| Team-swap features do not force p(swap)=1−p | The **features** are sign-equivariant by construction and tests, not the fully fitted logistic probability model. Radiant-side map asymmetry/intercepts mean output invariance is not assumed; no such claim in reports |

The event-state M4 failed its development screening gate (delta
log loss +0.001251, M4 worse), so the research stopped. The
original 500-match notebook and Draft PR #3 were NOT changed.
This appendix does not authorize a new search over feature ages,
phase cutoffs, LSTM architectures or old held-out labels.
