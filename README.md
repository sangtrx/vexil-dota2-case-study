# Live Dota 2 Win Probability — Vexil Capital Take-Home

Predict the probability that **Radiant wins at each match minute**, using only data available at that minute, from **500 parsed professional OpenDota matches** spanning a patch change.

**Status:** research and repository setup (not submission-ready yet). The final deliverable will be a single fully executed notebook and a report of at most four pages.

## Submission contract

- `live_dota2_win_probability.ipynb`: one self-contained Python notebook, all outputs saved, runnable top-to-bottom on a fresh Google Colab runtime and locally.
- `requirements.txt`: pinned packages; no API key or pre-downloaded data.
- `REPORT.md` or `REPORT.pdf`: at most four pages, explaining decisions, ablations, evaluation, uncertainty, limitations, and AI/public-code use.
- OpenDota endpoints **only**: `/api/proMatches` and `/api/matches/{match_id}`.
- A point-in-time feature invariant check, grouped temporal validation, gold-only logistic-regression baseline, one proposed model, and match-cluster bootstrap confidence intervals.
- Log loss, Brier score, and calibration plots on untouched held-out matches, overall and for 0–9, 10–19, 20–29, and 30+ minutes.
- Final notebook prints a table of the exact 500 `match_id`, `start_time`, and `patch`, plus held-out predictions.

## Local execution (once notebook implementation is complete)

Python 3.11+ recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Use **Run All**. The notebook downloads its own match payloads from OpenDota, rate-limits requests (~50/minute), and caches fetched payloads during execution. No credentials or local data files are required. A fresh run is expected to take materially longer than subsequent cells because of API pacing.

## Kaggle execution

Kaggle is the primary experiment runtime, but **GitHub is authoritative for source and review history**. A private Kaggle kernel will be configured with **internet enabled** and CPU execution; the OpenDota API reachability must pass a smoke test before any full pull. Syncing is done with `kaggle kernels push` / `pull`; only vetted notebook checkpoints are committed to GitHub. No GPU is required.

## Research design

See [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md), [docs/DECISIONS.md](docs/DECISIONS.md), and [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md).

**Submission deadline:** Thursday, 19 November 2026. Questions or extension requests: Long at long@vexil.capital.

*The supplied assignment brief is the source of truth; optional experiments must not compromise its rules.*
