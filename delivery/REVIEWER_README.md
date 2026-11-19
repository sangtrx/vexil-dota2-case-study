# Dota 2 Win Probability | Vexil Capital take-home

Truong Quang Sang | Senior Data Scientist | 19 November 2026

Start with **REPORT.pdf** (four pages), then **live_dota2_win_probability.ipynb**.
The notebook contains the original model code, plots, the evaluated 500-match
cohort and two appended verification cells. The CSV files under `artifacts/`
preserve the reported validation and TEST forecasts.

## Reproduce

**Google Colab:** Upload the `.ipynb` to a CPU runtime with Internet access
and select **Runtime > Run all**. It reads the frozen 500 OpenDota match IDs
from public endpoints; no API key is needed. A cold data pull may take time
because of rate limits. Google Colab may use newer scientific packages than
the local pinned environment; compare metrics with appropriate numerical
tolerance rather than requiring binary-identical exported CSVs. A fresh
19 November Colab CPU Run All of the shipped scientific source completed
16/16 cells without errors and matched the headline TEST metrics; see
`docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json`.

**Local Python 3.12:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Run all cells from the top. The saved outputs are included for inspection if
the OpenDota service is temporarily unavailable. Fresh reproduction requires
network access; the original raw match JSON cache is not part of this ZIP.

## What to evaluate

The gold-only logistic baseline M0 is compared with M1 (gold, time and their
interaction), selected using VALIDATION. On 106 games / 3,836 eligible TEST
minutes, M1 has lower point log loss (0.5040 versus 0.5164) and Brier
(0.1684 versus 0.1719). Match-resampled uncertainty includes zero and M1's
30+ minute Brier is worse (0.1074 versus 0.1028). The report recommends
keeping M0 as the reference.

The corrected TEST was assessed after an earlier terminal-row audit; it is
**not a newly blind holdout**. True live packet arrival times are not
available. Supplementary experiments and their negative results are
summarized in **SUPPLEMENTARY_EXPERIMENTS.md**. These do not constitute a
second independent evaluation of the original TEST.

AI/code-tool assistance and about 10 active hours, confirmed by the applicant,
are disclosed in the report.

This ZIP is intentionally concise. The wider research history and raw
verification protocols remain in the private source repository, available
for deeper review when access is arranged.
