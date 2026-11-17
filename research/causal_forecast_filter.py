#!/usr/bin/env python3
"""Locked two-policy, TRAIN-only probabilistic stream filtering study.

Neither policy is a new fitted model. Original VAL/TEST and submission files
are read neither during fit/eval nor in any model selection code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit

from conditional_gold_forward import FROZEN_CUTS
from rich_feature_models import (
    MODELS, PRIOR, cluster_bootstrap, create_pipeline, load_train, proper,
)
from train_time_effect_ci import cluster_ids

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "research/CAUSAL_FORECAST_FILTER_PROTOCOL.md"
RECEIPT = ROOT / "research/CAUSAL_FORECAST_FILTER_RECEIPT.json"
READOUT = ROOT / "research/CAUSAL_FORECAST_FILTER_READOUT.md"
PREVIOUS = ROOT / "research/RICH_FEATURE_MODEL_RECEIPT.json"
EVENTS = ("o_tower_delta", "o_rax_delta", "o_kills_delta")
POLICIES = ("S1_fixed", "S2_event_reset")
CONTROLS = ("M0_gold", "M1_interaction", "Q1_path")
ALPHA = 0.65


def filter_match(
    probabilities: np.ndarray, event_cumulative: np.ndarray, *, alpha: float = ALPHA
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Filter a single game's causal predictions; do not share state between games.

    Returns fixed filter, event-reset filter, event-reset flags.
    Cumulative event counts are as-of rows already available at each minute.
    """
    p = np.asarray(probabilities, dtype=float)
    c = np.asarray(event_cumulative, dtype=float)
    if p.ndim != 1 or len(p) < 1 or c.shape != (len(p), len(EVENTS)):
        raise ValueError("Expected one game's probability vector and 3 as-of event series")
    if not np.isfinite(p).all() or not np.isfinite(c).all():
        raise ValueError("Non-finite as-of input")
    if not ((p > 0) & (p < 1)).all() or not 0 < alpha < 1:
        raise ValueError("Probability or smoothing coefficient out of range")
    reset = np.zeros(len(p), dtype=bool)
    if len(p) > 1:
        reset[1:] = np.any(c[1:] != c[:-1], axis=1)
    s1, s2 = np.empty_like(p), np.empty_like(p)
    s1[0] = s2[0] = p[0]
    z = logit(p)
    for t in range(1, len(p)):
        s1[t] = expit(alpha * z[t] + (1-alpha) * logit(s1[t-1]))
        a = 1.0 if reset[t] else alpha
        s2[t] = expit(a * z[t] + (1-a) * logit(s2[t-1]))
    if not np.isfinite(s1).all() or not np.isfinite(s2).all():
        raise AssertionError("Invalid output probability")
    if not (np.all((s1 > 0) & (s1 < 1)) and np.all((s2 > 0) & (s2 < 1))):
        raise AssertionError("Output probability outside (0,1)")
    if not np.allclose(s2[reset], p[reset], rtol=0, atol=1e-14):
        raise AssertionError("Event reset did not reflect baseline prediction")
    return s1, s2, reset


def apply_per_match(ev: pd.DataFrame, p: np.ndarray) -> pd.DataFrame:
    out = ev[["match_id", "minute", "radiant_win", "series_id"]].copy()
    out["p_M1_interaction"] = np.asarray(p, float)
    out["p_S1_fixed"] = np.nan
    out["p_S2_event_reset"] = np.nan
    out["event_reset"] = False
    for _, group in ev.groupby("match_id", sort=False):
        minutes = group.minute.to_numpy(int)
        if not np.array_equal(minutes, np.arange(len(group))):
            raise ValueError("Each match must be an unbroken minute prefix starting at zero")
        ix = group.index
        base = out.loc[ix, "p_M1_interaction"].to_numpy(float)
        s1, s2, reset = filter_match(base, group[list(EVENTS)].to_numpy(float))
        out.loc[ix, "p_S1_fixed"] = s1
        out.loc[ix, "p_S2_event_reset"] = s2
        out.loc[ix, "event_reset"] = reset
    if out[["p_S1_fixed", "p_S2_event_reset"]].isna().any().any():
        raise AssertionError("A match stream was not filtered")
    return out


def revisions(frame: pd.DataFrame) -> dict:
    names = ("M1_interaction", *POLICIES)
    abs_revisions = {k: [] for k in names}
    large_revisions = {k: 0 for k in names}
    per_game_tv = {k: [] for k in names}
    transitions, resets, games = 0, 0, 0
    for _, game in frame.groupby("match_id", sort=False):
        games += 1
        n = len(game)
        transitions += n-1
        resets += int(game.event_reset.sum())
        for key in names:
            dif = np.abs(np.diff(game["p_" + key].to_numpy(float)))
            abs_revisions[key].extend(dif)
            large_revisions[key] += int(np.count_nonzero(dif > 0.05))
            per_game_tv[key].append(float(dif.sum()))
    def metrics(k):
        return {"mean_abs_revision": float(np.mean(abs_revisions[k])),
                "large_revisions_gt5pp": large_revisions[k],
                "total_variation_per_game": float(np.mean(per_game_tv[k]))}
    if transitions != sum(len(z) for z in [abs_revisions[names[0]]]):
        raise AssertionError("Revision opportunity count drift")
    return {"games":games, "transitions":transitions, "event_reset_minutes":resets,
            "baselines": {k: metrics(k) for k in names}}


def evaluate() -> dict:
    if not PROTO.is_file():
        raise ValueError("Protocol must exist before scoring")
    df, provenance = load_train()
    previous = json.loads(PREVIOUS.read_text())
    if tuple(FROZEN_CUTS) != (154, 176, 220, 252, 291):
        raise AssertionError("Frozen time cutpoints changed")
    meta = (df[["match_id", "series_id", "start_time", "duration"]]
            .drop_duplicates().sort_values(["start_time", "match_id"],
                                           kind="stable").reset_index(drop=True))
    if len(meta) != 291:
        raise AssertionError("Expected exactly 291 original TRAIN games")
    fold_summaries, saved = [], []
    for i, (left, right) in enumerate(zip(FROZEN_CUTS[:-1], FROZEN_CUTS[1:]), 1):
        before, current = meta.iloc[:left], meta.iloc[left:right]
        cutoff = int(current.iloc[0].start_time)
        eligible = before[before.start_time + before.duration <= cutoff]
        if set(cluster_ids(before)) & set(cluster_ids(current)):
            raise AssertionError("Series crossing chronological boundary")
        if set(cluster_ids(eligible)) & set(cluster_ids(current)):
            raise AssertionError("Mature label series crossing boundary")
        fit = df[df.match_id.isin(eligible.match_id)]
        ev = (df[df.match_id.isin(current.match_id)]
              .sort_values(["match_id", "minute"], kind="stable").reset_index(drop=True))
        y = ev.radiant_win.to_numpy(float)
        raw_probs = {}
        fold = {"fold":i, "fit_games":len(eligible), "eval_games":len(current),
                "eval_rows":len(ev), "embargoed_unmatured_games":len(before)-len(eligible)}
        for name in CONTROLS:
            trained = create_pipeline(name).fit(fit[MODELS[name]], fit.radiant_win.astype(int))
            raw_probs[name] = trained.predict_proba(ev[MODELS[name]])[:,1]
        rows = apply_per_match(ev, raw_probs["M1_interaction"])
        for name in CONTROLS:
            rows["p_" + name] = raw_probs[name]
        for name in (*CONTROLS, *POLICIES):
            ll, br = proper(y, rows["p_" + name].to_numpy(float))
            rows["ll_" + name] = ll
            rows["br_" + name] = br
            fold[name] = {"logloss":float(ll.mean()),"brier":float(br.mean()),
                          "late30_brier":float(br[ev.minute.to_numpy(int)>=30].mean())}
            if name in CONTROLS:
                prior = previous["folds"][i-1][name]
                for metric in ("logloss", "brier"):
                    if not math.isclose(fold[name][metric], prior[metric],
                                        rel_tol=0, abs_tol=1e-10):
                        raise AssertionError("Existing baseline prediction parity drift")
        fold["revisions"] = revisions(rows)
        fold_summaries.append(fold)
        saved.append(rows)
    allrows = pd.concat(saved, ignore_index=True)
    if (len(allrows) != 5081 or allrows.match_id.nunique() != 137
        or len(set(cluster_ids(allrows))) != 70
        or allrows[["match_id", "minute"]].duplicated().any()):
        raise AssertionError("Expected original 5,081 TRAIN OOF minute predictions")
    score = {policy: {} for policy in POLICIES}
    for policy in POLICIES:
        for comparator in CONTROLS:
            delta = cluster_bootstrap(allrows, policy, comparator)
            delta["folds_within_002_ll"] = sum(
                (f[policy]["logloss"]-f[comparator]["logloss"]) <= .002
                for f in fold_summaries)
            score[policy][comparator] = delta
    utility = revisions(allrows)
    base = utility["baselines"]["M1_interaction"]
    promotion = {}
    for policy in POLICIES:
        m = score[policy]["M1_interaction"]
        u = utility["baselines"][policy]
        avg_reduce = 1-u["mean_abs_revision"]/base["mean_abs_revision"]
        large_reduce = (1-u["large_revisions_gt5pp"]/base["large_revisions_gt5pp"]
                        if base["large_revisions_gt5pp"] else 0.)
        promotion[policy] = {
            "mean_abs_revision_reduction_fraction":float(avg_reduce),
            "large_revisions_reduction_fraction":float(large_reduce),
            "advance_to_future_independent_study_only":bool(
                m["delta_logloss"] <= .002 and m["ll_ci975_two_candidates"][1] <= .005
                and m["delta_brier"] <= .001 and m["late30_delta_brier"] <= .001
                and m["folds_within_002_ll"] >= 3 and avg_reduce >= .20
                and large_reduce >= .20)
        }
    return {
        "scope":"historical TRAIN-only, post-result exploratory, not unseen test",
        "source_train_sha256":provenance["source_train_sha256"],
        "source_rich_sha256":provenance["frozen_feature_csv_sha256"],
        "protocol_sha256":hashlib.sha256(PROTO.read_bytes()).hexdigest(),
        "n_train_games":291, "n_oof_games":137, "n_oof_rows":5081,
        "n_series_clusters":70, "folds":fold_summaries,
        "paired_bootstrap":score, "overall_revisions":utility,
        "exploratory_gate":promotion,
        "actual_received_at_timestamps_verified":False,
        "submitted_notebook_or_test_changed":False,
    }


def write_readout(r:dict)->str:
    text = [
        "# Causal live-forecast filter: TRAIN-only locked evaluation",
        "",
        "**Status:** post-result exploratory, no applicant submission change. "
        "Only the original TRAIN cohort was used.",
        "",
        "## Forecast safeguard (delta minus existing M1, positive = worse)",
        "",
        "| Policy | Delta LL | Two-policy adj. 97.5% interval | Delta Brier | "
        "Late30 Brier delta | LL within +.002 folds |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for policy in POLICIES:
        x=r["paired_bootstrap"][policy]["M1_interaction"]
        b=x["ll_ci975_two_candidates"]
        text.append(
            f"| {policy} | {x['delta_logloss']:+.6f} | "
            f"[{b[0]:+.6f}, {b[1]:+.6f}] | "
            f"{x['delta_brier']:+.6f} | {x['late30_delta_brier']:+.6f} | "
            f"{x['folds_within_002_ll']}/4 |"
        )
    u=r["overall_revisions"]
    text += ["", "## Live-output operational proxy, not demonstrated user benefit", "",
             f"137 games, {u['transitions']} intra-game revisions, "
             f"{u['event_reset_minutes']} observable-event resets (S2).", "",
             "| Stream | Mean abs revision | >5pp revision count | Total variation / game |",
             "| --- | ---: | ---: | ---: |"]
    for name in ("M1_interaction",*POLICIES):
        x=u["baselines"][name]
        text.append(f"| {name} | {x['mean_abs_revision']:.6f} | "
                    f"{x['large_revisions_gt5pp']} | {x['total_variation_per_game']:.5f} |")
    text += ["","## Fold-by-fold LL (all blocks)","","| Fold | Games | M0 | M1 | Q1 | S1 | S2 |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for fold in r["folds"]:
        text.append("| " + str(fold["fold"]) + " | " + str(fold["eval_games"]) + " | " +
                    " | ".join(f"{fold[k]['logloss']:.6f}" for k in
                                ("M0_gold","M1_interaction","Q1_path",*POLICIES)) + " |")
    text += ["","## Rivals and decision",
             "","| Policy | Vs M0 LL | Vs Q1 LL | Revision decline | >5pp count decline | Gate |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for policy in POLICIES:
        m=r["paired_bootstrap"][policy]
        z=r["exploratory_gate"][policy]
        text.append(f"| {policy} | {m['M0_gold']['delta_logloss']:+.6f} | "
                    f"{m['Q1_path']['delta_logloss']:+.6f} | "
                    f"{100*z['mean_abs_revision_reduction_fraction']:.1f}% | "
                    f"{100*z['large_revisions_reduction_fraction']:.1f}% | "
                    f"{'FUTURE-ONLY CANDIDATE' if z['advance_to_future_independent_study_only'] else 'REJECT'} |")
    text += ["","No policy is promoted to the Vexil employer notebook or private reviewer ZIP. "
             "A stable-looking forecast can still be statistically worse; series-cluster "
             "intervals are descriptive for the retrospectively reused TRAIN cohort. "
             "Signed event-net counts omit cancelling same-minute fights; actual received-at "
             "timestamps remain unavailable. Neither policy is certified live-safe.", ""]
    return "\n".join(text)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Commit-candidate results to research only")
    args=parser.parse_args()
    result=evaluate()
    print(write_readout(result))
    if args.write:
        RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        READOUT.write_text(write_readout(result))
