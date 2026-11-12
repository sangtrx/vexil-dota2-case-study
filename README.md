# Live Dota 2 Win Probability — Vexil Capital Take-Home

Predict the probability that **Radiant wins at each match minute**, using only data available at that minute, from **500 parsed professional OpenDota matches** spanning a patch change.

**Status:** 500-match patch-balanced manifest frozen; 26 offline tests passing; full-data BigLinux **and private one-account Kaggle CPU Run All: PASS**. The numerical outputs agree to floating-point precision (max probability difference 4.44e-16), despite different scientific Python versions. M1 was selected on validation. **Not submission-ready:** fresh hosted Google Colab acceptance and the candidate's actual time-spent entry are still pending. The current REPORT.md rendered to 3 A4 pages in a separate visual layout check (4-page maximum). See [REPORT.md](REPORT.md).

## Submission contract

- `live_dota2_win_probability.ipynb`: one self-contained Python notebook, all outputs saved, runnable top-to-bottom on a fresh Google Colab runtime and locally.
- `requirements.txt`: pinned packages; no API key or pre-downloaded data.
- `REPORT.md` or `REPORT.pdf`: at most four pages, explaining decisions, ablations, evaluation, uncertainty, limitations, and AI/public-code use.
- OpenDota endpoints **only**: `/api/proMatches` and `/api/matches/{match_id}`.
- A point-in-time feature invariant check, grouped temporal validation, gold-only logistic-regression baseline, one proposed model, and match-cluster bootstrap confidence intervals.
- Log loss, Brier score, and calibration plots on untouched held-out matches, overall and for 0–9, 10–19, 20–29, and 30+ minutes.
- Final notebook prints a table of the exact 500 `match_id`, `start_time`, and `patch`, plus held-out predictions.

## Local execution

Python 3.11+ recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Use **Run All**. The notebook downloads its own match payloads from OpenDota, rate-limits requests (about 37.5/minute), and caches fetched payloads during execution. No credentials or local data files are required. A cold API run takes substantially longer than a cached local rerun. The complete cached local execution has been verified; the source notebook still fetches the same 500 OpenDota records on a clean runtime.

## Offline checks

Run `python -m unittest discover -s tests -p "test_*.py" -v` in the local environment to verify point-in-time invariance, split boundaries and paired match-bootstrap behavior without network calls. The notebook has additionally passed a separate end-to-end synthetic integration smoke test. These offline tests alone do not establish model quality; held-out results from the complete real-data Run All are in REPORT.md.

## Derived outputs

After Run All, the notebook exports the frozen match manifest, validation ablations, held-out metrics, terminal-minute sensitivity and full held-out predictions as CSV, a calibration PNG, and a JSON run receipt with package versions, match manifest hash and a combined content hash of the 500 decoded OpenDota match payloads. The latter detects upstream reparsing even if the match IDs remain unchanged. These are outputs only: none is required to execute the notebook. Kaggle writes them to `/kaggle/working`; Colab/local use a temporary runtime directory.

## Kaggle execution

Kaggle is the primary experiment runtime, but **GitHub is authoritative for source and review history**. A private Kaggle CPU kernel using one authorized account successfully fetched an OpenDota pro-match page over the Internet (HTTP 200, 100 matches). The final notebook contains an immutable list of 500 unique match IDs selected without using game outcomes: 250 games from patch 59 (21–24 March 2026) and 250 from patch 60 (24–26 March 2026). The data preflight verified the selection and recorded its manifest digest. A private Kaggle CPU execution of the frozen notebook completed independently: 500 games, 18,304 match-minute rows, and 3,837 held-out predictions. All model outputs, validation scores, bootstrap CIs, and research sensitivities agreed with BigLinux to machine precision. The full raw API JSON hash differed because OpenDota can revise auxiliary fields (a spot check identified computed_mmr changes), although the forecast results were unchanged. This is a qualified scientific-output parity PASS, not a claim of identical raw API payloads. The private Kaggle notebook is at https://www.kaggle.com/code/sangtruong/vexil-dota2-patch-cohorts-20261113. Syncing is done with `kaggle kernels push` / `pull`; only vetted notebook checkpoints are committed to GitHub. No GPU is required.

## Fresh Colab acceptance (required before sending)

This final cross-environment check has **not yet been completed** on a hosted Colab runtime. In Colab, use **File → Open notebook → GitHub**, authorize access to this private repository, select branch research/pit-validation-20261113, and open live_dota2_win_probability.ipynb. Choose a fresh CPU runtime with Internet access; then select **Runtime → Run all**. Colab installs the pinned analysis packages from the notebook's Setup cell without external local files.

Check the saved output against the frozen receipt: exactly 500 matches, patch 59:250 and patch 60:250, 18,304 minute rows, train/validation/test 291/103/106 matches, proposed model M1_time_value, 3,837 test forecast rows and manifest hash e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea. Log loss/Brier should agree up to numerical tolerance. Full raw JSON digests can change as OpenDota reparses auxiliary fields. Do **not** edit feature cells or substitute a predownloaded dataset to make the check pass; report any actual runtime or API error.

## Research design

See [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md), [docs/DECISIONS.md](docs/DECISIONS.md), [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md), and [docs/REVIEW_NOTES.md](docs/REVIEW_NOTES.md).

**Submission deadline:** Thursday, 19 November 2026. Questions or extension requests: Long at long@vexil.capital.

*The supplied assignment brief is the source of truth; optional experiments must not compromise its rules.*
