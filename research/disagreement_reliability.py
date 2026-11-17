#!/usr/bin/env python3
"""No-tuning, TRAIN-forward, OOF model-disagreement error-warning falsifier."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from conditional_gold_forward import FROZEN_CUTS
from rich_feature_models import MODELS, create_pipeline, load_train, proper
from train_time_effect_ci import cluster_ids

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "research/DISAGREEMENT_RELIABILITY_PROTOCOL.md"
RECEIPT = ROOT / "research/DISAGREEMENT_RELIABILITY_RECEIPT.json"
REPORT = ROOT / "research/DISAGREEMENT_RELIABILITY_READOUT.md"
Q1_PRIOR = ROOT / "research/QUANT_BIBLE_PATH_RECEIPT.json"
MODELS_USED = ("M0_gold", "M1_interaction", "Q1_path")
DRAWS, SEED, TOP_FRAC = 2000, 20261118, 0.20
EXPECTED_HASHES = {
    "live_dota2_win_probability.ipynb": "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f",
    "artifacts/heldout_predictions.csv": "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441",
    "delivery/Vexil_Dota2_Takehome_20261116.zip": "8c97c9041a249ce5f7f540d461de30d41e4fe8423964f92b95c1717529ec02a3",
}


def guard_delivery() -> dict:
    results = {}
    for path, expected in EXPECTED_HASHES.items():
        got = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if got != expected:
            raise ValueError(f"Protected applicant artifact hash drift: {path}")
        results[path] = got
    return results


def risk_scores(m0: np.ndarray, m1: np.ndarray, q1: np.ndarray) -> dict[str, np.ndarray]:
    """Only current-minute OOF model probabilities, never winner labels."""
    p = [np.asarray(x, dtype=float) for x in (m0, m1, q1)]
    if any(x.shape != p[0].shape for x in p) or p[0].ndim != 1:
        raise ValueError("Probability arrays must be 1-D and aligned")
    if not all(np.isfinite(x).all() and ((x > 0) & (x < 1)).all() for x in p):
        raise ValueError("Invalid probability input")
    d_m0 = np.abs(p[1] - p[0])
    d_q1 = np.abs(p[1] - p[2])
    return {"disagreement": np.maximum(d_m0, d_q1),
            "uncertainty": np.minimum(p[1], 1 - p[1]),
            "component_m0": d_m0, "component_q1": d_q1}


def wrong_decision(final_radiant_winner: np.ndarray, m1: np.ndarray) -> np.ndarray:
    """Outcome is evaluation-only, never passed into risk_scores."""
    y, p = np.asarray(final_radiant_winner), np.asarray(m1)
    if y.shape != p.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("Wrong-decision evaluation label invalid")
    return ((p >= 0.5).astype(int) != y.astype(int)).astype(int)


def auc(y: np.ndarray, score: np.ndarray) -> float:
    if len(np.unique(y)) != 2:
        raise ValueError("Need both wrong-sided and correct forecasts for AUROC")
    return float(roc_auc_score(y, score))


def alert_budget(y: np.ndarray, score: np.ndarray, frac=TOP_FRAC) -> dict:
    """Retrospective percentile / not a learned production threshold."""
    n = len(y)
    take = int(math.ceil(n * frac))
    # Stable deterministic tie-breaker, never by outcome.
    ids = np.lexsort((np.arange(n), -score))[:take]
    return {"alerts": take, "wrong_alerts": int(y[ids].sum()),
            "precision":float(y[ids].mean()),
            "error_recall":float(y[ids].sum()/max(int(y.sum()),1)),
            "retrospective_lowest_alert_score":float(score[ids].min())}


def controlled_strata(rows: pd.DataFrame) -> dict:
    """Fixed coarse U + time cells. Compare high vs low D within each cell."""
    r = rows.copy()
    r["u_bin"] = np.minimum(np.floor(r.uncertainty.to_numpy() * 10).astype(int), 4)
    m = r.minute.to_numpy(dtype=int)
    r["phase"] = np.where(m < 10, 0, np.where(m < 20, 1, np.where(m < 30, 2, 3)))
    results = []
    eligible_rows = 0
    for (ub, phase), group in r.groupby(["u_bin","phase"],sort=True):
        n = len(group)
        if n < 20 or group.wrong.nunique() < 2:
            results.append({"u_bin":int(ub),"phase":int(phase),"n":n,
                            "eligible":False})
            continue
        cutoff = float(group.disagreement.median())
        high = group.disagreement > cutoff
        if not high.any() or high.all():
            results.append({"u_bin":int(ub),"phase":int(phase),"n":n,
                            "eligible":False, "why":"disagreement ties"})
            continue
        eligible_rows += n
        rhi = float(group.loc[high,"wrong"].mean())
        rlo = float(group.loc[~high,"wrong"].mean())
        results.append({"u_bin":int(ub), "phase":int(phase),"n":n,
                        "high_n":int(high.sum()), "low_n":int((~high).sum()),
                        "high_wrong_rate":rhi, "low_wrong_rate":rlo,
                        "high_minus_low_wrong_rate":rhi-rlo, "eligible":True})
    num = sum(x["n"]*x["high_minus_low_wrong_rate"] for x in results if x["eligible"])
    return {"eligible_rows":eligible_rows,"excluded_rows":len(r)-eligible_rows,
            "eligible_cells":sum(int(x["eligible"]) for x in results),
            "total_cells":len(results),
            "weighted_within_stratum_wrong_risk_difference":
              float(num / eligible_rows) if eligible_rows else None,
            "cells":results}


def paired_cluster_interval(rows: pd.DataFrame) -> dict:
    """Resample entire professional series clusters, not dependent minute rows."""
    keys = cluster_ids(rows[["match_id", "series_id"]])
    groups = pd.Series(np.arange(len(rows))).groupby(keys, sort=True).apply(
        lambda a: a.to_numpy(dtype=int)).to_list()
    if len(groups) != 70:
        raise AssertionError("Original independent series/singleton count drift")
    y = rows.wrong.to_numpy(int)
    d = rows.disagreement.to_numpy(float)
    u = rows.uncertainty.to_numpy(float)
    g = np.random.default_rng(SEED)
    sample_ids = g.integers(0, len(groups), size=(DRAWS,len(groups)))
    vals = np.empty(DRAWS, dtype=float)
    for b, sampled in enumerate(sample_ids):
        ix = np.concatenate([groups[int(k)] for k in sampled])
        vals[b] = auc(y[ix],d[ix])-auc(y[ix],u[ix])
    return {"draws":DRAWS, "seed":SEED,
            "delta_auroc_ci95":np.quantile(vals,[.025,.975]).tolist(),
            "fraction_bootstrap_delta_positive":float((vals > 0).mean())}


def evaluate() -> dict:
    if not PROTO.is_file():
        raise ValueError("Research protocol must be committed first")
    artifact_hashes = guard_delivery()
    df, provenance = load_train()
    prior = json.loads(Q1_PRIOR.read_text())
    meta = (df[["match_id","series_id","start_time","duration"]]
            .drop_duplicates().sort_values(["start_time","match_id"],kind="stable")
            .reset_index(drop=True))
    if len(meta) != 291 or tuple(FROZEN_CUTS) != (154,176,220,252,291):
        raise AssertionError("Frozen TRAIN evaluation geometry changed")
    saved, folds = [], []
    for i,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        older,cur=meta.iloc[:left],meta.iloc[left:right]
        cutoff = int(cur.iloc[0].start_time)
        mature = older[older.start_time + older.duration <= cutoff]
        if (set(cluster_ids(older)) & set(cluster_ids(cur))) or (
            set(cluster_ids(mature)) & set(cluster_ids(cur))):
            raise AssertionError("Series boundary violation")
        fit = df[df.match_id.isin(mature.match_id)]
        ev = (df[df.match_id.isin(cur.match_id)]
              .sort_values(["match_id","minute"],kind="stable").reset_index(drop=True))
        probs = {}
        for name in MODELS_USED:
            model=create_pipeline(name).fit(fit[MODELS[name]],fit.radiant_win.astype(int))
            probs[name]=model.predict_proba(ev[MODELS[name]])[:,1]
            ll,br=proper(ev.radiant_win.to_numpy(dtype=float),probs[name])
            saved_metric=prior["folds"][i-1][name]
            if not (math.isclose(float(ll.mean()),saved_metric["logloss"],abs_tol=1e-10,rel_tol=0)
                and math.isclose(float(br.mean()),saved_metric["brier"],abs_tol=1e-10,rel_tol=0)):
                raise AssertionError(f"Historical baseline parity failed for {name} fold {i}")
        risk=risk_scores(probs["M0_gold"],probs["M1_interaction"],probs["Q1_path"])
        err=wrong_decision(ev.radiant_win.to_numpy(int),probs["M1_interaction"])
        part=ev[["match_id","series_id","minute"]].copy()
        for k,v in risk.items():
            part[k]=v
        part["wrong"]=err
        part["m1"]=probs["M1_interaction"]
        part["fold"]=i
        fold={"fold":i,"games":len(cur),"rows":len(ev),
              "fit_completed_games":len(mature),
              "embargoed_unmatured_games":len(older)-len(mature),
              "wrong_n":int(err.sum()),"wrong_rate":float(err.mean()),
              "auroc_disagreement":auc(err,risk["disagreement"]),
              "auroc_uncertainty":auc(err,risk["uncertainty"])}
        fold["delta_auroc"]=fold["auroc_disagreement"]-fold["auroc_uncertainty"]
        folds.append(fold)
        saved.append(part)
    allrows=pd.concat(saved,ignore_index=True)
    if (len(allrows)!=5081 or allrows.match_id.nunique()!=137
        or len(set(cluster_ids(allrows)))!=70
        or allrows[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Wrong original TRAIN-forward evaluation count")
    y=allrows.wrong.to_numpy(int)
    s={k:allrows[k].to_numpy(float) for k in
       ("disagreement","uncertainty","component_m0","component_q1")}
    area={k:auc(y,v) for k,v in s.items()}
    ci=paired_cluster_interval(allrows)
    alerts={k:alert_budget(y,s[k]) for k in ("disagreement","uncertainty")}
    controlled=controlled_strata(allrows)
    confident=allrows[np.maximum(allrows.m1,1-allrows.m1)>=0.75]
    high={"n":len(confident),"wrong_n":int(confident.wrong.sum()),
          "wrong_rate":float(confident.wrong.mean()) if len(confident) else None}
    if 0 < int(confident.wrong.sum()) < len(confident):
        high.update({"auroc_disagreement":auc(confident.wrong,confident.disagreement),
                     "auroc_uncertainty":auc(confident.wrong,confident.uncertainty)})
    delta=area["disagreement"]-area["uncertainty"]
    strat=controlled["weighted_within_stratum_wrong_risk_difference"]
    gate=bool(delta>=.03 and ci["delta_auroc_ci95"][0]>0
        and sum(x["delta_auroc"]>0 for x in folds)>=3
        and alerts["disagreement"]["precision"]-alerts["uncertainty"]["precision"]>=.03
        and strat is not None and strat>0)
    after=guard_delivery()
    if after!=artifact_hashes:
        raise AssertionError("Applicant artifacts changed during scoring")
    return {
        "scientific_status":"post-result exploratory TRAIN-only; no independent holdout",
        "source_train_sha256":provenance["source_train_sha256"],
        "source_rich_sha256":provenance["frozen_feature_csv_sha256"],
        "protocol_sha256":hashlib.sha256(PROTO.read_bytes()).hexdigest(),
        "protected_submission_sha256":after,
        "n_train_games":291,"n_oof_games":137,"n_oof_rows":5081,
        "n_series_clusters":70, "n_wrong_decisions":int(y.sum()),
        "wrong_decision_prevalence":float(y.mean()),
        "auc":area,"delta_auroc_D_minus_U":delta,
        "bootstrap":ci,"alerts_top20pct":alerts,
        "folds":folds,"confounding_diagnostic":controlled,
        "high_confidence_diagnostic":high,
        "future_study_gate":gate,
        "past_many_experiments_adjustment":False,
        "actual_feed_received_at_verified":False,
        "employer_model_promotion":False,
    }


def fmt(x:float)->str:
    return f"{x:+.5f}"


def render(r:dict)->str:
    a=r["auc"]
    ci=r["bootstrap"]["delta_auroc_ci95"]
    alert=r["alerts_top20pct"]
    out=[
        "# Is model disagreement an honest forecast reliability signal?",
        "",
        "**Scope:** fixed, post-result exploratory TRAIN-forward; no original VAL, TEST, "
        "external holdout, applicant narrative, or deploy changes.",
        "",
        f"Evaluated {r['n_oof_rows']:,} minute predictions / {r['n_oof_games']} games / "
        f"{r['n_series_clusters']} independent series/singletons. "
        f"Wrong-side labels: {r['n_wrong_decisions']:,} "
        f"({r['wrong_decision_prevalence']:.1%}).",
        "",
        "## Primary falsifier",
        "",
        "| Risk score | Wrong-side AUROC |",
        "| --- | ---: |",
        f"| D: max model disagreement | {a['disagreement']:.5f} |",
        f"| U: M1 confidence-based uncertainty | {a['uncertainty']:.5f} |",
        "",
        f"**D minus U AUROC:** {fmt(r['delta_auroc_D_minus_U'])}; "
        f"series-cluster bootstrap 95% interval "
        f"[{fmt(ci[0])}, {fmt(ci[1])}] "
        f"({r['bootstrap']['draws']} paired draws).",
        "",
        "## Retrospective alert budget — NOT deployable thresholds",
        "",
        "| Score | Top20% alerts | Wrong alerts | Precision | Error recall |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for k in ("disagreement","uncertainty"):
        x=alert[k]
        out.append(f"| {k} | {x['alerts']} | {x['wrong_alerts']} | "
                   f"{x['precision']:.3f} | {x['error_recall']:.3f} |")
    out += ["", "## Four chronological TRAIN folds",
            "",
            "| Fold | Games | Wrong-sided | D AUROC | U AUROC | D-U |",
            "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for f in r["folds"]:
        out.append(f"| {f['fold']} | {f['games']} | {f['wrong_n']} "
                   f"({f['wrong_rate']:.1%}) | {f['auroc_disagreement']:.4f} | "
                   f"{f['auroc_uncertainty']:.4f} | {fmt(f['delta_auroc'])} |")
    conf=r["confounding_diagnostic"]
    out += ["", "## Mechanism/negative-control diagnostics",
            "",
            f"- Component |M1−M0| AUROC: {a['component_m0']:.5f}; "
            f"component |M1−Q1| AUROC: {a['component_q1']:.5f}. "
            "Do not select components after seeing their scores.",
            f"- Within fixed uncertainty/time cells: {conf['eligible_cells']}/"
            f"{conf['total_cells']} usable cells, {conf['eligible_rows']} included rows / "
            f"{conf['excluded_rows']} excluded. "
            f"High-D minus low-D wrong-sided rate: "
            f"{fmt(conf['weighted_within_stratum_wrong_risk_difference']) if conf['weighted_within_stratum_wrong_risk_difference'] is not None else 'undefined'}. "
            "This is an offline coarse-stratification diagnostic, not fitted adjustment.",
            f"- High-confidence (max M1 p >=0.75) n={r['high_confidence_diagnostic']['n']}, "
            f"wrong-sided={r['high_confidence_diagnostic']['wrong_n']}; "
            "outcome is only used for retrospective scoring.",
            "",
            "**Future independent study gate:** "
            + ("PASSED for further research only" if r["future_study_gate"]
               else "REJECT / not supported by fixed gate"),
            "",
            "**Limits:** minute labels share match outcomes; bootstrap respects series "
            "but uncertainty is descriptive for this repeatedly explored TRAIN cohort; "
            "top20% offline ranking has no calibrated real-time threshold; "
            "coarse confidence/time matching leaves residual confounding. "
            "Actual feed arrival timestamps are not known. This experiment says nothing "
            "about official Vexil grading, calibration superiority, or trading returns.",
            "",
            "Original 500-game notebook, locked 3,836 TEST forecasts, applicant "
            "report/ZIP and human disclosure remain unchanged.",
            ""]
    return "\n".join(out)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    receipt=evaluate()
    print(render(receipt))
    if args.write:
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        REPORT.write_text(render(receipt))
