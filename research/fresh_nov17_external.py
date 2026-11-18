#!/usr/bin/env python3
"""Precommitted 17 Nov 2026 post-selection, newly collected, outcome-blind study.

Workflow: freeze -> discover -> COMMIT freezes -> collect -> COMMIT source hashes
-> score. Never promote or submit this research to an employer.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import time
import numpy as np
import pandas as pd
import requests

from all_family_models import verify_original_artifacts
from cross_array_time_alignment import check_single_game
from minimal_economy_scoring import INPUTS, match_equal_weights
from quant_bible_path_risk_train_only import prefix_path_features
from rich_feature_models import create_pipeline,load_train,proper
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"research/FRESH_NOV17_LOCKED_PROTOCOL_20261118.md"
LOCK=ROOT/"research/FRESH_NOV17_MODEL_LOCK.json"
LISTING=ROOT/"research/FRESH_NOV17_LISTING.json"
FINAL=ROOT/"research/FRESH_NOV17_EXTERNAL_RECEIPT.json"
READOUT=ROOT/"research/FRESH_NOV17_EXTERNAL_READOUT.md"
DATA=Path("/srv/ai/tmp/vexil-fresh-nov17-20261118")
URL="https://api.opendota.com/api"
MODELS=("M0_gold","M1_interaction","Q1_path","MATCH_EQUAL")
START=int(dt.datetime(2026,11,17,tzinfo=dt.timezone.utc).timestamp())
END=int(dt.datetime(2026,11,18,tzinfo=dt.timezone.utc).timestamp())
MAX_PAGE=4
MAX_GAMES=45
SEED=20261118
DRAWS=5000


def sha(buf:bytes)->str:
    return hashlib.sha256(buf).hexdigest()


def sha_file(path:Path)->str:
    return sha(path.read_bytes())


def dump(path:Path,data:dict)->None:
    if path.exists():
        raise FileExistsError("Research evidence immutable: "+str(path))
    path.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")


def freeze_models():
    if not PROTO.exists():
        raise AssertionError("Precommitted protocol missing")
    train,source=load_train()
    weights=match_equal_weights(train)
    out={}
    models={}
    for name in MODELS:
        m=create_pipeline(name)
        kwargs={"logistic__sample_weight":weights} if name=="MATCH_EQUAL" else {}
        cols=list(INPUTS[name])
        m.fit(train[cols],train.radiant_win.astype(int),**kwargs)
        steps=m.named_steps
        arr=[steps["imputer"].statistics_,steps["scale"].mean_,steps["scale"].scale_,
             steps["logistic"].coef_,steps["logistic"].intercept_]
        raw=b"".join(np.asarray(a,dtype="<f8").ravel().tobytes() for a in arr)
        out[name]={
            "inputs":cols,
            "coefficient_preprocessor_sha256":sha(raw),
            "coefficients":steps["logistic"].coef_.ravel().tolist(),
            "intercept":steps["logistic"].intercept_.ravel().tolist(),
            "train_rows":len(train),
            "train_games":train.match_id.nunique(),
        }
        models[name]=m
    lock={
        "preselection_protocol_sha256":sha_file(PROTO),
        "model_family":"Original March-TRAIN-only C1 logistic; MATCH_EQUAL match-weighted only",
        "models":out,
        "source_training_hash":source["source_train_sha256"],
        "employer_artifacts":verify_original_artifacts(),
        "new_cohort_observed":False,
        "original_validation_or_test_read":False,
        "model_selection_origin":"Earlier inspected Oct/Nov research; new cohort is POST-SELECTION",
    }
    return models,lock


def frozen_overlap_ids()->set[int]:
    sources=[
      ROOT/"research/frozen_original_split_manifest.csv",
      ROOT/"docs/NOVEMBER_120_RESEARCH_MANIFEST.csv",
      ROOT/"artifacts/forward_100_metadata.csv",
      Path("/srv/ai/tmp/vexil-october-raw-20261117/metadata.csv"),
      Path("/srv/ai/tmp/vexil-prospective-nov17-data-20261117/metadata.csv")
    ]
    result=set()
    for path in sources:
        if not path.exists():
            raise FileNotFoundError("Prior-scored manifest missing: "+str(path))
        result.update(pd.read_csv(path,usecols=["match_id"]).match_id.astype(int))
    return result


def fetch_json(session:requests.Session,path:str,timeout=(7,26),attempts=3):
    error=None
    for i in range(attempts):
        try:
            resp=session.get(URL+path,timeout=timeout)
            if resp.status_code in (429,500,502,503,504):
                error="HTTP "+str(resp.status_code)
                time.sleep(2+i*3)
                continue
            resp.raise_for_status()
            return resp.json(),sha(resp.content),i+1
        except (requests.RequestException,ValueError) as e:
            error=str(e)[:200]
            time.sleep(1+i*2)
    raise RuntimeError("HTTP source failure "+path+" "+str(error))


def discover()->dict:
    if LOCK.exists() is False:
        raise AssertionError("First freeze source model coefficients")
    original=json.loads(LOCK.read_text())
    if original["preselection_protocol_sha256"]!=sha_file(PROTO):
        raise AssertionError("Protocol mutated since model freeze")
    old=frozen_overlap_ids()
    session=requests.Session()
    session.headers["User-Agent"]="Vexil-minimal-research-Nov17-immutable-protocol/1.0"
    cursor=None
    candidates=[]
    page_receipts=[]
    reached_boundary=False
    seen_ids=set()
    for page in range(MAX_PAGE):
        path="/proMatches"+("?less_than_match_id="+str(cursor) if cursor else "")
        items,body_sha,ntries=fetch_json(session,path)
        if not isinstance(items,list) or not items:
            raise AssertionError("Expected a nonempty OpenDota pro matches page")
        allowed_keys={"match_id","start_time","duration","series_id","leagueid"}
        page_receipts.append({
            "page":page+1,"raw_http_body_sha256":body_sha,
            "response_items":len(items),"attempts":ntries,
        })
        ids=[]
        starts=[]
        for it in items:
            if not isinstance(it,dict):
                raise AssertionError("Non-dict listing")
            mid=it.get("match_id")
            start=it.get("start_time")
            if type(mid)!=int or type(start)!=int:
                raise AssertionError("Non-integer listing identity")
            if mid in seen_ids:
                raise AssertionError("OpenDota discovery duplicate match")
            seen_ids.add(mid)
            ids.append(mid)
            starts.append(start)
            if START<=start<END:
                row={k:it.get(k) for k in allowed_keys}
                if (isinstance(row["duration"],int) and 600<=row["duration"]<=7200
                    and isinstance(row["leagueid"],int)
                    and (row["series_id"] is None or isinstance(row["series_id"],int))):
                    row["series_id"]=int(row["series_id"] or 0)
                    candidates.append(row)
        if ids!=sorted(ids,reverse=True):
            raise AssertionError("Expected descending match IDs / pagination")
        cursor=min(ids)
        if min(starts)<START:
            reached_boundary=True
            break
    candidates.sort(key=lambda x:(x["start_time"],x["match_id"]))
    if len(set(x["match_id"] for x in candidates))!=len(candidates):
        raise AssertionError("Duplicate eligible discovered IDs")
    selected=candidates[:MAX_GAMES]
    overlap=sorted(set(x["match_id"] for x in selected)&old)
    if overlap:
        raise AssertionError("New external cohort overlaps previous researched games: "+str(overlap[:9]))
    if not reached_boundary:
        # Record incomplete listing, but NEVER score the resulting subset.
        pass
    return {
        "window_utc":["2026-11-17T00:00:00Z","2026-11-18T00:00:00Z"],
        "protocol_sha256":sha_file(PROTO),
        "model_lock_sha256":sha_file(LOCK),
        "max_pages":MAX_PAGE,"max_selected":MAX_GAMES,
        "pages":page_receipts,
        "reached_start_boundary":reached_boundary,
        "valid_candidates_in_window":len(candidates),
        "selected":selected,
        "selected_games":len(selected),
        "previous_scored_game_ids_checked":len(old),
        "overlap_with_previous_scored_games":0,
        "winner_or_score_fields_read_for_selection":False,
        "selection_rule":"chronological earliest 45 valid pro listings in fixed UTC day; no replacement after raw exclusions",
    }


def check_payload(raw:dict,ref:dict)->tuple[str|None,dict|None]:
    try:
        if (int(raw["match_id"])!=ref["match_id"]
            or int(raw["start_time"])!=ref["start_time"]
            or int(raw["duration"])!=ref["duration"]):
            return "listed_identity_time_or_duration_mismatch",None
        if type(raw.get("radiant_win")) is not bool:
            return "missing_final_label",None
        if raw.get("patch") is None:
            return "missing_patch",None
        base=check_single_game(raw)
        n=math.ceil(float(raw["duration"])/60.)
        if base["raw_snapshots"]<n:
            return "incomplete_original_minute_grid",None
        if not (isinstance(raw["players"],list) and len(raw["players"])==10):
            return "not_ten_players",None
        return None,base
    except (ValueError,KeyError,TypeError,AssertionError,IndexError) as exc:
        return "source_schema_or_alignment_"+type(exc).__name__,None


def collect()->dict:
    if DATA.exists():
        raise FileExistsError("Immutable data dir already exists: "+str(DATA))
    if not LOCK.exists() or not LISTING.exists():
        raise AssertionError("Need committed model and listing freeze before collecting")
    listing=json.loads(LISTING.read_text())
    lock=json.loads(LOCK.read_text())
    if (not listing["reached_start_boundary"]
        or listing["model_lock_sha256"]!=sha_file(LOCK)
        or listing["protocol_sha256"]!=sha_file(PROTO)
        or len(listing["selected"])>MAX_GAMES):
        raise AssertionError("Source discovery not complete or uncommitted")
    models,model_lock=freeze_models()
    if model_lock["models"]!=lock["models"] or model_lock["employer_artifacts"]!=lock["employer_artifacts"]:
        raise AssertionError("Frozen model coefficient drift before source fetch")
    del models
    DATA.mkdir()
    rawdir=DATA/"accepted_raw"
    rawdir.mkdir()
    audit=[]
    accepted=[]
    session=requests.Session()
    session.headers["User-Agent"]="Vexil-Nov17-locked-cohort-source/1.0"
    for i,entry in enumerate(listing["selected"]):
        mid=int(entry["match_id"])
        reason=None
        detail=None
        payload=None
        try:
            payload,raw_http_sha,attempts=fetch_json(session,"/matches/"+str(mid))
        except Exception as exc:
            raw_http_sha=None
            attempts=3
            reason="source_http_failure_"+type(exc).__name__
        if reason is None:
            reason,detail=check_payload(payload,entry)
        if reason is None:
            exact=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
            packed=gzip.compress(exact,mtime=0)
            (rawdir/(str(mid)+".json.gz")).write_bytes(packed)
            accepted.append({
                "match_id":mid,
                "start_time":int(entry["start_time"]),
                "duration":int(entry["duration"]),
                "series_id":int(entry["series_id"]),
                "leagueid":int(entry["leagueid"]),
                "sha256_raw_exact":sha(exact),
                "sha256_raw_gzip":sha(packed),
                "source_http_sha256":raw_http_sha,
                "source_slots_checked":detail["verified_team_gold_array_slots"],
                "terminal_or_postterminal_array_slots":detail["terminal_or_postterminal_array_slots"],
            })
        audit.append({
            "match_id":mid,"accepted":reason is None,
            "exclusion_reason":reason,"source_request_attempts":attempts,
        })
        if i< len(listing["selected"])-1:
            time.sleep(0.85)
    return {
        "selection_sha256":sha_file(LISTING),
        "model_lock_sha256":sha_file(LOCK),
        "selected_count":len(listing["selected"]),
        "accepted_count":len(accepted),
        "accepted":accepted,
        "audit":audit,
        "source_games_collected_without_model_scoring":True,
        "all_exclusions_source_only":True,
        "true_received_at_verified":False,
        "outcome_preselection":False,
        "new_http_requests_bounded":True,
    }


def frame_for_score(source:dict)->pd.DataFrame:
    rows=[]
    for ent in source["accepted"]:
        mid=int(ent["match_id"])
        compressed=(DATA/"accepted_raw"/(str(mid)+".json.gz")).read_bytes()
        if sha(compressed)!=ent["sha256_raw_gzip"]:
            raise AssertionError("Source gzip changed after collection")
        rawbytes=gzip.decompress(compressed)
        if sha(rawbytes)!=ent["sha256_raw_exact"]:
            raise AssertionError("Source bytes changed after collection")
        raw=json.loads(rawbytes)
        reason,info=check_payload(raw,ent)
        if reason is not None:
            raise AssertionError("Source accepted eligibility changed: "+reason)
        gold=np.asarray(raw["radiant_gold_adv"],dtype=float)/1000.
        stop=int(math.ceil(float(raw["duration"])/60.))
        for t in range(stop):
            if 60*t>=float(raw["duration"]):
                raise AssertionError("Terminal minute entered forecast")
            q=prefix_path_features(gold[:t+1])
            rows.append({
                "match_id":mid,"minute":t,"series_id":int(ent["series_id"]),
                "leagueid":int(ent["leagueid"]),
                "radiant_win":int(raw["radiant_win"]),
                "gold_k":float(gold[t]),"minute10":float(t/10),
                "gold_x_time":float(gold[t]*math.log1p(t/10)),
                **dict(zip(INPUTS["Q1_path"][2:],q)),
            })
    result=pd.DataFrame(rows)
    if len(result)==0 or result[["match_id","minute"]].duplicated().any():
        raise AssertionError("Fresh scoring opportunity contract invalid")
    return result


def metrics_and_ci(frame:pd.DataFrame,name:str,control:str)->dict:
    losses=frame["ll_"+name].to_numpy()-frame["ll_"+control].to_numpy()
    brier=frame["br_"+name].to_numpy()-frame["br_"+control].to_numpy()
    clusters=cluster_ids(frame[["match_id","series_id"]])
    grouper=pd.DataFrame({"cluster":clusters,"n":1,"ll":losses,"br":brier}).groupby("cluster",sort=True).sum()
    game=(pd.DataFrame({"match_id":frame.match_id,"series_id":frame.series_id,"loss":losses})
        .groupby("match_id",as_index=False,sort=True).agg(series_id=("series_id","first"),loss=("loss","mean")))
    gg=cluster_ids(game[["match_id","series_id"]])
    game["cluster"]=gg
    a=game.assign(n=1).groupby("cluster",sort=True)[["n","loss"]].sum()
    if grouper.shape[0]!=a.shape[0]:
        raise AssertionError("Series cluster mismatch between minute and game rows")
    draws=np.random.default_rng(SEED).integers(0,len(a),size=(DRAWS,len(a)))
    v=grouper[["n","ll"]].to_numpy(dtype=float)[draws].sum(axis=1)
    z=a[["n","loss"]].to_numpy(dtype=float)[draws].sum(axis=1)
    minute_samples=v[:,1]/v[:,0]
    game_samples=z[:,1]/z[:,0]
    late=frame.minute.to_numpy(int)>=30
    mean_game=float(game.loss.mean())
    leave=[]
    groups=a.to_numpy(dtype=float)
    for one in groups:
        other=groups.sum(axis=0)-one
        leave.append(float(other[1]/other[0]))
    return {
        "equal_match_delta_logloss":mean_game,
        "minute_delta_logloss":float(losses.mean()),
        "delta_brier":float(brier.mean()),
        "late30_delta_brier":float(brier[late].mean()) if late.any() else None,
        "equal_match_95_ci":np.quantile(game_samples,[.025,.975]).tolist(),
        "equal_match_9875_ci":np.quantile(game_samples,[.00625,.99375]).tolist(),
        "minute_95_ci":np.quantile(minute_samples,[.025,.975]).tolist(),
        "minute_9875_ci":np.quantile(minute_samples,[.00625,.99375]).tolist(),
        "leave_one_series_out_equal_match": [float(min(leave)),float(max(leave))],
    }


def score()->dict:
    if not LOCK.exists() or not LISTING.exists() or not (DATA/"source_receipt.json").exists():
        raise AssertionError("Freeze model, discovery and source before scoring")
    listing=json.loads(LISTING.read_text())
    lock=json.loads(LOCK.read_text())
    receipt=json.loads((DATA/"source_receipt.json").read_text())
    if receipt["selection_sha256"]!=sha_file(LISTING) or receipt["model_lock_sha256"]!=sha_file(LOCK):
        raise AssertionError("Listing/model lock changed since source collection")
    if listing["reached_start_boundary"] is not True:
        raise AssertionError("Incomplete pro match listing")
    models,model_lock=freeze_models()
    if models.keys()!=lock["models"].keys() or model_lock["models"]!=lock["models"]:
        raise AssertionError("Model train drift since locked coefficients")
    if verify_original_artifacts()!=lock["employer_artifacts"]:
        raise AssertionError("Original Vexil applicant artifacts changed")
    selected={e["match_id"] for e in listing["selected"]}
    accepted={e["match_id"] for e in receipt["accepted"]}
    if not accepted.issubset(selected) or selected&frozen_overlap_ids():
        raise AssertionError("Collection selection overlap or drift")
    frame=frame_for_score(receipt)
    result={}
    target=frame.radiant_win.to_numpy(int)
    late=frame.minute.to_numpy(int)>=30
    for name,model in models.items():
        p=model.predict_proba(frame[list(INPUTS[name])])[:,1]
        ll,br=proper(target,p)
        frame["ll_"+name]=ll
        frame["br_"+name]=br
        result[name]={
            "minute_logloss":float(ll.mean()),
            "equal_match_logloss":float(pd.DataFrame({"match_id":frame.match_id,"ll":ll}).groupby("match_id").ll.mean().mean()),
            "minute_brier":float(br.mean()),
            "late30_brier":float(br[late].mean()) if late.any() else None,
            "range_p":[float(p.min()),float(p.max())],
        }
    compare={k:metrics_and_ci(frame,"MATCH_EQUAL",k) for k in ("M1_interaction","Q1_path")}
    games=int(frame.match_id.nunique())
    units=int(len(set(cluster_ids(frame[["match_id","series_id"]]))))
    leagues=int(frame.leagueid.nunique())
    sufficiently_powered=games>=30 and units>=15 and leagues>=2 and late.any()
    passed=bool(sufficiently_powered and all(
        z["equal_match_delta_logloss"]<=-.005
        and z["equal_match_9875_ci"][1]<0
        and z["delta_brier"]<=0
        and z["late30_delta_brier"]<=0
        for z in compare.values()
    ))
    out={
        "study_status":"NOV17 new source, model post-selected earlier; NOT LIVE validation",
        "unseen_cohort_since_previous_scoring":True,
        "prospectively_collected_in_game_time":False,
        "models_predeclared":list(MODELS),
        "protocol_sha256":sha_file(PROTO),
        "source_receipt_sha256":sha_file(DATA/"source_receipt.json"),
        "selection_sha256":sha_file(LISTING),
        "model_lock_sha256":sha_file(LOCK),
        "source_stats":{"selected":len(selected),"accepted":games,"minute_rows":len(frame),
                        "series":units,"leagues":leagues,
                        "start_time_min":min(e["start_time"] for e in receipt["accepted"]),
                        "start_time_max":max(e["start_time"] for e in receipt["accepted"])},
        "model_scores":result,"paired_match_equal_comparisons":compare,
        "research_gate_evidence_sufficient":sufficiently_powered,
        "research_gate_passed":passed,
        "employer_model_promotion_allowed":False,
        "source_ingress_received_at_verified":False,
        "original_applicant_artifact_hashes":lock["employer_artifacts"],
    }
    return out


def report(r:dict)->str:
    t=r["source_stats"]
    lines=["# Frozen MATCH_EQUAL on fresh Nov17 professional games",
           "",
           "**Retrospective after model selection on older inspected datasets.** New Nov17 source was "
           "discovered and selected after precommitted protocol/model hash, outcomes not used for "
           "inclusion. Not a live packet/arrival-time study.",
           "",
           "Games: **"+str(t["accepted"])+"/"+str(t["selected"])+
           "**; minute rows "+str(t["minute_rows"])+
           "; independent series+singletons "+str(t["series"])+
           "; leagues "+str(t["leagues"])+".",
           "",
           "| Frozen March model | Minute LL | Equal-match LL | Brier | Brier >=30 |",
           "| --- | ---: | ---: | ---: | ---: |"]
    for n in MODELS:
        s=r["model_scores"][n]
        lines.append(f"| {n} | {s['minute_logloss']:.6f} | {s['equal_match_logloss']:.6f} | "
                     f"{s['minute_brier']:.6f} | "
                     +(f"{s['late30_brier']:.6f}" if s['late30_brier'] is not None else "N/A")+" |")
    lines+=["","## Paired MATCH_EQUAL contrasts (negative is better)","",
            "| Comparator | Equal-game LL delta | 95% series CI | 98.75% series CI | "
            "Minute LL delta | 95% series CI | Brier delta | 30+ Brier delta |",
            "| --- | ---: | --- | --- | ---: | --- | ---: | ---: |"]
    for name,v in r["paired_match_equal_comparisons"].items():
        a,b=v["equal_match_95_ci"]
        c,d=v["equal_match_9875_ci"]
        e,f=v["minute_95_ci"]
        lines.append(f"| {name} | {v['equal_match_delta_logloss']:+.6f} | "
          f"[{a:+.6f},{b:+.6f}] | [{c:+.6f},{d:+.6f}] | "
          f"{v['minute_delta_logloss']:+.6f} | [{e:+.6f},{f:+.6f}] | "
          f"{v['delta_brier']:+.6f} | "
          +(f"{v['late30_delta_brier']:+.6f}" if v["late30_delta_brier"] is not None else "N/A")+" |")
    lines+=["",
           "Research gate sufficiently populated: **"+str(r["research_gate_evidence_sufficient"])+"**.",
           "Frozen research superiority gate passed: **"+str(r["research_gate_passed"])+"**.",
           "",
           "No re-fit on November, no original March TEST read. Match outcome labels were "
           "not used in the listing selection or source validity filter.",
           "Actual source received_at remains unavailable; source parser's game clock "
           "cannot certify live PIT availability.",
           "The original employer notebook, original 3,836-forecast TEST, report/PDF "
           "and submission ZIP were not modified. Do not promote this to employer release.",
           ""]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["freeze","discover","collect","score"])
    args=ap.parse_args()
    if args.action=="freeze":
        _,locked=freeze_models()
        dump(LOCK,locked)
        print("MODEL_FROZEN",sha_file(LOCK))
    elif args.action=="discover":
        result=discover()
        dump(LISTING,result)
        print("DISCOVERY_FROZEN",result["reached_start_boundary"],
              "pages",len(result["pages"]),"eligible",result["valid_candidates_in_window"],
              "selected",result["selected_games"],"sha",sha_file(LISTING))
    elif args.action=="collect":
        result=collect()
        dump(DATA/"source_receipt.json",result)
        print("SOURCE_COLLECTED selected",result["selected_count"],
              "accepted",result["accepted_count"],"sha",sha_file(DATA/"source_receipt.json"))
        print("EXCLUSION_COUNTS",dict(collections.Counter(
            row["exclusion_reason"] for row in result["audit"] if not row["accepted"]
        )))
    elif args.action=="score":
        r=score()
        dump(FINAL,r)
        READOUT.write_text(report(r))
        print(report(r))


if __name__=="__main__":
    main()
