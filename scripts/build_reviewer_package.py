#!/usr/bin/env python3
"""Ship a minimal, source-pinned Vexil take-home without internal research logs.

The full source/provenance archive is separately reproducible through
scripts/create_submission_package.py. Never conflate the two archives.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "delivery" / "Vexil_Dota2_Takehome_20261119.zip"
SOURCE_SHA = "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f"
PRED_SHA = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
FROZEN_SOURCES = {
    "README.md": "delivery/REVIEWER_README.md",
    "SUPPLEMENTARY_EXPERIMENTS.md": "delivery/SUPPLEMENTARY_EXPERIMENTS.md",
    "REPORT.pdf": "REPORT.pdf",
    "live_dota2_win_probability.ipynb": "live_dota2_win_probability.ipynb",
    "requirements.txt": "requirements.txt",
    "artifacts/heldout_predictions.csv": "artifacts/heldout_predictions.csv",
    "artifacts/validation_m0_m1_predictions.csv":
        "artifacts/validation_m0_m1_predictions.csv",
    "docs/ERROR_AUDIT_RECEIPT.json": "docs/ERROR_AUDIT_RECEIPT.json",
    "docs/SERIES_CI_RECEIPT.json": "docs/SERIES_CI_RECEIPT.json",
    "docs/REVIEWER_SCIENTIFIC_LIMITS.md": "docs/REVIEWER_SCIENTIFIC_LIMITS.md",
}
COLAB_RECEIPT = "docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json"
STAMP = (2026, 11, 19, 0, 0, 0)
# These are unmistakably internal process data, not Dota2 domain terminology.
BANNED = {
    "host_path": re.compile(r"/srv/ai/|/home/ai-agent/|/var/lib/sentinelx/"),
    "operator_receipt": re.compile(r"(?i)\b(?:SentinelX|job_[a-z0-9]{9,}|issue #2278)\b"),
    "internal_workflow": re.compile(
        r"(?i)(no main/PR9/Colab/Gmail mutation|no GitHub access grant|"
        r"recruiter email, no|do not send|do not merge|hostile committee|"
        r"Fable XHIGH|private Google Drive notebook)"
    ),
    "private_link": re.compile(
        r"https://(?:colab\.research\.google\.com/drive|"
        r"github\.com/sangtrx/vexil-dota2-win-probability)/"
    ),
    "credential": re.compile(r"(?:sk-proj-|ghp_[A-Za-z0-9]{20,}|"
                             r"-----BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY)"),
}
TEXT_EXTENSIONS = {".md", ".json", ".py", ".txt", ".ipynb"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_sources() -> dict:
    notebook = (ROOT / FROZEN_SOURCES["live_dota2_win_probability.ipynb"]).read_bytes()
    forecasts = (ROOT / FROZEN_SOURCES["artifacts/heldout_predictions.csv"]).read_bytes()
    if sha(notebook) != SOURCE_SHA or sha(forecasts) != PRED_SHA:
        raise ValueError("Original notebook / TEST forecasts changed")
    payload = json.loads(notebook)
    cells = [c for c in payload["cells"] if c["cell_type"] == "code"]
    if len(cells) != 16 or [c.get("execution_count") for c in cells] != list(range(1, 17)):
        raise ValueError("The one notebook must have 16 completed code cells")
    if any(out.get("output_type") == "error" for c in cells for out in c.get("outputs", [])):
        raise ValueError("Saved notebook contains a cell error")
    rows = list(csv.DictReader(io.StringIO(forecasts.decode())))
    if len(rows) != 3836 or len({r["match_id"] for r in rows}) != 106:
        raise ValueError("Saved TEST dimensions changed")
    if len({(r["match_id"], r["minute"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate game/minute forecasts")
    def score(key: str) -> tuple[float, float]:
        loss = brier = 0.
        for row in rows:
            p = float(row[key])
            y = int(row["radiant_win"])
            if not 0.0 < p < 1.0 or y not in (0, 1):
                raise ValueError("Invalid forecast/label")
            loss -= y * math.log(p) + (1 - y) * math.log1p(-p)
            brier += (p-y)**2
        return loss/len(rows), brier/len(rows)
    expected = ((0.5164444241748873, 0.1719121780368728),
                (0.504014697253528, 0.1683528340689237))
    for got, exp in zip((score("p_baseline"), score("p_model")), expected):
        if any(abs(x-y)>1e-12 for x, y in zip(got, exp)):
            raise ValueError("Saved score drift")
    pdf = ROOT / "REPORT.pdf"
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    pages = int(next(s.split(":", 1)[1].strip() for s in info.splitlines()
                     if s.startswith("Pages:")))
    if pages != 4:
        raise ValueError("PDF must be exactly four pages")
    text = " ".join(subprocess.check_output(
        ["pdftotext", str(pdf), "-"], text=True).split())
    for fact in ("10 active hours", "AI reviews are not independent human peer review",
                 "0.5164", "0.5040", "0.1028", "0.1074"):
        if fact not in text:
            raise ValueError("Missing PDF fact: "+fact)
    return {"games": 106, "test_minutes": 3836, "pdf_pages": pages,
            "notebook_code_cells": len(cells),
            "M0_log_loss": expected[0][0], "M1_log_loss": expected[1][0],
            "M0_brier": expected[0][1], "M1_brier": expected[1][1]}


def run() -> dict:
    scores = verify_sources()
    sources = dict(FROZEN_SOURCES)
    extra_path = ROOT / COLAB_RECEIPT
    colab_verified = False
    if extra_path.is_file():
        proof = json.loads(extra_path.read_text())
        if proof.get("original_uploaded_notebook_sha256") != SOURCE_SHA:
            raise ValueError("Colab receipt does not match frozen submitted source")
        if proof.get("execution_status") == "PASS_CURRENT_CLOUD_RUN_ALL":
            if (proof.get("executed_code_cells") != 16
                    or proof.get("error_cells") != 0
                    or proof.get("match_count") != 500
                    or proof.get("test_rows") != 3836):
                raise ValueError("Colab claim is unsupported by full output proof")
            sources[COLAB_RECEIPT] = COLAB_RECEIPT
            colab_verified = True
    data = {n: (ROOT / p).read_bytes() for n, p in sources.items()}
    # Deliver a single notebook, four-page report and a compact result record.
    if sum(x.endswith(".ipynb") for x in data) != 1:
        raise ValueError("Only one notebook can be shipped")
    if len(data) > 11:
        raise ValueError("Reviewer package unexpectedly grew")
    for name, b in data.items():
        if Path(name).suffix not in TEXT_EXTENSIONS:
            continue
        text = b.decode("utf8")
        for category, regex in BANNED.items():
            match = regex.search(text)
            if match:
                raise ValueError(f"Unshippable {category} in {name}: {match.group(0)}")
    manifest = {
        "project": "Vexil Capital Senior Data Scientist take-home",
        "version": "2026-11-19",
        "notebook_original_source_sha256": SOURCE_SHA,
        "heldout_predictions_sha256": PRED_SHA,
        "source_scores": scores,
        "exact_current_notebook_colab_run_verified": colab_verified,
        "notes": ("This is the minimal reviewer package, not the internal "
                  "research/protocol archive. Original TEST was previously inspected."),
        "files": {n: {"bytes": len(b), "sha256": sha(b)}
                  for n, b in sorted(data.items())},
    }
    data["PACKAGE_MANIFEST.json"] = (json.dumps(manifest, indent=2,
                                               sort_keys=True) + "\n").encode()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w") as z:
        for name, raw in sorted(data.items()):
            item = zipfile.ZipInfo(name, date_time=STAMP)
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, raw, compress_type=zipfile.ZIP_DEFLATED,
                       compresslevel=9)
    with zipfile.ZipFile(DEST) as z:
        assert z.testzip() is None
        for name, raw in data.items():
            if z.read(name) != raw:
                raise ValueError("Archived bytes differ from source: " + name)
        if len(z.namelist()) != len(data):
            raise ValueError("Unexpected archive entry")
    return {"zip": str(DEST), "size_bytes": DEST.stat().st_size,
            "sha256": sha(DEST.read_bytes()), "entries": len(data),
            "colab_verified": colab_verified, "scientific_inputs_frozen": True}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
