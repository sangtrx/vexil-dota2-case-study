#!/usr/bin/env python3
"""Exactly 5 frozen candidate families; TRAIN-forward 137-game falsification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from all_family_features import COLS, FAMILY, PROTO, build_frozen_train
from conditional_gold_forward import FROZEN_CUTS
from quant_path_signature_models import verify_original_artifacts
from rich_feature_models import MODELS, create_pipeline, load_train, proper
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/ALL_FAMILY_RESULTS.json"
READOUT=ROOT/"research/ALL_FAMILY_RESULTS.md"
PRIOR=ROOT/"research/QUANT_BIBLE_PATH_RECEIPT.json"
SEED,DRAWS=20261118,5000
BASE="M1_interaction"
OTHER="Q1_path"
CONTROLS=("M0_gold","A_additive",BASE,OTHER)
CANDIDATES=tuple(FAMILY)+("ALL",)
INPUTS={k:MODELS[k] for k in CONTROLS}
INPUTS.update({k:MODELS[BASE]+list(FAMILY[k]) for k in FAMILY})
INPUTS["ALL"]=MODELS[BASE]+list(COLS)


def series_delta(oof:pd.DataFrame,candidate:str,rival:str,indices:np.ndarray)->dict:
    d_ll=oof["ll_"+candidate].to_numpy(float)-oof["ll_"+rival].to_numpy(float)
    d_br=oof["br_"+candidate].to_numpy(float)-oof["br_"+rival].to_numpy(float)
    ids=cluster_ids(oof[["match_id","series_id"]])
    g=oof[["match_id","series_id"]].copy()
    g["cluster"]=ids
    g["dl"]=d_ll
    g["db"]=d_br
    agg=g.groupby("cluster",sort=True).agg(n=("dl","size"),sl=("dl","sum"),sb=("db","sum"))
    if len(agg)!=70 or indices.shape!=(DRAWS,70):
        raise AssertionError("Independent group count/bootstrap definition drift")
    a=agg[["n","sl","sb"]].to_numpy(float)
    picked=a[indices].sum(axis=1)
    sampled=picked[:,1:]/picked[:,0,None]
    if not np.isfinite(sampled).all():
        raise AssertionError("Bootstrap sampling invalid")
    lohi=np.quantile(sampled[:,0],[.025,.975])
    familywise=np.quantile(sampled[:,0],[.0025,.9975])
    late=oof.minute.to_numpy(int)>=30
    per_match=(oof[["match_id"]].copy().assign(dll=d_ll)
               .groupby("match_id",sort=True).dll.mean().mean())
    overall_gain=-d_ll.sum()
    gain=(-agg.sl).clip(lower=0)
    return {
      "delta_logloss":float(d_ll.mean()),
      "delta_brier":float(d_br.mean()),
      "late30_delta_brier":float(d_br[late].mean()),
      "per_match_weighted_delta_logloss":float(per_match),
      "series_bootstrap_95_ll":lohi.tolist(),
      "series_bootstrap_995_ll_bonf_10_tests":familywise.tolist(),
      "favorable_series":int((agg.sl<0).sum()),
      "biggest_positive_gain_share":float(gain.max()/overall_gain)
                                    if overall_gain>0 else None,
    }


def evaluate()->dict:
    if not PROTO.is_file():
        raise AssertionError("Precommitted scientific trial registry missing")
    protected=verify_original_artifacts()
    df,provenance=load_train()
    df,feature_report=build_frozen_train(df)
    if len(INPUTS)!=9 or len(CANDIDATES)!=5 or len(COLS)!=9:
        raise AssertionError("Frozen 5-family study candidate/feature count drift")
    for name in CANDIDATES:
        if len(INPUTS[name])!=3+(9 if name=="ALL" else len(FAMILY[name])):
            raise AssertionError("Candidate regression input set changed")
    prior=json.loads(PRIOR.read_text())
    meta=(df[["match_id","start_time","duration","series_id","patch_audit"]]
          .drop_duplicates().sort_values(["start_time","match_id"],
                                          kind="stable").reset_index(drop=True))
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("TRAIN time/series fold contract drift")
    fold_reports=[]
    scored=[]
    for idx,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        earlier,current=meta.iloc[:left],meta.iloc[left:right]
        cutoff=int(current.iloc[0].start_time)
        matured=earlier[earlier.start_time+earlier.duration<=cutoff]
        if (set(cluster_ids(earlier))&set(cluster_ids(current))
            or set(cluster_ids(matured))&set(cluster_ids(current))):
            raise AssertionError("Independent series crosses fold")
        fit=df[df.match_id.isin(matured.match_id)]
        ev=df[df.match_id.isin(current.match_id)]
        if len(fit)==0 or len(ev)==0 or set(fit.match_id)&set(ev.match_id):
            raise AssertionError("Train/validation match ID overlap")
        y=ev.radiant_win.to_numpy(int)
        result=ev[["match_id","minute","series_id","patch_audit"]].copy()
        fold={"fold":idx,"fit_matured_games":len(matured),"eval_games":len(current),
              "eval_minutes":len(ev),"unmatured_excluded":len(earlier)-len(matured)}
        for name,features in INPUTS.items():
            m=create_pipeline(name).fit(fit[features],fit.radiant_win.astype(int))
            p=m.predict_proba(ev[features])[:,1]
            ll,br=proper(y,p)
            result["ll_"+name]=ll
            result["br_"+name]=br
            fold[name]={"logloss":float(ll.mean()),"brier":float(br.mean()),
                        "late30_brier":float(br[ev.minute.to_numpy(int)>=30].mean())}
            if name in CONTROLS:
                saved=prior["folds"][idx-1][name]
                for metric in ("logloss","brier"):
                    if not math.isclose(fold[name][metric],saved[metric],rel_tol=0,abs_tol=1e-10):
                        raise AssertionError("Frozen baseline model parity failure: "+name+" "+str(idx))
        fold_reports.append(fold)
        scored.append(result)
    oof=pd.concat(scored,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
        or len(set(cluster_ids(oof)))!=70
        or oof[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Original 137-game 5081-minute OOF geometry drift")
    bootstrap_indices=np.random.default_rng(SEED).integers(0,70,size=(DRAWS,70))
    comparisons={}
    for candidate in CANDIDATES:
        comparisons[candidate]={}
        for rival in (BASE,OTHER):
            obj=series_delta(oof,candidate,rival,bootstrap_indices)
            obj["fold_wins"]=sum(
               f[candidate]["logloss"]<f[rival]["logloss"] for f in fold_reports)
            comparisons[candidate][rival]=obj
    gates={}
    for c in CANDIDATES:
        a,b=comparisons[c][BASE],comparisons[c][OTHER]
        gates[c]=bool(
           a["delta_logloss"]<=-.0025 and b["delta_logloss"]<=-.0025
           and a["series_bootstrap_995_ll_bonf_10_tests"][1]<0
           and b["series_bootstrap_995_ll_bonf_10_tests"][1]<0
           and a["fold_wins"]>=3 and b["fold_wins"]>=3
           and a["delta_brier"]<=0 and b["delta_brier"]<=0
           and a["late30_delta_brier"]<=0 and b["late30_delta_brier"]<=0
           and a["biggest_positive_gain_share"] is not None
           and a["biggest_positive_gain_share"]<.5)
    phase={}
    for label,low,high in (("0-9",0,10),("10-19",10,20),
                           ("20-29",20,30),("30+",30,100000)):
        part=oof[(oof.minute>=low)&(oof.minute<high)]
        phase[label]={"rows":len(part),**{
            c:{
                "delta_LL_vs_M1":float((part["ll_"+c]-part["ll_"+BASE]).mean()),
                "delta_LL_vs_Q1":float((part["ll_"+c]-part["ll_"+OTHER]).mean())
            } for c in CANDIDATES}}
    patch={}
    for val,part in oof.groupby("patch_audit",sort=True):
        patch[str(val)]={"games":part.match_id.nunique(),"rows":len(part),
                "m1_ll":float(part["ll_"+BASE].mean()),
                "q1_ll":float(part["ll_"+OTHER].mean()),
                **{c:float((part["ll_"+c]-part["ll_"+BASE]).mean()) for c in CANDIDATES}}
    feature_nonzero={k:float(np.mean(df[k].to_numpy(float)!=0)) for k in COLS}
    if verify_original_artifacts()!=protected:
        raise AssertionError("Protected applicant artifact hash drift during scoring")
    return {
       "scientific_class":"post-result, exploratory TRAIN-forward, 5 frozen candidates",
       "base_head_before_trial":"62ed7dc8c123b620c3a79998f803617d67a3aacf",
       "protocol_sha256":hashlib.sha256(PROTO.read_bytes()).hexdigest(),
       "train_csv_sha256":provenance["source_train_sha256"],
       "feature_source_provenance":feature_report,
       "protected_applicant_sha256":protected,
       "n_original_train_games":291,"n_oof_games":137,"n_oof_rows":5081,
       "n_oof_independent_series":70,
       "candidates":{k:INPUTS[k] for k in CANDIDATES},
       "folds":fold_reports,
       "comparisons":comparisons,"gates_future_only":gates,
       "phase_diagnostics":phase,"patch_diagnostics":patch,
       "feature_nonzero_fraction":feature_nonzero,
       "bootstrap_draws":DRAWS,"bootstrap_seed":SEED,
       "familywise_ci":"two-sided 99.5% per 10 candidate-comparator pairs",
       "corrected_for_prior_searches":False,
       "original_val_test_used":False,
       "real_received_at_verified":False,
       "item_purchase_live_time_availability_verified":False,
       "hero_upgrade_times_verified":False,
       "employer_submission_changed":False,
    }


def report(res:dict)->str:
    lines=[
      "# All four unfinished Dota feature families — fixed 5-model historical screen",
      "",
      "**Five complete finite candidates; original TRAIN-forward only. No fresh test, "
      "no original VAL/TEST, no main / employer / ZIP changes.**",
      "",
      "## Primary comparison: incremental log loss (negative = candidate better)",
      "",
      "| New family | vs M1 LL | 99.5% cluster CI vs M1 | vs Q1 LL | "
      "99.5% cluster CI vs Q1 | Wins vs M1 / vs Q1 | Research gate |",
      "| --- | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for c in CANDIDATES:
        a=res["comparisons"][c][BASE]; b=res["comparisons"][c][OTHER]
        al,ah=a["series_bootstrap_995_ll_bonf_10_tests"]
        bl,bh=b["series_bootstrap_995_ll_bonf_10_tests"]
        lines.append(f"| {c} | {a['delta_logloss']:+.6f} | "
                     f"[{al:+.6f},{ah:+.6f}] | "
                     f"{b['delta_logloss']:+.6f} | [{bl:+.6f},{bh:+.6f}] | "
                     f"{a['fold_wins']}/4 / {b['fold_wins']}/4 | "
                     f"{'RESEARCH ONLY PASS' if res['gates_future_only'][c] else 'FAIL'} |")
    lines+=["",
       "## Frozen four fold log loss",
       "",
       "| Fold | Games | M0 | Additive | M1 | Q1 | R | O | C | I | ALL |",
       "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in res["folds"]:
        names=("M0_gold","A_additive",BASE,OTHER,*CANDIDATES)
        lines.append(f"| {f['fold']} | {f['eval_games']} | "
                     +" | ".join(f"{f[k]['logloss']:.5f}" for k in names)+" |")
    lines+=["",
       "## Secondary: proper Brier and equal-match weighting",
       "",
       "| New family | Δ Brier vs M1 | Δ Brier 30+ vs M1 | "
       "Equal-match Δ LL vs M1 | Patch 59 / 60 Δ LL vs M1 |",
       "| --- | ---: | ---: | ---: | --- |"]
    for c in CANDIDATES:
        a=res["comparisons"][c][BASE]
        p59=res["patch_diagnostics"].get("59",{}).get(c)
        p60=res["patch_diagnostics"].get("60",{}).get(c)
        lines.append(f"| {c} | {a['delta_brier']:+.6f} | "
                     f"{a['late30_delta_brier']:+.6f} | "
                     f"{a['per_match_weighted_delta_logloss']:+.6f} | "
                     f"{p59:+.5f} / {p60:+.5f} |" if p59 is not None and p60 is not None
                     else f"| {c} | {a['delta_brier']:+.6f} | "
                     f"{a['late30_delta_brier']:+.6f} | "
                     f"{a['per_match_weighted_delta_logloss']:+.6f} | N/A |")
    lines+=["",
      "## Audits and exclusions",
      "",
      f"- Historical raw matches = {res['feature_source_provenance']['matches']}, "
      f"TRAIN snapshot checks = {res['feature_source_provenance']['minutes']}, "
      f"swap checks = {res['feature_source_provenance']['mirror_validated']}, "
      f"future-poison checks = {res['feature_source_provenance']['suffix_and_future_event_validated']}.",
      f"- Patches in raw TRAIN: {res['feature_source_provenance']['patch_match_counts']}; "
      f"OOF patch samples: "
      f"{ {p:d['games'] for p,d in res['patch_diagnostics'].items()} }. "
      "Patch is a diagnostic, not an interaction selected post-score.",
      f"- Nonzero feature fractions: { {k:round(v,4) for k,v in res['feature_nonzero_fraction'].items()} }.",
      "- Precise hero skill-level power-spike timestamps NOT present: BLOCKED, "
      "not silently approximated by final player level. Item BKB/Blink purchase proxy "
      "is historically reconstructed but not verified live-deliverable at the same minute.",
      "- 2016+ OpenDota raw arrays have no trustworthy per-sample received_at; "
      "minute-index parity does not establish actual live PIT. No original TEST opened.",
      "- All previous feature trials and the already inspected TEST create substantial "
      "researcher degrees of freedom. This one-screen 99.5% Bonferroni interval "
      "does not repair historical selection. Nothing here can be promoted.",
      "",
      "**Decision:** Keep negative findings visible; original Vexil submission on HOLD "
      "pending applicant AI disclosure/hours and access sign-off.",
      ""]
    return "\n".join(lines)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    r=evaluate()
    print(report(r))
    if args.write:
        RECEIPT.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
        READOUT.write_text(report(r))
