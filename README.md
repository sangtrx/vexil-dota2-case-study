# Live Dota 2 Win Probability — Vexil Capital Take-Home

Predict the probability that **Radiant wins at each match minute**, using only data available at that minute, from **500 parsed professional OpenDota matches** spanning a patch change.

**Status:** notebook implementation and 17 offline contract tests completed; one-account private Kaggle Internet smoke passed. **Not submission-ready:** the 500-match manifest, real held-out metrics, executed outputs and four-page report are still pending. Synthetic smoke-test scores are not research results.

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

## Offline checks

Run `python -m unittest discover -s tests -p "test_*.py" -v` in the local environment to verify point-in-time invariance, split boundaries and paired match-bootstrap behavior without network calls. The notebook has additionally passed a separate end-to-end synthetic integration smoke test. Neither establishes model quality on real matches.

## Kaggle execution

Kaggle is the primary experiment runtime, but **GitHub is authoritative for source and review history**. A private Kaggle CPU kernel using one authorized account successfully fetched an OpenDota pro-match page over the Internet (HTTP 200, 100 matches). An initial full-payload crawl was stopped before reaching the patch boundary. The revised implementation identifies the boundary from a few label-blind probes per page and then fetches a balanced 250/250 two-patch cohort. Its real run is not yet verified. Syncing is done with `kaggle kernels push` / `pull`; only vetted notebook checkpoints are committed to GitHub. No GPU is required.

## Research design

See [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md), [docs/DECISIONS.md](docs/DECISIONS.md), [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md), and [docs/REVIEW_NOTES.md](docs/REVIEW_NOTES.md).

**Submission deadline:** Thursday, 19 November 2026. Questions or extension requests: Long at long@vexil.capital.

*The supplied assignment brief is the source of truth; optional experiments must not compromise its rules.*
