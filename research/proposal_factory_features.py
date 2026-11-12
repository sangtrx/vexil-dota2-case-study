"""Frozen, source-limited per-minute innovation features for 28 proposals.

Only permitted OpenDota match payload fields and information at or before
minute T. No use of terminal aggregates, result, or duration as predictor.
No code copied from external repositories.
"""
from __future__ import annotations
import copy
import math
from collections import defaultdict
from collections.abc import Mapping
import numpy as np

HERO_DIM=160
HERO_COLUMNS=tuple("draft_h"+str(i) for i in range(1,HERO_DIM+1))
MAJOR_ITEM_KEYS=frozenset({
    "blink","black_king_bar","manta","force_staff","sphere",
    "aghanims_shard","ultimate_scepter","radiance","desolator",
    "bfury","assault","heart","satanic","skadi",
    "nullifier","octarine_core","abyssal_blade","refresher",
    "diffusal_blade","pipe","crimson_guard","orchid","bloodthorn",
    "shivas_guard","lotus_orb","silver_edge","monkey_king_bar",
    "heavens_halberd","bkb","glimmer_cape"
})

def valid_event_time(ev):
    if not isinstance(ev,Mapping):return None
    t=ev.get("time")
    return float(t) if type(t) in (int,float) and math.isfinite(t) else None

def signed_slot(slot):
    if type(slot) is not int:return None
    if 0<=slot<=4:return +1
    if 128<=slot<=132:return -1
    return None

def last(values,t):
    if not isinstance(values,list):return float("nan")
    for i in range(min(t,len(values)-1),-1,-1):
        x=values[i]
        if type(x) in (int,float) and math.isfinite(x):return float(x)
    return float("nan")

def age_weight(ev_time, cutoff, horizon_seconds):
    age=cutoff-ev_time
    return max(0.,1-age/horizon_seconds) if 0<=age<=horizon_seconds else 0.

def gini(vals):
    arr=np.asarray(vals,dtype=float)
    if not np.isfinite(arr).all() or np.sum(arr)<=0:return float("nan")
    arr=np.sort(arr)
    n=len(arr)
    return float(2.*np.dot(np.arange(1,n+1),arr)/(n*arr.sum())-(n+1)/n)

def _sum_close(events, cutoff, horizon, weighted=False):
    total=0.
    for ts,sign in events:
        if ts<=cutoff and (cutoff-ts)<=horizon:
            total+=sign*(age_weight(ts,cutoff,horizon) if weighted else 1.)
    return total

def _sum_cumulative(events, cutoff):
    return sum(sign for ts,sign in events if ts<=cutoff)

def build_match_events(match):
    """Validate event streams and capture signed events once per match."""
    players=match.get("players")
    obj=match.get("objectives")
    if not isinstance(players,list) or len(players)!=10:
        players=None
    if players is not None:
        slots=[p.get("player_slot") if isinstance(p,dict) else None for p in players]
        if len(set(slots))!=10 or any(signed_slot(x) is None for x in slots):
            players=None
    events={
        "tower":[],"roshan":[],"aegis":[],"buyback":[],"kills":[],
        "major":[],"impact":[],"player_major":defaultdict(list)
    }
    valid_obj=isinstance(obj,list)
    valid_kills=players is not None and all(isinstance(p.get("kills_log"),list) for p in players)
    valid_buyback=players is not None and all(isinstance(p.get("buyback_log"),list) for p in players)
    valid_purchases=players is not None and all(isinstance(p.get("purchase_log"),list) for p in players)
    if valid_obj:
        for event in obj:
            ts=valid_event_time(event)
            if ts is None:
                valid_obj=False
                continue
            kind=event.get("type")
            if kind=="building_kill":
                key=str(event.get("key") or "").lower()
                sign=+1 if "badguys" in key else -1 if "goodguys" in key else 0
                if sign==0:continue
                if "tower" in key:
                    if "tower1" in key:tier=1
                    elif "tower2" in key:tier=2
                    elif "tower3" in key:tier=3
                    elif "tower4" in key:tier=4
                    else:tier=1
                    events["tower"].append((ts,sign,tier))
            elif kind=="CHAT_MESSAGE_ROSHAN_KILL":
                team=event.get("team")
                sign=1 if team==2 else -1 if team==3 else None
                if sign is None:valid_obj=False
                else:events["roshan"].append((ts,sign))
            elif kind=="CHAT_MESSAGE_AEGIS":
                sign=signed_slot(event.get("player_slot"))
                if sign is None:valid_obj=False
                else:events["aegis"].append((ts,sign))
    if players:
        for p in players:
            sign=signed_slot(p["player_slot"])
            if valid_kills:
                for ev in p["kills_log"]:
                    ts=valid_event_time(ev)
                    if ts is None:valid_kills=False
                    else:events["kills"].append((ts,sign))
            if valid_buyback:
                for ev in p["buyback_log"]:
                    ts=valid_event_time(ev)
                    if ts is None:valid_buyback=False
                    else:events["buyback"].append((ts,sign))
            if valid_purchases:
                for ev in p["purchase_log"]:
                    ts=valid_event_time(ev)
                    if ts is None:
                        valid_purchases=False
                        continue
                    key=ev.get("key")
                    if key in MAJOR_ITEM_KEYS:
                        events["major"].append((ts,sign))
                        events["player_major"][int(p["player_slot"])].append(ts)
                    if key in ("blink","black_king_bar","bkb"):
                        events["impact"].append((ts,sign))
    return dict(events=events,obj_ok=valid_obj,kills_ok=valid_kills,
                buyback_ok=valid_buyback,purchases_ok=valid_purchases,
                players_ok=players is not None)

def make_snapshot(match, minute, base_snapshot, prepared=None):
    """Generate a full candidate feature row for one integer minute."""
    if type(minute) is not int or minute<0:raise ValueError("minute must be a nonnegative integer")
    x=dict(base_snapshot(match,minute))
    cutoff=60*minute
    gold_k=x["gold_k"]
    gold=gold_k*1000.
    hist=match.get("radiant_gold_adv")
    h5=last(hist,max(0,minute-5))
    h10=last(hist,max(0,minute-10))
    hprev=np.asarray([last(hist,i) for i in range(max(0,minute-10),minute+1)],dtype=float)
    steps5=np.diff(hprev[-6:])
    steps10=np.diff(hprev)
    flip=sum(int((hprev[i]>0 and hprev[i-1]<0) or (hprev[i]<0 and hprev[i-1]>0))
             for i in range(1,len(hprev)))
    gdraw=(gold-max(hprev) if gold>=0 else gold-min(hprev))/1000.
    persistence=np.mean(np.sign(hprev))*np.sign(gold)
    p=match.get("players")
    all_ok=(isinstance(p,list) and len(p)==10 and
            all(isinstance(z,dict) and signed_slot(z.get("player_slot")) is not None for z in p))
    team_gold={}
    team_xp={}
    team_lh={}
    if all_ok:
        for sign in (1,-1):
            ps=[z for z in p if signed_slot(z.get("player_slot"))==sign]
            vals_gold=[last(z.get("gold_t"),minute) for z in ps]
            vals_xp=[last(z.get("xp_t"),minute) for z in ps]
            vals_lh=[last(z.get("lh_t"),minute) for z in ps]
            if len(ps)!=5:all_ok=False;break
            team_gold[sign]=vals_gold;team_xp[sign]=vals_xp;team_lh[sign]=vals_lh
    if all_ok and all(np.isfinite(v).all() for v in [
        team_gold[1],team_gold[-1],team_xp[1],team_xp[-1],team_lh[1],team_lh[-1]]):
        rg,dg=team_gold[1],team_gold[-1]
        rx,dx=team_xp[1],team_xp[-1]
        rl,dl=team_lh[1],team_lh[-1]
        total_gold=sum(rg)+sum(dg)
        total_xp=sum(rx)+sum(dx)
        top2r=sum(sorted(rg)[-2:]);top2d=sum(sorted(dg)[-2:])
        x.update(relative_gold=100*gold/(total_gold+1000),
                 relative_xp=100*x["xp_k"]*1000/(total_xp+1000),
                 top2_share_gap=top2r/(sum(rg)+100)-top2d/(sum(dg)+100),
                 carry_gold_diff_k=(top2r-top2d)/1000,
                 bottom3_gold_diff_k=(sum(sorted(rg)[:3])-sum(sorted(dg)[:3]))/1000,
                 lh_diff10=(sum(rl)-sum(dl))/10,
                 gold_gini_gap=gini(rg)-gini(dg))
    else:
        x.update({f:float("nan") for f in ("relative_gold","relative_xp","top2_share_gap",
                 "carry_gold_diff_k","bottom3_gold_diff_k","lh_diff10","gold_gini_gap")})
    x.update(
        gold_signed_square=gold_k*abs(gold_k),
        gold_cubic=gold_k**3,
        gold_asinh=float(np.arcsinh(gold_k/2)),
        gold_x_early=gold_k*max(0,2-minute/10.),
        gold_x_late=gold_k*max(0,(minute-20)/10.),
        minute_sq=(minute/10.)**2,
        gold_x_minute_sq=gold_k*(minute/10.)**2,
        gold_accel10_k=(gold-2*h5+h10)/1000,
        gold_vol5_k=float(np.std(steps5)/1000) if len(steps5) else 0,
        gold_vol10_k=float(np.std(steps10)/1000) if len(steps10) else 0,
        lead_persistence10=float(persistence),
        gold_drawdown10_k=gdraw,
        lead_flip10=flip,
    )
    state=prepared if prepared is not None else build_match_events(match)
    ev=state["events"]
    if state["obj_ok"]:
        weighted=[(t,sign*{1:1.,2:1.5,3:2.5,4:3.}[tier]) for t,sign,tier in ev["tower"]]
        x["tower_tier_delta"]=_sum_cumulative(weighted,cutoff)
        x["tower_recent10"]=_sum_close([(t,sign) for t,sign,tier in ev["tower"]],cutoff,600,True)
        x["roshan_recent10"]=_sum_close(ev["roshan"],cutoff,600,True)
        x["aegis_claim5"]=_sum_close(ev["aegis"],cutoff,300,True)
        signed_structure=x["tower_delta"]+2*x["barracks_delta"]
        x["unconverted_gold_k"]=gold_k*float((gold*signed_structure)<0)
    else:
        x.update({key:float("nan") for key in ("tower_tier_delta","tower_recent10",
                  "roshan_recent10","aegis_claim5","unconverted_gold_k")})
    x["kills_recent5"]=_sum_close(ev["kills"],cutoff,300) if state["kills_ok"] else float("nan")
    x["buyback_commitment5"]=_sum_close(ev["buyback"],cutoff,300,True) if state["buyback_ok"] else float("nan")
    if state["purchases_ok"]:
        x["major_item_diff"]=_sum_cumulative(ev["major"],cutoff)
        x["blink_bkb_diff"]=_sum_cumulative(ev["impact"],cutoff)
        x["major_recent5"]=_sum_close(ev["major"],cutoff,300,True)
        x["purchasing_breadth5"]=sum(
            signed_slot(slot) for slot,times in ev["player_major"].items()
            if any(ts<=cutoff and cutoff-ts<=300 for ts in times)
        )
    else:
        x.update({key:float("nan") for key in ("major_item_diff","blink_bkb_diff",
                 "major_recent5","purchasing_breadth5")})
    heroes={key:0. for key in HERO_COLUMNS}
    if state["players_ok"]:
        for z in p:
            hid=z.get("hero_id")
            if type(hid) is int and 1<=hid<=HERO_DIM:
                heroes["draft_h"+str(hid)]+=signed_slot(z.get("player_slot"))
    x.update(heroes)
    return x

def prefix_poison(game,minute):
    """Strict future truncation and poison of all post-game/player totals."""
    if type(minute) is not int or minute<0:raise ValueError("minute must be nonnegative integer")
    clone=copy.deepcopy(game)
    cutoff=minute*60
    for key in ("radiant_gold_adv","radiant_xp_adv"):
        if isinstance(clone.get(key),list):clone[key]=clone[key][:minute+1]
    if isinstance(clone.get("objectives"),list):
        clone["objectives"]=[e for e in clone["objectives"]
                             if valid_event_time(e) is not None and valid_event_time(e)<=cutoff]
    for z in clone.get("players") or []:
        for key in ("gold_t","xp_t","lh_t","times"):
            if isinstance(z.get(key),list):z[key]=z[key][:minute+1]
        for key in ("kills_log","buyback_log","purchase_log"):
            if isinstance(z.get(key),list):
                z[key]=[e for e in z[key] if valid_event_time(e) is not None and valid_event_time(e)<=cutoff]
        for key in ("net_worth","kills","deaths","assists","total_gold","total_xp","gold_per_min","xp_per_min"):
            z[key]=-123456789
    clone["radiant_win"]=not bool(clone.get("radiant_win"))
    clone["duration"]=-123456789
    return clone
