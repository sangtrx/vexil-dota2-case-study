#!/usr/bin/env python3
"""Three offline, Kaggle-ready verification runs of saved Vexil probabilities.

These runs DO NOT train, query OpenDota, use heldout test data, promote
a model, or manufacture independent evidence. Kaggle must be PRIVATE.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import platform
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

MODEL_IDS=["M1_time_value"]+[f"P{i:02d}" for i in range(1,29)]
SEED=20261113
EPS=1e-15

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_json(p,obj):
    Path(p).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")

def verify_bundle(path):
    metadata=path/"dataset_files_sha256.json"
    assert metadata.is_file(),"Missing immutable input manifest"
    b=json.loads(metadata.read_text())
    assert len(b["files"])>=10
    for name,details in b["files"].items():
        f=path/name
        assert f.is_file(),name
        assert digest(f)==details["sha256"],("input drift",name)
    stability=json.loads((path/"stability_receipt.json").read_text())
    assert stability["input_predictions_sha256"]==digest(path/"dev_validation_predictions_28.csv")
    return b

def load(path):
    df=pd.read_csv(path/"dev_validation_predictions_28.csv")
    score=pd.read_csv(path/"all_28_candidate_scores.csv")
    assert len(df)==3784 and df.match_id.nunique()==103
    assert len(score)==29
    assert set(score.model)==set(MODEL_IDS)
    assert df.partition.eq("validation").all()
    pred=df[["p_"+m for m in MODEL_IDS]].to_numpy(float)
    y=df.radiant_win.to_numpy(int)
    assert np.isfinite(pred).all() and np.isin(y,[0,1]).all()
    p=np.clip(pred,EPS,1-EPS)
    loss=-(y[:,None]*np.log(p)+(1-y[:,None])*np.log1p(-p))
    brier=(pred-y[:,None])**2
    return df,score,loss,brier

def scores_mode(source,out):
    df,score,ll,br=load(source)
    archived=pd.read_csv(source/"calibration_and_phase_scores.csv")
    old=pd.read_csv(source/"all_estimator_weights.csv")
    summary=score.set_index("model")
    result=[]
    phase=np.select([df.minute<=9,df.minute<=19,df.minute<=29],
                    ["0-9","10-19","20-29"],default="30+")
    for j,name in enumerate(MODEL_IDS):
        logloss=float(ll[:,j].mean())
        brier=float(br[:,j].mean())
        assert abs(logloss-summary.loc[name,"logloss"])<1e-12
        assert abs(brier-summary.loc[name,"brier"])<1e-12
        for segment in ("overall","0-9","10-19","20-29","30+"):
            mask=np.ones(len(df),bool) if segment=="overall" else phase==segment
            p=df["p_"+name].to_numpy(float)[mask]
            y=df.radiant_win.to_numpy(int)[mask]
            bins=np.clip(np.floor(p*10).astype(int),0,9)
            ece=sum(((bins==b).sum()/len(p))*abs(p[bins==b].mean()-y[bins==b].mean())
                    for b in range(10) if (bins==b).any())
            a=archived[(archived.model==name)&(archived.phase==segment)]
            assert len(a)==1
            a=a.iloc[0]
            assert mask.sum()==a.rows
            assert abs(ll[mask,j].mean()-a.logloss)<1e-12
            assert abs(br[mask,j].mean()-a.brier)<1e-12
            assert abs(ece-a.ece10_descriptive)<1e-12
            result.append(dict(model=name,phase=segment,rows=int(mask.sum()),
                               logloss=float(ll[mask,j].mean()),
                               brier=float(br[mask,j].mean()),
                               ece10=float(ece)))
        # Alternative estimands from original saved predictions
        x=pd.DataFrame({"match_id":df.match_id,"ll":ll[:,j],"br":br[:,j]})
        pergame=x.groupby("match_id")[["ll","br"]].mean()
        expected=old[old.model==name].iloc[0]
        assert abs(pergame.ll.mean()-expected.equal_match_ll)<1e-12
        assert abs(pergame.br.mean()-expected.equal_match_brier)<1e-12
    pd.DataFrame(result).to_csv(out/"k1_recomputed_145_phase_metrics.csv",index=False)
    return dict(verified_models=29,verified_model_scores=58,verified_phase_rows=145,
                original_validation_matches=103,minute_rows=3784,
                M1_ll=float(ll[:,0].mean()),P20_ll=float(ll[:,MODEL_IDS.index("P20")].mean()),
                P20_minus_M1=float((ll[:,MODEL_IDS.index("P20")]-ll[:,0]).mean()))

def instability_mode(source,out):
    df,score,ll,br=load(source)
    meta=pd.read_csv(source/"validation_manifest_for_kaggle.csv")
    assert len(meta)==103
    df=df.merge(meta[["match_id","key","block"]],on="match_id",validate="many_to_one")
    assert df.key.notna().all() and sorted(df.block.unique())==[1,2,3,4,5,6]
    match_ll=pd.DataFrame(ll,columns=MODEL_IDS)
    match_ll["match_id"]=df.match_id
    pergame=match_ll.groupby("match_id").mean().merge(meta[["match_id","block"]],left_index=True,
                right_on="match_id",validate="one_to_one")
    comparisons=[]
    for idx,selection in enumerate(itertools.combinations(range(1,7),3),start=1):
        mask=pergame.block.isin(selection)
        ins=pergame.loc[mask,MODEL_IDS].mean()
        outs=pergame.loc[~mask,MODEL_IDS].mean()
        winner=min(MODEL_IDS,key=lambda k:(float(ins[k]),k))
        ordered=sorted(MODEL_IDS,key=lambda k:(float(outs[k]),k))
        comparisons.append(dict(split=idx,selected=winner,
                                OOS_rank=ordered.index(winner)+1,
                                OOS_worse_m1=int(outs[winner]>outs["M1_time_value"]),
                                rank_below_median=int(ordered.index(winner)+1>15),
                                OOS_dll_vs_M1=float(outs[winner]-outs["M1_time_value"])))
    cscv=pd.DataFrame(comparisons)
    original=pd.read_csv(source/"cscv_20_selections.csv")
    assert len(original)==len(cscv)==20
    assert (cscv.selected.to_numpy()==original.IS_winner.to_numpy()).all()
    assert (cscv.OOS_rank.to_numpy()==original.OOS_rank.to_numpy()).all()
    assert np.max(np.abs(cscv.OOS_dll_vs_M1.to_numpy()-original.OOS_winner_minus_M1.to_numpy()))<1e-12
    groups,keys=pd.factorize(df.key.astype(str),sort=True)
    assert len(keys)==53
    n=np.bincount(groups,minlength=len(keys)).astype(float)
    sums=np.stack([np.bincount(groups,weights=ll[:,j],minlength=len(keys)) for j in range(29)],axis=1)
    rng=np.random.default_rng(SEED)
    rows=[]
    for trial in range(3000):
        count=np.bincount(rng.integers(0,len(keys),len(keys)),minlength=len(keys))
        totals=count@sums
        choice=min(range(29),key=lambda j:(totals[j],MODEL_IDS[j]))
        omitted=np.where(count==0)[0]
        assert len(omitted)>0
        oob=sums[omitted].sum(axis=0)/n[omitted].sum()
        rows.append(dict(draw=trial+1,winner=MODEL_IDS[choice],
                         OOB_dll_vs_M1=float(oob[choice]-oob[0])))
    bs=pd.DataFrame(rows)
    orig_bs=pd.read_csv(source/"series_oob_3000_selection.csv")
    assert (bs.winner.to_numpy()==orig_bs.winner_IS.to_numpy()).all()
    assert np.max(np.abs(bs.OOB_dll_vs_M1.to_numpy()-orig_bs.OOB_winner_minus_M1.to_numpy()))<1e-12
    cscv.to_csv(out/"k2_cscv_20.csv",index=False)
    bs.to_csv(out/"k2_oob_3000.csv",index=False)
    return dict(confirmed_cscv_splits=20,confirmed_bootstrap_draws=3000,
                rank_reversal_frac=float(cscv.rank_below_median.mean()),
                chosen_worse_m1_cscv_frac=float(cscv.OOS_worse_m1.mean()),
                chosen_worse_m1_oob_frac=float((bs.OOB_dll_vs_M1>0).mean()),
                P20_selection_frac=float((bs.winner=="P20").mean()))

def maxt_mode(source,out):
    df,score,ll,br=load(source)
    groups=np.where(df.series_id.astype(int)>0,
                   "s"+df.series_id.astype(str),"m"+df.match_id.astype(str))
    gid,keys=pd.factorize(pd.Series(groups,dtype=object),sort=True)
    assert len(keys)==53
    n=np.bincount(gid,minlength=len(keys)).astype(float)
    differences=ll[:,1:]-ll[:,[0]]
    s=np.stack([np.bincount(gid,weights=differences[:,j],minlength=len(keys))
                for j in range(28)],axis=1)
    observed=s.sum(axis=0)/n.sum()
    rng=np.random.default_rng(SEED)
    samples=rng.integers(0,len(keys),size=(5000,len(keys)))
    boot=s[samples].sum(axis=1)/n[samples].sum(axis=1)[:,None]
    std=boot.std(axis=0,ddof=1)
    assert np.all(std>0)
    max_t=np.max(np.abs((boot-observed)/std),axis=1)
    multiplier=float(np.quantile(max_t,.95))
    expected=pd.read_csv(source/"familywise_simultaneous_ci.csv").set_index("model")
    records=[]
    for j,model in enumerate(MODEL_IDS[1:]):
        row=expected.loc[model]
        low=float(observed[j]-multiplier*std[j])
        high=float(observed[j]+multiplier*std[j])
        assert abs(observed[j]-row.series_grouped_delta_ll)<1e-12
        assert abs(low-row.maxT_familywise95_low)<1e-12
        assert abs(high-row.maxT_familywise95_high)<1e-12
        records.append(dict(model=model,delta_ll=float(observed[j]),
                            familywise95_low=low,familywise95_high=high))
    pd.DataFrame(records).to_csv(out/"k3_maxt_28_ci.csv",index=False)
    # Source ledger also verifies human-transparent incomplete family accounting.
    ledger=pd.read_csv(source/"known_trial_ledger.csv")
    assert len(ledger)==38 and ledger.trial_id.nunique()==38
    return dict(verified_comparisons=28,bootstrap_draws=5000,
                model_familywise95_multiplier=multiplier,
                all_28_ci_parity=True,known_trial_attempts=38,
                independence_of_38_trials_not_claimed=True)

def chronology_mode(source,out):
    # Recompute the group/time overlap check from frozen 103-match
    # metadata; no network, training or external test dataset.
    matches=pd.read_csv(source/"validation_approx_intervals.csv")
    series=pd.read_csv(source/"series_approx_intervals.csv")
    expected_comp=pd.read_csv(source/"chronology_components.csv")
    overlap=pd.read_csv(source/"old_six_bucket_overlap_audit.csv")
    prior_scores=pd.read_csv(source/"chronology_4component_scores.csv")
    timeblocks=pd.read_csv(source/"time_blocks.csv")
    assert len(matches)==103 and len(series)==53
    assert matches.match_id.nunique()==103 and len(expected_comp)==4
    assert sorted(expected_comp.games.astype(int).tolist())==[2,3,36,62]
    recompute=matches.groupby("key").agg(
        first_start=("start_time","min"),
        last_approx_end=("approx_end","max"),
        games=("match_id","size")).reset_index()
    for key in ("first_start","last_approx_end","games"):
        aligned=recompute.set_index("key")[key].sort_index()
        original=series.set_index("key")[key].sort_index()
        assert np.array_equal(aligned.to_numpy(),original.to_numpy())
    ordered=series.sort_values(["first_start","key"],kind="mergesort")
    cid=[];last=-1;counter=0
    for row in ordered.itertuples():
        if row.first_start>last:
            counter+=1
        last=max(last,row.last_approx_end)
        cid.append(counter)
    assert counter==4
    assert np.array_equal(np.asarray(cid),ordered.component.astype(int).to_numpy())
    joined=series.merge(timeblocks[["key","block"]],on="key",validate="one_to_one")
    overlaps=[]
    for k in range(1,6):
        prev=joined[joined.block==k]
        later=joined[joined.block==k+1]
        overlaps.append(int(prev.last_approx_end.max()>later.first_start.min()))
    assert sum(overlaps)==4
    assert np.array_equal(np.asarray(overlaps),overlap.intervals_overlap.astype(int))
    df,_,ll,_=load(source)
    vals=df.merge(matches[["match_id","key"]],on="match_id",validate="many_to_one")
    vals=vals.merge(series[["key","component"]],on="key",validate="many_to_one")
    assert len(vals)==3784
    audited=[]
    old=prior_scores.set_index(["component","model"])
    for component in sorted(vals.component.unique()):
        mask=(vals.component.to_numpy()==component)
        current=ll[mask].mean(axis=0)
        for j,model in enumerate(MODEL_IDS):
            row=old.loc[(component,model)]
            assert abs(row.logloss-current[j])<1e-12
            assert row.games==vals.loc[mask,"match_id"].nunique()
            audited.append(dict(component=int(component),model=model,
                                games=int(row.games),logloss=float(current[j])))
    pd.DataFrame(audited).to_csv(out/"k4_chronology_116_scores.csv",index=False)
    return dict(verified_match_intervals=103,verified_series=53,
                approximate_disjoint_components=4,
                approximate_component_games=[62,2,3,36],
                overlapping_boundaries_in_prior_six_buckets=4,
                out_of_5_boundaries=5,
                verified_component_model_scores=116,
                actual_wallclock_end_times_not_available=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=["scores","instability","maxt","chronology"])
    p.add_argument("--input-dir",required=True)
    p.add_argument("--output-dir",required=True)
    a=p.parse_args()
    source=Path(a.input_dir)
    bundle=verify_bundle(source)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    cases={"scores":scores_mode,"instability":instability_mode,"maxt":maxt_mode,"chronology":chronology_mode}
    result=cases[a.mode](source,out)
    receipt={
        "mode":a.mode,"status":"PASS","run_location":"kaggle" if
            (Path("/kaggle/working").is_dir() and bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))) else "local",
        "kaggle_execution_env_detected":bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE")),
        "dataset_manifest_sha256":digest(source/"dataset_files_sha256.json"),
        "verification_script_sha256":digest(Path(__file__)),
        "stability_source_sha256":digest(source/"stability.py"),
        "packaged_from_source_head":bundle["source_repository_head_at_packaging"],
        "numpy_version":np.__version__,"pandas_version":pd.__version__,
        "python_version":platform.python_version(),
        "seed":SEED,
        "source_prediction_sha256":digest(source/"dev_validation_predictions_28.csv"),
        "source_known_trial_ledger_sha256":digest(source/"known_trial_ledger.csv"),
        "not_new_blind_data":True,
        "no_model_fit":True,
        "results":result
    }
    write_json(out/("kaggle_"+a.mode+"_receipt.json"),receipt)
    print("KAGGLE_BIBLE_QA_DONE",json.dumps(receipt,sort_keys=True))

if __name__=="__main__":
    main()
