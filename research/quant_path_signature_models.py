#!/usr/bin/env python3
"""One frozen 7-feature Dota economic-path hypothesis, TRAIN-only evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from conditional_gold_forward import FROZEN_CUTS
from rich_feature_models import (
    MODELS, cluster_bootstrap, create_pipeline, load_train, proper,
)
from train_time_effect_ci import cluster_ids
from quant_path_signature_features import FIELDS, PROTOCOL, attach_features

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/QUANT_PATH_SIGNATURES_RECEIPT.json"
READOUT=ROOT/"research/QUANT_PATH_SIGNATURES_READOUT.md"
PRIOR=ROOT/"research/QUANT_BIBLE_PATH_RECEIPT.json"
M0="M0_gold"
A="A_additive"
M1="M1_interaction"
Q1="Q1_path"
C="C4_path_micro"
BASE=tuple(MODELS[M1])
INPUTS={M0:MODELS[M0],A:MODELS[A],M1:MODELS[M1],
        Q1:MODELS[Q1],C:list(BASE)+list(FIELDS)}
TARGET_ARTIFACTS={
    "live_dota2_win_probability.ipynb":
    "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f",
    "artifacts/heldout_predictions.csv":
    "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441",
    "delivery/Vexil_Dota2_Takehome_20261116.zip":
    "8c97c9041a249ce5f7f540d461de30d41e4fe8423964f92b95c1717529ec02a3",
}
CORRELATION_OLD=(
    "gold_retreat10", "gold_flips10", "gold_eff10",
    "gold_xp_flow_gap", "gold_xp_gap", "o_tower5_delta",
)


def verify_original_artifacts()->dict:
    receipt={}
    for rel,expected in TARGET_ARTIFACTS.items():
        got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        if got!=expected:
            raise AssertionError("Frozen employer artifact changed: "+rel)
        receipt[rel]=got
    return receipt


def minutely_phase(minute:int)->str:
    return ("0-9" if minute<10 else "10-19" if minute<20 else
            "20-29" if minute<30 else "30+")


def evaluate()->dict:
    if not PROTOCOL.is_file():
        raise RuntimeError("Protocol required before original TRAIN scoring")
    artifact_hashes=verify_original_artifacts()
    original,source=load_train()  # 291 frozen TRAIN and prior 81-feature hash/parity
    df,extraction=attach_features(original,check_all=True)
    values=df[list(FIELDS)].to_numpy(dtype=float)
    if not np.isfinite(values).all() or any(np.std(values[:,j])<=0 for j in range(4)):
        raise AssertionError("New features degenerate/nonfinite in frozen TRAIN")
    prior=json.loads(PRIOR.read_text())
    meta=(df[["match_id","start_time","duration","series_id"]]
          .drop_duplicates().sort_values(["start_time","match_id"],
                                          kind="stable").reset_index(drop=True))
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("Frozen historical train cutpoints changed")
    reports,folds=[],[]
    for k,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        before,current=meta.iloc[:left],meta.iloc[left:right]
        t0=int(current.iloc[0].start_time)
        eligible=before[before.start_time+before.duration<=t0]
        if (set(cluster_ids(before))&set(cluster_ids(current))
            or set(cluster_ids(eligible))&set(cluster_ids(current))):
            raise AssertionError("Series spans forward split")
        past=df[df.match_id.isin(eligible.match_id)]
        ev=df[df.match_id.isin(current.match_id)]
        if not len(past) or not len(ev) or set(past.match_id)&set(ev.match_id):
            raise AssertionError("Training and evaluation matches overlap")
        y=ev.radiant_win.to_numpy(int)
        fold={"fold":k,"fit_completed_games":len(eligible),
              "eval_games":len(current),"eval_rows":len(ev),
              "embargoed_unmatured_games":len(before)-len(eligible)}
        saved=ev[["match_id","series_id","minute"]].copy()
        for name,cols in INPUTS.items():
            fitted=create_pipeline(name).fit(past[cols],past.radiant_win.astype(int))
            p=fitted.predict_proba(ev[cols])[:,1]
            ll,br=proper(y,p)
            saved["ll_"+name]=ll
            saved["br_"+name]=br
            fold[name]={"logloss":float(ll.mean()),"brier":float(br.mean())}
            if name!=C:
                prev=prior["folds"][k-1][name]
                for metric in ("logloss","brier"):
                    if not math.isclose(fold[name][metric],prev[metric],
                                        abs_tol=1e-10,rel_tol=0):
                        raise AssertionError("Original "+name+" fold parity changed")
        folds.append(fold)
        reports.append(saved)
    oof=pd.concat(reports,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
        or len(set(cluster_ids(oof)))!=70
        or oof[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Original OOF geometry changed")
    comparative={}
    for rival in (M0,A,M1,Q1):
        x=cluster_bootstrap(oof,C,rival)
        x["favorable_folds"]=sum(f[C]["logloss"]<f[rival]["logloss"] for f in folds)
        comparative[rival]=x
    phases={}
    for phase in ("0-9","10-19","20-29","30+"):
        minute=oof.minute.to_numpy(int)
        if phase=="0-9":sel=(minute<10)
        elif phase=="10-19":sel=(minute>=10)&(minute<20)
        elif phase=="20-29":sel=(minute>=20)&(minute<30)
        else:sel=(minute>=30)
        if not sel.any():
            raise AssertionError("Expected at least one observation per phase")
        phases[phase]={
            "n":int(sel.sum()),
            "delta_ll_vs_m1":float((oof.loc[sel,"ll_"+C]-oof.loc[sel,"ll_"+M1]).mean()),
            "delta_ll_vs_q1":float((oof.loc[sel,"ll_"+C]-oof.loc[sel,"ll_"+Q1]).mean()),
            "delta_brier_vs_m1":float((oof.loc[sel,"br_"+C]-oof.loc[sel,"br_"+M1]).mean()),
        }
    feature_diagnostics={}
    for name in FIELDS:
        col=df[name].to_numpy(float)
        corr={}
        for old in CORRELATION_OLD:
            v=df[old].to_numpy(float)
            cc=float(np.corrcoef(col,v)[0,1]) if np.std(v)>1e-14 else None
            corr[old]=cc
        valid=[(abs(z),k,z) for k,z in corr.items() if z is not None and np.isfinite(z)]
        feature_diagnostics[name]={
            "nonzero_fraction":float(np.mean(col!=0)),
            "std":float(np.std(col)),
            "top_abs_corr_old_feature":max(valid)[1] if valid else None,
            "top_abs_corr_old_value":float(max(valid)[2]) if valid else None,
            "old_correlations":corr,
        }
    m1,q1=comparative[M1],comparative[Q1]
    admitted=bool(
        m1["delta_logloss"]<=-.0025 and q1["delta_logloss"]<=-.0025
        and m1["ll_ci95_series"][1]<0 and q1["ll_ci95_series"][1]<0
        and m1["favorable_folds"]>=3 and q1["favorable_folds"]>=3
        and m1["delta_brier"]<=0 and q1["delta_brier"]<=0
        and m1["late30_delta_brier"]<=0 and q1["late30_delta_brier"]<=0
        and m1["largest_positive_series_share"] is not None
        and m1["largest_positive_series_share"]<.50)
    if verify_original_artifacts()!=artifact_hashes:
        raise AssertionError("Protected applicant files changed during evaluation")
    return {
        "scope":"post-result exploratory historical TRAIN-only, not new validation",
        "new_features":list(FIELDS), "n_feature_inputs":len(INPUTS[C]),
        "frozen_train_sha256":source["source_train_sha256"],
        "frozen_rich_sha256":source["frozen_feature_csv_sha256"],
        "protocol_sha256":hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "protected_applicant_hashes":artifact_hashes,
        "extraction":extraction,
        "n_train_games":291,"n_forward_games":137,"n_forward_rows":5081,
        "n_series_groups":70,"folds":folds,
        "comparisons":comparative,"phases":phases,
        "feature_diagnostics":feature_diagnostics,
        "advance_only_to_independent_future_study":admitted,
        "fresh_TEST_claim":False,"verified_feed_received_at":False,
        "model_submission_promoted":False
    }


def render(r:dict)->str:
    rows=[
      "# Quant Bible-inspired gold/XP path geometry and durability — TRAIN-only",
      "",
      "This is one **pre-scoring committed exploratory** candidate, "
      "not new blind validation. Data from original VAL/TEST were not "
      "used for this evaluation. Prior search multiplicity remains.",
      "",
      f"Extracted {len(r['new_features'])} new fixed-window features over "
      f"{r['extraction']['all_rows']:,} rows / 291 TRAIN matches; "
      f"{r['extraction']['side_mirror_checks']:,} mirrors and "
      f"{r['extraction']['causal_suffix_checks']:,} suffix checks.",
      "",
      "## Log loss and Brier against locked controls",
      "",
      "| Baseline | C4−baseline log loss | Series 95% CI | Delta Brier | "
      "Late30 delta Brier | Folds C4 wins |",
      "| --- | ---: | --- | ---: | ---: | ---: |"
    ]
    for name in (M0,A,M1,Q1):
        x=r["comparisons"][name];lo,hi=x["ll_ci95_series"]
        rows.append(f"| {name} | {x['delta_logloss']:+.6f} | "
                    f"[{lo:+.6f},{hi:+.6f}] | {x['delta_brier']:+.6f} | "
                    f"{x['late30_delta_brier']:+.6f} | {x['favorable_folds']}/4 |")
    rows += ["","## Every chronological TRAIN fold",
             "","| Fold | Games | M0 LL | A LL | M1 LL | Q1 LL | C4 LL |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in r["folds"]:
        rows.append(f"| {f['fold']} | {f['eval_games']} | " +
            " | ".join(f"{f[n]['logloss']:.6f}" for n in (M0,A,M1,Q1,C)) + " |")
    rows+=["","## Time-phase diagnostics (not selection)",
           "","| Phase | Rows | ΔLL C4−M1 | ΔLL C4−Q1 |",
           "| --- | ---: | ---: | ---: |"]
    for name,p in r["phases"].items():
        rows.append(f"| {name} | {p['n']} | {p['delta_ll_vs_m1']:+.6f} | "
                    f"{p['delta_ll_vs_q1']:+.6f} |")
    rows+=["","## Feature diversity (diagnostic, not post-hoc selection)",
           "","| Feature | Nonzero share | Most correlated fixed legacy feature | Correlation |",
           "| --- | ---: | --- | ---: |"]
    for name,f in r["feature_diagnostics"].items():
        rows.append(f"| {name} | {f['nonzero_fraction']:.1%} | "
                    f"{f['top_abs_corr_old_feature']} | "
                    f"{f['top_abs_corr_old_value']:+.3f} |")
    rows+=["",
           "**Frozen gate:** "+("Future independent evaluation candidate ONLY" if
             r["advance_only_to_independent_future_study"] else
             "FAILED; no model promotion"),
           "",
           "C4 is a small mechanistic feature hypothesis, not causal evidence "
           "that XP leads gold or a distinct live edge. With 291 historical TRAIN "
           "matches, independent evidence is limited; minute snapshots repeat "
           "the same game winner and historical source arrival times are unverified. "
           "A 2026 published OpenDota time-axis correction is a reason to request "
           "further timestamp audit, not proof this dataset is affected.",
           "",
           "Research branch only. Original applicant TEST predictions, notebook, "
           "4-page report, ZIP, time spent and AI disclosure remain unchanged.",
           ""]
    return "\n".join(rows)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    receipt=evaluate()
    print(render(receipt))
    if args.write:
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        READOUT.write_text(render(receipt))
