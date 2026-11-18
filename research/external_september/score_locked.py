#!/usr/bin/env python3
"""Single-shot external Sept replay with March frozen models; no cohort reselection."""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import requests

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
RAW_DIR=Path("/srv/ai/tmp/vexil-september-raw-20261118")
PROTOCOL=BASE/"PROTOCOL.md"
METADATA=BASE/"selected_metadata.json"
LOCKED=BASE/"locked_model_parameters.json"
SCORES=BASE/"external_september_scores.json"
CSV=BASE/"external_september_predictions.csv"
SEED=20261118

sys.path.insert(0,str(BASE))
from frozen_models import describe_models,fit_models,INPUTS  # noqa: E402

def sha(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_precommitted():
    if SCORES.exists() or CSV.exists():
        raise FileExistsError("External outcome already scored. No repeat scoring or reroll.")
    expected={
        "research/external_september/PROTOCOL.md":PROTOCOL,
        "research/external_september/selected_metadata.json":METADATA,
        "research/external_september/locked_model_parameters.json":LOCKED,
        "research/external_september/score_locked.py":Path(__file__),
    }
    for rel,path in expected.items():
        committed=subprocess.check_output(
            ["git","show",f"HEAD:{rel}"],cwd=ROOT
        )
        if committed != path.read_bytes():
            raise RuntimeError("Study rule differs from prior commit: "+rel)
    metadata=json.loads(METADATA.read_text())
    assert len(metadata["matches"])==metadata["selected_count"]==200
    assert len({v["match_id"] for v in metadata["matches"]})==200
    assert metadata["selected_metadata_sha256"]==hashlib.sha256(
        json.dumps(metadata["matches"],sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    assert all("radiant_win" not in row for row in metadata["matches"])
    from frozen_models import filehash
    locked=json.loads(LOCKED.read_text())
    now=describe_models()
    for k in ("train_sha256","dev_feature_sha256",
              "original_test_sha256","original_notebook_sha256","sklearn","models"):
        if locked[k]!=now[k]:raise RuntimeError("Model lock changed: "+k)
    if max(now["original_validation_max_abs_prediction_delta"].values())>1e-10:
        raise RuntimeError("Historical model parity failed")
    return metadata, locked

def exact_feature_functions():
    """Execute ONLY the pure named original feature definitions; no notebook training or TEST."""
    nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
    code="".join(nb["cells"][7]["source"])
    marker="\nminute_table = make_minute_table(matches)"
    if code.count(marker)!=1:raise RuntimeError("Original notebook source no longer matches expected layout")
    definitions=code.split(marker,1)[0]
    ns={"np":np,"pd":pd,"math":math}
    exec(compile(definitions, "frozen_original_feature_definitions", "exec"),ns)
    return ns["make_minute_table"]

def download_raw(match_id,session):
    RAW_DIR.mkdir(parents=True,exist_ok=True)
    file=RAW_DIR/f"{match_id}.json.gz"
    if file.exists():
        with gzip.open(file,"rt",encoding="utf-8") as f:
            raw=json.load(f)
        if raw.get("match_id")!=match_id:
            raise ValueError("Cached ID mismatch")
        return raw,sha(file),"cache"
    url=f"https://api.opendota.com/api/matches/{match_id}"
    for retry in range(7):
        try:
            resp=session.get(url,timeout=35)
            if resp.status_code in (429,500,502,503,504):
                time.sleep(min(3*(retry+1),24))
                continue
            resp.raise_for_status()
            raw=resp.json()
            if not isinstance(raw,dict) or raw.get("match_id")!=match_id:
                raise ValueError("Nonmatching match payload")
            with gzip.open(file,"wt",encoding="utf8",compresslevel=6) as f:
                json.dump(raw,f,sort_keys=True,separators=(",",":"))
            return raw,sha(file),"api"
        except (requests.RequestException,ValueError):
            if retry==6:raise
            time.sleep(min(3*(retry+1),24))
    raise RuntimeError("No successful fetch")

def minute_losses(y,p):
    p=np.clip(np.asarray(p,dtype=float),1e-12,1-1e-12)
    y=np.asarray(y,dtype=int)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def ece10(y,p):
    p=np.asarray(p)
    y=np.asarray(y)
    edges=np.minimum((p*10).astype(int),9)
    return float(sum(
        np.count_nonzero(edges==b)/len(p)*abs(
            np.mean(y[edges==b])-np.mean(p[edges==b]))
        for b in range(10) if np.any(edges==b)
    ))

def grouped_ci(frame, seed=SEED, count=5000):
    groups=frame.groupby("series_group",sort=True,dropna=False)
    arr=np.asarray([
       (len(g),float((g["ll_m1"]-g["ll_m0"]).sum()))
       for _,g in groups
    ],dtype=float)
    rng=np.random.default_rng(seed)
    n=len(arr)
    if n<2:raise ValueError("Cannot bootstrap fewer than two groups")
    res=np.empty(count)
    for idx in range(count):
        sample=rng.integers(0,n,size=n)
        a=arr[sample]
        res[idx]=a[:,1].sum()/a[:,0].sum()
    return [float(x) for x in np.quantile(res,[0.025,0.975])],n

def evaluate():
    meta,locked=verify_precommitted()
    features=exact_feature_functions()
    fixed_models=fit_models()
    s=requests.Session();s.headers["User-Agent"]="vexil-external-sept-locked-eval/1.0"
    rejected=[]
    payload_hashes=[]
    frames=[]
    for index,item in enumerate(meta["matches"],1):
        match_id=item["match_id"]
        try:
            match,digest,mode=download_raw(match_id,s)
            payload_hashes.append({"match_id":match_id,"gz_sha256":digest,"mode":mode})
            if int(match.get("start_time",-1))!=item["start_time"]:
                raise ValueError("Source start_time drift")
            if int(match.get("duration",-1))!=item["duration"]:
                raise ValueError("Source duration drift")
            if int(match.get("duration",0))<600:raise ValueError("Short match")
            if "radiant_win" not in match:raise ValueError("Missing outcome")
            # Do not silently replace any excluded IDs. Source feature checks are the original notebook's.
            f=features([match])
            f["series_group"]=int(item.get("series_id") or 0) or -match_id
            f["league_id"]=int(item.get("leagueid") or 0)
            frames.append(f)
        except Exception as err:
            rejected.append({"match_id":match_id,"reason":type(err).__name__+": "+str(err)[:180]})
        if mode=="api" if "mode" in locals() else False:
            time.sleep(1.65)
        if index%25==0:
            print("RAW_FETCH_PROGRESS",index,"of",len(meta["matches"]),
                  "accepted",len(frames),"excluded",len(rejected),flush=True)

    # Outcomes are read for scoring ONLY here, after all original locked IDs have been fetched/checked.
    if not frames:
        report={"status":"NO_USABLE_PARSED_MATCHES", "selected":200,"rejected":rejected}
        SCORES.write_text(json.dumps(report,indent=2)+"\n")
        print("NO_USABLE_PARSED_MATCHES")
        return
    table=pd.concat(frames,ignore_index=True)
    assert table.match_id.nunique()==len(frames)
    for tag,model in fixed_models.items():
        table[f"p_{tag.lower()}"]=model.predict_proba(table[INPUTS[tag]])[:,1]
        table[f"ll_{tag.lower()}"]=minute_losses(table.radiant_win,table[f"p_{tag.lower()}"])
        table[f"brier_{tag.lower()}"]=(table[f"p_{tag.lower()}"]-table.radiant_win)**2
    ci,n_groups=grouped_ci(table)
    phase_masks={
        "0-9":table.minute.lt(10),
        "10-19":table.minute.ge(10)&table.minute.lt(20),
        "20-29":table.minute.ge(20)&table.minute.lt(30),
        "30+":table.minute.ge(30)
    }
    phases={}
    for name,mask in phase_masks.items():
        f=table.loc[mask]
        if f.empty:phases[name]={"matches":0,"minute_rows":0}
        else:phases[name]={
            "matches":int(f.match_id.nunique()),"minute_rows":len(f),
            "m0_ll":float(f.ll_m0.mean()),"m1_ll":float(f.ll_m1.mean()),
            "m0_brier":float(f.brier_m0.mean()),"m1_brier":float(f.brier_m1.mean()),
            "brier_delta":float(f.brier_m1.mean()-f.brier_m0.mean())
        }
    ll0=float(table.ll_m0.mean());ll1=float(table.ll_m1.mean())
    b0=float(table.brier_m0.mean());b1=float(table.brier_m1.mean())
    brier30=phases.get("30+",{}).get("brier_delta")
    is_support=(len(frames)>=150 and n_groups>=40 and
                (ll0-ll1)>=0.005 and ci[1]<0 and
                brier30 is not None and brier30<=0.002)
    evidence={
        "study":"sept2026_external_200",
        "no_reselection":True,
        "locked_preselection_model_commit":"90203d7596ef4279bf4f7c16c1f20e50045d02e7",
        "locked_selection_commit":"5b9c96e3042943af56ca8eb2b2fb6e9cabf947b1",
        "selection_sha256":meta["selected_metadata_sha256"],
        "original_train_sha256":locked["train_sha256"],
        "source_notebook_sha256":locked["original_notebook_sha256"],
        "selected_count":200,"usable_count":len(frames),
        "missing_or_invalid_count":len(rejected),"rejections":rejected,
        "raw_payload_receipts":payload_hashes,
        "source_received_at_available":False,
        "series_or_singleton_groups":n_groups,
        "minute_rows":len(table),
        "primary_logloss":{"m0":ll0,"m1":ll1,"m1_minus_m0":ll1-ll0,
                           "paired_group_bootstrap_95_ci":ci,
                           "n_boot":5000,"seed":SEED},
        "brier":{"m0":b0,"m1":b1,"m1_minus_m0":b1-b0},
        "ece10":{"m0":ece10(table.radiant_win,table.p_m0),
                 "m1":ece10(table.radiant_win,table.p_m1)},
        "phases":phases,
        "frozen_external_support_gate":"PASS" if is_support else "FAIL",
        "promotion":"NO AUTOMATIC PROMOTION; independent fresh future work and real received_at still needed",
        "outcome_viewed_before_selection":False,
        "original_test_is_new_blind":False
    }
    table[["match_id","minute","series_group","league_id",
           "radiant_win","p_m0","p_m1"]].to_csv(CSV,index=False,float_format="%.12g")
    evidence["scored_predictions_sha256"]=sha(CSV)
    SCORES.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print("FULL_EVALUATION_RESULT",json.dumps({
      "usable":len(frames),"excluded":len(rejected),"groups":n_groups,
      "minute_rows":len(table),"ll_m0":ll0,"ll_m1":ll1,
      "ll_delta":ll1-ll0,"ci":ci,"late_brier_delta":brier30,
      "external_support_gate":evidence["frozen_external_support_gate"]
    }))

if __name__=="__main__":
    evaluate()
