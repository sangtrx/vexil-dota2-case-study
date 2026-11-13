"""Independent, read-only Vexil delivery audit.

Never fits a model or queries OpenDota. Recomputes proper scores from the
frozen held-out probabilities and checks chronological completion and
multi-game series dependence against raw cached OpenDota payloads.

Run (on authorized BigLinux):
python research/independent_delivery_audit.py --outputs /path/to/vexil_takehome_outputs \
    --cache /path/to/api-cache --receipt /path/to/audit.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss


def _json_match_filename(match_id: int) -> str:
    url = "/matches/" + str(int(match_id))
    key = hashlib.sha256(json.dumps([url, {}], sort_keys=True).encode()).hexdigest()
    return key + ".json.gz"


def load_provenance(manifest: pd.DataFrame, cache: Path) -> pd.DataFrame:
    rows = []
    for m in manifest.itertuples(index=False):
        path = cache / _json_match_filename(int(m.match_id))
        if not path.is_file():
            raise FileNotFoundError(f"Missing offline frozen OpenDota source: {m.match_id}")
        with gzip.open(path, "rt", encoding="utf8") as handle:
            payload = json.load(handle)
        if int(payload.get("match_id") or -1) != int(m.match_id):
            raise ValueError(f"Cache payload ID mismatch: {m.match_id}")
        if str(payload.get("patch")) != str(m.patch):
            raise ValueError(f"Patch changed for {m.match_id}")
        if int(payload["start_time"]) != int(m.start_time):
            raise ValueError(f"Start-time provenance drift: {m.match_id}")
        league = int(payload.get("leagueid") or 0)
        rows.append(dict(
            match_id=int(m.match_id),
            partition=str(m.partition),
            series_id=int(m.series_id),
            start_time=int(m.start_time),
            estimated_end_time=int(m.start_time) + int(payload["duration"]),
            leagueid=league,
        ))
    return pd.DataFrame(rows).sort_values(["start_time", "match_id"], kind="mergesort")


def proper_scores(predictions: pd.DataFrame) -> pd.DataFrame:
    z = predictions.copy()
    if z[["match_id", "minute"]].duplicated().any():
        raise ValueError("Duplicate held-out forecast key")
    if not z["radiant_win"].isin([0, 1]).all():
        raise ValueError("Malformed outcome")
    y = z["radiant_win"].to_numpy(dtype=int)
    for model in ("model", "baseline"):
        p = z["p_" + model].to_numpy(dtype=float)
        if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
            raise ValueError(f"Malformed probabilities: {model}")
        eps_p = np.clip(p, 1e-15, 1 - 1e-15)
        z["logloss_" + model] = -(y * np.log(eps_p) + (1-y) * np.log1p(-eps_p))
        z["brier_" + model] = (p - y) ** 2
    return z


def bootstrap_delta(frame: pd.DataFrame, group_name: str, loss_name: str,
                    n_boot: int = 12000, seed: int = 20261114) -> dict:
    if n_boot < 100 or not 0 < len(frame):
        raise ValueError("Bootstrapping needs non-empty data and draws")
    grouped = frame.groupby(group_name, sort=True).agg(
        count=("minute", "size"),
        proposed=("{}_model".format(loss_name), "sum"),
        baseline=("{}_baseline".format(loss_name), "sum")
    )
    arrays = grouped[["count", "proposed", "baseline"]].to_numpy(dtype=float)
    n = len(arrays)
    if n < 2:
        raise ValueError("Too few groups")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    b = arrays[idx].sum(axis=1)
    b_delta = (b[:, 1] - b[:, 2]) / b[:, 0]
    actual = arrays.sum(axis=0)
    lo, hi = np.quantile(b_delta, [.025, .975])
    return dict(clusters=n, minutes=int(actual[0]),
                delta=float((actual[1]-actual[2])/actual[0]),
                ci95=[float(lo), float(hi)], draws=n_boot, seed=seed)


def independent_metric_oracle(frame: pd.DataFrame, metrics: pd.DataFrame) -> None:
    for phase in ["overall", "0–9", "10–19", "20–29", "30+"]:
        window = frame if phase == "overall" else frame.loc[
            pd.cut(frame.minute, bins=[-1, 9, 19, 29, np.inf],
                   labels=["0–9", "10–19", "20–29", "30+"]) == phase
        ]
        for metric in ("logloss", "brier"):
            stored = metrics.loc[(metrics.phase == phase) &
                                 (metrics.metric == metric)]
            if len(stored) != 1:
                raise ValueError(f"Missing or duplicate frozen metric {phase}/{metric}")
            row = stored.iloc[0]
            y = window.radiant_win.to_numpy(dtype=int)
            if metric == "logloss":
                want_m = log_loss(y, window.p_model.to_numpy(), labels=[0, 1])
                want_b = log_loss(y, window.p_baseline.to_numpy(), labels=[0, 1])
            else:
                want_m = brier_score_loss(y, window.p_model.to_numpy())
                want_b = brier_score_loss(y, window.p_baseline.to_numpy())
            if not (np.isclose(want_m, row.model, atol=1e-12, rtol=0) and
                    np.isclose(want_b, row.baseline, atol=1e-12, rtol=0) and
                    np.isclose(want_m-want_b, row.difference, atol=1e-12, rtol=0)):
                raise ValueError(f"Frozen metric does not match independent oracle {phase}/{metric}")


def audit(outputs: Path, cache: Path) -> dict:
    manifest = pd.read_csv(outputs/"match_manifest.csv")
    raw_preds = pd.read_csv(outputs/"heldout_predictions.csv")
    frozen_metrics = pd.read_csv(outputs/"heldout_metrics.csv")
    if len(manifest) != 500 or manifest.match_id.nunique() != 500:
        raise ValueError("Manifest is not 500 unique games")
    if set(manifest.partition) != {"train", "validation", "test"}:
        raise ValueError("Unexpected split names")
    if len(raw_preds) != 3837 or raw_preds.match_id.nunique() != 106:
        raise ValueError("Unexpected frozen heldout length")
    if set(raw_preds.match_id) != set(manifest.loc[manifest.partition == "test", "match_id"]):
        raise ValueError("Test IDs drifted from frozen manifest")
    src = load_provenance(manifest, cache)
    for label in ("train", "validation", "test"):
        ids = src.loc[src.partition == label]
        if not (ids.estimated_end_time >= ids.start_time).all():
            raise ValueError("Negative source duration")
        if not ids.start_time.is_monotonic_increasing:
            raise ValueError("Chronology disorder")

    train = src[src.partition == "train"]
    val = src[src.partition == "validation"]
    test = src[src.partition == "test"]
    if not (train.start_time.max() <= val.start_time.min() <=
            val.start_time.max() <= test.start_time.min()):
        raise ValueError("Train-validation-test time order violated")
    positive = src.loc[src.series_id > 0]
    if (positive.groupby("series_id").partition.nunique() > 1).any():
        raise ValueError("Same professional series leaked across partitions")
    train_val_overlaps = train[train.estimated_end_time > val.start_time.min()]
    val_test_overlaps = val[val.estimated_end_time > test.start_time.min()]
    if len(val_test_overlaps):
        raise ValueError("Validation labels were not yet available at first test start")
    forecasts = proper_scores(raw_preds)
    independent_metric_oracle(forecasts, frozen_metrics)
    forecasts = forecasts.merge(test[["match_id", "series_id", "leagueid"]],
                                on="match_id", validate="many_to_one")
    if forecasts[["series_id", "leagueid"]].isna().any().any():
        raise ValueError("Missing held-out cluster metadata")
    # Nonpositive series IDs are match-level fallbacks, never one false cluster.
    forecasts["series_cluster"] = np.where(
        forecasts.series_id > 0,
        "series:" + forecasts.series_id.astype(str),
        "match:" + forecasts.match_id.astype(str)
    )
    phases = dict(overall=forecasts, early=forecasts[forecasts.minute < 10],
                  mid=forecasts[(forecasts.minute >= 10)&(forecasts.minute < 30)],
                  late=forecasts[forecasts.minute >= 30])
    scores = {}
    for phase_name, df in phases.items():
        scores[phase_name] = {
            "logloss_match": bootstrap_delta(df, "match_id", "logloss"),
            "logloss_series": bootstrap_delta(df, "series_cluster", "logloss"),
            "brier_match": bootstrap_delta(df, "match_id", "brier"),
            "brier_series": bootstrap_delta(df, "series_cluster", "brier"),
        }
    forecast_delta = forecasts.logloss_model - forecasts.logloss_baseline
    loo = []
    for league, group in forecasts.groupby("leagueid"):
        other = forecasts.loc[forecasts.leagueid != league]
        loo.append(dict(leagueid=int(league),
                        games=int(group.match_id.nunique()),
                        league_logloss_delta=float((group.logloss_model - group.logloss_baseline).mean()),
                        excluding_league_logloss_delta=float((other.logloss_model - other.logloss_baseline).mean())))
    return dict(
        provenance="Frozen 500 OpenDota cached payloads, no external API calls or model fits",
        source_games=int(len(src)),
        split_games={str(k):int(v) for k,v in src.partition.value_counts().items()},
        label_completion_overlap=dict(
            train_before_first_validation=int(len(train_val_overlaps)),
            max_train_validation_overlap_seconds=int(
                max((train_val_overlaps.estimated_end_time-val.start_time.min()).max(), 0)
                if len(train_val_overlaps) else 0),
            validation_before_first_test=int(len(val_test_overlaps))),
        heldout_series=int(forecasts.series_cluster.nunique()),
        heldout_leagues=int(forecasts.leagueid.nunique()),
        heldout_games=int(forecasts.match_id.nunique()),
        heldout_minutes=int(len(forecasts)),
        heldout_label_win_rate=float(test.merge(
            raw_preds.groupby("match_id").radiant_win.first().reset_index(),
            on="match_id", validate="one_to_one").radiant_win.mean()),
        league_leave_one_out=loo,
        bootstrap=scores,
        limitations=[
            "Post-hoc reuse of previously inspected held-out data; no new blind test.",
            "Bootstrap series clusters may still share teams, leagues, and patch-specific common shocks.",
            "Estimated completion is start_time+game duration; pauses and source receipt timing unavailable.",
            "Series bootstrap intervals are descriptive, not multiplicity-adjusted or market PnL."
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.outputs, args.cache)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("INDEPENDENT_DELIVERY_AUDIT_PASS", json.dumps({
        "source_games":result["source_games"],
        "heldout_games":result["heldout_games"],
        "heldout_series":result["heldout_series"],
        "heldout_leagues":result["heldout_leagues"],
        "completion_overlap":result["label_completion_overlap"],
        "logloss_series":result["bootstrap"]["overall"]["logloss_series"],
        "brier_series":result["bootstrap"]["overall"]["brier_series"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
