"""Build a deterministic external Vexil submission ZIP without private notes."""
from __future__ import annotations
import argparse
import hashlib
import json
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

def verify_source(root: Path) -> None:
    nb=json.loads((root/"live_dota2_win_probability.ipynb").read_text())
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
    manifest={
        "package":"Vexil Dota 2 take-home",
        "created_on":"2026-11-14",
        "status":"PREPARED_NOT_SUBMITTED",
        "report_page_limit":4,
        "estimated_human_active_hours":8,
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
