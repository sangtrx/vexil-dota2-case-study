#!/usr/bin/env python3
"""Run a predeclared finite structural feature ablation on ORIGINAL DEVELOPMENT ONLY.

This script must not load labels from the new 200-game holdout. A separate
mode freezes model selection before optional forward evaluation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions
from research.edge_features import SPECS, structural_rows

N=load_definitions()
BASE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
OUT=Path("/home/ai-agent/.cache/vexil-edge-v2-20261113")
OUT.mkdir(exist_ok=True,parents=True)
N_BOOT=2000
SEED=20261113

def load_development():
    manifest=pd.read_csv(BASE/"vexil_takehome_outputs/match_manifest.csv")
    assert manifest.match_id.nunique()==500
    assert set(manifest.partition)=={"train","validation","test"}
    develop=manifest[manifest.partition.isin(["train","validation"])].copy()
    api=N["OpenDota"](cache_dir=BASE/"api-cache",interval=1.65)
    games=[api.get("/matches/"+str(int(mid))) for mid in develop.match_id]
    assert api.calls==0, "Never recrawl source silently on the dev experiment"
    table=structural_rows(games,N["snapshot_features"]).merge(
        develop[["match_id","partition","start_time","series_id","patch"]],
        on="match_id",validate="many_to_one"
    )
    return develop,table

def fit(frame,columns):
    # Exactly the same impute/scale/logistic pipeline as the existing take-home.
    return N["fit_model"](frame,list(columns))

def compare_bootstrap(p_candidate,p_baseline,frame):
    data=frame[["match_id","minute","radiant_win"]].copy()
    y=data.radiant_win.to_numpy(dtype=int)
    for name,p in (("candidate",p_candidate),("baseline",p_baseline)):
        p=np.clip(np.asarray(p,dtype=float),1e-15,1-1e-15)
        data[name]=-(y*np.log(p)+(1-y)*np.log1p(-p))
    g=data.groupby("match_id").agg(n=("minute","size"),
                                  c=("candidate","sum"),b=("baseline","sum")).sort_index()
    m=g[["n","c","b"]].to_numpy(dtype=float)
    rng=np.random.default_rng(SEED)
    inds=rng.integers(0,len(m),size=(N_BOOT,len(m)))
    sums=m[inds].sum(axis=1)
    draws=(sums[:,1]-sums[:,2])/sums[:,0]
    observed=(m[:,1].sum()-m[:,2].sum())/m[:,0].sum()
    lo,hi=np.quantile(draws,[.025,.975])
    return dict(difference=float(observed),lo=float(lo),hi=float(hi),
                matches=len(m),minute_rows=len(data))

def dev_validation():
    manifest,full=load_development()
    train=full.loc[full.partition=="train"]
    val=full.loc[full.partition=="validation"]
    assert train.match_id.nunique()==291 and val.match_id.nunique()==103
    cover=full.groupby("partition")[
        ["econ_share_gap","top2_share_gap","core_gold_gap_share",
         "relative_shock5","signed_lead_persistence10"]].apply(
        lambda a: a.notna().mean().round(6).to_dict()
    )
    print("ENGINEERED_FEATURE_AVAILABILITY",cover.to_dict(),flush=True)
    models={}
    probabilities={}
    for name,cols in SPECS.items():
        model=fit(train,cols)
        models[name]=model
        probabilities[name]=model.predict_proba(val[list(cols)])[:,1]
    y=val.radiant_win.to_numpy(dtype=int)
    baseline=probabilities["M1_time_value"]
    base_ll=float(log_loss(y,baseline,labels=[0,1]))
    items=[]
    for name,cols in SPECS.items():
        p=probabilities[name]
        ll=float(log_loss(y,p,labels=[0,1]))
        br=float(brier_score_loss(y,p))
        boot=compare_bootstrap(p,baseline,val)
        items.append(dict(name=name,n_predictors=len(cols),val_logloss=ll,val_brier=br,
                          delta_vs_M1=ll-base_ll,delta_ci_lo=boot["lo"],
                          delta_ci_hi=boot["hi"],val_match_count=boot["matches"]))
    scores=pd.DataFrame(items).sort_values(["val_logloss","n_predictors","name"],
                                           kind="mergesort").reset_index(drop=True)
    scores.to_csv(OUT/"development_validation_scores.csv",index=False)
    print("DEVELOPMENT_VALIDATION_ABLATIONS")
    print(scores.to_string(index=False,float_format=lambda f:f"{f:.6f}"),flush=True)
    passers=[x for x in items if x["name"]!="M1_time_value"
              and x["delta_vs_M1"]<=-0.005 and x["delta_ci_hi"]<0]
    passers=sorted(passers,key=lambda x:(x["val_logloss"],x["n_predictors"],
                                         list(SPECS).index(x["name"])))
    selected=passers[0]["name"] if passers else "M1_time_value"
    decision=dict(
        selection=selected,
        qualified_incremental_edge=bool(passers),
        rules="delta logloss <= -0.005 and 95 percent whole-match bootstrap upper <0",
        bootstrap_repetitions=N_BOOT,seed=SEED,
        models_considered=list(SPECS.keys()),
        developer_game_count=int(manifest.match_id.nunique()),
        refit_data="original full 500, once selected"
    )
    (OUT/"development_selection_receipt.json").write_text(
        json.dumps(decision,sort_keys=True,indent=2)+"\n")
    print("DEVELOPMENT_SELECTION_LOCKED",json.dumps(decision,sort_keys=True),flush=True)
    return decision

if __name__=="__main__":
    dev_validation()
