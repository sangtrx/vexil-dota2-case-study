#!/usr/bin/env python3
"""81 causal, mirrored match-state features from frozen original TRAIN raw JSON.

Every forecast input is explicitly projected to <=minute t *before* any
features are computed. Final outcome, duration-derived state, static
end-of-game player stats and post-t events are never in the view.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/frozen_original_train_features.csv.gz"
# New post-result artifact. Never overwrite the historic 84-input experiment.
FEATURES = ROOT / "research/RICH_FEATURE_TRAIN_ONLY_ROSHAN_CORRECTED.csv.gz"
PROVENANCE = ROOT / "research/RICH_FEATURE_RAW_PROVENANCE_ROSHAN_CORRECTED.json"
TRAIN_SHA = "066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
BASE = ["gold_k", "minute10", "gold_x_time"]
FAMILIES = {
    "gold": [
        "gold_d1","gold_d3","gold_d5","gold_d10","gold_acc3","gold_acc5",
        "gold_vol3","gold_vol5","gold_vol10","gold_range5","gold_range10",
        "gold_retreat5","gold_retreat10","gold_eff5","gold_eff10",
        "gold_flips10","gold_peak_age10","gold_slope5","gold_ewma_gap10",
    ],
    "xp": [
        "xp_level","xp_d3","xp_d5","xp_d10","xp_acc5","xp_vol5","xp_vol10",
        "xp_retreat10","xp_eff10","xp_flips10","xp_slope5",
        "gold_xp_gap","gold_xp_flow_gap",
    ],
    "players": [
        "p_gold_top1_diff","p_gold_top2_diff","p_gold_bottom2_diff",
        "p_gold_median_diff","p_gold_std_diff","p_gold_gini_diff",
        "p_gold_top1_share_diff","p_gold_top2_share_diff",
        "p_gold_bottom2_share_diff","p_gold_growth3_top2_diff",
        "p_gold_growth5_bottom2_diff","p_xp_top2_share_diff","p_xp_gini_diff",
        "p_lh_total_diff","p_lh_top2_diff","p_lh_growth3_diff",
        "p_dn_total_diff","p_lh_balance_diff","p_concentration_gap",
    ],
    "objectives": [
        "o_tower_delta","o_rax_delta","o_roshan_delta","o_kills_delta",
        "o_tower5_delta","o_tower10_delta","o_kill3_delta","o_kill5_delta",
        "o_last_tower_age_diff","o_last_kill_age_diff",
        "o_roshan10_delta","o_aegis5_delta","o_tower_weighted",
        "o_rax10_delta","o_firstblood_side","o_highground_delta",
        "o_objective_tempo",
    ],
    "interactions": [
        "x_gold_per_sqrt_time","x_xp_per_sqrt_time","x_economy_gap",
        "x_gold_vol_adj","x_opp_kill_mismatch","x_gold_tower_mismatch",
        "x_xp_tower_mismatch","x_gold_early","x_gold_late",
        "x_gold_times_abs_tower","x_tower_times_abs_gold",
        "x_gold_times_abs_kill","x_volatile_retreat",
    ],
}
RICH = [key for cols in FAMILIES.values() for key in cols]
assert len(RICH) == 81 and len(set(RICH)) == 81


def source_key(match_id: int) -> str:
    # Same stable cache scheme as the original notebook replay.
    return hashlib.sha256(
        json.dumps([f"/matches/{match_id}", {}], sort_keys=True).encode()
    ).hexdigest()


def side_from_slot(v) -> int:
    if type(v) is not int:
        return 0
    if 0 <= v <= 4:
        return 1
    if 128 <= v <= 132:
        return -1
    return 0


def _past_events(events, cutoff: int):
    if not isinstance(events, list):
        return []
    return [
        e for e in events if isinstance(e, dict)
        and isinstance(e.get("time"), (int, float))
        and math.isfinite(e["time"])
        and 0 <= e["time"] <= cutoff
    ]


def project_asof(raw: dict, minute: int) -> dict:
    """Only these fields enter the model; no winner/terminal aggregate exists."""
    if minute < 0 or not isinstance(minute, (int, np.integer)):
        raise ValueError("Minute must be nonnegative integer")
    cutoff = int(minute) * 60
    out = {}
    for k in ("radiant_gold_adv", "radiant_xp_adv"):
        a = raw.get(k)
        if not isinstance(a, list) or len(a) <= minute:
            raise ValueError(f"Missing exact minute {minute} from {k}")
        out[k] = a[:minute+1]
    out["objectives"] = _past_events(raw.get("objectives"), cutoff)
    players = raw.get("players")
    if not isinstance(players, list) or len(players) != 10:
        raise ValueError("Expected 10 players")
    out["players"] = []
    for p in players:
        slot = p.get("player_slot")
        if not side_from_slot(slot):
            raise ValueError("Unassigned player slot")
        row = {"player_slot": slot}
        for k in ("gold_t", "xp_t", "lh_t", "dn_t"):
            a = p.get(k)
            if not isinstance(a, list) or len(a) <= minute:
                raise ValueError(f"Player {slot} missing {k}[{minute}]")
            row[k] = a[:minute+1]
        row["kills_log"] = _past_events(p.get("kills_log"), cutoff)
        out["players"].append(row)
    if [side_from_slot(p["player_slot"]) for p in out["players"]].count(1) != 5:
        raise ValueError("Team membership mismatch")
    if len({p["player_slot"] for p in out["players"]}) != 10:
        raise ValueError("Duplicate player slot")
    return out


def trail(a, horizon: int) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    return a[max(0, len(a)-horizon-1):]


def delta(a, horizon: int) -> float:
    v = trail(a, horizon)
    return float(v[-1] - v[0])


def acceleration(a, h: int) -> float:
    a = np.asarray(a, dtype=float)
    t = len(a)-1
    return float((a[t]-a[max(0,t-h)]) - (a[max(0,t-h)]-a[max(0,t-2*h)]))


def volatility(a, h: int) -> float:
    d = np.diff(trail(a, h))
    return float(np.sqrt(np.mean(d*d))) if len(d) else 0.0


def retreat(a, h: int) -> float:
    v = trail(a, h)
    s = np.sign(v[-1])
    return float(s * max(0.0, float(np.max(s*v)) - abs(float(v[-1]))))


def efficiency(a, h: int) -> float:
    v = trail(a, h)
    d = np.diff(v)
    return float((v[-1]-v[0])/(np.abs(d).sum()+1e-6)) if len(d) else 0.0


def slope(a, h: int) -> float:
    v = trail(a, h)
    if len(v) == 1:
        return 0.0
    x = np.arange(len(v), dtype=float)
    x -= x.mean()
    return float(np.dot(x,v)/(np.dot(x,x)+1e-12))


def flips(a, h: int) -> float:
    v = trail(a, h)
    s = np.sign(v)
    return float(np.sum((s[1:]*s[:-1]) < 0))


def peak_age(a, h: int) -> float:
    v = trail(a, h)
    s = float(np.sign(v[-1]))
    if not s:
        return 0.0
    # Use latest equal peak for a stable time-since-peak.
    k = len(v)-1-int(np.argmax((s*v)[::-1]))
    return float(s*(len(v)-1-k))


def ewm_gap(a: np.ndarray) -> float:
    # Two forward recursions: no symmetric filtering, no future observations.
    fast = slow = float(a[0])
    for v in a[1:]:
        fast = 0.6*float(v) + 0.4*fast
        slow = 0.18*float(v) + 0.82*slow
    return fast-slow


def gini(a) -> float:
    a = np.asarray(a, dtype=float)
    den = a.sum()
    return float(np.abs(a[:,None]-a[None,:]).sum()/(2*len(a)*den)) if den > 0 else 0.0


def _top(a, n: int) -> float:
    return float(np.sort(a)[-n:].sum())


def _bottom(a, n: int) -> float:
    return float(np.sort(a)[:n].sum())


def features_from_asof(view: dict) -> dict[str, float]:
    gold = np.asarray(view["radiant_gold_adv"],dtype=float)/1000.0
    xp = np.asarray(view["radiant_xp_adv"],dtype=float)/1000.0
    t = len(gold)-1
    if not len(xp)==len(gold) or not np.isfinite(gold).all() or not np.isfinite(xp).all():
        raise ValueError("Gold/XP prefixes not aligned")
    s=float(np.sign(gold[-1])); sx=float(np.sign(xp[-1]))
    o={}
    for h in (1,3,5,10):
        o[f"gold_d{h}"]=delta(gold,h)
    for h in (3,5):
        o[f"gold_acc{h}"]=acceleration(gold,h)
    for h in (3,5,10):
        o[f"gold_vol{h}"]=s*volatility(gold,h)
    for h in (5,10):
        v=trail(gold,h)
        o[f"gold_range{h}"]=float(s*(v.max()-v.min()))
        o[f"gold_retreat{h}"]=retreat(gold,h)
        o[f"gold_eff{h}"]=efficiency(gold,h)
    o["gold_flips10"]=s*flips(gold,10)
    o["gold_peak_age10"]=peak_age(gold,10)
    o["gold_slope5"]=slope(gold,5)
    o["gold_ewma_gap10"]=ewm_gap(gold)
    o["xp_level"]=float(xp[-1])
    for h in (3,5,10):
        o[f"xp_d{h}"]=delta(xp,h)
    o["xp_acc5"]=acceleration(xp,5)
    for h in (5,10):
        o[f"xp_vol{h}"]=sx*volatility(xp,h)
    o["xp_retreat10"]=retreat(xp,10)
    o["xp_eff10"]=efficiency(xp,10)
    o["xp_flips10"]=sx*flips(xp,10)
    o["xp_slope5"]=slope(xp,5)
    o["gold_xp_gap"]=float(gold[-1]-0.35*xp[-1])
    o["gold_xp_flow_gap"]=delta(gold,5)-0.35*delta(xp,5)

    player_teams = {1:[], -1:[]}
    for p in view["players"]:
        player_teams[side_from_slot(p["player_slot"])].append(p)
    if len(player_teams[1]) != 5 or len(player_teams[-1]) != 5:
        raise ValueError("Exactly 5 per team required")
    def vals(side,key,earlier=0):
        team=player_teams[side]
        return np.array([float(p[key][max(0,len(p[key])-1-earlier)]) for p in team])
    rg, dg = vals(1,"gold_t"), vals(-1,"gold_t")
    rx, dx = vals(1,"xp_t"), vals(-1,"xp_t")
    rh, dh = vals(1,"lh_t"), vals(-1,"lh_t")
    rd, dd = vals(1,"dn_t"), vals(-1,"dn_t")
    rsum,dsum=rg.sum(),dg.sum()
    share=lambda a, n, bottom=False: (
        (_bottom(a,n) if bottom else _top(a,n))/(a.sum()+1e-6)
        if a.sum() > 0 else 0.0
    )
    o["p_gold_top1_diff"]=(_top(rg,1)-_top(dg,1))/1000.
    o["p_gold_top2_diff"]=(_top(rg,2)-_top(dg,2))/1000.
    o["p_gold_bottom2_diff"]=(_bottom(rg,2)-_bottom(dg,2))/1000.
    o["p_gold_median_diff"]=float((np.median(rg)-np.median(dg))/1000.)
    o["p_gold_std_diff"]=float((np.std(rg)-np.std(dg))/1000.)
    o["p_gold_gini_diff"]=gini(rg)-gini(dg)
    o["p_gold_top1_share_diff"]=share(rg,1)-share(dg,1)
    o["p_gold_top2_share_diff"]=share(rg,2)-share(dg,2)
    o["p_gold_bottom2_share_diff"]=share(rg,2,True)-share(dg,2,True)
    o["p_gold_growth3_top2_diff"]=(
        (_top(rg,2)-_top(vals(1,"gold_t",3),2))
        -(_top(dg,2)-_top(vals(-1,"gold_t",3),2))
    )/1000.
    o["p_gold_growth5_bottom2_diff"]=(
        (_bottom(rg,2)-_bottom(vals(1,"gold_t",5),2))
        -(_bottom(dg,2)-_bottom(vals(-1,"gold_t",5),2))
    )/1000.
    o["p_xp_top2_share_diff"]=share(rx,2)-share(dx,2)
    o["p_xp_gini_diff"]=gini(rx)-gini(dx)
    o["p_lh_total_diff"]=(rh.sum()-dh.sum())/100.
    o["p_lh_top2_diff"]=(_top(rh,2)-_top(dh,2))/100.
    o["p_lh_growth3_diff"]=(
        (rh.sum()-vals(1,"lh_t",3).sum())
        -(dh.sum()-vals(-1,"lh_t",3).sum())
    )/10.
    o["p_dn_total_diff"]=(rd.sum()-dd.sum())/100.
    o["p_lh_balance_diff"]=float((rh.sum()-dh.sum())/(rh.sum()+dh.sum()+1))
    o["p_concentration_gap"]=o["p_gold_gini_diff"]-o["p_xp_gini_diff"]

    cutoff=t*60
    events={"tower":[],"rax":[],"roshan":[],"kill":[],"aegis":[],"firstblood":[]}
    weighted_towers=0.
    highground=0.
    for e in view["objectives"]:
        tm=float(e["time"]); typ=str(e.get("type",""))
        if typ=="building_kill":
            key=str(e.get("key","")).lower()
            side = 1 if "badguys" in key else (-1 if "goodguys" in key else 0)
            if not side:
                continue
            if "tower" in key:
                events["tower"].append((tm,side))
                rank=3 if "tower3" in key else (2 if "tower2" in key else 1)
                weighted_towers += side*rank
                if rank==3:highground+=side
            elif "rax" in key or "barracks" in key:
                events["rax"].append((tm,side))
                highground+=side
        elif typ=="CHAT_MESSAGE_ROSHAN_KILL":
            # OpenDota attributes Roshan kills to Dota team 2 (Radiant)
            # or 3 (Dire). Roshan kill events do not carry player slots.
            team=e.get("team")
            side=1 if type(team) is int and team==2 else (
                -1 if type(team) is int and team==3 else 0
            )
            if side:
                events["roshan"].append((tm,side))
        elif typ in ("CHAT_MESSAGE_AEGIS","CHAT_MESSAGE_FIRSTBLOOD"):
            # Item pickup/first-blood events carry player_slot (or slot),
            # unlike Roshan kills. Do not infer the Roshan winner from Aegis.
            side=side_from_slot(
                e.get("player_slot") if e.get("player_slot") is not None else e.get("slot")
            )
            if side:
                category="aegis" if typ=="CHAT_MESSAGE_AEGIS" else "firstblood"
                events[category].append((tm,side))
    for side, team in player_teams.items():
        for p in team:
            for e in p["kills_log"]:
                events["kill"].append((float(e["time"]),side))

    def total(key,h=None):
        xs=events[key]
        lower=cutoff-h*60 if h is not None else -1e99
        return float(sum(side for tm,side in xs if tm > lower))
    def age_difference(key):
        xs=events[key]
        def age(side):
            entries=[tm for tm,k in xs if k==side]
            return (cutoff-max(entries)) if entries else cutoff+600
        return (age(-1)-age(1))/600.
    o["o_tower_delta"]=total("tower")
    o["o_rax_delta"]=total("rax")
    o["o_roshan_delta"]=total("roshan")
    o["o_kills_delta"]=total("kill")
    o["o_tower5_delta"]=total("tower",5)
    o["o_tower10_delta"]=total("tower",10)
    o["o_kill3_delta"]=total("kill",3)
    o["o_kill5_delta"]=total("kill",5)
    o["o_last_tower_age_diff"]=age_difference("tower")
    o["o_last_kill_age_diff"]=age_difference("kill")
    o["o_roshan10_delta"]=total("roshan",10)
    o["o_aegis5_delta"]=total("aegis",5)
    o["o_tower_weighted"]=float(weighted_towers)
    o["o_rax10_delta"]=total("rax",10)
    o["o_firstblood_side"]=float(events["firstblood"][0][1]) if events["firstblood"] else 0.
    o["o_highground_delta"]=float(highground)
    o["o_objective_tempo"]=(o["o_tower5_delta"]+1.5*o["o_rax10_delta"]
        +1.5*o["o_roshan10_delta"]+0.2*o["o_kill5_delta"])

    g=float(gold[-1]);x=float(xp[-1]);m=float(t)
    o["x_gold_per_sqrt_time"]=g/math.sqrt(1+m)
    o["x_xp_per_sqrt_time"]=x/math.sqrt(1+m)
    o["x_economy_gap"]=g-0.35*x
    o["x_gold_vol_adj"]=g/(1+abs(o["gold_vol5"]))
    o["x_opp_kill_mismatch"]=g-0.4*o["o_kills_delta"]
    o["x_gold_tower_mismatch"]=g-2.*o["o_tower_delta"]
    o["x_xp_tower_mismatch"]=x-o["o_tower_delta"]
    o["x_gold_early"]=g*math.exp(-m/10.)
    o["x_gold_late"]=g*(1-math.exp(-m/10.))
    o["x_gold_times_abs_tower"]=g*abs(o["o_tower_delta"])
    o["x_tower_times_abs_gold"]=o["o_tower_delta"]*abs(g)
    o["x_gold_times_abs_kill"]=g*abs(o["o_kills_delta"])
    o["x_volatile_retreat"]=s*abs(o["gold_vol5"])*abs(o["gold_retreat10"])

    if set(o)!=set(RICH):
        raise AssertionError(f"81-feature registry mismatch: {set(RICH)-set(o)}, {set(o)-set(RICH)}")
    if not all(math.isfinite(float(v)) for v in o.values()):
        raise ValueError("Nonfinite engineered feature")
    return {k:float(o[k]) for k in RICH}


def develop(cache_dir: Path) -> tuple[pd.DataFrame, dict]:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=TRAIN_SHA:
        raise ValueError("Original TRAIN source hash drift")
    base=pd.read_csv(SOURCE,float_precision="round_trip")
    if len(base)!=10675 or base.match_id.nunique()!=291 or set(base.partition)!={"train"}:
        raise ValueError("Unexpected original TRAIN scope")
    if base[["match_id","minute"]].duplicated().any():
        raise ValueError("Duplicate minute")
    hashes=[]
    out=[]
    mirror_checks=0
    gold_parity=0
    for mid, sub in base.groupby("match_id",sort=True):
        key=source_key(int(mid))
        path=cache_dir/(key+".json.gz")
        blob=path.read_bytes()
        raw=json.loads(gzip.decompress(blob))
        if raw.get("match_id")!=int(mid):
            raise ValueError("Wrong raw source match ID")
        hashes.append([int(mid),hashlib.sha256(blob).hexdigest()])
        minute=sub.minute.to_numpy(int)
        if not np.array_equal(np.sort(minute),np.arange(len(sub))):
            raise ValueError("Expected continuous prefix minutes")
        for row in sub.sort_values("minute").itertuples(index=False):
            t=int(row.minute)
            view=project_asof(raw,t)
            score=features_from_asof(view)
            actual=float(view["radiant_gold_adv"][-1])/1000.
            if not math.isclose(actual,float(row.gold_k),rel_tol=0,abs_tol=1e-12):
                raise AssertionError("Original gold_k frozen feature parity failed")
            gold_parity+=1
            # Mirror test on a deterministic 3-point grid per match; the
            # all-minute leakage gate is structural because the view
            # physically cannot contain t+1 or any terminal labels.
            if t in (0,5,10):
                mirrored=mirror_view(view)
                m=features_from_asof(mirrored)
                if not all(math.isclose(score[k],-m[k],rel_tol=0,abs_tol=1e-8) for k in RICH):
                    bad=[k for k in RICH if not math.isclose(score[k],-m[k],rel_tol=0,abs_tol=1e-8)]
                    raise AssertionError(f"Side-mirror parity failed: {bad[:12]}")
                mirror_checks+=1
            out.append([int(mid),t,*[score[k] for k in RICH]])
    derived=pd.DataFrame(out,columns=["match_id","minute",*RICH])
    combined=base.merge(derived,on=["match_id","minute"],how="left",validate="one_to_one",sort=False)
    if len(combined)!=10675 or combined[RICH].isna().any().any():
        raise AssertionError("Derived model rows changed or incomplete")
    return combined, {
        "source_train_sha256":TRAIN_SHA,
        "source_payload_bytes_sha256":hashlib.sha256(
            json.dumps(hashes,separators=(",",":"),sort_keys=True).encode()).hexdigest(),
        "raw_games_read":len(hashes),
        "minute_prefixes_checked":len(out),
        "original_gold_lead_parity":gold_parity,
        "side_mirror_checks":mirror_checks,
        "inputs_from_live_received_at_confirmed":False,
        "no_validation_test_match_payloads_read":True,
        "features":RICH,"families":{k:len(v) for k,v in FAMILIES.items()},
    }


def mirror_view(v:dict) -> dict:
    """Synthetic team-side exchange on already truncated data."""
    flipped=copy.deepcopy(v)
    for k in ("radiant_gold_adv","radiant_xp_adv"):
        flipped[k]=[-float(x) for x in v[k]]
    for p in flipped["players"]:
        slot=p["player_slot"]
        p["player_slot"]=slot+128 if slot<5 else slot-128
    for e in flipped["objectives"]:
        slot=e.get("player_slot")
        if side_from_slot(slot):
            e["player_slot"]=slot+128 if slot<5 else slot-128
        slot=e.get("slot")
        if side_from_slot(slot):
            e["slot"]=slot+128 if slot<5 else slot-128
        team=e.get("team")
        if e.get("type")=="CHAT_MESSAGE_ROSHAN_KILL" and type(team) is int:
            if team in (2,3):
                e["team"]=5-team
        key=e.get("key")
        if isinstance(key,str):
            e["key"]=key.replace("badguys","__swap__").replace("goodguys","badguys").replace("__swap__","goodguys")
    return flipped


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mx=ap.add_mutually_exclusive_group(required=True)
    mx.add_argument("--write",action="store_true")
    mx.add_argument("--check",action="store_true")
    ap.add_argument("--cache-dir",type=Path,required=True)
    args=ap.parse_args()
    frame, receipt=develop(args.cache_dir)
    # Bit reproducible gz stream: mtime=0 and exact stable file order.
    if args.write:
        frame.to_csv(FEATURES,index=False,compression={"method":"gzip","mtime":0},
                     float_format="%.15g")
        receipt["frozen_feature_csv_sha256"]=hashlib.sha256(FEATURES.read_bytes()).hexdigest()
        PROVENANCE.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        print("WROTE",len(frame),"ROWS",len(RICH),"FEATURES")
    else:
        stored=json.loads(PROVENANCE.read_text())
        if hashlib.sha256(FEATURES.read_bytes()).hexdigest()!=stored["frozen_feature_csv_sha256"]:
            raise AssertionError("Feature data drifted")
        receipt["frozen_feature_csv_sha256"]=stored["frozen_feature_csv_sha256"]
        if receipt!=stored:
            raise AssertionError("Source raw provenance differs")
        frozen=pd.read_csv(FEATURES,float_precision="round_trip")
        if not np.allclose(frozen[RICH],frame[RICH],rtol=1e-13,atol=1e-12):
            raise AssertionError("81 features do not reproduce original data")
        print("PASS",len(frame),"TRAIN PREFIXES",len(RICH),"FEATURES")

if __name__=="__main__":
    main()
