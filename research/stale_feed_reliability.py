#!/usr/bin/env python3
"""Bounded synthetic late-gold feed counterfactual; strictly TRAIN-forward."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from conditional_gold_forward import FROZEN_CUTS
from disagreement_reliability import guard_delivery
from rich_feature_models import MODELS, create_pipeline, load_train, proper
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"research/STALE_FEED_PROTOCOL.md"
RECEIPT=ROOT/"research/STALE_FEED_RECEIPT.json"
READOUT=ROOT/"research/STALE_FEED_READOUT.md"
PRIOR=ROOT/"research/QUANT_BIBLE_PATH_RECEIPT.json"
SEED,DRAWS=20261118,2000
LAGS=(1,3)
M1="M1_interaction"


def lagged_views(ev:pd.DataFrame,fresh:np.ndarray, lag:int)->tuple[pd.DataFrame,np.ndarray,int]:
    """Both policies operate on current/past input only, with match restarts."""
    if not isinstance(lag,int) or lag<0:
        raise ValueError("Lag must be nonnegative complete minutes")
    req={"match_id","minute","minute10","gold_k"}
    if not req.issubset(ev):
        raise ValueError("Expected original source columns")
    fresh=np.asarray(fresh,dtype=float)
    if len(ev)!=len(fresh) or ev[["match_id","minute"]].duplicated().any():
        raise ValueError("Forecast alignment violated")
    if not np.isfinite(fresh).all() or not ((fresh>0)&(fresh<1)).all():
        raise ValueError("Fresh reference forecast invalid")
    if not np.isfinite(ev[["gold_k","minute10"]].to_numpy(float)).all():
        raise ValueError("Base model inputs invalid")
    lagged_gold=np.empty(len(ev),dtype=float)
    held=np.empty(len(ev),dtype=float)
    prefix_count=0
    # Internal group indices are 0..len(ev)-1; no out-of-game carryover.
    for _,grp in ev.groupby("match_id",sort=False):
        idx=grp.index.to_numpy(dtype=int)
        minutes=grp.minute.to_numpy(dtype=int)
        if not np.array_equal(minutes,np.arange(len(grp))):
            raise ValueError("Minute order/gaps violate causal-prefix contract")
        history=grp.gold_k.to_numpy(dtype=float)
        old=np.maximum(0,minutes-lag)
        if (old>minutes).any():
            raise AssertionError("Lookahead in old minute reference")
        lagged_gold[idx]=history[old]
        held[idx]=fresh[idx[old]]
        prefix_count+=int((minutes<lag).sum())
    curr_time=ev.minute10.to_numpy(float)
    frame=pd.DataFrame({
        "gold_k":lagged_gold, "minute10":curr_time,
        "gold_x_time":lagged_gold*np.log1p(curr_time),
    },index=ev.index)
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise AssertionError("Nonfinite delayed clock-based feature")
    if "gold_x_time" in ev:
        original=ev.gold_k.to_numpy(float)*np.log1p(curr_time)
        if not np.allclose(original,ev.gold_x_time.to_numpy(float),rtol=0,atol=1e-12):
            raise AssertionError("Original M1 gold x log1p(time) feature contract violated")
    if lag==0:
        if "gold_x_time" in ev and not np.allclose(frame.gold_x_time,ev.gold_x_time,rtol=0,atol=1e-12):
            raise AssertionError("Zero-lag interaction parity against original M1 failed")
        if not np.allclose(frame.gold_k,ev.gold_k,rtol=0,atol=0):
            raise AssertionError("Zero-lag gold parity failed")
        if not np.array_equal(held,fresh):
            raise AssertionError("Zero-lag held reference must match fresh")
    return frame,held,prefix_count


def paired_cluster_ci(rows:pd.DataFrame,lag:int)->dict:
    cid=cluster_ids(rows[["match_id","series_id"]])
    x=rows.copy()
    x["cid"]=cid
    dh=x[f"ll_HOLD{lag}"].to_numpy(float)-x[f"ll_CLOCK{lag}"].to_numpy(float)
    db=x[f"br_HOLD{lag}"].to_numpy(float)-x[f"br_CLOCK{lag}"].to_numpy(float)
    x["dll"]=dh
    x["dbr"]=db
    g=x.groupby("cid",sort=True).agg(n=("minute","size"),dll=("dll","sum"),dbr=("dbr","sum"))
    if len(g)!=70:
        raise AssertionError("Expected exactly 70 series/singleton units")
    arr=g[["n","dll","dbr"]].to_numpy(float)
    ids=np.random.default_rng(SEED).integers(0,len(arr),size=(DRAWS,len(arr)))
    agg=arr[ids].sum(axis=1)
    v=agg[:,1:]/agg[:,0,None]
    if not np.isfinite(v).all():
        raise AssertionError("Invalid clustered bootstrap draw")
    late=rows.minute.to_numpy(int)>=30
    return {
        "hold_minus_clock_delta_logloss":float(dh.mean()),
        "hold_minus_clock_delta_brier":float(db.mean()),
        "late30_hold_minus_clock_delta_brier":float(db[late].mean()),
        "series_bootstrap_95_ll":np.quantile(v[:,0],[.025,.975]).tolist(),
        "series_bootstrap_975_ll_two_lags":np.quantile(v[:,0],[.0125,.9875]).tolist(),
        "series_bootstrap_95_brier":np.quantile(v[:,1],[.025,.975]).tolist(),
    }


def evaluate()->dict:
    if not PROTOCOL.is_file():
        raise ValueError("Pre-outcome protocol missing")
    artifacts=guard_delivery()
    df,provenance=load_train()
    prior=json.loads(PRIOR.read_text())
    meta=(df[["match_id","start_time","duration","series_id"]]
          .drop_duplicates().sort_values(["start_time","match_id"],kind="stable")
          .reset_index(drop=True))
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("Frozen split not respected")
    allparts=[]
    folds=[]
    for i,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        previous,current=meta.iloc[:left],meta.iloc[left:right]
        cutoff=int(current.iloc[0].start_time)
        mature=previous[previous.start_time+previous.duration<=cutoff]
        if set(cluster_ids(previous))&set(cluster_ids(current)):
            raise AssertionError("Nominal series crosses fold")
        if set(cluster_ids(mature))&set(cluster_ids(current)):
            raise AssertionError("Mature-label series crosses fold")
        fit=df[df.match_id.isin(mature.match_id)]
        ev=(df[df.match_id.isin(current.match_id)]
            .sort_values(["match_id","minute"],kind="stable").reset_index(drop=True))
        if len(ev)==0 or set(fit.match_id)&set(ev.match_id):
            raise AssertionError("Fit/eval overlap")
        y=ev.radiant_win.to_numpy(float)
        fitted=create_pipeline(M1).fit(fit[MODELS[M1]],fit.radiant_win.astype(int))
        fresh=fitted.predict_proba(ev[MODELS[M1]])[:,1]
        loss,br=proper(y,fresh)
        prior_values=prior["folds"][i-1][M1]
        for name,computed in (("logloss",loss.mean()),("brier",br.mean())):
            if not math.isclose(float(computed),prior_values[name],rel_tol=0,abs_tol=1e-10):
                raise AssertionError("Original M1 score parity failed")
        part=ev[["match_id","series_id","minute"]].copy()
        part["ll_FRESH"],part["br_FRESH"]=loss,br
        scores={"FRESH":{"logloss":float(loss.mean()),"brier":float(br.mean())}}
        fold={"fold":i,"games":len(current),"rows":len(ev),
              "fit_completed_games":len(mature),
              "embargoed_unfinished_games":len(previous)-len(mature)}
        for lag in LAGS:
            clock_frame,held,short_count=lagged_views(ev,fresh,lag)
            clock=fitted.predict_proba(clock_frame[MODELS[M1]])[:,1]
            if len(clock)!=len(held):
                raise AssertionError("Stale stream alignment failed")
            for kind,p in (("CLOCK",clock),("HOLD",held)):
                name=f"{kind}{lag}"
                llv,brv=proper(y,p)
                part[f"ll_{name}"]=llv
                part[f"br_{name}"]=brv
                scores[name]={"logloss":float(llv.mean()),"brier":float(brv.mean()),
                              "late30_brier":float(brv[ev.minute.to_numpy(int)>=30].mean())}
            fold[f"lag{lag}_t_below_lag_rows"]=short_count
            fold[f"lag{lag}_hold_minus_clock_logloss"]=scores[f"HOLD{lag}"]["logloss"]-scores[f"CLOCK{lag}"]["logloss"]
        fold["score"]=scores
        folds.append(fold)
        allparts.append(part)
    rows=pd.concat(allparts,ignore_index=True)
    if len(rows)!=5081 or rows.match_id.nunique()!=137 or len(set(cluster_ids(rows)))!=70:
        raise AssertionError("TRAIN forward geometry mismatch")
    if rows[["match_id","minute"]].duplicated().any():
        raise AssertionError("Repeated minute prediction")
    ci={str(lag):paired_cluster_ci(rows,lag) for lag in LAGS}
    summary={}
    for name in ("FRESH","CLOCK1","HOLD1","CLOCK3","HOLD3"):
        ll=rows[f"ll_{name}"].to_numpy(float)
        br=rows[f"br_{name}"].to_numpy(float)
        late=rows.minute.to_numpy(int)>=30
        summary[name]={"logloss":float(ll.mean()),
                       "brier":float(br.mean()),
                       "late30_brier":float(br[late].mean())}
    for name in ("CLOCK1","HOLD1","CLOCK3","HOLD3"):
        summary[name]["delta_ll_vs_fresh"]=summary[name]["logloss"]-summary["FRESH"]["logloss"]
        summary[name]["delta_brier_vs_fresh"]=summary[name]["brier"]-summary["FRESH"]["brier"]
    x=ci["3"]
    gate=bool(
        x["hold_minus_clock_delta_logloss"]<=-.003
        and x["series_bootstrap_975_ll_two_lags"][1]<0
        and x["late30_hold_minus_clock_delta_brier"]<=0
        and sum(f["lag3_hold_minus_clock_logloss"]<0 for f in folds)>=3)
    if guard_delivery()!=artifacts:
        raise AssertionError("Protected source artifacts changed")
    return {"scope":"hypothetical stale-gold perturbation on original TRAIN only",
            "protocol_sha256":hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
            "original_train_sha256":provenance["source_train_sha256"],
            "protected_artifact_hashes":artifacts,
            "n_games_train":291,"n_games_oof":137,"n_minutes_oof":5081,
            "n_series_or_singletons":70,
            "source_received_at_known":False,
            "lags_minutes":list(LAGS),
            "held_vs_clock_cluster_ci":ci,"overall_metrics":summary,
            "folds":folds,"future_mitigation_gate":gate,
            "original_employer_model_changed":False,
            "prior_multiple_experiments_corrected":False}


def report(r:dict)->str:
    out=[
        "# Does a stale gold feed warrant holding the last forecast?",
        "",
        "**Counterfactual offline TRAIN-only test. Not observed ingress latency.**",
        "",
        f"{r['n_games_oof']} games; {r['n_minutes_oof']} snapshots; "
        f"{r['n_series_or_singletons']} professional series/singletons.",
        "",
        "## Proper scores vs fresh original M1",
        "",
        "| Forecast stream | Log loss | ΔLL vs fresh | Brier | ΔBrier vs fresh | 30+ Brier |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name,x in r["overall_metrics"].items():
        out.append(f"| {name} | {x['logloss']:.6f} | "
                   f"{x.get('delta_ll_vs_fresh',0):+.6f} | "
                   f"{x['brier']:.6f} | "
                   f"{x.get('delta_brier_vs_fresh',0):+.6f} | "
                   f"{x['late30_brier']:.6f} |")
    out+=["",
        "## HOLD vs current clock with delayed gold (negative = HOLD better)",
        "",
        "| Lag | Δ LL HOLD−CLOCK | 95% series CI | Bonferroni 97.5% series CI | Δ Brier HOLD−CLOCK | 30+ Δ Brier |",
        "| --- | ---: | --- | --- | ---: | ---: |"]
    for lag in LAGS:
        x=r["held_vs_clock_cluster_ci"][str(lag)]
        c=x["series_bootstrap_95_ll"];b=x["series_bootstrap_975_ll_two_lags"]
        out.append(f"| {lag} min | {x['hold_minus_clock_delta_logloss']:+.6f} | "
                   f"[{c[0]:+.6f},{c[1]:+.6f}] | "
                   f"[{b[0]:+.6f},{b[1]:+.6f}] | "
                   f"{x['hold_minus_clock_delta_brier']:+.6f} | "
                   f"{x['late30_hold_minus_clock_delta_brier']:+.6f} |")
    out+=["", "## All four forward TRAIN folds",
          "", "| Fold | Games | Fresh LL | CLOCK1 LL | HOLD1 LL | CLOCK3 LL | HOLD3 LL |",
          "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in r["folds"]:
        s=f["score"]
        out.append(f"| {f['fold']} | {f['games']} | " +
                   " | ".join(f"{s[name]['logloss']:.6f}" for name in
                            ("FRESH","CLOCK1","HOLD1","CLOCK3","HOLD3")) + " |")
    out+=["",
          "## Scientific decision",
          "",
          "**Future independent mitigation gate:** " + (
              "PASSED for prospective evaluation only" if r["future_mitigation_gate"]
              else "REJECTED (no promotion)"),
          "",
          "The FRESH stream is a historical hypothetical oracle for unavailable current gold "
          "under an actual feed delay. CLOCK and HOLD are deterministic counterfactuals. "
          "This cannot measure the real frequency of delayed packets, UI latency, player utility, "
          "calibration under drift, or performance after missing events. Bootstrap CIs are "
          "descriptive on retrospectively reused TRAIN data and do not correct many prior screens.",
          "",
          "Original submission, pre-scored VAL/TEST, reviewer package and applicant-owned "
          "hours/disclosure are unchanged.",
          ""]
    return "\n".join(out)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    receipt=evaluate()
    print(report(receipt))
    if args.write:
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        READOUT.write_text(report(receipt))
