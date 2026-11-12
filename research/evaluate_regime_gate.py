#!/usr/bin/env python3
"""One-shot third-cohort stage-shrinkage test, never fits on confirmation data."""
from __future__ import annotations
import hashlib
import json
import gzip
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.regime_gate import gate, weight
from tests.test_notebook_contracts import load_definitions

N=load_definitions()
BASE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
PREV=Path("/home/ai-agent/.cache/vexil-edge-v2-20261113")
OUT=Path("/home/ai-agent/.cache/vexil-edge-v3-20261113")
SEED=20261113
BOOTS=10000


def cluster_vector(data,group="series"):
    if group=="match":
        groups=pd.factorize(data.match_id.astype(str),sort=False)[0]
    else:
        keys=[("series",int(s)) if int(s)>0 else ("match",int(mid))
              for s,mid in zip(data.series_id,data.match_id)]
        groups=pd.factorize(pd.Series(keys,dtype="object"),sort=False)[0]
    x=data.assign(group=groups)
    g=x.groupby("group",sort=True).agg(
        n=("minute","size"),
        base=("ll_base","sum"),
        full=("ll_m1","sum"),
        gated=("ll_gate","sum")
    )
    return g[["n","base","full","gated"]].to_numpy(dtype=float)


def two_way_simultaneous_interval(data,group="series"):
    """Max-t 95% familywise CI across gate-minus-M0 and gate-minus-M1."""
    a=cluster_vector(data,group=group)
    obs=np.array([(a[:,3]-a[:,1]).sum()/a[:,0].sum(),
                  (a[:,3]-a[:,2]).sum()/a[:,0].sum()])
    rng=np.random.default_rng(SEED)
    inds=rng.integers(0,len(a),size=(BOOTS,len(a)))
    sample=a[inds].sum(axis=1)
    b=np.column_stack(((sample[:,3]-sample[:,1])/sample[:,0],
                       (sample[:,3]-sample[:,2])/sample[:,0]))
    std=np.maximum(b.std(axis=0,ddof=1),1e-12)
    t=np.max(np.abs((b-obs[None,:])/std[None,:]),axis=1)
    q=float(np.quantile(t,.95))
    rows=[]
    for i,against in enumerate(("M0_gold_only","M1_time_value")):
        lo,hi=np.quantile(b[:,i],[.025,.975])
        rows.append({
            "comparison":"GATE_minus_"+against,
            "difference":float(obs[i]),
            "unadjusted_lo":float(lo),"unadjusted_hi":float(hi),
            "simultaneous_95_lo":float(obs[i]-q*std[i]),
            "simultaneous_95_hi":float(obs[i]+q*std[i]),
            "grouping":group,"clusters":len(a),
            "bootstrap_reps":BOOTS,"seed":SEED
        })
    return pd.DataFrame(rows)


def main():
    # Final confirmation is a single-shot evaluation, never a tuning loop.
    lock_path=OUT/"gate_confirmation_consumed.lock.json"
    result_path=OUT/"gate_confirmation_evaluation_receipt.json"
    if lock_path.exists() or result_path.exists():
        raise RuntimeError("Confirmation cohort already consumed; refuse to rerun")
    committed_manifest=ROOT/"research/gate_confirmation_manifest.json"
    committed_receipt=ROOT/"research/gate_confirmation_manifest_receipt.json"
    if not committed_manifest.exists() or not committed_receipt.exists():
        raise RuntimeError("Manifest must be committed before reading holdout results")
    repo_receipt=json.loads(committed_receipt.read_text())
    manifest_bytes=committed_manifest.read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest()==repo_receipt["full_manifest_sha256"]
    assert (OUT/"gate_confirmation_manifest.json").read_bytes()==manifest_bytes
    repo_head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    dirty=subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain"],text=True)
    assert not dirty, "Repository must be clean and manifest committed"
    metadata=json.loads((OUT/"gate_confirmation_manifest.json").read_text())
    receipt=json.loads((OUT/"gate_confirmation_manifest_receipt.json").read_text())
    assert receipt["ordered_id_sha256"]==repo_receipt["ordered_id_sha256"]
    assert len(metadata)==receipt["cohort_size"]==repo_receipt["cohort_size"]==200
    ids=[int(x["match_id"]) for x in metadata]
    assert hashlib.sha256(json.dumps(ids,separators=(",",":")).encode()).hexdigest()==receipt["ordered_id_sha256"]
    older=json.loads((BASE/"manifest_metadata.json").read_text())
    earlier=json.loads((PREV/"forward_holdout_manifest.json").read_text())
    assert len(older)==500 and len(earlier)==200
    original_manifest_ids=[int(x["match_id"]) for x in older]
    assert hashlib.sha256(json.dumps(original_manifest_ids).encode()).hexdigest()==(
        "f2be53e16ae29df1f62aa9907187fdba846d9af9fb7a3f69e7dd7504be43b776"
    )
    assert max(int(m["start_time"]) for m in older) < min(int(m["start_time"]) for m in metadata)
    prior_ids={int(x["match_id"]) for x in older+earlier}
    prior_series={int(x["series_id"]) for x in older+earlier if int(x["series_id"])>0}
    assert not prior_ids.intersection(ids)
    assert not prior_series.intersection(x["series_id"] for x in metadata if x["series_id"]>0)
    assert all(x["patch"]=="60" for x in metadata)
    assert all(x["start_time"]>max(r["start_time"] for r in earlier) for x in metadata)

    # Prohibit a network request even on a cache miss or corrupted file.
    cache_root=BASE/"api-cache"
    for mid in [int(r["match_id"]) for r in older+metadata]:
        request_key=hashlib.sha256(
            json.dumps(["/matches/"+str(mid),{}],sort_keys=True).encode()
        ).hexdigest()
        path=cache_root/(request_key+".json.gz")
        if not path.exists():
            raise RuntimeError("Missing frozen match in cache: "+str(mid))
        try:
            with gzip.open(path,"rt",encoding="utf8") as stream:
                payload=json.load(stream)
            assert isinstance(payload.get("radiant_gold_adv"),list) and len(payload["radiant_gold_adv"])>0
        except (OSError,EOFError,ValueError,AssertionError) as exc:
            raise RuntimeError("Corrupt frozen cache entry: "+str(mid)) from exc
    api=N["OpenDota"](cache_dir=cache_root,interval=1.65)
    train_games=[api.get("/matches/"+str(int(x["match_id"]))) for x in older]
    test_games=[api.get("/matches/"+str(int(x["match_id"]))) for x in metadata]
    assert api.calls==0,"No network fetch allowed after third manifest freeze"
    assert all(N["usable"](x) for x in train_games+test_games)
    for source,row in zip(test_games,metadata):
        assert int(source["match_id"])==row["match_id"]
        assert int(source["start_time"])==row["start_time"]
    # PIT check independently on all new games at six cutoffs.
    checks=0
    for match in test_games:
        for t in sorted(set([0,1,5,9,10,11,15,19,20,
                             min(30,int(match["duration"])//60),
                             int(match["duration"])//60])):
            N["assert_same_features"](
                N["snapshot_features"](match,t),
                N["snapshot_features"](N["prefix_truncated"](match,t),t))
            checks+=1

    # START the one-shot gate BEFORE test outcomes are materialized in a frame.
    lock_path.write_text(json.dumps({
        "repo_head":repo_head,
        "full_manifest_sha256":repo_receipt["full_manifest_sha256"],
        "criterion":"frozen gate vs both existing baselines",
        "note":"Do not delete without documenting independent adjudication"
    },indent=2,sort_keys=True)+"\n")
    train=N["make_minute_table"](train_games)
    test=N["make_minute_table"](test_games)
    assert train.match_id.nunique()==500 and test.match_id.nunique()==200
    assert len(train)==sum(int(m["duration"])//60+1 for m in train_games)
    assert len(test)==sum(int(m["duration"])//60+1 for m in test_games)
    base_cols=N["SETS"]["M0_gold_only"]
    m1_cols=N["SETS"]["M1_time_value"]
    m0=N["fit_model"](train,base_cols)
    m1=N["fit_model"](train,m1_cols)
    p0=m0.predict_proba(test[base_cols])[:,1]
    p1=m1.predict_proba(test[m1_cols])[:,1]
    pg=gate(p1,p0,test.minute.to_numpy())
    pred=test[["match_id","minute","radiant_win"]].copy().reset_index(drop=True)
    pred["series_id"]=pred.match_id.map({x["match_id"]:x["series_id"] for x in metadata})
    for name,p in (("base",p0),("m1",p1),("gate",pg)):
        pp=np.clip(p,1e-15,1-1e-15)
        y=pred.radiant_win.to_numpy(dtype=int)
        pred["p_"+name]=p
        pred["ll_"+name]=-(y*np.log(pp)+(1-y)*np.log1p(-pp))
        pred["brier_"+name]=(p-y)**2
        pred["acc_"+name]=((p>=0.5)==y).astype(int)
    pred["weight"]=weight(pred.minute.to_numpy())
    assert pred.weight.between(0,1).all()
    assert not pred[["p_base","p_m1","p_gate"]].isna().any().any()

    estimates=[]
    for label,x in [("overall",pred),
                    ("0-9",pred[pred.minute<10]),
                    ("10-19",pred[(pred.minute>=10)&(pred.minute<20)]),
                    ("20-29",pred[(pred.minute>=20)&(pred.minute<30)]),
                    ("30+",pred[pred.minute>=30])]:
        results={"phase":label,"games":int(x.match_id.nunique()),"rows":len(x)}
        for name in ("base","m1","gate"):
            for metric in ("ll","brier","acc"):
                results[metric+"_"+name]=float(x[metric+"_"+name].mean())
        estimates.append(results)
    summary=pd.DataFrame(estimates)
    uncertainty_match=two_way_simultaneous_interval(pred,group="match")
    uncertainty_series=two_way_simultaneous_interval(pred,group="series")
    # A two-comparison family, no phase search and no post-hoc threshold change.
    overall=summary.loc[summary.phase=="overall"]
    assert len(overall)==1
    delta_brier_base=float(overall.iloc[0]["brier_gate"]-overall.iloc[0]["brier_base"])
    delta_brier_m1=float(overall.iloc[0]["brier_gate"]-overall.iloc[0]["brier_m1"])
    passed=bool(
        (uncertainty_series["difference"]<=-0.005).all()
        and (uncertainty_series["simultaneous_95_hi"]<0).all()
        and delta_brier_base<=0 and delta_brier_m1<=0
    )
    summary.to_csv(OUT/"gate_confirmation_phase_results.csv",index=False)
    uncertainty_match.to_csv(OUT/"gate_confirmation_match_ci.csv",index=False)
    uncertainty_series.to_csv(OUT/"gate_confirmation_series_ci.csv",index=False)
    pred.to_csv(OUT/"gate_confirmation_predictions.csv",index=False)
    result_receipt={
        "hypothesis_registered_commit":"40d8961",
        "evaluation_code_head":repo_head,
        "full_manifest_sha256":repo_receipt["full_manifest_sha256"],
        "source_sha256":{
            name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ("research/regime_gate.py","research/evaluate_regime_gate.py",
                         "research/fetch_gate_confirmation.py")
        },
        "versions":{
            "numpy":np.__version__,"pandas":pd.__version__,
            "sklearn":__import__("sklearn").__version__
        },
        "holdout_manifest_sha256":receipt["ordered_id_sha256"],
        "third_holdout_games":len(test_games),
        "third_holdout_minute_rows":len(pred),
        "original_training_games":len(train_games),
        "prior_exploration_games_not_used_in_training":len(earlier),
        "pit_checks":checks,"http_calls":api.calls,
        "model_decision":"GO" if passed else "HOLD",
        "criterion":"gate must improve log loss by >=0.005 with both simultaneous 95% series-clustered upper bounds <0 and Brier nonworse vs M0 and full M1"
    }
    result_path.write_text(json.dumps(result_receipt,indent=2,sort_keys=True)+"\n")
    # Present the metrics only after all output files and provenance were saved.
    print("THIRD_CONFIRMATION_PHASE_RESULTS")
    print(summary.to_string(index=False,float_format=lambda x:f"{x:.6f}"))
    print("GATE_FAMILYWISE_CI_MATCH_LEVEL")
    print(uncertainty_match.to_string(index=False,float_format=lambda x:f"{x:.6f}"))
    print("GATE_FAMILYWISE_CI_SERIES_LEVEL")
    print(uncertainty_series.to_string(index=False,float_format=lambda x:f"{x:.6f}"))
    print("CANDIDATE_ACCEPTANCE",passed,"Brier_deltas",delta_brier_base,delta_brier_m1)
    print("THIRD_HOLDOUT_PIT_CHECKS",checks,"HTTP_CALLS",api.calls)
    print("GATE_CONFIRMATION_COMPLETE",json.dumps(result_receipt,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
