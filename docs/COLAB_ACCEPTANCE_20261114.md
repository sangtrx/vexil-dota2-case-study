# Fresh Colab acceptance procedure for Vexil

**Status: fresh Google Colab CPU V4 Run All COMPLETE and independently
VERIFIED on 14 November 2026**, in addition to private Kaggle V4.

The notebook was uploaded and run through an authenticated Google Colab
browser session at
https://colab.research.google.com/drive/19pbbGdEM_NANnbtt9LpKG-2lbP8U-0u1.
This was a **browser execution**, not a Colab CLI invocation; the CLI is
installed on BigLinux but its separate OAuth/ADC authorization is not
complete. Colab's real downloaded .ipynb and /content output ZIP were
recovered and checked locally. The 26 source cells matched the pinned
V4 notebook exactly; 14/14 code cells executed with zero error outputs,
4/4 PNG charts were embedded, 512 fresh HTTP requests with zero cache
hits returned the original 500 games/18,304 minute rows, and the 3,837
held-out forecasts and selected M1 were unchanged. All 8 CSVs matched
the BigLinux reference (max absolute numerical deviation 4.9982e-16).
All four exported PNGs matched local decoded RGB pixels exactly.
Original raw JSON digests changed on reparse but the semantic model
input/outcome/cohort hashes were equal.

**Independent receipt:** research/results/colab_v4_strict_acceptance_20261114.json
and research/results/colab_v4_provider_provenance_20261114.json.
The verifier's original strict base64 decoder rejected the one terminal
newline that Colab inserts after each valid image/png string; this was
repaired narrowly with a dedicated negative tampering test. Full
BigLinux offline suite remains 65/65 PASS. This does **not** mean Vexil
external submission was sent or that real-time feed arrival was proved.

V3 and V4 Kaggle receipts remain in the research/results directory.
The remaining instructions document how to repeat this Colab check
without changing the original model, frozen manifest, or held-out evidence.

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
