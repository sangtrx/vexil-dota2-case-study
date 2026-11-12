#!/usr/bin/env python3
"""Development-only, series-cluster and multiplicity robustness for registered models."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.edge_experiment import load_development, fit, OUT, SEED
from research.edge_features import SPECS

N_BOOT=4000

def losses(p,y):
    p=np.clip(np.asarray(p,dtype=float),1e-15,1-1e-15)
    y=np.asarray(y,dtype=int)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def bootstrap_simultaneous(frame, predictions, cluster="match"):
    """Simultaneous max-t intervals and series-wise sensitivity, no model selection."""
    y=frame.radiant_win.to_numpy(dtype=int)
    base=losses(predictions["M1_time_value"],y)
    names=[name for name in SPECS if name!="M1_time_value"]
    loss_diffs=np.column_stack([losses(predictions[name],y)-base for name in names])
    if cluster=="series":
        keys=[("series",int(s)) if int(s)>0 else ("match",int(m))
              for s,m in zip(frame.series_id,frame.match_id)]
        # Pandas can group on tuples via Series, preserving match-within-series.
        labels=pd.factorize(pd.Series(keys,dtype="object"),sort=False)[0]
    else:
        labels=pd.factorize(frame.match_id,sort=False)[0]
    data=pd.DataFrame(loss_diffs,columns=names)
    data["grp"]=labels
    data["n"]=1
    ag=data.groupby("grp",sort=True).sum().reset_index(drop=True)
    lens=ag["n"].to_numpy(dtype=float)
    delta=ag[names].to_numpy(dtype=float)
    total=lens.sum()
    observed=delta.sum(axis=0)/total
    rng=np.random.default_rng(SEED)
    samples=rng.integers(0,len(ag),size=(N_BOOT,len(ag)))
    denominators=lens[samples].sum(axis=1)
    bs=delta[samples].sum(axis=1)/denominators[:,None]
    sd=np.maximum(bs.std(axis=0,ddof=1),1e-12)
    deviations=(bs-observed[None,:])/sd[None,:]
    max_abs=np.max(np.abs(deviations),axis=1)
    cutoff=float(np.quantile(max_abs,.95))
    rows=[]
    for i,name in enumerate(names):
        unadj=np.quantile(bs[:,i],[.025,.975])
        rows.append({
            "candidate":name,"clusters":len(ag),"difference":float(observed[i]),
            "unadjusted_lo":float(unadj[0]),"unadjusted_hi":float(unadj[1]),
            "simultaneous_95_lo":float(observed[i]-cutoff*sd[i]),
            "simultaneous_95_hi":float(observed[i]+cutoff*sd[i]),
            "simultaneous_max_t_cutoff":cutoff
        })
    return pd.DataFrame(rows)

def valid_cuts(m):
    groups=[("s",int(s)) if int(s)>0 else ("m",int(mid))
            for s,mid in zip(m.series_id,m.match_id)]
    minidx,maxidx={},{}
    for j,key in enumerate(groups):
        minidx[key]=min(j,minidx.get(key,j))
        maxidx[key]=max(j,maxidx.get(key,j))
    return [i for i in range(1,len(m)) if all(not(lo<i<=maxidx[k]) for k,lo in minidx.items())]

def walkforward(m,table):
    m=m[m.partition=="train"].sort_values(["start_time","match_id"]).reset_index(drop=True)
    cuts=valid_cuts(m)
    records=[]
    for fold,(target_start,target_end) in enumerate(((120,170),(175,225),(230,280)),start=1):
        start=min((i for i in cuts if 70<=i<=240),key=lambda i:abs(i-target_start))
        end=min((i for i in cuts if start+35<=i<=min(len(m)-1,start+70)),key=lambda i:abs(i-target_end))
        ids_train=set(m.iloc[:start].match_id)
        ids_eval=set(m.iloc[start:end].match_id)
        tr=table[table.match_id.isin(ids_train)]
        va=table[table.match_id.isin(ids_eval)]
        assert len(ids_train&ids_eval)==0
        assert not (set(m.iloc[:start].series_id)-{0})&(set(m.iloc[start:end].series_id)-{0})
        y=va.radiant_win.to_numpy(dtype=int)
        candidate={}
        for name,columns in SPECS.items():
            model=fit(tr,columns)
            p=model.predict_proba(va[list(columns)])[:,1]
            candidate[name]=float(log_loss(y,p,labels=[0,1]))
        for name,ll in candidate.items():
            records.append({"fold":fold,"train_games":len(ids_train),"eval_games":len(ids_eval),
                            "name":name,"log_loss":ll,
                            "diff_vs_M1":ll-candidate["M1_time_value"]})
    return pd.DataFrame(records)

def main():
    manifest,data=load_development()
    tr=data.loc[data.partition=="train"].copy()
    va=data.loc[data.partition=="validation"].copy()
    preds={}
    for name,features in SPECS.items():
        model=fit(tr,features)
        preds[name]=model.predict_proba(va[list(features)])[:,1]
    by_match=bootstrap_simultaneous(va,preds,cluster="match")
    by_series=bootstrap_simultaneous(va,preds,cluster="series")
    rolling=walkforward(manifest,data)
    print("VALIDATION_MULTIPLICITY_MATCH_CLUSTERS")
    print(by_match.to_string(index=False,float_format=lambda n:f"{n:.6f}"))
    print("VALIDATION_MULTIPLICITY_SERIES_CLUSTERS")
    print(by_series.to_string(index=False,float_format=lambda n:f"{n:.6f}"))
    print("TRAIN_ONLY_WALK_FORWARD_LOG_LOSS")
    print(rolling.to_string(index=False,float_format=lambda n:f"{n:.6f}"))
    by_match.to_csv(OUT/"validation_simultaneous_match.csv",index=False)
    by_series.to_csv(OUT/"validation_simultaneous_series.csv",index=False)
    rolling.to_csv(OUT/"train_walkforward.csv",index=False)
    receipt={"data":"original 291 train +103 validation; old 106 heldout excluded",
             "n_boot":N_BOOT,"seed":SEED,"candidate_family":list(SPECS)}
    (OUT/"robustness_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")

if __name__=="__main__":main()
