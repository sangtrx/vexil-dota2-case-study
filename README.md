# Live Dota 2 Win Probability — Vexil Capital Take-Home

Predict the probability that **Radiant wins at each match minute**, using only data available at that minute, from **500 parsed professional OpenDota matches** spanning a patch change.

**Status:** 14 November source-integrity V4: full 500-match BigLinux Run All **PASS**, **55/55** offline tests **PASS**, and eight scientific CSVs unchanged (maximum numerical delta 4.44e-16). All 3,837 held-out forecasts and the selected M1 remain fixed. Private Kaggle V3 completed a genuine 500-match cold run with 505 HTTP calls, zero cache hits and complete 8-CSV parity; its source precedes V4 identity/manifest guards. A separate private Kaggle V4 cold run has been launched, but must not be called PASS until its outputs are downloaded and checked. Submission HOLD pending final hosted acceptance, actual human work hours, applicant review and reviewer access.

## Submission contract

- `live_dota2_win_probability.ipynb`: one self-contained Python notebook, all outputs saved, runnable top-to-bottom on a fresh Google Colab runtime and locally.
- `requirements.txt`: pinned packages; no API key or pre-downloaded data.
- `REPORT.pdf` (**3 A4 pages, with two real-data figures**) and the matching editable `REPORT.md`: the same report in two formats, explaining decisions, ablations, evaluation, uncertainty, limitations, and AI/public-code use. The notebook also contains one strictly development-only item-purchase hypothesis; it never alters the original M0–M3 model selection or held-out scores. Re-export the PDF after the candidate fills in real human hours.
- OpenDota endpoints **only**: `/api/proMatches` and `/api/matches/{match_id}`.
- A point-in-time feature invariant check, grouped temporal validation, gold-only logistic-regression baseline, one proposed model, and match-cluster bootstrap confidence intervals.
- Log loss, Brier score, and calibration plots on untouched held-out matches, overall and for 0–9, 10–19, 20–29, and 30+ minutes.
- The notebook prints all 500 match identifiers, start times and patch IDs, and previews 16 held-out predictions. All 3,837 held-out probability rows are exported to heldout_predictions.csv. Four charts are embedded directly in the saved notebook output.

## Local execution

Python 3.11+ recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter notebook live_dota2_win_probability.ipynb
```

Use **Run All**. The notebook downloads its own match payloads from OpenDota, rate-limits requests (about 37.5/minute), retries transient 429/5xx/transport errors with bounded backoff, and caches fetched payloads during execution. A shared-IP rate limit or temporary OpenDota outage can still prevent a cold hosted run from finishing; such failure is reported, never silently replaced with a different match. No credentials or local data files are required. A cold API run takes substantially longer than a cached local rerun. The complete cached local execution has been verified; the source notebook still fetches the same 500 OpenDota records on a clean runtime.

## Report and figures

REPORT.md is the editable source of the three-page A4 REPORT.pdf.
The report embeds two real-data figures under docs/figures. To regenerate
locally on BigLinux, install the optional authoring dependency
mistune==3.4.0, ensure Chrome/Chromium is available, then run:

    python scripts/render_report.py

The renderer does not touch source matches, models or held-out predictions.
Keep the assistance/hours disclosure honest and visually verify the PDF.

## Offline checks

The frozen-cohort gate now checks each requested /matches/{id} response
against its actual integer match_id, invalidates switched cached payloads
and rejects incorrect HTTP replies. It also pins the SHA-256 of the 500
match IDs, start times and patch IDs **before fitting** (the hash excludes
win labels). Tests demonstrated the old code accepted an intentionally
swapped same-patch match; V4 rejects it. See docs/REDTEAM_20261114.md.

The optional read-only independent research audit uses the existing cached
OpenDota payloads and saved forecast CSVs, never retrains or calls the API:

    python research/independent_delivery_audit.py --outputs /path/to/vexil_takehome_outputs --cache /path/to/api-cache --receipt /path/to/audit.json

This recomputes log loss and Brier from probabilities, checks label
completion and measures post-hoc match/series-bootstrap sensitivity.
See [docs/REDTEAM_20261114.md](docs/REDTEAM_20261114.md). The one notebook
remains completely self-contained; this audit is not a runtime input.


The notebook now rejects misaligned player minute clocks before making its 18,304 forecasts. The current 500-game cohort passed all 5,000 player clock sequences and all 500 paired team gold/XP axis-length checks. Invalid NaN/infinite/boolean event times, invalid gold values and duplicate player slots have explicit regression tests. These checks do not establish that a live feed received events at the same time as their retrospective match timestamps.

Run `python -m unittest discover -s tests -p "test_*.py" -v` in the local environment to verify point-in-time invariance, split boundaries and paired match-bootstrap behavior without network calls. The notebook has additionally passed a separate end-to-end synthetic integration smoke test. These offline tests alone do not establish model quality; held-out results from the complete real-data Run All are in REPORT.md.

## Derived outputs

Run All exports eight science CSV tables, all 3,837 held-out probability rows, a calibration PNG and a JSON receipt. The receipt separates full raw OpenDota JSON digests from canonical model-input, label, item and cohort fingerprints, and records runtime identity and HTTP/cache-call counts. None of these derived outputs is an input. Kaggle writes to /kaggle/working; Colab writes to /content/vexil_takehome_outputs and creates a ZIP in its Files sidebar; local runs use a temporary directory. Four plots are embedded in the saved notebook, with training-support-masked time-value scenarios. The same four PNGs are individually exported on Kaggle/Colab; the Colab ZIP contains 13 derived files (eight CSVs, one receipt and four PNGs).

## Kaggle execution

A complete cold hosted execution of the **pre-14-November source** finished successfully on private Kaggle CPU with Internet ON, no attached datasets or notebook inputs, and no OpenDota API key:

- [Final Kaggle Run All](https://www.kaggle.com/code/sangtruong/vexil-final-dota2-takehome-v2-20261113)
- [Immutable numerical QA receipt](docs/HOSTED_KAGGLE_FINAL_RUN_20261113.json)
- Status COMPLETE; original 500 IDs loaded from the OpenDota API itself.
- 500 games, patch 59:250 / patch 60:250; 18,304 minute rows and 3,837 held-out probabilities.
- Eight exported CSV tables (including purchase-event ablation and train-only folds) compared field-by-field to BigLinux; maximum absolute numeric difference 4.44e-16.
- The 26 source cells pulled back through Kaggle's API matched the **earlier pre-guard source** exactly, not the current branch. Its numerical parity remains a historical reference.
- Local stack: Python 3.12.3, NumPy 2.2.6, scikit-learn 1.7.2. Kaggle: Python 3.13.18, NumPy 2.1.3, scikit-learn 1.6.1.
- OpenDota raw payload digest changed between requests, consistent with reparsing of auxiliary fields. **Forecast and evaluation parity is confirmed; byte-identical raw API payloads are not claimed.**

The prior attempt failed on transient OpenDota requests despite later single-request HTTP 200 diagnostics; the completed V2 ran after bounded-retry improvements. The notebook never silently replaces frozen matches or reads predownloaded match data. The Kaggle account was accessed through the installed credential pool; those credentials are **not shipped**.

## Fresh-source drift canary and calibration audit

The 14 November read-only **10-match source canary** across both patches
re-fetched only the permitted match endpoint: all ten raw JSON digests
changed, yet every one of the 344 checked minute-level snapshots had
identical model/item features and valid time alignment. These are existing
matches, not new blind test games or a full 500-match cold run. See
research/current_source_canary.py and
research/results/current_source_canary_20261114.json.

The independent audit validates all 500 source labels and professional
series IDs before recomputing scoring. Whole-series bootstrap identifies
M1 mean probability 0.54271 against minute-weighted outcome rate 0.60438
(+0.06167 calibration-in-the-large gap); the 54-series confidence interval
includes zero. Do not recalibrate using the already-inspected held-out set.

## Fresh Colab acceptance (required before sending)

This final cross-environment check has **not yet been completed** on a hosted Colab runtime. In Colab, use **File → Open notebook → GitHub**, authorize access to this private repository, select branch fix/vexil-delivery-audit-20261114, and open live_dota2_win_probability.ipynb. Choose a fresh CPU runtime with Internet access; then select **Runtime → Run all**. Colab uses its installed scientific stack when already available (to avoid live-kernel NumPy ABI conflicts), installing only missing libraries at the pinned versions. Local requirements.txt fixes exact versions; the notebook records all actual package versions.

Colab now creates vexil_takehome_outputs.zip next to the output folder.
After Run All, download that ZIP from the Colab Files sidebar and save
the executed notebook via File > Download > Download .ipynb. The
research/verify_hosted_run.py script checks the 8 CSV tables, all source
cells, semantic fingerprints and self-reported API/cache-call counts.
A cached local replay is rejected when cloud cold-run acceptance is
requested. Self-reported environment flags alone do not authenticate a
Colab run: separately check the actual hosted run URL and history.
See docs/COLAB_ACCEPTANCE_20261114.md.

Check the saved output against the frozen receipt: exactly 500 matches, patch 59:250 and patch 60:250, 18,304 minute rows, train/validation/test 291/103/106 matches, proposed model M1_time_value, 3,837 test forecast rows and manifest hash e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea. Log loss/Brier should agree up to numerical tolerance. Full raw JSON digests can change as OpenDota reparses auxiliary fields. Do **not** edit feature cells or substitute a predownloaded dataset to make the check pass; report any actual runtime or API error.

## Research design

See [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md), [docs/DECISIONS.md](docs/DECISIONS.md), [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md), and [docs/REVIEW_NOTES.md](docs/REVIEW_NOTES.md).

**Submission deadline:** Thursday, 19 November 2026. Questions or extension requests: Long at long@vexil.capital.

*The supplied assignment brief is the source of truth; optional experiments must not compromise its rules.*
