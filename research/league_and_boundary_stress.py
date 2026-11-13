"""Read-only league and time-boundary sensitivity of frozen Vexil outcomes.

This script never refits models, uses held-out results for selection, or
makes network requests. It consumes OpenDota payloads ALREADY cached
under the exact 500-game frozen manifest. The saved JSON is descriptive,
post-hoc and not an independent evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.independent_delivery_audit import (
    bootstrap_delta, load_provenance, proper_scores,
)

PARTITIONS = ("train", "validation", "test")


def timing_boundaries(provenance: pd.DataFrame) -> dict:
    required = {"match_id","partition","start_time","estimated_end_time","series_id"}
    if not required.issubset(provenance.columns):
        raise ValueError("Missing time or identity fields")
    if provenance.match_id.duplicated().any():
        raise ValueError("Duplicate match IDs")
    if set(provenance.partition) != set(PARTITIONS):
        raise ValueError("Missing named chronological partition")
    bounds = {}
    positive_series = provenance.loc[provenance.series_id > 0]
    counts = positive_series.groupby("series_id").partition.nunique()
    if (counts > 1).any():
        raise ValueError("Series overlaps partitions")
    for first, later in zip(PARTITIONS[:-1], PARTITIONS[1:]):
        a=provenance.loc[provenance.partition==first]
        b=provenance.loc[provenance.partition==later]
        start=int(b.start_time.min())
        if int(a.start_time.max()) > start:
            raise ValueError("Non-chronological time boundary")
        differences=a.estimated_end_time.astype(int)-start
        overlap=differences[differences>0]
        bounds[first+"_to_"+later] = dict(
            preceding_games=len(a),
            following_games=len(b),
            prior_estimated_not_finished=int(len(overlap)),
            max_estimated_overlap_seconds=int(overlap.max()) if len(overlap) else 0,
            first_following_start=start,
            latest_prior_estimated_end=int(a.estimated_end_time.max()),
            estimated_availability_slack_seconds=int(start-a.estimated_end_time.max()),
        )
    return bounds


def league_stress(frame: pd.DataFrame, seed: int = 20261114,
                  draws: int = 40000) -> dict:
    required = {"match_id","minute","radiant_win","p_model","p_baseline","leagueid"}
    if not required.issubset(frame.columns):
        raise ValueError("Missing forecast or league columns")
    if frame[["match_id","minute"]].duplicated().any():
        raise ValueError("Duplicate forecast key")
    if frame[["match_id","leagueid"]].drop_duplicates().match_id.duplicated().any():
        raise ValueError("Game assigned to multiple leagues")
    scored=proper_scores(frame)
    league_rows=[]
    for league,group in scored.groupby("leagueid",sort=True):
        if int(league)<=0:
            raise ValueError("Unknown league identity cannot form independent cluster")
        for metric in ("logloss","brier"):
            v=float((group[metric+"_model"]-group[metric+"_baseline"]).mean())
            if metric=="logloss":
                record=dict(leagueid=int(league), matches=int(group.match_id.nunique()),
                            minutes=len(group), mean_logloss_delta=v)
            else:
                record["mean_brier_delta"]=v
        league_rows.append(record)
    per_league=pd.DataFrame(league_rows)
    if len(per_league)<3:
        raise ValueError("Too few leagues for t-interval sensitivity")
    effects={}
    for name in ("logloss","brier"):
        vals=per_league["mean_"+name+"_delta"].to_numpy(float)
        mean=float(vals.mean())
        sem=float(vals.std(ddof=1)/np.sqrt(len(vals)))
        critical=float(student_t.ppf(0.975,len(vals)-1))
        bootstrap=bootstrap_delta(scored,"leagueid",name,n_boot=draws,seed=seed)
        effects[name] = dict(
            minute_weighted_delta=float((scored[name+"_model"]-
                                        scored[name+"_baseline"]).mean()),
            equal_league_delta=mean,
            equal_league_t95=[mean-critical*sem,mean+critical*sem],
            league_cluster_percentile95=bootstrap["ci95"],
            per_league_favoring_m1=int((vals<0).sum()),
            per_league_favoring_m0=int((vals>0).sum()),
            bootstrap_draws=draws,
        )
    return dict(
        leagues=len(per_league),matches=int(scored.match_id.nunique()),
        minutes=len(scored),
        league_game_counts={str(int(r.leagueid)):int(r.matches)
                            for r in per_league.itertuples(index=False)},
        effects=effects,
        caveat=("Post-hoc evaluation on nine uneven-sized leagues. "
                "Equal-league t95 uses a small-sample approximation; "
                "league bootstrap can under-cover with few groups. "
                "Neither is adjusted for model search or independent prospective replication."),
    )


def audit(output_dir: Path, cache: Path) -> dict:
    manifest=pd.read_csv(output_dir/"match_manifest.csv")
    forecast=pd.read_csv(output_dir/"heldout_predictions.csv")
    if len(manifest)!=500 or manifest.match_id.nunique()!=500:
        raise ValueError("Not the frozen 500-game population")
    if len(forecast)!=3837 or forecast.match_id.nunique()!=106:
        raise ValueError("Not the frozen 106-game test output")
    source=load_provenance(manifest,cache)
    test_source=source.loc[source.partition=="test",
                           ["match_id","leagueid","source_radiant_win"]]
    merged=forecast.merge(test_source,on="match_id",
                          how="left",validate="many_to_one",indicator=True)
    if not (merged["_merge"]=="both").all():
        raise ValueError("Held-out source provenance mismatch")
    if not (merged.radiant_win==merged.source_radiant_win).all():
        raise ValueError("Held-out labels differ from source")
    result=dict(
        scope="Read-only descriptive sensitivity, no fitting/selection",
        source_match_ids_sha256=hashlib.sha256(json.dumps(
            sorted(manifest.match_id.astype(int))).encode()).hexdigest(),
        prediction_file_sha256=hashlib.sha256(
            (output_dir/"heldout_predictions.csv").read_bytes()).hexdigest(),
        split_counts={str(k):int(v) for k,v in
                      manifest.partition.value_counts().items()},
        patch_counts_by_partition={
            str(part):{str(k):int(v) for k,v in
                       g.patch.value_counts().items()}
            for part,g in manifest.groupby("partition",sort=True)
        },
        estimated_label_availability=timing_boundaries(source),
        heldout_league=league_stress(merged),
    )
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--outputs",type=Path,required=True)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    out=audit(args.outputs,args.cache)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("LEAGUE_AND_BOUNDARY_STRESS",json.dumps({
        "league_count":out["heldout_league"]["leagues"],
        "effects":out["heldout_league"]["effects"],
        "timing":out["estimated_label_availability"],
    },sort_keys=True))


if __name__=="__main__":
    main()
