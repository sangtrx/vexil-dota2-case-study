#!/usr/bin/env python3
"""Offline candidate-facing audit of the optional 100-game November score receipts.

This never fits/chooses/recalibrates a model, requires no original OpenDota
payloads and makes no claim that external file hashes are notarized.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PRED=ROOT/"artifacts/forward_100_predictions.csv"
META=ROOT/"artifacts/forward_100_metadata.csv"
CANDIDATES=ROOT/"docs/FORWARD_100_CANDIDATES.json"
EVIDENCE=ROOT/"docs/FORWARD_100_EVIDENCE.json"
EXPECTED_ORIGINAL_TEST_SHA="03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def assert_close(got,want,key,atol=1e-10):
    if not np.isfinite(got) or abs(float(got)-float(want))>atol:
        raise ValueError(f"Forward evidence mismatch {key}: {got} vs {want}")

def proper_loss(y,p):
    p=np.clip(np.asarray(p,dtype=float),1e-15,1.-1e-15)
    y=np.asarray(y,dtype=float)
    return -(y*np.log(p)+(1.-y)*np.log1p(-p))

def ece(y,p):
    indices=np.clip((np.asarray(p,dtype=float)*10).astype(int),0,9)
    y=np.asarray(y,dtype=float)
    p=np.asarray(p,dtype=float)
    total=0.
    for k in range(10):
        sample=indices==k
        if sample.any():
            total+=sample.mean()*abs(y[sample].mean()-p[sample].mean())
    return float(total)

def verify()->dict:
    evidence=json.loads(EVIDENCE.read_text())
    raw=evidence["cohort_collection_receipt"]
    score=evidence["forward_scores"]
    forward=evidence["offline_replay_receipt"]
    parity=evidence["train_parity_receipt"]
    league=evidence["league_concentration_receipt"]
    note=evidence["provenance_receipt"]
    listing=json.loads(CANDIDATES.read_text())
    if (sha(CANDIDATES)!=evidence["candidate_listing_sha256"]
            or sha(CANDIDATES)!=raw["listing_sha256"]
            or listing["candidate_count"]!=1073
            or listing["page_count"]!=15
            or len(listing["candidate_ids_and_start_times"])!=1073):
        raise ValueError("Forward candidate listing provenance changed")
    if (evidence["protocol_git_commit"]!="9d6cddf" or
            not evidence["source_provenance_and_method_self_attested"] or
            not note["games_happened_before_protocol"] or
            note["status"]!="SELF_ATTESTED_LOCAL_TIMELINE_CONSISTENT"):
        raise ValueError("Forward-provenance limitation hidden or inconsistent")
    if not (raw["complete"] and raw["accepted_count"]==100 and
            raw["details_queried"]==101 and
            raw["rejection_reasons"]=={"unparsed_gold":1}):
        raise ValueError("Original 101 screened candidates and 1 exclusion changed")
    listing_ids=[int(x["match_id"]) for x in listing["candidate_ids_and_start_times"]]
    if listing_ids!=sorted(set(listing_ids),reverse=True):
        raise ValueError("Frozen candidate list not unique descending")
    audit=raw["candidate_audit"]
    accepted=raw["eligible"]
    if [x["match_id"] for x in audit]!=listing_ids[:101]:
        raise ValueError("Outcomes may have influenced candidate order")
    accepted_ids=[int(x["match_id"]) for x in audit if x["accepted"]]
    if accepted_ids!=[int(x["match_id"]) for x in accepted]:
        raise ValueError("Accepted candidate selection differs")
    if not all(int(x["duration"])>=600 and str(x["patch"])=="60" for x in accepted):
        raise ValueError("Accepted game eligibility or patch changed")
    p=pd.read_csv(PRED)
    m=pd.read_csv(META)
    if list(p.columns)!=["match_id","minute","radiant_win","p_M0","p_M1"]:
        raise ValueError("Unexpected probability CSV columns")
    if list(m.columns)!=["match_id","start_time","patch","duration","series_id",
                         "league_id","radiant_team_id","dire_team_id","radiant_win"]:
        raise ValueError("Unexpected per-match metadata columns")
    if not (len(p)==4355 and p.match_id.nunique()==100
            and len(m)==100 and m.match_id.is_unique
            and not p[["match_id","minute"]].duplicated().any()
            and p.notna().all().all()):
        raise ValueError("Prediction or metadata completeness failed")
    if list(m.match_id.astype(int))!=accepted_ids:
        raise ValueError("Metadata match order/ID differs from frozen accepted games")
    if not p.match_id.isin(accepted_ids).all():
        raise ValueError("Unexpected forecast game in optional sample")
    if (not set(p.radiant_win).issubset({0,1})
            or not set(m.radiant_win).issubset({0,1})
            or any((p[key]<=0).any() or (p[key]>=1).any() for key in ("p_M0","p_M1"))):
        raise ValueError("Probability or label outside valid range")
    lookup={int(x["match_id"]):x for x in accepted}
    for row in m.itertuples():
        ref=lookup[int(row.match_id)]
        if (int(row.duration)!=int(ref["duration"]) or
                int(row.start_time)!=int(ref["start_time"]) or
                int(row.series_id)!=int(ref["series_id"]) or
                str(row.patch)!=str(ref["patch"])):
            raise ValueError("Per-match metadata contradicts immutable collection receipt")
    for mid,group in p.groupby("match_id",sort=False):
        row=m.loc[m.match_id==mid].iloc[0]
        if (len(group)!=((int(row.duration)-1)//60)+1
                or not np.array_equal(group.minute.to_numpy(dtype=int),
                                      np.arange(len(group),dtype=int))
                or group.radiant_win.nunique()!=1
                or int(group.radiant_win.iloc[0])!=int(row.radiant_win)):
            raise ValueError("Forecast horizon, label or minute identity corrupted")
    if (sha(PRED)!=forward["original_prediction_csv_sha256"]
            or sha(PRED)!=evidence["source_prediction_csv_sha256"]
            or sha(META)!=evidence["source_metadata_csv_sha256"]
            or forward["original_matches"]!=100
            or forward["original_minute_rows"]!=4355
            or not forward["no_new_http"]
            or not forward["no_forward_refit_or_recalibration"]
            or not evidence["no_model_promotion_authorized"]):
        raise ValueError("Frozen source predictions not matching replay receipt")
    if (sha(ROOT/"artifacts/heldout_predictions.csv")!=EXPECTED_ORIGINAL_TEST_SHA or
            parity["original_test_forecast_rows_checked"]!=3836 or
            max(parity["original_test_pred_max_abs_probability_error"].values())>=1e-12
            or not parity["same_train_model_coefficients"] or
            parity["model_coefficient_sha256"]!=score["source_model_coeff_sha256"]):
        raise ValueError("Original 500-game model or TEST lineage modified")
    frame=p.merge(m[["match_id","series_id","league_id"]],
                  on="match_id",validate="many_to_one")
    y=frame.radiant_win.to_numpy(dtype=int)
    p0=frame.p_M0.to_numpy(dtype=float)
    p1=frame.p_M1.to_numpy(dtype=float)
    l0=proper_loss(y,p0)
    l1=proper_loss(y,p1)
    b0=(p0-y)**2;b1=(p1-y)**2
    for k,val in (("M0_logloss",l0.mean()),("M1_logloss",l1.mean()),
                  ("M0_brier",b0.mean()),("M1_brier",b1.mean()),
                  ("M0_ece",ece(y,p0)),("M1_ece",ece(y,p1))):
        model="M0" if k.startswith("M0") else "M1"
        metric=k.split("_",1)[1]
        assert_close(val,score[model][metric],k)
    assert_close(float(y.mean()),score["radiant_win_rate_minute_rows"],"observed_rate")
    assert_close(float(p0.mean()),score["mean_prob_M0"],"mean_p_M0")
    assert_close(float(p1.mean()),score["mean_prob_M1"],"mean_p_M1")
    delta=score["M1_minus_M0"]
    assert_close(float(np.mean(l1-l0)),delta["logloss"],"delta_ll")
    assert_close(float(np.mean(b1-b0)),delta["brier"],"delta_brier")

    keys=np.where(frame.series_id.to_numpy(dtype=int)>0,
                  "s"+frame.series_id.astype(str).to_numpy(),
                  "m"+frame.match_id.astype(str).to_numpy())
    unique,indices=np.unique(keys,return_inverse=True)
    if len(unique)!=56 or delta["logloss_ci_95_series"][0]>=0 or delta["logloss_ci_95_series"][1]<=0:
        raise ValueError("56-group uncertainty or interval interpretation changed")
    counts=np.bincount(indices,minlength=len(unique)).astype(float)
    rng=np.random.default_rng(20261115)
    draw=rng.integers(0,len(unique),size=(5000,len(unique)))
    for name,values in (("logloss",l1-l0),("brier",b1-b0)):
        total=np.bincount(indices,weights=values,minlength=len(unique))
        sampled=total[draw].sum(axis=1)/counts[draw].sum(axis=1)
        ci=np.quantile(sampled,(.025,.975))
        for i in (0,1):
            assert_close(ci[i],delta[name+"_ci_95_series"][i],"bootstrap_"+name,1e-10)
    # Full league calculations, with no dropping original games from the main estimate.
    if (len(set(m.league_id))!=4 or
            sum(x["games"] for x in league["league_summaries"][:2])!=85):
        raise ValueError("League concentration numbers changed")
    by_league={}
    for lid,part in frame.groupby("league_id"):
        yy=part.radiant_win.to_numpy(dtype=int)
        lo=proper_loss(yy,part.p_M0.to_numpy(float))
        hi=proper_loss(yy,part.p_M1.to_numpy(float))
        by_league[int(lid)]=(len(part),int(part.match_id.nunique()),
                              float((hi-lo).mean()))
    for record in league["league_summaries"]:
        actual=by_league[int(record["leagueid"])]
        if record["minute_rows"]!=actual[0] or record["games"]!=actual[1]:
            raise ValueError("League counts are not replicated")
        assert_close(actual[2],record["M1_minus_M0_logloss"],"league_ll")
    for record in league["leave_one_league_out"]:
        subset=frame.loc[frame.league_id!=int(record["league_omitted"])]
        yy=subset.radiant_win.to_numpy(dtype=int)
        diff=(proper_loss(yy,subset.p_M1)-proper_loss(yy,subset.p_M0)).mean()
        if subset.match_id.nunique()!=record["games_kept"]:
            raise ValueError("Leave-one-league case size mismatch")
        assert_close(diff,record["M1_minus_M0_logloss"],"league_omission_ll")
    phase_rules={"0-9":(0,10),"10-19":(10,20),"20-29":(20,30),"30+":(30,100000)}
    for name,(low,hi) in phase_rules.items():
        subset=frame[(frame.minute>=low)&(frame.minute<hi)]
        scores=score["phase_descriptive"][name]
        if len(subset)!=scores["minute_rows"] or subset.match_id.nunique()!=scores["games"]:
            raise ValueError("Phase sample size differs")
        label=subset.radiant_win.to_numpy(dtype=int)
        for mdl in ("M0","M1"):
            prob=subset["p_"+mdl].to_numpy(float)
            assert_close(float(((label-prob)**2).mean()),scores["brier_"+mdl],"phase_brier")
            assert_close(ece(label,prob),scores["ece_"+mdl],"phase_ece")
    if not (score["patch_counts"]=={"60":100}
            and score["games"]==100 and score["clusters"]==56 and score["minutes"]==4355
            and score["M1_minus_M0"]["logloss_ci_95_series"][0]<0<
                score["M1_minus_M0"]["logloss_ci_95_series"][1]):
        raise ValueError("Interpretive boundary was lost")
    return {
       "status":"PASS_ZIP_ONLY_100_FROZEN_FORECAST_AUDIT",
       "source_csv_sha256":sha(PRED),
       "metadata_csv_sha256":sha(META),
       "100_matches":int(len(m)),"minute_rows":int(len(p)),
       "series_or_singletons":len(unique),"leagues":len(by_league),
       "logloss_M0":float(l0.mean()),"logloss_M1":float(l1.mean()),
       "CI_M1_minus_M0_logloss":delta["logloss_ci_95_series"],
       "requires_original_raw_json":False,
       "recomputed_original_500_model":False,
       "no_model_selection":True,
    }

if __name__=="__main__":
    print(json.dumps(verify(),sort_keys=True,indent=2))
