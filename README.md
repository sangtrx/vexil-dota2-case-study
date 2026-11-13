# Live Dota 2 Win Probability — Vexil Capital Take-Home

Predict the probability that **Radiant wins at each match minute**, using only data available at that minute, from **500 parsed professional OpenDota matches** spanning a patch change.

**Status:** Local full 500-match Run All **PASS**; extended notebook fresh private Kaggle CPU/Internet-ON Run All **PASS**. All **26 notebook cells** pulled back from Kaggle match the GitHub source exactly. All **8 numeric CSV outputs** match the local run within 4.44e-16. **30/30 offline tests PASS**. Frozen manifest: patch 59/60 = 250/250, 18,304 minute rows, 291/103/106 split and 3,837 held-out forecasts. M1 remains the selected model; the additional purchase-timing experiment is development-only. **[REPORT.pdf](REPORT.pdf) is two A4 pages**. Submission still needs a genuine hosted Google Colab Run All, the candidate's actual human hours, and reviewer access to the private repo.

## Submission contract

- `live_dota2_win_probability.ipynb`: one self-contained Python notebook, all outputs saved, runnable top-to-bottom on a fresh Google Colab runtime and locally.
- `requirements.txt`: pinned packages; no API key or pre-downloaded data.
- `REPORT.pdf` (**2 A4 pages**) and the matching editable `REPORT.md`: the same report in two formats, explaining decisions, ablations, evaluation, uncertainty, limitations, and AI/public-code use. The notebook also contains one strictly development-only item-purchase hypothesis; it never alters the original M0–M3 model selection or held-out scores. Re-export the PDF after the candidate fills in real human hours.
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

Use **Run All**. The notebook downloads its own match payloads from OpenDota, rate-limits requests (about 37.5/minute), retries transient 429/5xx/transport errors with bounded backoff, and caches fetched payloads during execution. A shared-IP rate limit or temporary OpenDota outage can still prevent a cold hosted run from finishing; such failure is reported, never silently replaced with a different match. No credentials or local data files are required. A cold API run takes substantially longer than a cached local rerun. The complete cached local execution has been verified; the source notebook still fetches the same 500 OpenDota records on a clean runtime.

## Offline checks

Run `python -m unittest discover -s tests -p "test_*.py" -v` in the local environment to verify point-in-time invariance, split boundaries and paired match-bootstrap behavior without network calls. The notebook has additionally passed a separate end-to-end synthetic integration smoke test. These offline tests alone do not establish model quality; held-out results from the complete real-data Run All are in REPORT.md.

## Derived outputs

After Run All, the notebook exports the frozen match manifest, four-model validation ablations, the exploratory item-purchase comparison and three earlier train-only fold results, held-out metrics, terminal-minute sensitivity and full held-out predictions as CSV, a calibration PNG, and a JSON run receipt with package versions, match manifest hash and a combined content hash of the 500 decoded OpenDota match payloads. The latter detects upstream reparsing even if the match IDs remain unchanged. These are outputs only: none is required to execute the notebook. Kaggle writes them to `/kaggle/working`; Colab/local use a temporary runtime directory.

## Kaggle execution

A complete cold hosted execution of this **exact extended notebook** finished successfully on private Kaggle CPU with Internet ON, no attached datasets or notebook inputs, and no OpenDota API key:

- [Final Kaggle Run All](https://www.kaggle.com/code/sangtruong/vexil-final-dota2-takehome-v2-20261113)
- [Immutable numerical QA receipt](docs/HOSTED_KAGGLE_FINAL_RUN_20261113.json)
- Status COMPLETE; original 500 IDs loaded from the OpenDota API itself.
- 500 games, patch 59:250 / patch 60:250; 18,304 minute rows and 3,837 held-out probabilities.
- Eight exported CSV tables (including purchase-event ablation and train-only folds) compared field-by-field to BigLinux; maximum absolute numeric difference 4.44e-16.
- The 26 source cells pulled back through Kaggle's API match this branch's saved notebook source exactly.
- Local stack: Python 3.12.3, NumPy 2.2.6, scikit-learn 1.7.2. Kaggle: Python 3.13.18, NumPy 2.1.3, scikit-learn 1.6.1.
- OpenDota raw payload digest changed between requests, consistent with reparsing of auxiliary fields. **Forecast and evaluation parity is confirmed; byte-identical raw API payloads are not claimed.**

The prior attempt failed on transient OpenDota requests despite later single-request HTTP 200 diagnostics; the completed V2 ran after bounded-retry improvements. The notebook never silently replaces frozen matches or reads predownloaded match data. The Kaggle account was accessed through the installed credential pool; those credentials are **not shipped**.

## Fresh Colab acceptance (required before sending)

This final cross-environment check has **not yet been completed** on a hosted Colab runtime. In Colab, use **File → Open notebook → GitHub**, authorize access to this private repository, select branch research/pit-validation-20261113, and open live_dota2_win_probability.ipynb. Choose a fresh CPU runtime with Internet access; then select **Runtime → Run all**. Colab uses its installed scientific stack when already available (to avoid live-kernel NumPy ABI conflicts), installing only missing libraries at the pinned versions. Local requirements.txt fixes exact versions; the notebook records all actual package versions.

Check the saved output against the frozen receipt: exactly 500 matches, patch 59:250 and patch 60:250, 18,304 minute rows, train/validation/test 291/103/106 matches, proposed model M1_time_value, 3,837 test forecast rows and manifest hash e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea. Log loss/Brier should agree up to numerical tolerance. Full raw JSON digests can change as OpenDota reparses auxiliary fields. Do **not** edit feature cells or substitute a predownloaded dataset to make the check pass; report any actual runtime or API error.

## Research design

See [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md), [docs/DECISIONS.md](docs/DECISIONS.md), [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md), and [docs/REVIEW_NOTES.md](docs/REVIEW_NOTES.md).

**Submission deadline:** Thursday, 19 November 2026. Questions or extension requests: Long at long@vexil.capital.

*The supplied assignment brief is the source of truth; optional experiments must not compromise its rules.*
