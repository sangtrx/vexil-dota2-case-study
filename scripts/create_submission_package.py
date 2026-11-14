#!/usr/bin/env python3
"""Build and verify a deterministic reviewer-facing Vexil submission archive."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "delivery" / "Vexil_Dota2_Takehome_20261114.zip"
MODEL_CODE_SHA256 = "d3a12a5bb2c272b10f6a16384eb760d52efba89a856b95b9d651bd001a57eba5"
EXPECTED_NOTEBOOK_SHA256 = "bbac94f53890825ade6f7654946f427be3b26f0c032f67271fc11c6525060877"
EXPECTED_FORECAST_SHA256 = "e3b2c843172fdde029f5f5ec05536ea837ec023b8b860543cadedf028bb3cb32"
FILES = (
    "README.md",
    "SUBMISSION_PACKAGE_README.md",
    "live_dota2_win_probability.ipynb",
    "requirements.txt",
    "REPORT.md",
    "REPORT.pdf",
    "artifacts/heldout_predictions.csv",
    "docs/figures/heldout_reliability.png",
    "docs/figures/illustrative_game.png",
    "tests/test_notebook_contracts.py",
    "tests/test_report_contract.py",
    "tests/test_submission_forecasts.py",
)
STAMP = (2026, 11, 14, 0, 0, 0)


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
        raise ValueError("Scientific code is not the independently reviewed version.")
    setup = "".join(cells[2]["source"])
    setup_out = "".join(
        "".join(x.get("text", "")) if isinstance(x.get("text"), list)
        else str(x.get("text", ""))
        for x in cells[2].get("outputs", [])
        if x.get("output_type") == "stream"
    )
    if "8 hours active" not in setup or "Approximately 8 hours active" not in setup_out:
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
    report = (ROOT / "REPORT.md").read_text()
    if not all(x in report for x in ("**Time spent:**", "**Assistance disclosure:**", "**Result:**")):
        raise ValueError("Missing hours, assistance or results in report.")

    forecasts = (ROOT / "artifacts/heldout_predictions.csv").read_bytes()
    if sha(forecasts) != EXPECTED_FORECAST_SHA256:
        raise ValueError("Frozen held-out predictions have changed.")
    rows = list(csv.DictReader(io.StringIO(forecasts.decode("utf8"))))
    if len(rows) != 3837 or len({r["match_id"] for r in rows}) != 106:
        raise ValueError("Expected exactly 106 games and 3,837 forecasts.")
    if not rows or list(rows[0]) != ["match_id", "minute", "p_model", "p_baseline", "radiant_win"]:
        raise ValueError("Missing required held-out probability columns.")
    for row in rows:
        if row["radiant_win"] not in ("0", "1"):
            raise ValueError("Invalid held-out target.")
        for key in ("p_model", "p_baseline"):
            p = float(row[key])
            if not math.isfinite(p) or p <= 0 or p >= 1:
                raise ValueError("Invalid probability in held-out CSV.")

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
    reference = ((0.5163046946798686, 0.17185915685725403),
                 (0.5039056145604591, 0.168311943059945))
    if any(abs(a - b) > 1e-12
           for computed, expected in zip((m0, m1), reference)
           for a, b in zip(computed, expected)):
        raise ValueError("Recomputed held-out metrics differ from report.")
    return {"pages": pages, "forecast_rows": len(rows), "heldout_games": 106,
            "M0": m0, "M1": m1}


def run() -> dict:
    acceptance = verify()
    entries = {name: (ROOT / name).read_bytes() for name in FILES}
    manifest = {
        "project": "Vexil Capital Senior Data Scientist Dota 2 take-home",
        "created_on": "2026-11-14",
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
            "science_code_unchanged": True, **acceptance}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
