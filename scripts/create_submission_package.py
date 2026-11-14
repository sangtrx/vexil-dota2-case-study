"""Build a deterministic external Vexil submission ZIP without private notes."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import zipfile

FILES=(
    "SUBMISSION_PACKAGE_README.md", "README.md",
    "live_dota2_win_probability.ipynb", "requirements.txt",
    "REPORT.pdf", "REPORT.md", "artifacts/heldout_predictions.csv",
    "docs/figures/heldout_reliability.png", "docs/figures/illustrative_game.png",
)
COLAB_OUTPUTS=(
    "derived_run_receipt.json", "match_manifest.csv", "heldout_metrics.csv",
    "validation_ablations.csv", "terminal_sensitivity.csv",
    "minute20_comeback.csv", "exploratory_item_ablation.csv",
    "exploratory_item_folds.csv", "heldout_predictions.csv", "calibration.png",
    "time_value_scenarios.png", "heldout_game_trajectory.png",
    "minute20_comeback.png",
)
STAMP=(2026,11,14,0,0,0)

def read_predictions(data: bytes) -> list[dict]:
    # Read the public derived predictions as data, without importing a modelling library.
    rows=list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    names=("match_id","minute","p_model","p_baseline","radiant_win")
    if not rows or tuple(rows[0])!=names:
        raise ValueError("Expected five columns in final heldout forecast CSV")
    seen=set()
    for row in rows:
        key=(int(row["match_id"]),int(row["minute"]))
        if key in seen: raise ValueError("Duplicate (match_id,minute) in heldout output")
        seen.add(key)
        if row["radiant_win"] not in ("0","1"):raise ValueError("Invalid outcome label")
        for name in ("p_model","p_baseline"):
            p=float(row[name])
            if not math.isfinite(p) or not 0<p<1:
                raise ValueError("Invalid or out-of-range probability")
    return rows

def assert_hosted_parity(entries: dict[str, bytes], root: Path) -> None:
    local=read_predictions((root/"artifacts/heldout_predictions.csv").read_bytes())
    cloud=read_predictions(entries["results/colab/heldout_predictions.csv"])
    if len(local)!=len(cloud):raise ValueError("Colab heldout row count differs from published forecast")
    for a,b in zip(local,cloud):
        if any(a[k]!=b[k] for k in ("match_id","minute","radiant_win")):
            raise ValueError("Colab output prediction key or label changed")
        for k in ("p_model","p_baseline"):
            if not math.isclose(float(a[k]),float(b[k]),rel_tol=0,abs_tol=1e-12):
                raise ValueError("Colab forecast value differs from published frozen result")
    valid=list(csv.DictReader(io.StringIO(entries["results/colab/heldout_metrics.csv"].decode("utf-8"))))
    score=lambda row,typ: (-(int(row["radiant_win"])*math.log(float(row[typ]))+(1-int(row["radiant_win"]))*math.log1p(-float(row[typ]))),
                           (float(row[typ])-int(row["radiant_win"]))**2)
    for name,offset in (("logloss",0),("brier",1)):
        row=next((z for z in valid if z.get("phase")=="overall" and z.get("metric")==name),None)
        if row is None or int(row["matches"])!=106 or int(row["rows"])!=3837:
            raise ValueError("Missing / wrong overall metrics in Colab export")
        actual=sum(score(z,"p_model")[offset] for z in local)/len(local)
        baseline=sum(score(z,"p_baseline")[offset] for z in local)/len(local)
        if not math.isclose(actual,float(row["model"]),rel_tol=0,abs_tol=1e-12):
            raise ValueError("Heldout model metric inconsistent with probabilities")
        if not math.isclose(baseline,float(row["baseline"]),rel_tol=0,abs_tol=1e-12):
            raise ValueError("Heldout baseline metric inconsistent with probabilities")

def verify_source(root: Path) -> None:
    source=(root/"live_dota2_win_probability.ipynb").read_bytes()
    provenance=json.loads((root/"research/results/colab_v4_provider_provenance_20261114.json").read_text())
    if hashlib.sha256(source).hexdigest()!=provenance["source_notebook_sha256"]:
        raise ValueError("Frozen notebook source differs from independently checked Colab provenance")
    forecast=(root/"artifacts/heldout_predictions.csv").read_bytes()
    receipt=json.loads((root/"research/results/league_and_boundary_stress_20261114.json").read_text())
    if hashlib.sha256(forecast).hexdigest()!=receipt["prediction_file_sha256"]:
        raise ValueError("Frozen 3,837-row heldout forecasts changed")
    expected=read_predictions(forecast)
    if len(expected)!=3837 or len({r["match_id"] for r in expected})!=106:
        raise ValueError("Wrong heldout match/row count")
    nb=json.loads(source)

    code=[c for c in nb["cells"] if c["cell_type"]=="code"]
    if len(code)!=14 or any(c.get("execution_count") is None for c in code):
        raise ValueError("Expected 14 executed code cells")
    if any(o.get("output_type")=="error" for c in code for o in c.get("outputs",[])):
        raise ValueError("Error outputs in notebook")
    if sum("image/png" in o.get("data",{}) for c in code for o in c.get("outputs",[]))!=4:
        raise ValueError("Four saved image outputs required")
    lines=[p.strip() for p in (root/"requirements.txt").read_text().splitlines()
           if p.strip() and not p.strip().startswith("#")]
    if not lines or any("==" not in p for p in lines):
        raise ValueError("Unpinned requirements")
    if "Approximately **8 hours of active work**" not in (root/"REPORT.md").read_text():
        raise ValueError("Real active-hours statement not recorded")
    info=subprocess.check_output(["pdfinfo",str(root/"REPORT.pdf")],text=True)
    pages=next(int(p.split(":",1)[1]) for p in info.splitlines() if p.startswith("Pages:"))
    if not (1<=pages<=4): raise ValueError("Report exceeds four pages")

def add(z: zipfile.ZipFile,name: str,data: bytes) -> None:
    item=zipfile.ZipInfo(name,date_time=STAMP)
    item.compress_type=zipfile.ZIP_DEFLATED
    item.external_attr=0o100644<<16
    z.writestr(item,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def create(root: Path,hosted: Path|None,destination: Path)->dict:
    verify_source(root)
    entries={}
    for rel in FILES:
        path=root/rel
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing unsafe source: "+rel)
        entries[rel]=path.read_bytes()
    if hosted is not None:
        for name in COLAB_OUTPUTS:
            path=hosted/name
            if not path.is_file() or path.is_symlink():
                raise ValueError("Missing hosted artifact: "+name)
            entries["results/colab/"+name]=path.read_bytes()
        receipt=json.loads(entries["results/colab/derived_run_receipt.json"])
        if receipt.get("matches")!=500 or receipt.get("minute_rows")!=18304:
            raise ValueError("Unrecognized match manifest")
        if (receipt.get("runtime") or {}).get("colab_detected") is not True:
            raise ValueError("Missing actual Colab runtime flag")
        if (receipt.get("retrieval") or {}).get("cache_hits")!=0:
            raise ValueError("Hosted run not fresh")
        if (receipt.get("retrieval") or {}).get("api_calls",0)<500:
            raise ValueError("Hosted run HTTP calls too few for a cold 500-game fetch")
        local=json.loads((root/"research/results/v4_local_replay_20261114.json").read_text())
        # Raw replay JSON may be reparsed, but selected model and cohort identity must stay fixed.
        for key in ("model_selected_on_validation","manifest_sha256","model_input_sha256","outcome_label_sha256","cohort_metadata_sha256"):
            expected=local.get(key)
            if expected is not None and receipt.get(key)!=expected:
                raise ValueError("Hosted run changed scientific source identity: "+key)
        assert_hosted_parity(entries,root)
    manifest={
        "package":"Vexil Dota 2 take-home",
        "created_on":"2026-11-14",
        "report_page_count":3,
        "estimated_human_active_hours":8,
        "source_notebook_sha256":hashlib.sha256(entries["live_dota2_win_probability.ipynb"]).hexdigest(),
        "files":{n:{"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
                 for n,raw in sorted(entries.items())},
    }
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,"w") as z:
        for name,raw in sorted(entries.items()):add(z,name,raw)
        add(z,"PACKAGE_MANIFEST.json",(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode())
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None:raise ValueError("ZIP CRC check failed")
        for name,meta in manifest["files"].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=meta["sha256"]:
                raise ValueError("ZIP checksum mismatch: "+name)
    return {"path":str(destination),"files":len(entries)+1,
            "bytes":destination.stat().st_size,
            "sha256":hashlib.sha256(destination.read_bytes()).hexdigest()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--colab-outputs-dir",type=Path)
    ap.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[1]/"delivery/Vexil_Dota2_Takehome_20261114.zip")
    a=ap.parse_args()
    print(json.dumps(create(a.root,a.colab_outputs_dir,a.output),sort_keys=True))

if __name__=="__main__":main()
