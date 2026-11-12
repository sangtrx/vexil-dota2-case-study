#!/usr/bin/env python3
"""ONE-SHOT out-of-time M1 vs M0 replication (no structural candidates).

Protocol amended before external outcomes were examined; never train on
future-cohort games or use them to select new structural features.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions

N=load_definitions()
BASE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
OUT=Path("/home/ai-agent/.cache/vexil-edge-v2-20261113")
SEED=20261113
BOOTS=2000

def paired_interval(data,field,unit="match_id"):
    key=(data.match_id.astype(str) if unit=="match_id" else
         np.where(data.series_id.astype(int)>0,
                  data.series_id.astype(str),"match-"+data.match_id.astype(str)))
    x=data.assign(cluster=key).groupby("cluster",sort=True).agg(
        n=("minute","size"),
        m=("{}_model".format(field),"sum"),
        b=("{}_baseline".format(field),"sum")
    )
    vec=x[["n","m","b"]].to_numpy(dtype=float)
    obs=(vec[:,1].sum()-vec[:,2].sum())/vec[:,0].sum()
    rng=np.random.default_rng(SEED)
    inds=rng.integers(0,len(vec),size=(BOOTS,len(vec)))
    sums=vec[inds].sum(axis=1)
    draws=(sums[:,1]-sums[:,2])/sums[:,0]
    lo,hi=np.quantile(draws,[.025,.975])
    return dict(delta=float(obs),lo=float(lo),hi=float(hi),clusters=len(vec))

def feature_cutoff_audit(games):
    tests=0
    for m in games:
        for t in sorted(set([0,1,5,10,20,min(int(m["duration"])//60,30)])):
            a=N["snapshot_features"](m,t)
            b=N["snapshot_features"](N["prefix_truncated"](m,t),t)
            N["assert_same_features"](a,b)
            tests+=1
    return tests

def main():
    spec=json.loads((OUT/"development_selection_receipt.json").read_text())
    assert spec["selection"]=="M1_time_value" and not spec["qualified_incremental_edge"],(
        "Structural model selection changed; frozen baseline audit not authorized"
    )
    forward_receipt=json.loads((OUT/"forward_holdout_receipt.json").read_text())
    metadata=json.loads((OUT/"forward_holdout_manifest.json").read_text())
    assert forward_receipt["cohort_size"]==len(metadata)==200
    expected=forward_receipt["ordered_id_sha256"]
    ids=[r["match_id"] for r in metadata]
    assert hashlib.sha256(json.dumps(ids,separators=(",",":")).encode()).hexdigest()==expected
    older=json.loads((BASE/"manifest_metadata.json").read_text())
    original_ids={x["match_id"] for x in older}
    orig_series={x["series_id"] for x in older if x["series_id"]>0}
    assert not original_ids.intersection(ids)
    assert not orig_series.intersection(
        x["series_id"] for x in metadata if x["series_id"]>0
    )

    api=N["OpenDota"](cache_dir=BASE/"api-cache",interval=1.65)
    originals=[api.get("/matches/"+str(int(r["match_id"]))) for r in older]
    forward=[api.get("/matches/"+str(int(r["match_id"]))) for r in metadata]
    assert api.calls==0,"No network calls during frozen evaluation"
    assert all(N["usable"](g) for g in originals+forward)
    assert len({g["match_id"] for g in forward})==200
    for game,row in zip(forward,metadata):
        assert int(game["match_id"])==row["match_id"]
        assert int(game["start_time"])==row["start_time"]
        assert str(game["patch"])=="60"
    checked=feature_cutoff_audit(forward)
    train=N["make_minute_table"](originals)
    test=N["make_minute_table"](forward)
    assert train.match_id.nunique()==500 and test.match_id.nunique()==200
    base_cols=N["SETS"]["M0_gold_only"]
    model_cols=N["SETS"]["M1_time_value"]
    base=N["fit_model"](train,base_cols)
    new=N["fit_model"](train,model_cols)
    p_base=base.predict_proba(test[base_cols])[:,1]
    p_new=new.predict_proba(test[model_cols])[:,1]

    preds=test[["match_id","minute","radiant_win"]].copy().reset_index(drop=True)
    preds["series_id"]=preds.match_id.map({x["match_id"]:x["series_id"] for x in metadata})
    preds["p_baseline"]=p_base
    preds["p_model"]=p_new
    y=preds.radiant_win.to_numpy(dtype=int)
    for name,p in (("model",p_new),("baseline",p_base)):
        prob=np.clip(p,1e-15,1-1e-15)
        preds["logloss_"+name]=-(y*np.log(prob)+(1-y)*np.log1p(-prob))
        preds["brier_"+name]=(prob-y)**2
        preds["correct_"+name]=((p>=.5).astype(int)==y).astype(int)
    phases=[("overall",preds),
            ("0-9",preds[preds.minute<=9]),
            ("10-19",preds[(preds.minute>=10)&(preds.minute<=19)]),
            ("20-29",preds[(preds.minute>=20)&(preds.minute<=29)]),
            ("30+",preds[preds.minute>=30])]
    rows=[]
    for phase,win in phases:
        for metric in ("logloss","brier"):
            unc=paired_interval(win,metric,"match_id")
            series=paired_interval(win,metric,"series_id")
            rows.append(dict(phase=phase,metric=metric,minute_rows=len(win),
                             matches=win.match_id.nunique(),
                             baseline=float(win[metric+"_baseline"].mean()),
                             model=float(win[metric+"_model"].mean()),
                             delta=unc["delta"],ci_lo=unc["lo"],ci_hi=unc["hi"],
                             series_clusters=series["clusters"],
                             series_ci_lo=series["lo"],series_ci_hi=series["hi"]))
    scores=pd.DataFrame(rows)
    acc=pd.DataFrame([
        dict(phase=phase,matches=win.match_id.nunique(),minute_rows=len(win),
             acc_baseline=win.correct_baseline.mean(),
             acc_model=win.correct_model.mean())
        for phase,win in phases
    ])
    calibration=[]
    for name in ("baseline","model"):
        prob=preds["p_"+name].to_numpy()
        bins=np.clip(np.searchsorted(np.linspace(0,1,11),prob,side="right")-1,0,9)
        for b in range(10):
            sel=(bins==b)
            if not sel.any():continue
            calibration.append(dict(model=name,bin=b,minute_rows=int(sel.sum()),
                                    matches=int(preds.loc[sel,"match_id"].nunique()),
                                    mean_probability=float(prob[sel].mean()),
                                    observed_win_rate=float(y[sel].mean())))
    cal=pd.DataFrame(calibration)
    match_mean=preds.groupby("match_id")[[
        "logloss_model","logloss_baseline","brier_model","brier_baseline"
    ]].mean()
    equal_match={metric:float((match_mean[metric+"_model"]-
                               match_mean[metric+"_baseline"]).mean())
                 for metric in ("logloss","brier")}

    print("INDEPENDENT_FORWARD_BASELINE_REPLICATION")
    print(scores.to_string(index=False,float_format=lambda n:f"{n:.6f}"))
    print("EXTERNAL_ACCURACY")
    print(acc.to_string(index=False,float_format=lambda n:f"{n:.6f}"))
    print("EQUAL_MATCH_DIFFERENCES",equal_match)
    print("EXTERNAL_CALIBRATION",cal.to_string(index=False,float_format=lambda n:f"{n:.4f}"))
    print("PIT_CHECKS",checked,"NO_NETWORK",api.calls==0)
    scores.to_csv(OUT/"forward_baseline_scores.csv",index=False)
    acc.to_csv(OUT/"forward_baseline_accuracy.csv",index=False)
    cal.to_csv(OUT/"forward_baseline_calibration.csv",index=False)
    preds.to_csv(OUT/"forward_baseline_predictions.csv",index=False)
    (OUT/"forward_evaluation_receipt.json").write_text(json.dumps({
        "not_new_structural_candidate":"M1_time_value_vs_M0_gold_only_only",
        "forward_manifest_sha256":expected,"external_games":len(forward),
        "forward_minute_rows":len(preds),"prior_games":len(originals),
        "pit_checks":checked,"http_calls":api.calls,
        "equal_match_deltas":equal_match,
        "model_selected_before_external_labels":spec["selection"],
        "seed":SEED,"bootstrap":BOOTS
    },sort_keys=True,indent=2)+"\n")
    print("FORWARD_BASELINE_REPLICATION_COMPLETE",flush=True)

if __name__=="__main__":
    main()
