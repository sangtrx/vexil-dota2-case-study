# Fresh Colab acceptance procedure for Vexil

**Status: private Kaggle V4 exact-source cold Run All COMPLETE and
independently VERIFIED; fresh Google Colab specifically remains untested.**
V3 and the newer V4 both completed authenticated Kaggle runs.
V4 verified the final frozen-ID and metadata guard source and
all scientific tables and four PNG exports. See
research/results/kaggle_v4_strict_acceptance_20261114.json.
This Colab procedure documents an additional platform-specific
acceptance check, not a claim that Colab has run already. This procedure never modifies the original
500-match manifest or uses unseen held-out outcomes to choose a model.

## 1. Source and runtime

Use the exact GitHub branch named fix/vexil-delivery-audit-20261114,
file live_dota2_win_probability.ipynb, without editing its source.
The repository is private, so if Colab GitHub import cannot authenticate,
download that notebook from GitHub and use Colab File > Upload notebook.
Start a fresh **CPU** Colab runtime with Internet access. Do not attach a
cached OpenDota dataset, download the 500 JSONs separately, or substitute
another cohort. The notebook itself only requests the permitted
/proMatches and /matches/{match_id} endpoints and enforces fixed match IDs.

Use Runtime > Run all. When successful, verify from actual cell outputs:
- Environment line identifies Colab True and Kaggle False.
- API requests are fresh, with 500 match responses and zero cache hits,
  unless documented, legitimate retries increase the API-call count.
- Exactly 500 parsed games, two 250-game patch cohorts, 18,304 minute
  forecasts, 291/103/106 train/validation/test games, selected M1_time_value,
  and 3,837 held-out forecasts.
- Exactly 14 code cells execute; there must be no error outputs.
- Four PNG figures must be embedded in the saved executed notebook:
  reliability, time-value, illustrative match and comeback-risk.
  All 3,837 held-out probabilities remain in the exported CSV; the
  notebook displays a compact preview only.
- Source fingerprint warnings and changes must be investigated, not ignored.

OpenDota may apply rate limits or temporarily return unparsed matches.
If this happens, keep the failed output and actual error diagnostics.
Do not replace missing matches to force the check to pass.

## 2. Export both forms of evidence

The notebook writes its derived artifacts into the Colab Files sidebar
at /content/vexil_takehome_outputs and creates a ready-to-download ZIP
at /content/vexil_takehome_outputs.zip. The ZIP contains eight exported
CSV data tables, a JSON receipt, and **four exported PNG figures**. It never contains
raw match cache files.

Download the ZIP from the Colab Files sidebar. Also download the
executed notebook using File > Download > Download .ipynb. Saving only
a screenshot is insufficient: the saved notebook carries exact source
cells and execution counts, and the CSVs carry numerical evidence.

## 3. Verify locally after downloading (no network needed)

Unzip the Colab artifact into a dedicated local directory. The extracted
folder should contain vexil_takehome_outputs, with eight CSV files,
four PNG figures and derived_run_receipt.json. Also place the executed Colab
notebook in that directory.

Set LOCAL_OUTPUTS to the reference output folder from the local validated
500-match run, HOSTED_OUTPUTS to the extracted Colab output folder, and
HOSTED_NOTEBOOK to the downloaded executed .ipynb. Activate the project's
pinned Python environment, change to the repository root, then run:

    python research/verify_hosted_run.py
      --local-output-dir "$LOCAL_OUTPUTS"
      --hosted-output-dir "$HOSTED_OUTPUTS"
      --local-notebook live_dota2_win_probability.ipynb
      --hosted-notebook "$HOSTED_NOTEBOOK"
      --expected-runtime colab
      --receipt hosted_acceptance.json

The arguments above are shown on separate lines for readability; use
shell line continuations or join them into a single command when executing.
Verification requires exact saved notebook source cells,
14 completed code cells, a Colab-specific receipt, at least 500 fresh API
calls with zero cache hits, all eight scientific CSVs within 2e-7 numeric
tolerance, exact frozen cohort identity and matching semantic source
hashes and four valid exported PNG files. Full raw JSON hashes may
differ due to reparsing: semantic
inputs, labels and cohort metadata must not drift.

This script checks numeric and notebook evidence only. It cannot
authenticate that the downloaded notebook came from Colab. Capture
and review the actual signed-in Colab notebook URL, run history and
source identity separately before declaring hosted acceptance.

## Kaggle CPU acceptance difference

A Kaggle notebook downloaded using the Kaggle CLI may retain source
cells and execution counts but omit inline output images. That is
not by itself evidence of missing executed charts. For a Kaggle
verification, use --expected-runtime kaggle, pull the matching
notebook source and download all Kaggle output artifacts, including
all four PNG files. The offline verifier checks exact code, output
CSV parity, source semantic fingerprints, 500+ source HTTP calls,
zero cached responses and four actual valid PNGs. The Kaggle provider
must independently confirm a COMPLETE kernel run; the verifier does
not authenticate the provider account or run history.

For Colab downloads, all four PNG outputs must still be present
inline in the saved notebook as well as in exported artifacts.

An optional --require-plot-pixel-parity switch verifies **exact decoded
RGB pixel equality** between local and hosted PNGs, after ignoring
PNG-container metadata differences. It passed on Kaggle V4. Do not use
it as a universal Colab gate if Colab runs a different Matplotlib/font
renderer: exact pixels can change without changing underlying forecast
data. The default verifier records pixel parity but gates on science
CSV/semantic-source consistency and four structurally valid figures.

## 4. Submission checklist

- Keep the primary selected M1 fixed; M0 remains the gold-only baseline.
- Do not promote exploratory item models or recalibrate from test.
- Use the actual final PDF (<=4 pages) matching REPORT.md.
- Replace the hours placeholder with the candidate's **actual human
  active time** only; never derive human hours from kernel elapsed time.
- Keep the assistance/public-code disclosure accurate.
- Confirm Vexil reviewers have GitHub access and the notebook outputs
  are saved on the branch being submitted.
- Do not mark the take-home submitted until the candidate has verified
  that the external handoff was completed.

The primary task deadline is **Thursday 19 November 2026**.
