#!/usr/bin/env python3
"""Locked, no-retuning forward domain-shift check. See committed PROTOCOL.md."""
from __future__ import annotations
import argparse, ast, collections, datetime as dt, gzip, hashlib, json, math
import os, time, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

ROOT=Path(__file__).resolve().parents[2]
SOURCE_NOTEBOOK=ROOT/"research/frozen_original_notebook_source.json"
TRAIN_CSV=ROOT/"research/frozen_original_train_features.csv.gz"
DATA_SHA="066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
CODE_SHA="e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b"
LISTING_SHA=None  # Hash frozen listing at scoring time; do not choose by labels.
FIRST=100
FETCH_LIMIT=500
MAX_START=int(dt.datetime(2026,11,16,tzinfo=dt.timezone.utc).timestamp())
MIN_START=int(dt.datetime(2026,10,1,tzinfo=dt.timezone.utc).timestamp())
FEATURE_COLUMNS=("gold_k","minute10","gold_x_time","xp_k","gold_velocity5_k",
                 "xp_velocity5_k","tower_delta","barracks_delta","roshan_delta","kill_delta")
SEED=20261113

def sha(x:bytes):return hashlib.sha256(x).hexdigest()

def frozen_functions():
    notebook=json.loads(SOURCE_NOTEBOOK.read_text())
    code="".join("".join(cell["source"]) for i,cell in enumerate(notebook["cells"])
                 if cell["cell_type"]=="code" and i!=2)
    if sha(code.encode())!=CODE_SHA:raise ValueError("Frozen notebook science code drift")
    cell7="".join(notebook["cells"][7]["source"])
    fragment=cell7.split("\nminute_table = make_minute_table(matches)",1)[0]
    if "def make_minute_table(games)" not in fragment:raise ValueError("Cannot source feature functions")
    namespace={"np":np,"pd":pd,"math":math,"FEATURE_COLUMNS":FEATURE_COLUMNS}
    exec(compile(fragment,"frozen_original_notebook_cell7","exec"),namespace)
    need=("validate_minute_alignment","snapshot_features","make_minute_table")
    if any(k not in namespace for k in need):raise ValueError("Original feature extractor incomplete")
    return namespace

def models_from_frozen_train():
    if sha(TRAIN_CSV.read_bytes())!=DATA_SHA:
        raise ValueError("Original development TRAIN source checksum differs")
    train=pd.read_csv(TRAIN_CSV)
    if (len(train)!=10675 or train.match_id.nunique()!=291
            or set(train.partition)!={"train"}):
        raise ValueError("Frozen original TRAIN split no longer 291 games")
    nb=json.loads(SOURCE_NOTEBOOK.read_text())
    cell12="".join(nb["cells"][12]["source"])
    before=cell12.split("\nmodels = {name: fit_model(train, cols)",1)[0]
    if "def fit_model(frame, columns)" not in before:
        raise ValueError("Cannot extract original fit_model source")
    environment={"Pipeline":Pipeline,"SimpleImputer":SimpleImputer,
                 "StandardScaler":StandardScaler,"LogisticRegression":LogisticRegression,
                 "SEED":SEED}
    exec(compile(before,"frozen_original_notebook_cell12","exec"),environment)
    fit_model=environment["fit_model"]
    specs={"M0":["gold_k"],"M1":["gold_k","minute10","gold_x_time"]}
    models={name:fit_model(train,cols) for name,cols in specs.items()}
    # Freeze fitted coefficients/standardization fingerprints BEFORE scoring.
    fingerprints={}
    for name,model in models.items():
        numeric=np.concatenate([model.named_steps["scale"].mean_,
                       model.named_steps["scale"].scale_,
                       model.named_steps["logistic"].coef_.ravel(),
                       model.named_steps["logistic"].intercept_.ravel()])
        fingerprints[name]=sha(np.asarray(numeric,dtype="<f8").tobytes())
    return models,specs,fingerprints

def eligible(payload,expected_mid,listed_start,features):
    """All exclusions are based on metadata/source validity, not model score."""
    if not isinstance(payload,dict) or type(payload.get("match_id"))!=int:
        return "identity_missing"
    if payload["match_id"]!=expected_mid:return "identity_mismatch"
    try:
        start=int(payload["start_time"])
    except (TypeError,ValueError,KeyError):return "missing_start"
    if start!=listed_start:return "listing_start_drift"
    if not MIN_START<=start<MAX_START:return "outside_window"
    if payload.get("patch") is None:return "missing_patch"
    if type(payload.get("radiant_win")) is not bool:return "missing_final_outcome"
    duration=payload.get("duration")
    if type(duration) not in (int,float) or not math.isfinite(duration) or duration<600:
        return "under_ten_minutes"
    if not isinstance(payload.get("radiant_gold_adv"),list) or not payload["radiant_gold_adv"]:
        return "unparsed_gold"
    if not isinstance(payload.get("radiant_xp_adv"),list) or not payload["radiant_xp_adv"]:
        return "unparsed_xp"
    try:
        features["validate_minute_alignment"](payload)
    except (ValueError,TypeError,KeyError,AssertionError):
        return "invalid_or_incomplete_minute_clock"
    return None

def get_payload(session,mid,last_api_timestamp):
    """Bounded 9-attempt retry. No fallback to an alternate endpoint."""
    url="https://api.opendota.com/api/matches/"+str(mid)
    attempts=0
    last_error=None
    for retry in range(9):
        gap=time.monotonic()-last_api_timestamp
        if gap<1.65:time.sleep(1.65-gap)
        last_api_timestamp=time.monotonic()
        try:
            r=session.get(url,timeout=(8,35))
            attempts+=1
            if r.status_code==404:
                return {},last_api_timestamp,attempts,"not_found"
            if r.status_code==429 or r.status_code in (500,502,503,504):
                h=r.headers.get("Retry-After","")
                try:wait=float(h)
                except ValueError:wait=max(8.,min(60.,2**retry))
                time.sleep(min(max(8.,wait),60.))
                last_error="HTTP "+str(r.status_code)
                continue
            r.raise_for_status()
            return r.json(),last_api_timestamp,attempts,None
        except (requests.RequestException,ValueError) as e:
            last_error=type(e).__name__+" "+str(e)[:100]
            time.sleep(min(2**retry,32))
    raise RuntimeError("Network retries exhausted at match "+str(mid)+": "+str(last_error))

def collect(listing:Path,output_dir:Path,features):
    if output_dir.exists():
        raise FileExistsError("Forward collection is immutable once started; never overwrite")
    data=json.loads(listing.read_text())
    assert data["protocol"].endswith("9d6cddf") and data["page_count"]==15
    candidates=data["candidate_ids_and_start_times"]
    if candidates!=sorted(candidates,key=lambda x:x["match_id"],reverse=True):
        raise ValueError("Discovery order was modified")
    if len(candidates)<FIRST:raise ValueError("Too few potential matches in fixed listing")
    output_dir.mkdir(parents=True)
    source=output_dir/"accepted_raw"
    source.mkdir()
    log=[]
    accepted=[]
    calls=0
    session=requests.Session()
    session.headers["User-Agent"]="vexil-frozen-model-forward-science/1.0"
    last_time=0.
    try:
        for i,row in enumerate(candidates[:FETCH_LIMIT]):
            mid=int(row["match_id"])
            result,last_time,attempts,download_error=get_payload(session,mid,last_time)
            calls+=attempts
            if download_error is not None:
                reason=download_error
            else:
                reason=eligible(result,mid,int(row["start_time"]),features)
            if reason is None:
                compressed=source/(str(mid)+".json.gz")
                with gzip.open(compressed,"wt",encoding="utf8") as z:
                    json.dump(result,z,separators=(",",":"),sort_keys=True)
                accepted.append({"match_id":mid,"start_time":int(row["start_time"]),
                                 "series_id":int(result.get("series_id") or 0),
                                 "patch":str(result["patch"]),
                                 "duration":int(result["duration"]),
                                 "raw_sha256":sha(json.dumps(result,sort_keys=True,
                                               separators=(",",":")).encode())})
            log.append({"match_id":mid,"start_time":int(row["start_time"]),
                        "accepted":reason is None,
                        "reason":"eligible" if reason is None else reason})
            if (i+1)%15==0:
                print("DETAIL",i+1,"ACCEPTED",len(accepted),
                      "REJECT",dict(collections.Counter(z["reason"] for z in log if not z["accepted"])),
                      flush=True)
            # Audit checkpoint, can be resumed only with original immutable IDs and
            # existing exact raw payloads; do not skip already scored IDs.
            if len(accepted)>=FIRST:break
    finally:
        session.close()
        manifest={
          "listing_sha256":sha(listing.read_bytes()),
          "first_eligible_target":FIRST,"max_details":FETCH_LIMIT,
          "details_queried":len(log),"http_attempts":calls,
          "accepted_count":len(accepted),"rejection_reasons":dict(collections.Counter(
            x["reason"] for x in log if not x["accepted"])),
          "eligible":accepted,"candidate_audit":log,
          "complete":len(accepted)==FIRST
        }
        (output_dir/"collection_receipt.json").write_text(
            json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        print("COLLECTION_RESULT",len(accepted),"/",FIRST,"DETAILS",len(log),
              "CALLS",calls,"COMPLETE",manifest["complete"],flush=True)
    if len(accepted)<FIRST:raise RuntimeError("PREDECLARED COHORT INCOMPLETE; preserve manifest, do not change inclusion")
    return accepted,manifest

def ll(y,p):
    p=np.clip(p,1e-15,1-1e-15)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def ece(y,p):
    indices=np.clip((np.asarray(p)*10).astype(int),0,9)
    value=0.
    for k in range(10):
        m=indices==k
        if m.any():value+=m.mean()*abs(np.mean(y[m])-np.mean(p[m]))
    return float(value)

def summarize(frame,meta,model_fingerprints,raw_manifest):
    y=frame.radiant_win.to_numpy(dtype=int)
    p0=frame.p_M0.to_numpy(float);p1=frame.p_M1.to_numpy(float)
    if any(not np.isfinite(p).all() for p in (p0,p1)):raise ValueError("Nonfinite probability")
    if any(not ((p>0)&(p<1)).all() for p in (p0,p1)):raise ValueError("Invalid probability")
    nrows=len(frame)
    l0=ll(y,p0);l1=ll(y,p1)
    b0=(y-p0)**2;b1=(y-p1)**2
    x=frame.copy()
    x["d_ll"]=l1-l0;x["d_brier"]=b1-b0
    groups=x.merge(meta[["match_id","series_id"]],on="match_id",validate="many_to_one")
    groups["cluster"]=groups.apply(
        lambda row:"s"+str(int(row.series_id)) if int(row.series_id)>0 else
             "m"+str(int(row.match_id)),axis=1)
    keys,inds=np.unique(groups.cluster.to_numpy(str),return_inverse=True)
    counts=np.bincount(inds).astype(float)
    rng=np.random.default_rng(20261115)
    n=len(keys)
    draws=rng.integers(0,n,size=(5000,n))
    def ci_delta(arr):
        tot=np.bincount(inds,weights=np.asarray(arr),minlength=n)
        means=tot[draws].sum(axis=1)/counts[draws].sum(axis=1)
        return list(map(float,np.quantile(means,(.025,.975))))
    phases={}
    for name,low,high in [("0-9",0,10),("10-19",10,20),("20-29",20,30),("30+",30,9999)]:
        sub=x[(x.minute>=low)&(x.minute<high)]
        if len(sub)==0:
            phases[name]={"minute_rows":0}
            continue
        o=sub.radiant_win.to_numpy(dtype=int)
        phases[name]={"minute_rows":len(sub),
           "games":int(sub.match_id.nunique()),
           "brier_M0":float(((o-sub.p_M0)**2).mean()),
           "brier_M1":float(((o-sub.p_M1)**2).mean()),
           "ece_M0":ece(o,sub.p_M0),
           "ece_M1":ece(o,sub.p_M1)}
    per_match=groups.groupby("match_id")[["d_ll","d_brier"]].mean()
    out={
      "status":"PRESPECIFIED_POSTTEST_DOMAIN_SHIFT_CHECK; NO MODEL PROMOTION",
      "candidate_listing_sha256":raw_manifest["listing_sha256"],
      "selection_rule":"first 100 eligible in descending frozen proMatches match_id",
      "games":int(frame.match_id.nunique()),
      "clusters":len(keys),"minutes":nrows,
      "date_min_utc":dt.datetime.fromtimestamp(int(meta.start_time.min()),dt.timezone.utc).isoformat(),
      "date_max_utc":dt.datetime.fromtimestamp(int(meta.start_time.max()),dt.timezone.utc).isoformat(),
      "patch_counts":{str(k):int(v) for k,v in meta.patch.value_counts().items()},
      "radiant_win_rate_minute_rows":float(y.mean()),
      "radiant_win_rate_game_weighted":float(meta.radiant_win.mean()),
      "mean_prob_M0":float(p0.mean()),"mean_prob_M1":float(p1.mean()),
      "M0":{"logloss":float(l0.mean()),"brier":float(b0.mean()),"ece":ece(y,p0)},
      "M1":{"logloss":float(l1.mean()),"brier":float(b1.mean()),"ece":ece(y,p1)},
      "M1_minus_M0":{
         "logloss":float((l1-l0).mean()),
         "logloss_ci_95_series":ci_delta(l1-l0),
         "brier":float((b1-b0).mean()),
         "brier_ci_95_series":ci_delta(b1-b0),
         "equal_game_weighted_logloss_diff":float(per_match.d_ll.mean()),
         "equal_game_weighted_brier_diff":float(per_match.d_brier.mean())},
      "phase_descriptive":phases,
      "bootstrap":{"groups":"series_id positive else singleton match",
                   "draws":5000,"seed":20261115},
      "source_model_coeff_sha256":model_fingerprints,
      "source_train_sha256":DATA_SHA,"original_science_code_sha256":CODE_SHA,
      "no_forward_cohort_fit":True,"no_recalibration":True,
      "original_500_test_predictions_changed":False,
      "no_live_packet_timing":True,
    }
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--listing",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    functions=frozen_functions()
    models,specs,fingerprints=models_from_frozen_train()
    # Model and cohort protocol are committed/frozen BEFORE any new label access.
    accepted,audit=collect(args.listing,args.output_dir,functions)
    matches=[]
    for item in accepted:
        with gzip.open(args.output_dir/"accepted_raw"/(str(item["match_id"])+".json.gz"),"rt") as f:
            match=json.load(f)
        if eligible(match,item["match_id"],item["start_time"],functions) is not None:
            raise ValueError("Previously accepted match now ineligible")
        matches.append(match)
    forward=functions["make_minute_table"](matches)
    meta=pd.DataFrame([{"match_id":int(m["match_id"]),
                        "start_time":int(m["start_time"]),
                        "series_id":int(m.get("series_id") or 0),
                        "patch":str(m["patch"]),"radiant_win":int(m["radiant_win"])}
                       for m in matches])
    for name,model in models.items():
        forward["p_"+name]=model.predict_proba(forward[specs[name]])[:,1]
    receipt=summarize(forward,meta,fingerprints,audit)
    (args.output_dir/"forward_scores.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    forward[["match_id","minute","radiant_win","p_M0","p_M1"]].to_csv(
        args.output_dir/"forward_predictions.csv",index=False)
    print("SCORES",json.dumps({k:receipt[k] for k in ("games","minutes","M0","M1","M1_minus_M0")}),flush=True)
    print("NO PROMOTION",flush=True)

if __name__=="__main__":main()
