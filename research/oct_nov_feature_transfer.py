#!/usr/bin/env python3
"""Historical October/November transfer falsifier for a fixed March-trained ALL/Q1.

Existing Oct/Nov outcomes were already observed for M0/M1; this is NOT blind.
No external API calls, no employer-facing model selection or source mutation.
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

from all_family_features import (
    COLS, build_frozen_train, mirror, one_snapshot,
    parse_item_milestones, parse_objectives,
)
from all_family_models import INPUTS,verify_original_artifacts
from cross_array_time_alignment import check_single_game
from quant_bible_path_risk_train_only import prefix_path_features
from rich_feature_models import create_pipeline, load_train, proper
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"research/OCT_NOV_FEATURE_TRANSFER_PROTOCOL_20261118.md"
OUT=ROOT/"research/OCT_NOV_FEATURE_TRANSFER_RECEIPT.json"
MD=ROOT/"research/OCT_NOV_FEATURE_TRANSFER_READOUT.md"
SCOPE={
    "October": {
        "root":Path("/srv/ai/tmp/vexil-october-raw-20261117"),
        "n_games":180, "n_rows":7346, "n_series":107,
        "collection_hash":"700ecf86ad7245cb9acf72d3a67321050c4eafa488565a7f61bdc2ce7de55bb8",
        "metadata_hash":"03cded4444dfed2286af7f20add8e59433fe67dbddbe2e4c71741a6bf3c54e4d",
        "predictions_hash":"3c0a4404294fbafec61bd518bdc41b95d7b631c830da31af6d90c91c663ebdf0",
    },
    "November":{
        "root":Path("/srv/ai/tmp/vexil-prospective-nov17-data-20261117"),
        "n_games":22, "n_rows":952, "n_series":9,
        "collection_hash":"347729971519f1a65ad00e93c1ab739c0b2ab8db2d7864f763f4f5d850285b33",
        "metadata_hash":"911d8589d0ad44948ea1ed66cf41b708c6ee565e3fbfcb3e9908936a2faa580e",
        "predictions_hash":"b8fba05d2be581c797b35dbf28506e95bf378960dd6b60dc223d1220eeda9788",
    },
}
MODEL_NAMES=("M0_gold","M1_interaction","Q1_path","ALL")
SEED,DRAWS=20261118,5000
Q1=tuple(INPUTS["Q1_path"])
NINE=tuple(COLS)


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_scope_file(root:Path,name:str,expected:str):
    h=sha256(root/name)
    if h!=expected:
        raise AssertionError("Previously scored later-source file changed: "+str(root/name))


def load_raw_octnov(name:str, spec:dict)->tuple[pd.DataFrame,pd.DataFrame,dict]:
    root=spec["root"]
    for fname,key in (("collection_receipt.json","collection_hash"),
                      ("metadata.csv","metadata_hash"),
                      ("predictions.csv","predictions_hash")):
        check_scope_file(root,fname,spec[key])
    info=json.loads((root/"collection_receipt.json").read_text())
    meta=pd.read_csv(root/"metadata.csv")
    locked=pd.read_csv(root/"predictions.csv")
    if (len(meta)!=spec["n_games"] or len(locked)!=spec["n_rows"]
        or meta.match_id.nunique()!=spec["n_games"]
        or locked[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Frozen later cohort row count or keys changed")
    if set(meta.match_id)!=set(locked.match_id):
        raise AssertionError("Original scored IDs differ from metadata")
    indexed_receipt={int(x["match_id"]):x for x in info.get("accepted",[])}
    if len(indexed_receipt)!=spec["n_games"]:
        raise AssertionError("Original accepted game raw manifest changed")
    matches=[]
    parity=0
    swap=0
    for row in meta.itertuples(index=False):
        match_id=int(row.match_id)
        p=root/"accepted_raw"/(str(match_id)+".json.gz")
        if sha256(p)!=indexed_receipt[match_id]["raw_gzip_sha256"]:
            raise AssertionError("Raw JSON cache hash mismatch")
        raw=json.loads(gzip.decompress(p.read_bytes()))
        if (int(raw["match_id"])!=match_id or int(raw["start_time"])!=int(row.start_time)
            or int(raw["series_id"])!=int(row.series_id)
            or int(raw["radiant_win"])!=int(row.radiant_win)
            or str(raw["patch"])!=str(row.patch)):
            raise AssertionError("Original source metadata parity drift")
        source_audit=check_single_game(raw)
        if source_audit["verified_team_gold_array_slots"]!=len(raw["radiant_gold_adv"]):
            raise AssertionError("Raw team economy index alignment")
        parity+=source_audit["verified_team_gold_array_slots"]
        gold=np.asarray(raw["radiant_gold_adv"],dtype=float)/1000
        events=parse_objectives(raw)
        items=parse_item_milestones(raw)
        neg_events,neg_items=mirror(events,items)
        duration=int(raw["duration"])
        if len(gold)==0 or len(gold)<math.ceil(duration/60):
            raise AssertionError("Original raw minute history too short")
        pred=locked[locked.match_id==match_id].sort_values("minute",kind="stable")
        ts=pred.minute.to_numpy(dtype=int)
        if not np.array_equal(ts,np.arange(len(pred),dtype=int)):
            raise AssertionError("Original prediction minute grid changed")
        if not (ts[-1]*60<duration and np.all(60*ts<duration)
                and len(pred)==int(math.ceil(duration/60))):
            raise AssertionError("Original nonterminal prediction time scope drift")
        feats=[]
        for t in ts:
            row_vals=one_snapshot(gold,int(t),events,items)
            swapped=one_snapshot(-gold,int(t),neg_events,neg_items)
            if not np.allclose(list(row_vals.values()),
                               -np.asarray(list(swapped.values())),rtol=0,atol=1e-10):
                raise AssertionError("New family feature violates side-swap symmetry")
            swap+=1
            history=gold[:t+1]
            q=prefix_path_features(history)
            base={
                "match_id":match_id,
                "minute":int(t),
                "radiant_win":int(row.radiant_win),
                "series_id":int(row.series_id),
                "league_id":int(row.league_id),
                "start_time":int(row.start_time),
                "gold_k":float(gold[t]),
                "minute10":float(t/10.),
                "gold_x_time":float(gold[t]*math.log1p(t/10.)),
                **dict(zip(Q1[2:],q)),
                **row_vals,
            }
            if not np.isfinite(np.asarray([base[k] for k in MODEL_NAMES_INPUTS_ALL],dtype=float)).all():
                raise AssertionError("Nonfinite external feature vector")
            feats.append(base)
        matches.extend(feats)
    result=pd.DataFrame(matches).sort_values(["match_id","minute"],kind="stable").reset_index(drop=True)
    original=locked.sort_values(["match_id","minute"],kind="stable").reset_index(drop=True)
    if len(result)!=spec["n_rows"] or not np.array_equal(
        result[["match_id","minute"]],original[["match_id","minute"]]):
        raise AssertionError("Original scored keys do not align with new raw replay features")
    if not np.array_equal(result.radiant_win.to_numpy(dtype=int),
                          original.radiant_win.to_numpy(dtype=int)):
        raise AssertionError("Original final outcomes differ from source")
    groups=len(set(cluster_ids(result[["match_id","series_id"]])))
    if groups!=spec["n_series"]:
        raise AssertionError("Original series grouping drift")
    return result,original,{"scope":name,"games":len(meta),"rows":len(result),"groups":groups,
          "raw_team_cross_array_slots_verified":parity,
          "side_mirror_checks":swap,
          "new_raw_downloads":0,
          "predictor_ingress_timestamp_verified":False}


MODEL_NAMES_INPUTS_ALL=tuple(INPUTS["ALL"])


def paired_series_metric(rows:pd.DataFrame,lhs:str,rhs:str,seed:int)->dict:
    ll=rows["ll_"+lhs].to_numpy()-rows["ll_"+rhs].to_numpy()
    br=rows["br_"+lhs].to_numpy()-rows["br_"+rhs].to_numpy()
    unit=rows[["match_id","series_id"]].copy()
    unit["cluster"]=cluster_ids(unit)
    unit["ll"]=ll
    unit["br"]=br
    grouped=unit.groupby("cluster",sort=True).agg(
        n=("ll","size"),sl=("ll","sum"),sb=("br","sum"))
    nclusters=len(grouped)
    if nclusters<2:
        raise AssertionError("Insufficient independent groups")
    a=grouped[["n","sl","sb"]].to_numpy(dtype=float)
    ids=np.random.default_rng(seed).integers(0,len(a),size=(DRAWS,len(a)))
    picked=a[ids].sum(axis=1)
    samples=picked[:,1:]/picked[:,0,None]
    if not np.isfinite(samples).all():
        raise AssertionError("Bootstrap loss samples invalid")
    late=rows.minute.to_numpy(int)>=30
    if not late.any():
        raise AssertionError("Missing minute 30+ phase")
    oof_match=pd.DataFrame({"id":rows.match_id,"ll":ll}).groupby("id").ll.mean()
    leave_one_out=[]
    for i in range(len(a)):
        remain=np.delete(a,i,axis=0)
        leave_one_out.append(float(remain[:,1].sum()/remain[:,0].sum()))
    total_gain=-ll.sum()
    positive=(-grouped.sl).clip(lower=0)
    return {
        "delta_ll":float(ll.mean()),
        "delta_brier":float(br.mean()),
        "late30_delta_brier":float(br[late].mean()),
        "equal_match_delta_ll":float(oof_match.mean()),
        "series_bootstrap_95_ll":np.quantile(samples[:,0],[.025,.975]).tolist(),
        "series_bootstrap_95_brier":np.quantile(samples[:,1],[.025,.975]).tolist(),
        "leave_one_series_out_ll_min":min(leave_one_out),
        "leave_one_series_out_ll_max":max(leave_one_out),
        "most_positive_series_share":float(positive.max()/total_gain) if total_gain>0 else None,
    }


def evaluate()->dict:
    if not PROTO.exists():
        raise AssertionError("Pre-scoring external transfer protocol missing")
    artifact_hashes=verify_original_artifacts()
    train,source=load_train()
    fitted_train,feature_source=build_frozen_train(train)
    if set(fitted_train.partition)!={"train"}:
        raise AssertionError("Unexpected held-out March source in fitted models")
    models={}
    for name in MODEL_NAMES:
        inputs=INPUTS[name]
        model=create_pipeline(name)
        model.fit(fitted_train[inputs],fitted_train.radiant_win.astype(int))
        models[name]=model
    results={}
    cohort_ids={}
    for title,scope in SCOPE.items():
        matrix,previous,proof=load_raw_octnov(title,scope)
        cohort_ids[title]=set(matrix.match_id)
        for name in MODEL_NAMES:
            p=models[name].predict_proba(matrix[INPUTS[name]])[:,1]
            ll,br=proper(matrix.radiant_win.to_numpy(dtype=int),p)
            matrix["ll_"+name]=ll
            matrix["br_"+name]=br
            matrix["p_"+name]=p
        for name in ("M0_gold","M1_interaction"):
            prev_col="p_M0" if name=="M0_gold" else "p_M1"
            maxerr=float(np.max(np.abs(matrix["p_"+name]-previous[prev_col])))
            if maxerr>1e-7:
                raise AssertionError("Original "+title+" "+name+" prediction parity "+str(maxerr))
            proof["max_earlier_probability_parity_"+name]=maxerr
        y=matrix.radiant_win.to_numpy(dtype=int)
        scores={}
        for name in MODEL_NAMES:
            ll=matrix["ll_"+name].to_numpy(float)
            br=matrix["br_"+name].to_numpy(float)
            scores[name]={
                "logloss":float(ll.mean()),
                "brier":float(br.mean()),
                "late30_brier":float(br[matrix.minute.to_numpy(dtype=int)>=30].mean()),
                "equal_match_logloss":float(
                    matrix[["match_id","ll_"+name]].groupby("match_id")["ll_"+name].mean().mean()),
            }
        compared={
            "ALL_minus_Q1":paired_series_metric(matrix,"ALL","Q1_path",SEED),
            "ALL_minus_M1":paired_series_metric(matrix,"ALL","M1_interaction",SEED),
            "ALL_minus_M0":paired_series_metric(matrix,"ALL","M0_gold",SEED),
            "Q1_minus_M1":paired_series_metric(matrix,"Q1_path","M1_interaction",SEED),
        }
        # The accepted "NO-POSTHOC-PROMOTION" rule is unconditional.
        falsified=bool(compared["ALL_minus_Q1"]["delta_ll"]>=.005)
        results[title]={
            "data_provenance":proof,
            "period_scoring":scores,
            "comparisons":compared,
            "ALL_outperformance_robustness_refuted":falsified,
            "genuinely_blind_new_validation":False,
        }
    if cohort_ids["October"]&cohort_ids["November"]:
        raise AssertionError("Two reused periods overlap")
    if cohort_ids["October"]&set(fitted_train.match_id) or cohort_ids["November"]&set(fitted_train.match_id):
        raise AssertionError("Original March TRAIN contaminated future periods")
    if verify_original_artifacts()!=artifact_hashes:
        raise AssertionError("Original employer artifacts changed")
    return {
        "status":"202 historical matches 2 reused out-of-time periods, not blind",
        "scientific_class":"post-result and post model-search exploratory falsification",
        "protocol_sha256":sha256(PROTO),
        "original_march_train_sha256":source["source_train_sha256"],
        "march_feature_source":feature_source,
        "submission_file_hashes":artifact_hashes,
        "cohorts":results,
        "cohorts_disjoint":True,
        "periods_held_out_from_fitting":True,
        "original_march_VAL_TEST_read":False,
        "new_external_HTTP_requests":0,
        "candidate_promoted":False,
        "live_received_at_verified":False,
    }


def report(receipt:dict)->str:
    rows=[
        "# Fixed March-trained rich-features on October and November reused cohorts",
        "",
        "**Research-only transfer falsification. Earlier M0/M1 October and November outcomes had already been scored. "
        "Not a blind independent validation and never model promotion.**",
        "",
        "| Cohort | Games / rows / series | M0 log loss | M1 log loss | Q1 log loss | ALL log loss | "
        "ALL−Q1 LL (95% series bootstrap) | ALL−Q1 equal-match LL |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for name in ("October","November"):
        e=receipt["cohorts"][name]
        p=e["data_provenance"]
        s=e["period_scoring"]
        c=e["comparisons"]["ALL_minus_Q1"]
        lo,hi=c["series_bootstrap_95_ll"]
        rows.append(f"| {name} | {p['games']} / {p['rows']} / {p['groups']} | "
                    + " | ".join(f"{s[k]['logloss']:.6f}" for k in MODEL_NAMES)
                    + f" | {c['delta_ll']:+.6f} [{lo:+.6f},{hi:+.6f}] | "
                    + f"{c['equal_match_delta_ll']:+.6f} |")
    rows+=["",
       "## Comparison and generalization audit",
       "",
       "| Cohort | ALL−M1 LL | ALL−M0 LL | ALL−Q1 Brier | ALL−Q1 Brier 30+ | "
       "Delete-one-series ALL−Q1 LL range | Frozen refutation threshold reached? |",
       "| --- | ---: | ---: | ---: | ---: | --- | --- |"]
    for name in ("October","November"):
        e=receipt["cohorts"][name]
        c=e["comparisons"]["ALL_minus_Q1"]
        rows.append(f"| {name} | "
                    f"{e['comparisons']['ALL_minus_M1']['delta_ll']:+.6f} | "
                    f"{e['comparisons']['ALL_minus_M0']['delta_ll']:+.6f} | "
                    f"{c['delta_brier']:+.6f} | {c['late30_delta_brier']:+.6f} | "
                    f"[{c['leave_one_series_out_ll_min']:+.6f},"
                    f"{c['leave_one_series_out_ll_max']:+.6f}] | "
                    f"{e['ALL_outperformance_robustness_refuted']} |")
    rows+=["",
       "## Reproduction and scientific limitations",
       "",
       "- Fit all four fixed model recipes once on original March TRAIN only. "
       "The original 202 October/November metadata, previously scored rows, raw gz files "
       "and per-match hash manifests were verified; no new network downloads.",
       "- M0/M1 predictions independently re-created against earlier saved probabilities "
       "within 1e-7; all held-out source rows exact (match_id,minute) match.",
       "- Even an ALL improvement in both periods cannot repair prior broad March feature search "
       "or the fact these October/November outcomes were already observed for M0/M1.",
       "- True live per-source ingress timestamps remain unverified. OpenDota post-game "
       "parser coherence does not prove fresh live availability.",
       "- Original notebook, heldout TEST CSV, report, reviewer ZIP and Draft PR #9 unchanged.",
       "",
    ]
    return "\n".join(rows)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    r=evaluate()
    print(report(r))
    if args.write:
        OUT.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
        MD.write_text(report(r))
