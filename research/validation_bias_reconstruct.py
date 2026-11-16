#!/usr/bin/env python3
"""Reconstruct *already selected* validation M0/M1 forecasts from 500 cached raw matches.

Uses the original frozen notebook's exact cohort, chronological series split,
point-in-time feature extraction and TRAIN-fitted M0/M1 pipeline. This makes
no new model, re-selection, calibration fit, or held-out TEST claim. Requires
the author's separately retained raw source cache, not bundled with ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import gzip
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research/posttest_temporal"))
from collect_and_score import frozen_functions,models_from_frozen_train,sha

EXPECTED_NOTEBOOK_RESULTS={
    "M0_logloss":.532490,
    "M1_logloss":.519714,
    "M0_brier":.181075,
    "M1_brier":.175902,
}
SOURCE_SEED=20261116

def load_original_500(cache:Path):
    notebook=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
    cell4="".join(notebook["cells"][4]["source"])
    fragment=cell4.split("\nclass MatchNotFound(",1)[0]
    if "FROZEN_MATCH_IDS = (" not in fragment:
        raise ValueError("Notebook has no frozen cohort")
    ns={}
    exec(compile(fragment,"frozen_ids_from_original_notebook","exec"),ns)
    ids=ns["FROZEN_MATCH_IDS"]
    if len(ids)!=500 or len(set(ids))!=500:
        raise ValueError("Expected original 500 unique frozen IDs")
    matches=[]
    for mid in ids:
        name=sha(json.dumps(["/matches/"+str(mid),{}],sort_keys=True).encode())+".json.gz"
        file=cache/name
        if not file.is_file():
            raise FileNotFoundError("Missing original raw cache for "+str(mid))
        with gzip.open(file,"rt") as f:
            match=json.load(f)
        if match.get("match_id")!=mid:
            raise ValueError("Wrong match identity: "+str(mid))
        matches.append(match)
    return notebook,matches

def split_from_original_code(notebook,matches):
    info=pd.DataFrame([{
        "match_id":int(m["match_id"]),"start_time":int(m["start_time"]),
        "patch":str(m.get("patch")), "series_id":int(m.get("series_id") or 0),
        "duration":int(m["duration"]),"radiant_win":int(m["radiant_win"])
    } for m in matches])
    cell10="".join(notebook["cells"][10]["source"])
    definition=cell10.split("\nmanifest = series_safe_split(manifest)",1)[0]
    if "def series_safe_split(" not in definition:
        raise ValueError("Cannot load exact series-safe splitter")
    ns={"np":np}
    exec(compile(definition,"original_notebook_split_code","exec"),ns)
    split=ns["series_safe_split"](info)
    expected={"train":291,"validation":103,"test":106}
    if split.groupby("partition").size().to_dict()!=expected:
        raise ValueError("Original split counts changed")
    return split

def proper_loss(y,p):
    return -(y*np.log(np.clip(p,1e-15,1.-1e-15))+
             (1-y)*np.log1p(-np.clip(p,1e-15,1.-1e-15)))

def ece(y,p,bins=10):
    bucket=np.clip((p*bins).astype(int),0,bins-1)
    total=0.
    for i in range(bins):
        has=bucket==i
        if np.any(has):
            total+=float(np.mean(has)*abs(np.mean(y[has])-np.mean(p[has])))
    return total

def run(cache:Path,dest:Path,receipt:Path):
    if dest.exists() or receipt.exists():
        raise FileExistsError("Never silently replace previously published validation audit")
    notebook,matches=load_original_500(cache)
    split=split_from_original_code(notebook,matches)
    ids=set(split.loc[split.partition=="validation","match_id"].astype(int))
    if len(ids)!=103:raise AssertionError("Unexpected validation IDs")
    funcs=frozen_functions()
    subset=[m for m in matches if int(m["match_id"]) in ids]
    minute=funcs["make_minute_table"](subset)
    if len(minute)!=3781 or minute.match_id.nunique()!=103:
        raise ValueError("Original validation feature count drift")
    aux=split.loc[split.partition=="validation",
                  ["match_id","series_id","patch","start_time","radiant_win","duration"]]
    frame=minute.merge(aux,on="match_id",validate="many_to_one",suffixes=("","_meta"))
    # Rebuild original TRAIN-only M0/M1 fits; TEST source metadata was
    # read to reproduce the split, but TEST rows are not featurized,
    # fitted to, predicted or scored by this diagnostic.
    models,features,fingerprints=models_from_frozen_train()
    for name,model in models.items():
        frame["p_"+name]=model.predict_proba(frame[features[name]])[:,1]
    frame=frame.sort_values(["match_id","minute"],kind="mergesort").reset_index(drop=True)
    if not (frame.groupby("match_id").minute.min()==0).all():
        raise ValueError("Forecast must begin at game-minute zero")
    if not (frame.minute*60<frame.duration).all():
        raise ValueError("Terminal leak from original validation")
    if not (frame.patch.astype(str)=="60").all():
        raise ValueError("Expected patch-60 validation cohort")
    groups=np.where(frame.series_id.to_numpy(dtype=int)>0,
                    "s"+frame.series_id.astype(str).to_numpy(),
                    "m"+frame.match_id.astype(str).to_numpy())
    group_keys,index=np.unique(groups,return_inverse=True)
    y=frame.radiant_win.to_numpy(dtype=int)
    metrics={}
    for name in ("M0","M1"):
        p=frame["p_"+name].to_numpy(dtype=float)
        metrics[name]={
            "logloss":float(proper_loss(y,p).mean()),
            "brier":float(((p-y)**2).mean()),
            "ece_10bin_descriptive":float(ece(y,p)),
            "mean_predicted_minute_weighted":float(p.mean()),
            "bias_predicted_minus_observed_minute":float((p-y).mean()),
            "bias_predicted_minus_observed_equal_game":float(
                (frame.assign(res=p-y).groupby("match_id").res.mean()).mean()
            )
        }
        for key,expected in (("logloss",EXPECTED_NOTEBOOK_RESULTS[name+"_logloss"]),
                             ("brier",EXPECTED_NOTEBOOK_RESULTS[name+"_brier"])):
            if abs(metrics[name][key]-expected)>=5e-7:
                raise ValueError("Frozen notebook validation "+name+" "+key+" mismatch")
    counts=np.bincount(index).astype(float)
    cluster_bias=np.stack([
        np.bincount(index,weights=(frame["p_"+name]-y).to_numpy(),minlength=len(group_keys))
        for name in ("M0","M1")],axis=1)
    gameavg=frame.assign(res0=frame.p_M0-y,res1=frame.p_M1-y).groupby(
        ["match_id"],sort=True)[["res0","res1"]].mean()
    games_meta=aux.set_index("match_id").loc[gameavg.index].copy()
    per_game_key=np.where(games_meta.series_id.to_numpy(dtype=int)>0,
        "s"+games_meta.series_id.astype(str).to_numpy(),
        "m"+games_meta.index.astype(str).to_numpy())
    indexes={key:i for i,key in enumerate(group_keys)}
    per_game_cluster=np.array([indexes[k] for k in per_game_key],dtype=int)
    gamecounts=np.bincount(per_game_cluster,minlength=len(group_keys)).astype(float)
    game_bias=np.stack([
        np.bincount(per_game_cluster,weights=gameavg[name],minlength=len(group_keys))
        for name in ("res0","res1")],axis=1)
    rng=np.random.default_rng(SOURCE_SEED)
    draws=rng.integers(0,len(group_keys),size=(10000,len(group_keys)))
    minutes_den=counts[draws].sum(axis=1)
    game_den=gamecounts[draws].sum(axis=1)
    for index_name,name in enumerate(("M0","M1")):
        row_distribution=cluster_bias[:,index_name][draws].sum(axis=1)/minutes_den
        game_distribution=game_bias[:,index_name][draws].sum(axis=1)/game_den
        metrics[name]["bias_minute_ci_95_series"]=[
            float(x) for x in np.quantile(row_distribution,[.025,.975])]
        metrics[name]["bias_equal_game_ci_95_series"]=[
            float(x) for x in np.quantile(game_distribution,[.025,.975])]
    cols=["match_id","minute","radiant_win","series_id","patch","p_M0","p_M1"]
    dest.parent.mkdir(parents=True,exist_ok=True)
    frame[cols].to_csv(dest,index=False,float_format="%.17g",lineterminator="\n")
    score={
        "status":"FROZEN_ORIGINAL_VALIDATION_POST_SELECTION_BIAS_AUDIT",
        "analysis_is_post_selection_and_descriptive":True,
        "original_frozen_500_raw_matches":500,
        "original_train_games":291,
        "original_validation_games":103,
        "original_test_games_not_scored":106,
        "validation_minute_rows":len(frame),
        "validation_series_or_singletons":len(group_keys),
        "patch_counts":frame.groupby("patch").match_id.nunique().astype(int).to_dict(),
        "win_rate_per_game":float(aux.radiant_win.mean()),
        "win_rate_per_minute_row":float(y.mean()),
        "train_game_win_rate_from_frozen_csv":float(pd.read_csv(ROOT/"research/frozen_original_train_features.csv.gz").groupby("match_id").radiant_win.first().mean()),
        "model_fingerprints":fingerprints,
        "bootstrap_draws":10000,
        "bootstrap_seed":SOURCE_SEED,
        "bootstrap_unit":"positive professional series ID, otherwise singleton match",
        "models":metrics,
        "validation_forecasts_sha256":sha(dest.read_bytes()),
        "no_TEST_recalibration_or_score":True,
        "raw_cache_required_only_for_source_reconstruction":True,
        "source_validation_ids":[int(m) for m in sorted(ids)],
    }
    receipt.write_text(json.dumps(score,sort_keys=True,indent=2)+"\n")
    print("PASS validation source reconstruction",len(frame),"rows",len(group_keys),"clusters")
    print(json.dumps({
        "win_rate_validation":score["win_rate_per_minute_row"],
        "score_M0":metrics["M0"],
        "score_M1":metrics["M1"],
        "receipt":str(receipt)
    },indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-cache",type=Path,required=True)
    ap.add_argument("--output-predictions",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    run(a.source_cache,a.output_predictions,a.receipt)
