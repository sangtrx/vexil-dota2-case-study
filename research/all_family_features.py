#!/usr/bin/env python3
"""Five *pre-scoring fixed* Dota feature sets from prior-only gold/objective/item info.

No final inventories, hero terminal stats, winner, match duration in predictors.
Historical as-of by index is not proof of actual live packet observability.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from rich_feature_engineering import PROVENANCE, source_key, side_from_slot

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("/home/ai-agent/.cache/vexil-real-data-20261113/api-cache")
PROTO = ROOT / "research/FEATURE_FAMILIES_EXHAUSTIVE_PROTOCOL.md"
FAMILY = {
    "R": ("reg_cusum10", "reg_shift3"),
    "O": ("ordinal_run_balance10", "ordinal_entropy10"),
    "C": ("objective_conversion5", "objective_followthrough10"),
    "I": ("item_bkb_diff", "item_blink_diff", "item_recent5_diff"),
}
COLS = tuple(x for names in FAMILY.values() for x in names)
assert len(COLS) == 9 and len(set(COLS)) == 9


def parse_objectives(raw: dict) -> list[tuple[float,int]]:
    """Typed objective side is from *killed building*, not final tower status."""
    result=[]
    for e in raw.get("objectives") or []:
        if not isinstance(e,dict) or e.get("type") != "building_kill":
            continue
        tm=e.get("time")
        k=e.get("key")
        if not isinstance(tm,(float,int)) or isinstance(tm,bool) or not math.isfinite(tm) or tm<0:
            continue
        if not isinstance(k,str):
            continue
        k=k.lower()
        if not any(s in k for s in ("tower","rax","barracks")):
            continue
        if "badguys" in k and "goodguys" not in k:
            side=1
        elif "goodguys" in k and "badguys" not in k:
            side=-1
        else:
            continue
        result.append((float(tm),side))
    return sorted(result)


def parse_item_milestones(raw:dict) -> list[tuple[float,int,str,int]]:
    """Historical purchase log only. Explicitly discard pre-game negative timestamps."""
    result=[]
    players=raw.get("players")
    if not isinstance(players,list) or len(players)!=10:
        raise ValueError("Exactly 10 players required for item family")
    if sum(side_from_slot(p.get("player_slot"))==1 for p in players)!=5:
        raise ValueError("Invalid Radiant membership")
    for p in players:
        slot=p.get("player_slot")
        side=side_from_slot(slot)
        if not side:
            raise ValueError("Invalid player slot")
        for e in p.get("purchase_log") or []:
            if not isinstance(e,dict):continue
            tm=e.get("time")
            key=e.get("key")
            if key not in ("black_king_bar","blink"):
                continue
            if not isinstance(tm,(int,float)) or isinstance(tm,bool) or not math.isfinite(tm) or tm<0:
                continue
            result.append((float(tm),side,str(key),int(slot)))
    return sorted(result)


def one_snapshot(gold_full, minute: int, objectives, purchases)->dict[str,float]:
    """Supplied *full* history is trimmed internally before any statistic or event."""
    g=np.asarray(gold_full,dtype=float)
    if (type(minute) not in (int,np.int64,np.int32) or minute<0
        or g.ndim!=1 or len(g)<=minute or not np.isfinite(g[:minute+1]).all()):
        raise ValueError("Invalid known gold prefix")
    hist=g[max(0,minute-10):minute+1]
    dg=np.diff(hist)
    output={}
    # R: one-sided CUSUMs on signed gold innovation; odd under team swap.
    pos=neg=0.
    for k,step in enumerate(dg):
        preceding=dg[max(0,k-5):k]
        scale=0.25+(float(np.median(np.abs(preceding))) if len(preceding) else 0.)
        z=float(np.clip(step/scale,-5.,5.))
        pos=max(0.,pos+z-0.5)
        neg=max(0.,neg-z-0.5)
    output["reg_cusum10"]=(pos-neg)/(len(dg)+1)
    if len(dg)>=4:
        previous=dg[max(0,len(dg)-6):-3]
        output["reg_shift3"]=float((np.mean(dg[-3:])-np.mean(previous))
                / (0.5+np.sqrt(np.mean(dg[-6:]**2))))
    else:
        output["reg_shift3"]=0.

    # O: strict ordinal pairs, tie-aware, and sign-symmetric permutation entropy.
    signs=np.sign(dg)
    n=max(0,len(signs)-1)
    if n:
        first,second=signs[:-1],signs[1:]
        pp=int(np.sum((first>0)&(second>0)))
        nn=int(np.sum((first<0)&(second<0)))
        pn=int(np.sum((first>0)&(second<0)))
        npair=int(np.sum((first<0)&(second>0)))
        valid=pp+nn+pn+npair
        output["ordinal_run_balance10"]=(pp-nn)/n
        if valid:
            ps=np.asarray([pp,nn,pn,npair],dtype=float)/valid
            ps=ps[ps>0]
            entropy=float(-np.sum(ps*np.log(ps))/math.log(4.))
            output["ordinal_entropy10"]=float(np.sign(g[minute])*entropy)
        else:
            output["ordinal_entropy10"]=0.
    else:
        output["ordinal_run_balance10"]=0.
        output["ordinal_entropy10"]=0.

    # C: past tower/barracks events, only while observed at current minute.
    cutoff=float(minute*60)
    cv5=cv10=0.
    n5=n10=0
    for tm,side in objectives:
        if tm<0 or tm>cutoff:continue
        age=cutoff-tm
        if age>600:continue
        event_min=int(tm//60)
        if event_min>minute:raise AssertionError("Objective event lookahead")
        # Signed increase in *size* of lead since a team won a building.
        delta=abs(float(g[minute]))-abs(float(g[event_min]))
        if age<=300:
            cv5+=side*delta
            n5+=1
        cv10+=side*delta*math.exp(-age/300.)
        n10+=1
    output["objective_conversion5"]=cv5/(1+n5)
    output["objective_followthrough10"]=cv10/(1+n10)

    # I: first BKB/Blink completion per player, strictly filtered at time <=t.
    first_item={}
    for tm,side,key,slot in purchases:
        if tm<0 or tm>cutoff or key not in ("black_king_bar","blink"):
            continue
        ix=(slot,key)
        if ix not in first_item or tm<first_item[ix][0]:
            first_item[ix]=(tm,side)
    bkb=blink=recent=0
    for (slot,key),(tm,side) in first_item.items():
        if key=="black_king_bar":bkb+=side
        else:blink+=side
        if 0<=cutoff-tm<=300:
            recent+=side
    output["item_bkb_diff"]=float(bkb)
    output["item_blink_diff"]=float(blink)
    output["item_recent5_diff"]=float(recent)
    if tuple(output)!=COLS or not all(math.isfinite(v) for v in output.values()):
        raise AssertionError("Feature family ordering, type or finiteness")
    return output


def mirror(objectives,purchases):
    return [(tm,-side) for tm,side in objectives],[
       (tm,-side,key,slot) for tm,side,key,slot in purchases]


def build_frozen_train(df:pd.DataFrame,cache:Path=CACHE)->tuple[pd.DataFrame,dict]:
    """Only 291 already-derived TRAIN source matches; all outcome joins later."""
    prior=json.loads(PROVENANCE.read_text())
    if len(df)!=10675 or df.match_id.nunique()!=291 or set(df.partition)!={"train"}:
        raise ValueError("Not original 291 TRAIN matches")
    work=df.sort_values(["match_id","minute"],kind="stable").reset_index(drop=True).copy()
    vals=np.empty((len(work),len(COLS)),dtype=float)
    patch_counts={}
    digest=[]
    checks=0
    for match,part in work.groupby("match_id",sort=False):
        path=cache/(source_key(int(match))+".json.gz")
        blob=path.read_bytes()
        digest.append([int(match),hashlib.sha256(blob).hexdigest()])
        raw=json.loads(gzip.decompress(blob))
        if (int(raw.get("match_id",-1))!=int(match)
            or int(raw.get("duration",-1))!=int(part.duration.iloc[0])):
            raise AssertionError("Original raw-cache match identifier/duration parity")
        patch=str(raw.get("patch"))
        if patch not in ("59","60"):
            raise ValueError("Unknown original patch; check data provenance")
        patch_counts[patch]=patch_counts.get(patch,0)+1
        idx=part.index.to_numpy(dtype=int)
        mins=part.minute.to_numpy(int)
        if not np.array_equal(mins,np.arange(len(part))):
            raise AssertionError("Unexpected match-minute grid")
        gold=part.gold_k.to_numpy(float)
        original=raw.get("radiant_gold_adv")
        if (not isinstance(original,list) or len(original)<len(part)
            or not np.allclose(gold,np.asarray(original[:len(part)],float)/1000,atol=1e-12,rtol=0)):
            raise AssertionError("Original replay gold input mismatch")
        objective=parse_objectives(raw)
        purchase=parse_item_milestones(raw)
        mo,mp=mirror(objective,purchase)
        for j,t in zip(idx,mins):
            feat=one_snapshot(gold,int(t),objective,purchase)
            m=one_snapshot(-gold,int(t),mo,mp)
            v=np.asarray(list(feat.values()),dtype=float)
            vm=np.asarray(list(m.values()),dtype=float)
            if not np.allclose(v,-vm,rtol=0,atol=1e-10):
                raise AssertionError("Radiant/Dire sign mirror broken")
            # Explicit suffix poison and future events; current minute unchanged.
            if t+1<len(gold):
                poisoned=gold.copy()
                poisoned[t+1:]=1e8
                fo=objective+[(float((t+1)*60),1)]
                fp=purchase+[(float((t+1)*60),1,"blink",0)]
                if one_snapshot(poisoned,int(t),fo,fp)!=feat:
                    raise AssertionError("Future suffix or event changes an earlier prediction")
            vals[j]=v
            checks+=1
        work.loc[idx,"patch_audit"]=patch
    full_digest=hashlib.sha256(json.dumps(sorted(digest),separators=(",",":"),sort_keys=True).encode()).hexdigest()
    if full_digest!=prior["source_payload_bytes_sha256"]:
        raise AssertionError("Frozen raw aggregate digest mismatch")
    if checks!=10675 or not np.isfinite(vals).all():
        raise AssertionError("Feature coverage drift")
    for j,name in enumerate(COLS):
        work[name]=vals[:,j]
    return work,{
        "features":list(COLS),
        "family_counts":{k:len(v) for k,v in FAMILY.items()},
        "raw_cache_digest":full_digest,
        "matches":291,"minutes":checks,
        "mirror_validated":checks,"suffix_and_future_event_validated":checks,
        "patch_match_counts":patch_counts,
        "used_end_of_game_inventory":False,
        "used_ability_upgrade_without_timestamp":False,
        "actual_feed_received_at_verified":False,
    }
