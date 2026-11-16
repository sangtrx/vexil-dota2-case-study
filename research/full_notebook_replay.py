#!/usr/bin/env python3
"""Fail-closed 500-game OpenDota notebook replay from pinned local raw cache.

This *optional* BigLinux QA runs all original notebook cells in a brand-new
Jupyter kernel. It does not change source code, fit a new model, query OpenDota,
or modify the employer package. Requires optional nbclient and ipykernel.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

EXPECTED_NOTEBOOK_CODE_SHA="e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b"
EXPECTED_TEST_SHA="03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
EXPECTED_MANIFEST_SHA="e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea"
EXPECTED_MATCHES=500
EXPECTED_CODE_CELLS=14
EXPECTED_ROWS=18292
EXPECTED_SPLIT_GAMES={"train":291,"validation":103,"test":106}
EXPECTED_PATCHES={"59":250,"60":250}
SOURCE_LINEAGE_KEYS=("model_inputs","outcome_labels","dev_item_inputs","cohort_metadata")
ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/"research/frozen_original_notebook_source.json"
COLAB=ROOT/"docs/COLAB_COLD_RUN_RECEIPT.json"


def sha_bytes(content:bytes)->str:
    return hashlib.sha256(content).hexdigest()


def source_ids(nb)->tuple[int,...]:
    """Parse literal frozen IDs from the original unchanged notebook source."""
    cells=[c for c in nb.cells if c.cell_type=="code"]
    candidates=[]
    for cell in cells:
        source=cell.source
        if "FROZEN_MATCH_IDS = (" not in source:
            continue
        tree=ast.parse(source)
        for statement in tree.body:
            if not isinstance(statement,ast.Assign):
                continue
            if any(isinstance(x,ast.Name) and x.id=="FROZEN_MATCH_IDS"
                   for x in statement.targets):
                value=ast.literal_eval(statement.value)
                if not isinstance(value,tuple) or any(type(x)!=int for x in value):
                    raise ValueError("Frozen cohort ID literal must be a tuple of ints")
                candidates.append(value)
    if len(candidates)!=1:
        raise ValueError("Cannot uniquely identify the literal frozen ID tuple")
    ids=candidates[0]
    if len(ids)!=EXPECTED_MATCHES or len(set(ids))!=EXPECTED_MATCHES:
        raise ValueError("Frozen cohort must be exactly 500 unique IDs")
    return ids


def scientific_fingerprint(nb)->str:
    # Cell index 2 is the environment-setup cell; it is intentionally excluded
    # by the original historical science-code fingerprint.
    src="".join(c.source for i,c in enumerate(nb.cells)
                if c.cell_type=="code" and i!=2)
    return sha_bytes(src.encode("utf-8"))


def key_for(mid:int)->str:
    path="/matches/"+str(mid)
    return sha_bytes(json.dumps([path,{}],sort_keys=True).encode("utf-8"))


def preflight_cache(source_dir:Path, match_ids:tuple[int,...]):
    """Read only cached RAW JSON and fail before launching kernel if incomplete."""
    by_name={}
    digest={}
    patches={}
    for mid in match_ids:
        source=source_dir/(key_for(mid)+".json.gz")
        if not source.is_file():
            raise FileNotFoundError("Missing frozen local match cache: match_id "+str(mid))
        with gzip.open(source,"rt",encoding="utf-8") as f:
            payload=json.load(f)
        if (not isinstance(payload,dict) or type(payload.get("match_id")) is not int
                or payload["match_id"]!=mid):
            raise ValueError("Cached match identity mismatch: "+str(mid))
        gold=payload.get("radiant_gold_adv")
        if not isinstance(gold,list) or not gold:
            raise ValueError("Cached match is not parsed: "+str(mid))
        duration=payload.get("duration")
        if (not isinstance(duration,(int,float)) or duration<600
                or type(payload.get("radiant_win")) is not bool):
            raise ValueError("Cached match eligibility drift: "+str(mid))
        # Self-contained provenance against content changes, not gzip header.
        h=sha_bytes(json.dumps(payload,sort_keys=True,
                 separators=(",",":"),ensure_ascii=True).encode("utf-8"))
        by_name[mid]=source
        digest[str(mid)]=h
        p=str(payload.get("patch"))
        patches[p]=patches.get(p,0)+1
    if patches!=EXPECTED_PATCHES:
        raise ValueError("Cached sources no longer have frozen 250/250 patches")
    source_digest=sha_bytes(json.dumps(digest,sort_keys=True,
                    separators=(",",":")).encode("utf-8"))
    return by_name,source_digest


def copy_frozen_sources(source_map:dict, temp_root:Path)->Path:
    dest=temp_root/"vexil_opendota_json_v1"
    dest.mkdir(parents=True,exist_ok=False)
    for mid,src in source_map.items():
        shutil.copyfile(src,dest/(key_for(mid)+".json.gz"))
    if len(list(dest.iterdir()))!=EXPECTED_MATCHES:
        raise AssertionError("Copied source-cache count differs")
    return dest


def stable_artifact_checks(folder:Path)->dict[str,str]:
    expected={
        "match_manifest.csv","validation_ablations.csv","heldout_metrics.csv",
        "terminal_sensitivity.csv","heldout_predictions.csv",
        "minute20_comeback.csv","exploratory_item_ablation.csv",
        "exploratory_item_folds.csv","derived_run_receipt.json",
        "calibration.png","time_value_scenarios.png",
        "heldout_game_trajectory.png","minute20_comeback.png",
    }
    names={p.name for p in folder.iterdir() if p.is_file()}
    if not expected.issubset(names):
        raise ValueError("Notebook did not write required scientific outputs: "
                         +repr(sorted(expected-names)))
    return {name:sha_bytes((folder/name).read_bytes()) for name in sorted(expected)}


def execute_replay(raw_cache:Path,output_root:Path):
    raw_cache=raw_cache.expanduser().resolve()
    output_root=output_root.expanduser().resolve()
    try:
        import nbformat
        import pandas as pd
        from jupyter_client.kernelspec import KernelSpecManager
        from nbclient import NotebookClient
    except ImportError as exc:
        raise RuntimeError("Offline replay optionally requires nbformat and nbclient") from exc
    nb=nbformat.read(str(NB),as_version=4)
    if scientific_fingerprint(nb)!=EXPECTED_NOTEBOOK_CODE_SHA:
        raise ValueError("Frozen notebook scientific source has been modified")
    ids=source_ids(nb)
    cold=json.loads(COLAB.read_text())
    if cold["scientific_code_sha256"]!=EXPECTED_NOTEBOOK_CODE_SHA:
        raise ValueError("Cold Colab source fingerprint differs")
    source_map,src_digest=preflight_cache(raw_cache,ids)
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError("Refusing to overwrite nonempty replay directory")
    output_root.mkdir(parents=True,exist_ok=True)
    ktmp=output_root/"kernel_tmp"
    ktmp.mkdir()
    copy_frozen_sources(source_map,ktmp)
    # Run the unchanged notebook in a new kernel, with no eligible HTTP work
    # remaining. If notebook tries to fetch a new endpoint, the dead proxy
    # rejects any HTTP(S) request rather than silently using the Internet.
    env_backup={key:os.environ.get(key) for key in (
        "TMPDIR","TEMP","TMP","HTTP_PROXY","HTTPS_PROXY",
        "http_proxy","https_proxy","NO_PROXY","no_proxy",
        "MPLBACKEND","OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","PATH"
    )}
    # Force the Jupyter kernel's Python launcher to use this same
    # verified controller environment, not a user-level global python.
    controller_executable=Path(sys.executable).resolve()
    os.environ["PATH"]=str(Path(sys.executable).parent)+os.pathsep+os.environ.get("PATH","")
    spec=KernelSpecManager().get_kernel_spec("python3")
    kernel_launcher=shutil.which(spec.argv[0])
    if not kernel_launcher or Path(kernel_launcher).resolve()!=controller_executable:
        raise ValueError("Jupyter kernel would use another Python interpreter")
    os.environ.update({
        "TMPDIR":str(ktmp),"TEMP":str(ktmp),"TMP":str(ktmp),
        "HTTP_PROXY":"http://127.0.0.1:9",
        "HTTPS_PROXY":"http://127.0.0.1:9",
        "http_proxy":"http://127.0.0.1:9",
        "https_proxy":"http://127.0.0.1:9",
        "NO_PROXY":"127.0.0.1,localhost",
        "no_proxy":"127.0.0.1,localhost",
        "MPLBACKEND":"Agg",
        "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
    })
    # NBClient has no data-independent shortcut: all notebook code cells run.
    try:
        client=NotebookClient(nb,timeout=900, kernel_name="python3",
                              allow_errors=False,
                              resources={"metadata":{"path":str(output_root)}})
        executed=client.execute()
    finally:
        for k,v in env_backup.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

    code=[c for c in executed.cells if c.cell_type=="code"]
    if len(code)!=EXPECTED_CODE_CELLS:
        raise AssertionError("Unexpected executed code cell count")
    errored=[(i,o) for i,c in enumerate(code) for o in c.outputs
             if o.get("output_type")=="error"]
    if errored or any(c.execution_count is None for c in code):
        raise AssertionError("Notebook execution has errors or skipped cells")
    if scientific_fingerprint(executed)!=EXPECTED_NOTEBOOK_CODE_SHA:
        raise AssertionError("Notebook source changed during execution")
    # Keep executed outputs outside the source repo and recruiter ZIP.
    nbformat.write(executed,str(output_root/"executed_fresh_kernel.ipynb"))

    folder=ktmp/"vexil_takehome_outputs"
    artifact_sha=stable_artifact_checks(folder)
    if artifact_sha["heldout_predictions.csv"]!=EXPECTED_TEST_SHA:
        raise ValueError("Replay TEST predictions not byte-identical to frozen file: "
                         +artifact_sha["heldout_predictions.csv"])
    receipt=json.loads((folder/"derived_run_receipt.json").read_text())
    # Independently derive strict preterminal counts from saved 500 match
    # durations and the same canonical match->partition manifest.
    meta=pd.read_csv(folder/"match_manifest.csv")
    if (len(meta)!=EXPECTED_MATCHES or meta.match_id.nunique()!=EXPECTED_MATCHES
            or set(meta.match_id)!=set(ids)):
        raise ValueError("Notebook split manifest has wrong match IDs")
    durations={}
    for mid,source in source_map.items():
        with gzip.open(source,"rt",encoding="utf-8") as z:
            data=json.load(z)
        durations[mid]=int(data["duration"])
    meta["admissible_rows"]=meta.match_id.map(
        lambda mid: ((durations[int(mid)]-1)//60)+1)
    minutes={str(k):int(v) for k,v in meta.groupby("partition").admissible_rows.sum().items()}
    expected_minutes={"train":10675,"validation":3781,"test":3836}
    if minutes!=expected_minutes:
        raise ValueError("Split minute row counts changed: "+str(minutes))
    val=pd.read_csv(folder/"validation_ablations.csv")
    expected_val={
        "M0_gold_only":(0.5324900423908928,0.1810746830906831),
        "M1_time_value":(0.519713962581423,0.1759016844633338),
        "M2_lead_fragility":(0.5223863883284187,0.17779381881266196),
        "M3_objective_conversion":(0.5282050730295414,0.18063144342728849),
    }
    if (len(val)!=4 or set(val.model)!=set(expected_val)
            or val.model.duplicated().any()):
        raise ValueError("Validation candidate family changed")
    for model_name,(want_ll,want_brier) in expected_val.items():
        row=val[val.model==model_name].iloc[0]
        if abs(float(row.log_loss)-want_ll)>1e-9 or abs(float(row.brier)-want_brier)>1e-9:
            raise ValueError("Original validation model score changed: "+model_name)
    measured=pd.read_csv(folder/"heldout_metrics.csv")
    overall=measured[measured.phase=="overall"]
    if set(overall.metric)!={"logloss","brier"} or len(overall)!=2:
        raise ValueError("Overall held-out score output changed")
    want_test={
        "logloss":(0.5164444241748873,0.504014697253528),
        "brier":(0.1719121780368728,0.1683528340689237),
    }
    for metric,(expected_base,expected_model) in want_test.items():
        row=overall[overall.metric==metric].iloc[0]
        if (abs(float(row.baseline)-expected_base)>1e-9
                or abs(float(row.model)-expected_model)>1e-9):
            raise ValueError("Frozen TEST score differs: "+metric)
    if (receipt["matches"]!=500 or receipt["minute_rows"]!=EXPECTED_ROWS
            or receipt["split_match_counts"]!=EXPECTED_SPLIT_GAMES
            or receipt["patch_counts"]!=EXPECTED_PATCHES
            or receipt["model_selected_on_validation"]!="M1_time_value"
            or receipt["retrieval"]["api_calls"]!=0
            or receipt["retrieval"]["cache_hits"]!=500
            or receipt["manifest_sha256"]!=cold["frozen_manifest_sha256"]):
        raise ValueError("Original 500-game replay scientific contract failed")
    # The exact notebook-produced figures used in REPORT.pdf must be
    # byte-identical, not merely visually similar or independently redrawn.
    report_figure_names={
        "calibration.png":"docs/figures/heldout_reliability.png",
        "time_value_scenarios.png":"docs/figures/time_value_scenarios.png",
        "heldout_game_trajectory.png":"docs/figures/heldout_game_trajectory.png",
    }
    for generated,repo_path in report_figure_names.items():
        if artifact_sha[generated]!=sha_bytes((ROOT/repo_path).read_bytes()):
            raise ValueError("Report figure differs from frozen notebook output: "+repo_path)
    for k in SOURCE_LINEAGE_KEYS:
        field={"model_inputs":"model_input_sha256",
               "outcome_labels":"outcome_label_sha256",
               "dev_item_inputs":"dev_item_input_sha256",
               "cohort_metadata":"cohort_metadata_sha256"}[k]
        if receipt[field]!=cold["source_lineage_sha256"][k]:
            raise ValueError("Original source-lineage fingerprint changed: "+k)
    return {
        "evidence_class":"AUTHOR_CONTROLLED_NO_NETWORK_500_MATCH_FRESH_KERNEL_REPLAY",
        "execution_date_utc":datetime.now(timezone.utc).date().isoformat(),
        "source_code_sha256":EXPECTED_NOTEBOOK_CODE_SHA,
        "source_notebook_sha256":sha_bytes(NB.read_bytes()),
        "setup_cell_sha256":sha_bytes(nb.cells[2].source.encode("utf-8")),
        "original_test_predictions_sha256":artifact_sha["heldout_predictions.csv"],
        "local_fresh_kernel_test_csv_byte_parity_verified":True,
        "report_figures_byte_equal_to_notebook_outputs":True,
        "source_cached_json_canonical_digest":src_digest,
        "data_origin":"author's pre-existing OpenDota raw-match cache; no new HTTP",
        "source_gzip_files_copied":len(source_map),
        "controller_python_executable":sys.executable,
        "kernel_launcher_executable":kernel_launcher,
        "kernel_spec_argv":spec.argv,
        "jupyter_kernel_is_controller_python":True,
        "split_minute_rows":minutes,
        "validation_model_scores":{k:{"logloss":v[0],"brier":v[1]} for k,v in expected_val.items()},
        "heldout_scores":{k:{"M0":v[0],"M1":v[1]} for k,v in want_test.items()},
        "executed_code_cells":len(code),"cell_execution_errors":len(errored),
        "zero_http_calls":receipt["retrieval"]["api_calls"]==0,
        "cache_hits":receipt["retrieval"]["cache_hits"],
        "matches":receipt["matches"],
        "minute_rows":receipt["minute_rows"],
        "split_match_counts":receipt["split_match_counts"],
        "selected_model":receipt["model_selected_on_validation"],
        "source_lineage_sha256":{
            key:receipt[{"model_inputs":"model_input_sha256",
                          "outcome_labels":"outcome_label_sha256",
                          "dev_item_inputs":"dev_item_input_sha256",
                          "cohort_metadata":"cohort_metadata_sha256"}[key]]
            for key in SOURCE_LINEAGE_KEYS},
        "environment":{"python":receipt["python"],"versions":receipt["versions"]},
        "outputs_sha256":artifact_sha,
        "cloud_csv_byte_parity_claimed":False,
        "employer_release_or_submission_modified":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir",type=Path,required=True)
    parser.add_argument("--out-dir",type=Path,required=True)
    args=parser.parse_args()
    receipt=execute_replay(args.cache_dir,args.out_dir)
    target=args.out_dir/"no_network_replay_receipt.json"
    target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("PASS: 500-game notebook, 14 cells, 0 HTTP, exact frozen TEST CSV")
    print("PASS: source, outcome and metadata lineage; 3 exact report figure PNGs")
    print("Receipt:",target)


if __name__=="__main__":
    main()
