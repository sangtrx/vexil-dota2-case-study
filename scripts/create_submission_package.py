#!/usr/bin/env python3
"""Build and verify a deterministic reviewer-facing Vexil submission archive."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import numpy as np
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "delivery" / "Vexil_Dota2_Takehome_20261115.zip"
MODEL_CODE_SHA256 = "e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b"
EXPECTED_NOTEBOOK_SHA256 = "63ec9510940dfa88532fccf488196b73660327bef87ed7a115ab8da44cc8d0dd"
EXPECTED_FORECAST_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
FILES = (
    "README.md",
    "SUBMISSION_PACKAGE_README.md",
    "HISTORY.md",
    "live_dota2_win_probability.ipynb",
    "requirements.txt",
    "REPORT.md",
    "REPORT.pdf",
    "artifacts/heldout_predictions.csv",
    "docs/figures/heldout_reliability.png",
    "docs/figures/time_value_scenarios.png",
    "docs/figures/heldout_game_trajectory.png",
    "docs/EXPERIMENT_REGISTER.md",
    "docs/STRICT_SERIES_ECE_RECEIPT.json",
    "docs/ERROR_ANALYSIS.md",
    "docs/ERROR_AUDIT_RECEIPT.json",
    "docs/COLAB_COLD_RUN_RECEIPT.json",
    "docs/SERIES_GROUPS_TEST.json",
    "docs/SERIES_CI_RECEIPT.json",
    "research/series_cluster_sensitivity.py",
    "docs/figures/phase_error_audit.png",
    "research/error_diagnostics.py",
    "research/render_error_figure.py",
    "scripts/render_report.py",
    "scripts/render_report_weasyprint.py",
    "scripts/report.css",
    "tests/test_notebook_contracts.py",
    "tests/test_report_contract.py",
    "tests/test_submission_forecasts.py",
    "tests/test_error_diagnostics.py",
)
STAMP = (2026, 11, 15, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify() -> dict:
    raw = (ROOT / "live_dota2_win_probability.ipynb").read_bytes()
    if sha(raw) != EXPECTED_NOTEBOOK_SHA256:
        raise ValueError("Frozen, output-saved reviewer notebook has changed.")
    notebook = json.loads(raw)
    cells = notebook["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    if len(cells) != 26 or len(code) != 14:
        raise ValueError("Expected exactly 26 notebook cells, 14 executable.")
    if any(c.get("execution_count") is None for c in code):
        raise ValueError("The notebook must have all 14 execution outputs saved.")
    if any(x.get("output_type") == "error" for c in code for x in c.get("outputs", [])):
        raise ValueError("Notebook contains an execution error.")
    if sum("image/png" in x.get("data", {}) for c in code for x in c.get("outputs", [])) != 4:
        raise ValueError("Expected four real, embedded notebook figures.")
    model_code = "".join("".join(c["source"]) for i, c in enumerate(cells)
                         if c["cell_type"] == "code" and i != 2)
    if sha(model_code.encode()) != MODEL_CODE_SHA256:
        raise ValueError("Scientific code does not match the pinned and locally tested corrected source.")
    setup = "".join(cells[2]["source"])
    setup_out = "".join(
        "".join(x.get("text", "")) if isinstance(x.get("text"), list)
        else str(x.get("text", ""))
        for x in cells[2].get("outputs", [])
        if x.get("output_type") == "stream"
    )
    if "10 hours active" not in setup or "Approximately 10 hours active" not in setup_out:
        raise ValueError("Missing candidate-estimated hours in Setup and saved output.")

    pins = (ROOT / "requirements.txt").read_text().splitlines()
    pins = [line.strip() for line in pins if line.strip() and not line.startswith("#")]
    if not pins or any("==" not in line for line in pins):
        raise ValueError("Unpinned dependency in requirements.txt.")
    page_info = subprocess.check_output(["pdfinfo", str(ROOT / "REPORT.pdf")], text=True)
    pages = int(next(x.split(":", 1)[1] for x in page_info.splitlines()
                     if x.startswith("Pages:")))
    if pages > 4:
        raise ValueError("Report exceeds the four-page assignment limit.")
    # A PDF with no embedded figures or local-only file:// links is not shippable.
    info_urls = subprocess.check_output(["pdfinfo", "-url", str(ROOT / "REPORT.pdf")], text=True)
    if "file:///" in info_urls:
        raise ValueError("PDF contains machine-local file hyperlinks.")
    if "https://github.com/" not in info_urls:
        raise ValueError("PDF source/experiment hyperlinks are missing.")
    images = subprocess.check_output(["pdfimages", "-list", str(ROOT / "REPORT.pdf")], text=True)
    image_lines = [line for line in images.splitlines() if line.lstrip()[:1].isdigit()]
    if len(image_lines) < 4:
        raise ValueError("Report PDF has missing rendered figures.")
    report = (ROOT / "REPORT.md").read_text()
    if not all(x in report for x in ("**Time spent:**", "**Assistance disclosure:**", "**Result:**")):
        raise ValueError("Missing hours, assistance or results in report.")

    cloud_receipt=json.loads((ROOT / "docs/COLAB_COLD_RUN_RECEIPT.json").read_text())
    if (cloud_receipt["scientific_code_sha256"]!=MODEL_CODE_SHA256
            or cloud_receipt["repo_main_notebook_sha256"]!=EXPECTED_NOTEBOOK_SHA256
            or cloud_receipt["code_cells_executed"]!=14
            or cloud_receipt["test_minute_rows"]!=3836
            or cloud_receipt["cloud_csv_byte_equality_verified"]):
        raise ValueError("Colab execution receipt conflicts with pinned scientific delivery.")

    forecasts = (ROOT / "artifacts/heldout_predictions.csv").read_bytes()
    series_receipt=json.loads((ROOT / "docs/SERIES_CI_RECEIPT.json").read_text())
    series_meta=(ROOT / "docs/SERIES_GROUPS_TEST.json").read_bytes()
    if (series_receipt["source_csv_sha256"]!=EXPECTED_FORECAST_SHA256
            or series_receipt["series_group_metadata_sha256"]!=sha(series_meta)
            or series_receipt["series_clusters"]!=54
            or series_receipt["matches"]!=106
            or series_receipt["minute_rows"]!=3836):
        raise ValueError("Series-cluster sensitivity receipt is stale or ungrounded.")

    if sha(forecasts) != EXPECTED_FORECAST_SHA256:
        raise ValueError("Frozen held-out predictions have changed.")
    # Never package a stale post-hoc audit under a new frozen forecast receipt.
    audit = json.loads((ROOT / "docs/ERROR_AUDIT_RECEIPT.json").read_text())
    if audit.get("source_forecasts_sha256") != EXPECTED_FORECAST_SHA256:
        raise ValueError("Error-audit receipt does not match frozen source CSV.")
    if audit.get("overall", {}).get("minute_rows") != 3836 or audit.get("overall", {}).get("matches") != 106:
        raise ValueError("Error-audit receipt dimensions have changed.")
    rows = list(csv.DictReader(io.StringIO(forecasts.decode("utf8"))))
    if len(rows) != 3836 or len({r["match_id"] for r in rows}) != 106:
        raise ValueError("Expected exactly 106 games and 3,836 forecasts.")
    if not rows or list(rows[0]) != ["match_id", "minute", "p_model", "p_baseline", "radiant_win"]:
        raise ValueError("Missing required held-out probability columns.")
    for row in rows:
        if row["radiant_win"] not in ("0", "1"):
            raise ValueError("Invalid held-out target.")
        for key in ("p_model", "p_baseline"):
            p = float(row[key])
            if not math.isfinite(p) or p <= 0 or p >= 1:
                raise ValueError("Invalid probability in held-out CSV.")

    # Reproduce the original paired whole-match bootstrap on the immutable
    # corrected forecasts, not a new test or a new model-selection procedure.
    # Match clusters are the resampling unit and minute opportunities are the
    # scoring denominator; same-series correlation remains a limitation.
    ids=sorted({int(r["match_id"]) for r in rows})
    grouped={mid:[] for mid in ids}
    for row in rows:
        grouped[int(row["match_id"])].append(row)
    def match_ci(metric: str) -> tuple[float,float]:
        values=[]
        for mid in ids:
            subset=grouped[mid]
            def loss(row,model):
                y=int(row["radiant_win"])
                p=float(row[model])
                return (p-y)**2 if metric=="brier" else -(y*math.log(p)+(1-y)*math.log1p(-p))
            values.append([len(subset),
                           sum(loss(x,"p_model") for x in subset),
                           sum(loss(x,"p_baseline") for x in subset)])
        a=np.asarray(values,dtype=float)
        rng=np.random.default_rng(20261113)
        idx=rng.integers(0,len(a),size=(2000,len(a)))
        vals=a[idx].sum(axis=1)
        delta=(vals[:,1]-vals[:,2])/vals[:,0]
        return tuple(map(float,np.quantile(delta,[.025,.975])))
    ci_ll=match_ci("logloss")
    ci_brier=match_ci("brier")
    for got,expected in [
        (ci_ll,(-.03037142153342258,.0014126953857700388)),
        (ci_brier,(-.006938042296466374,.00019175815572719667)),
    ]:
        if any(abs(a-b)>1e-10 for a,b in zip(got,expected)):
            raise ValueError("Paired whole-match bootstrap CI contract drifted.")
    readme=(ROOT/"README.md").read_text()
    report=(ROOT/"REPORT.md").read_text()
    if "[-0.0304, +0.0014]" not in readme or "[−0.0304,+0.0014]" not in report:
        raise ValueError("README and report CI display does not match corrected forecasts.")
    if "28-way adjusted" not in report or "[−0.0169,+0.0064]" not in report:
        raise ValueError("Historical exploratory P20 interval/provenance absent.")
    if "AI reviews are not independent human peer review" not in report:
        raise ValueError("Mandatory accurate AI-review disclosure missing.")
    if "https://github.com/sangtrx/vexil-dota2-assessment" in report:
        raise ValueError("Reviewer PDF links to retired snapshot repository.")
    if "https://github.com/sangtrx/dota2-live-win-probability/blob/main/" not in report:
        raise ValueError("Reviewer PDF must link to canonical original repository main branch.")

    def measures(key: str) -> tuple[float, float]:
        ll = brier = 0.0
        for row in rows:
            y = int(row["radiant_win"])
            p = float(row[key])
            ll -= y * math.log(p) + (1 - y) * math.log1p(-p)
            brier += (p-y)**2
        return ll / len(rows), brier / len(rows)

    m0 = measures("p_baseline")
    m1 = measures("p_model")
    reference = ((0.5164444241748873, 0.1719121780368728),
                 (0.504014697253528, 0.1683528340689237))
    if any(abs(a - b) > 1e-12
           for computed, expected in zip((m0, m1), reference)
           for a, b in zip(computed, expected)):
        raise ValueError("Recomputed held-out metrics differ from report.")
    return {"pages": pages, "forecast_rows": len(rows), "heldout_games": 106,
            "paired_match_ci_logloss": ci_ll, "paired_match_ci_brier": ci_brier,
            "M0": m0, "M1": m1}


def run() -> dict:
    acceptance = verify()
    entries = {name: (ROOT / name).read_bytes() for name in FILES}
    manifest = {
        "project": "Vexil Capital Senior Data Scientist Dota 2 take-home",
        "created_on": "2026-11-15",
        "report_pages": acceptance["pages"],
        "notebook_sha256": EXPECTED_NOTEBOOK_SHA256,
        "scientific_code_sha256": MODEL_CODE_SHA256,
        "files": {n: {"bytes": len(v), "sha256": sha(v)}
                  for n, v in sorted(entries.items())},
    }
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    entries["PACKAGE_MANIFEST.json"] = payload
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w") as target:
        for name, data in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=STAMP)
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            target.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)
    with zipfile.ZipFile(DEST) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed.")
        for name, original in entries.items():
            if sha(archive.read(name)) != sha(original):
                raise ValueError("ZIP file changed: " + name)
    return {"path": str(DEST), "zip_sha256": sha(DEST.read_bytes()),
            "size_bytes": DEST.stat().st_size, "files": len(entries),
            "science_code_sha256_pinned": True, **acceptance}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
