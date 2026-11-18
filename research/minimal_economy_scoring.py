#!/usr/bin/env python3
"""Three frozen small-model hypotheses: normalized earned gold, asinh, match weighting.

TRAIN-only March fits; October and November reused cohorts are retrospective
falsification only, NOT fresh blind evidence or employer delivery.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from all_family_models import verify_original_artifacts
from oct_nov_feature_transfer import SCOPE, load_raw_octnov
from rich_feature_engineering import source_key
from rich_feature_models import create_pipeline, load_train, proper
from role_dynamics_features import CACHE, team_array
from train_time_effect_ci import cluster_ids

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT/"research/MINIMAL_ECONOMY_SCORE_PROTOCOL_20261118.md"
EXISTING = ROOT/"research/OCT_NOV_FEATURE_TRANSFER_RECEIPT.json"
PROVENANCE = ROOT/"research/RICH_FEATURE_RAW_PROVENANCE.json"
OUT = ROOT/"research/MINIMAL_ECONOMY_SCORE_RECEIPT.json"
READOUT = ROOT/"research/MINIMAL_ECONOMY_SCORE_READOUT.md"
DRAWS = 5000
SEED = 20261118
BASE=("M0_gold","M1_interaction","Q1_path")
NEW=("E_SHARE1","SAT_ASINH3","MATCH_EQUAL")
MODELS=BASE+NEW
M1=("gold_k","minute10","gold_x_time")
Q1=("gold_k","minute10","adverse_excursion10_k",
    "signed_realized_vol10_k","directional_efficiency10")
INPUTS={
    "M0_gold":("gold_k",),
    "M1_interaction":M1,
    "Q1_path":Q1,
    "E_SHARE1":M1+("earned_share_lead",),
    "SAT_ASINH3":("gold_asinh_3k","minute10","gold_asinh_x_time"),
    "MATCH_EQUAL":M1,
}


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_earned_share(r:np.ndarray,d:np.ndarray,minute:int)->float:
    """Five-by-time earned-gold arrays; uses prefix index t only."""
    a,b=np.asarray(r,dtype=float),np.asarray(d,dtype=float)
    if (not isinstance(minute,(int,np.integer)) or minute<0
        or a.ndim!=2 or b.ndim!=2 or a.shape[0]!=5 or b.shape[0]!=5
        or a.shape[1]<=minute or b.shape[1]<=minute):
        raise ValueError("Invalid exactly-five-per-side positive prefix")
    x,y=a[:,minute],b[:,minute]
    if (not np.isfinite(x).all() or not np.isfinite(y).all()
        or np.any(x<0) or np.any(y<0)):
        raise ValueError("Missing or negative player earned gold at as-of minute")
    u,v=float(x.sum()),float(y.sum())
    ret=(u-v)/(u+v+1000.0)
    if not np.isfinite(ret) or abs(ret)>1.0:
        raise AssertionError("Relative earned gold feature invalid")
    return float(ret)


def sat_asinh(df:pd.DataFrame)->pd.DataFrame:
    if not {"gold_k","minute10"}.issubset(df):
        raise ValueError("Missing original inputs")
    x=df.copy()
    z=np.arcsinh(x.gold_k.to_numpy(float)/3.)
    m=x.minute10.to_numpy(float)
    if not np.isfinite(z).all() or not np.isfinite(m).all() or (m<0).any():
        raise AssertionError("Original gold path invalid")
    x["gold_asinh_3k"]=z
    x["gold_asinh_x_time"]=z*np.log1p(m)
    if not np.isfinite(x[["gold_asinh_3k","gold_asinh_x_time"]].to_numpy()).all():
        raise AssertionError("Asinh overflow")
    return x


def match_equal_weights(train:pd.DataFrame)->np.ndarray:
    if "match_id" not in train or "minute" not in train:
        raise ValueError("Missing match-group training scope")
    if train[["match_id","minute"]].duplicated().any():
        raise AssertionError("Duplicate decision in weighting")
    counts=train.groupby("match_id").match_id.transform("size")
    nrows,nmatch=len(train),train.match_id.nunique()
    if nrows!=10675 or nmatch!=291 or (counts<1).any():
        raise AssertionError("Not frozen original 291 TRAIN matches")
    weights=(nrows/(nmatch*counts.to_numpy(float))).astype(float)
    check=pd.DataFrame({"m":train.match_id,"w":weights}).groupby("m").w.sum()
    if not np.isfinite(weights).all() or not np.allclose(check,check.iloc[0],rtol=0,atol=1e-10):
        raise AssertionError("Unequal per-game total fit weights")
    if not np.isclose(weights.sum(),nrows,rtol=0,atol=1e-9):
        raise AssertionError("Unexpected L2 penalty scale after weighting")
    return weights


def attach_economy_share(
    frame:pd.DataFrame,source_folder:Path,
    train_scope:bool
)->tuple[pd.DataFrame,dict]:
    if frame[["match_id","minute"]].duplicated().any():
        raise AssertionError("Duplicate game-minute")
    if train_scope and (len(frame)!=10675 or frame.match_id.nunique()!=291
                        or set(frame.partition)!={"train"}):
        raise AssertionError("Train read crossed frozen March scope")
    result=frame.copy()
    shares=np.full(len(frame),np.nan,dtype=float)
    original_indices={index:i for i,index in enumerate(frame.index)}
    raw_digest=[]
    team_checks=0
    side_checks=0
    source_checks=0
    for match,part in frame.groupby("match_id",sort=False):
        mid=int(match)
        file=(source_folder/(source_key(mid)+".json.gz")) if train_scope else (
            source_folder/(str(mid)+".json.gz"))
        packed=file.read_bytes()
        if train_scope:
            raw_digest.append([mid,hashlib.sha256(packed).hexdigest()])
        raw=json.loads(gzip.decompress(packed))
        if int(raw["match_id"])!=mid:
            raise AssertionError("Wrong raw match file")
        r=team_array(raw,"gold_t",1)
        d=team_array(raw,"gold_t",-1)
        if r.shape[1]!=d.shape[1]:
            raise AssertionError("Source player clock mismatch")
        gold=np.asarray(raw["radiant_gold_adv"],dtype=float)
        for j,row in part.iterrows():
            t=int(row.minute)
            if t>=len(gold) or t>=r.shape[1] or t*60>=int(raw["duration"]):
                raise AssertionError("Out-of-bounds or terminal as-of time")
            snapshot_diff=float(r[:,t].sum()-d[:,t].sum())
            if abs(snapshot_diff-float(gold[t]))>1e-9:
                raise AssertionError("Team gold not equal sum of player earned gold")
            if abs(snapshot_diff/1000-float(row.gold_k))>1e-9:
                raise AssertionError("Original gold_k transformed or mismatched")
            v=relative_earned_share(r,d,t)
            if abs(v+relative_earned_share(d,r,t))>1e-12:
                raise AssertionError("Side-swapped earned-share feature not odd")
            shares[original_indices[j]]=v
            team_checks+=1
            side_checks+=1
        source_checks+=1
    if train_scope:
        digest=hashlib.sha256(json.dumps(
            sorted(raw_digest),sort_keys=True,separators=(",",":")).encode()).hexdigest()
        expected=json.loads(PROVENANCE.read_text())["source_payload_bytes_sha256"]
        if digest!=expected:
            raise AssertionError("Original frozen 291 raw payloads differ")
    else:
        digest=None
    if (not np.isfinite(shares).all() or team_checks!=len(frame)
        or source_checks!=frame.match_id.nunique()):
        raise AssertionError("Incomplete as-of share source coverage")
    result["earned_share_lead"]=shares
    return result,{
        "unique_matches":source_checks,
        "asof_minutes_checked":team_checks,
        "team_earned_gold_parity_checks":team_checks,
        "side_swap_checks":side_checks,
        "march_raw_digest_if_applicable":digest,
        "true_received_at_verified":False,
    }


def grouped_delta(df:pd.DataFrame,name:str,against:str,draws:np.ndarray)->dict:
    delta=(df["ll_"+name]-df["ll_"+against]).to_numpy(float)
    db=(df["br_"+name]-df["br_"+against]).to_numpy(float)
    group=cluster_ids(df[["match_id","series_id"]])
    table=pd.DataFrame({"cluster":group,"n":1,"sl":delta,"sb":db})
    g=table.groupby("cluster",sort=True)[["n","sl","sb"]].sum().to_numpy(float)
    if draws.shape!=(DRAWS,len(g)):
        raise AssertionError("Source group bootstrap mismatch")
    sums=g[draws].sum(axis=1)
    v=sums[:,1:]/sums[:,0,None]
    lo95,hi95=np.quantile(v[:,0],[.025,.975])
    # 12 within-screen comparisons, 0.05 / 12 two-sided interval.
    lo_adj,hi_adj=np.quantile(v[:,0],[.05/24.,1-.05/24.])
    leave=[
        float((g[:,1].sum()-row[1])/(g[:,0].sum()-row[0]))
        for row in g]
    late=(df.minute.to_numpy(int)>=30)
    game=(pd.DataFrame({"match_id":df.match_id,"series_id":df.series_id,"ll":delta})
          .groupby("match_id",sort=True,as_index=False)
          .agg(series_id=("series_id","first"),ll=("ll","mean")))
    game["cluster"]=cluster_ids(game[["match_id","series_id"]])
    match=game.ll
    grouped_games=(game.assign(n=1.)
                   .groupby("cluster",sort=True)[["n","ll"]].sum())
    if len(grouped_games)!=len(g):
        raise AssertionError("Game-level and minute-level series count mismatch")
    denom=grouped_games.to_numpy(float)[draws].sum(axis=1)
    equal_game_draws=denom[:,1]/denom[:,0]
    ci_match_95=np.quantile(equal_game_draws,[.025,.975])
    ci_match_995833=np.quantile(equal_game_draws,[.05/24.,1-.05/24.])
    return {
        "delta_logloss":float(delta.mean()),
        "delta_brier":float(db.mean()),
        "late30_delta_brier":float(db[late].mean()),
        "equal_match_delta_logloss":float(match.mean()),
        "equal_match_95_series_interval_ll":[float(t) for t in ci_match_95],
        "equal_match_995833_series_interval_ll":[float(t) for t in ci_match_995833],
        "95_series_interval_ll":[float(lo95),float(hi95)],
        "995833_series_interval_ll":[float(lo_adj),float(hi_adj)],
        "leave_one_series_out_range_ll":[float(min(leave)),float(max(leave))],
    }


def evaluate()->dict:
    if not PROTO.exists():
        raise AssertionError("Study preregistration absent")
    originals=verify_original_artifacts()
    prior=json.loads(EXISTING.read_text())
    train,source=load_train()
    train,train_check=attach_economy_share(train,CACHE,True)
    train=sat_asinh(train)
    w=match_equal_weights(train)
    models={}
    for name in MODELS:
        p=create_pipeline(name)
        args={"logistic__sample_weight":w} if name=="MATCH_EQUAL" else {}
        p.fit(train[list(INPUTS[name])],train.radiant_win.astype(int),**args)
        models[name]=p
    output={}
    ids=[]
    for period,spec in SCOPE.items():
        later,old_predictions,base_checks=load_raw_octnov(period,spec)
        later,share_checks=attach_economy_share(later,spec["root"]/"accepted_raw",False)
        later=sat_asinh(later)
        ids.append(set(later.match_id))
        y=later.radiant_win.to_numpy(int)
        scores={}
        for name in MODELS:
            p=models[name].predict_proba(later[list(INPUTS[name])])[:,1]
            ll,br=proper(y,p)
            later["ll_"+name]=ll
            later["br_"+name]=br
            late=(later.minute.to_numpy(int)>=30)
            scores[name]={
                "logloss":float(ll.mean()),
                "brier":float(br.mean()),
                "brier_30plus":float(br[late].mean()),
                "equal_match_logloss":float(
                    pd.DataFrame({"match_id":later.match_id,"ll":ll})
                    .groupby("match_id").ll.mean().mean()),
            }
            if name in BASE:
                expected=prior["cohorts"][period]["period_scoring"][name]
                keys={"logloss":"logloss","brier":"brier",
                      "brier_30plus":"late30_brier",
                      "equal_match_logloss":"equal_match_logloss"}
                for a,b in keys.items():
                    if not math.isclose(scores[name][a],expected[b],rel_tol=0,abs_tol=1e-10):
                        raise AssertionError("Previously established "+period+" "+name+" baseline parity changed")
                if name in ("M0_gold","M1_interaction"):
                    previous="p_M0" if name=="M0_gold" else "p_M1"
                    error=np.max(np.abs(p-old_predictions[previous].to_numpy(float)))
                    if error>1e-7:
                        raise AssertionError("Original saved probabilities not reproduced")
                    base_checks["max_prior_p_error_"+name]=float(error)
        groups=len(set(cluster_ids(later[["match_id","series_id"]])))
        if groups!=spec["n_series"]:
            raise AssertionError("Professional series grouping drift")
        rng=np.random.default_rng(SEED)
        draws=rng.integers(0,groups,size=(DRAWS,groups))
        comparisons={}
        per_cohort_gates={}
        for name in NEW:
            comparisons[name]={
                rival:grouped_delta(later,name,rival,draws)
                for rival in ("M1_interaction","Q1_path")}
            per_cohort_gates[name]=all(
                comparisons[name][rival]["delta_logloss"]<=-.005
                and comparisons[name][rival]["995833_series_interval_ll"][1]<0
                and comparisons[name][rival]["delta_brier"]<=0
                and comparisons[name][rival]["late30_delta_brier"]<=0
                for rival in ("M1_interaction","Q1_path"))
        output[period]={
            "games":spec["n_games"],"forecast_rows":len(later),
            "independent_series":groups,"source":base_checks,
            "earned_economy":share_checks,
            "models":scores,
            "comparisons":comparisons,
            "period_gate":per_cohort_gates,
        }
    if ids[0]&ids[1] or ids[0]&set(train.match_id) or ids[1]&set(train.match_id):
        raise AssertionError("March TRAIN shares a later match ID")
    if verify_original_artifacts()!=originals:
        raise AssertionError("Original user submission changed")
    return {
        "status":"post-result nonblind model-design screen; NOT holdout certification",
        "protocol_sha256":sha256(PROTO),
        "training_provenance_sha256":source["source_train_sha256"],
        "new_train_source_checks":train_check,
        "cohorts":output,
        "all_periods_scientific_gate":{
             n:all(output[period]["period_gate"][n] for period in SCOPE)
             for n in NEW},
        "training_weighting":"match-equal training only, no duration inference feature",
        "fit_source":"March 291 TRAIN games only; original March VAL/TEST untouched",
        "new_external_api_requests":0,
        "bootstrap_draws":DRAWS,
        "bootstrap_seed":SEED,
        "candidate_models":list(NEW),
        "source_ingress_time_verified":False,
        "employer_model_promoted":False,
        "protected_artifacts_sha256":originals,
    }


def readout(r:dict)->str:
    lines=[
        "# Minimal economic representation and match-balanced training: October/November",
        "",
        "**Exploratory after previously observed outcomes, not an untouched test.** "
        "No new data, no April/October/November outcome-driven fitting, no recruiter package changes.",
        "",
        "| Period | Model | Log loss | Brier | 30+ Brier | Equal-match LL |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name in SCOPE:
        for model in MODELS:
            s=r["cohorts"][name]["models"][model]
            lines.append(f"| {name} | {model} | {s['logloss']:.6f} | "
                         f"{s['brier']:.6f} | {s['brier_30plus']:.6f} | {s['equal_match_logloss']:.6f} |")
    lines+=["",
        "## Predeclared comparisons (negative LL delta is improvement)",
        "",
        "| Cohort | Candidate | vs | LL delta | 95% series CI | "
        "99.5833% within-screen interval | Brier delta | Late 30+ Brier delta | "
        "Equal-match LL delta | Equal-match 95% series CI | Drop-one-series LL range |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for period in SCOPE:
        for name in NEW:
            for comp in ("M1_interaction","Q1_path"):
                d=r["cohorts"][period]["comparisons"][name][comp]
                l,h=d["95_series_interval_ll"]
                a,b=d["995833_series_interval_ll"]
                x,y=d["leave_one_series_out_range_ll"]
                u,v=d["equal_match_95_series_interval_ll"]
                lines.append(f"| {period} | {name} | {comp} | "
                    f"{d['delta_logloss']:+.6f} | [{l:+.6f},{h:+.6f}] | "
                    f"[{a:+.6f},{b:+.6f}] | {d['delta_brier']:+.6f} | "
                    f"{d['late30_delta_brier']:+.6f} | "
                    f"{d['equal_match_delta_logloss']:+.6f} | "
                    f"[{u:+.6f},{v:+.6f}] | [{x:+.6f},{y:+.6f}] |")
    lines+=["",
        "## Decision, evidence and limits",
        "",
        "- All-period gate (gain >=.005 LL vs M1 and Q1 in both periods; "
        "within-screen 99.5833% upper bound <0; no overall/late30 Brier regression): "
        +str(r["all_periods_scientific_gate"])+".",
        "- Fit uses only original 291 March TRAIN games. October and November data were already inspected "
        "for previous models; within-screen adjusted intervals do not correct cumulative feature searches.",
        "- Source player gold_t is *cumulative earned gold*, NOT actual inventory net worth. "
        "Source as-of game clock consistency does not imply available real-time received_at.",
        "- A match-equal TRAIN objective does not mean forecasts within the same match are independent. "
        "All intervals bootstrap whole professional series/singletons.",
        "- The equal-match cluster-bootstrap interval was added as an explicitly POST-RESULT "
        "sensitivity after inspecting the first scoring receipt. No model, feature, "
        "hyperparameter, population, frozen comparator or approval gate was changed.",
        "- Employer notebook, original TEST forecasts, report/PDF, ZIP, original Draft PR and main unchanged.",
        "",
    ]
    return "\n".join(lines)


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--write",action="store_true")
    args=cli.parse_args()
    receipt=evaluate()
    print(readout(receipt))
    if args.write:
        OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        READOUT.write_text(readout(receipt))
