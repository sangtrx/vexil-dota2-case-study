#!/usr/bin/env python3
"""Six unusual prefix-only player role-transition features for Dota.

Raw earned-gold and XP arrays only; no player identity, final gold, postmatch
inventory or true live received_at. Model package is historical research only.
"""
from __future__ import annotations

import hashlib
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from rich_feature_engineering import PROVENANCE, source_key, side_from_slot

CACHE = Path("/home/ai-agent/.cache/vexil-real-data-20261113/api-cache")
RANK3 = ("role_rank_turnover5","flow_hhi5_gap","flow_funnel_shift5_gap")
COUPLING3=("star_xp_share_gap","gold_xp_rank_alignment_gap","leader_flow_funnel")
ALL6=RANK3+COUPLING3


def team_array(raw, field:str,side:int)->np.ndarray:
    if side not in (1,-1) or field not in ("gold_t","xp_t"):
        raise ValueError("Unsupported role/field")
    persons=[p for p in raw.get("players",[]) if side_from_slot(p.get("player_slot"))==side]
    if len(persons)!=5:
        raise AssertionError("Not exactly five players on each team")
    arrays=[np.asarray(p.get(field),dtype=float) for p in persons]
    if len({len(a) for a in arrays})!=1:
        raise AssertionError("Player statistics have inconsistent lengths")
    values=np.stack(arrays,axis=0)
    if values.ndim!=2 or not np.isfinite(values).all() or np.any(values<0):
        raise AssertionError("Player earned-gold/XP arrays invalid")
    return values


def hhi(a)->float:
    x=np.asarray(a,dtype=float)
    if np.any(x<0):
        raise ValueError("Negative income count")
    total=float(x.sum())
    return float(np.square(x/total).sum()) if total>0 else 0.


def max_share(a)->float:
    x=np.asarray(a,dtype=float)
    total=float(x.sum())
    if np.any(x<0):
        raise ValueError("Negative role share")
    return float(x.max()/total) if total>0 else 0.


def rank_flip(a0,a1)->float:
    """Pair reversals among 5 players; ignore tied starting/end order."""
    if len(a0)!=5 or len(a1)!=5:
        raise ValueError("Five players expected")
    valid=changed=0
    for i in range(5):
        for j in range(i+1,5):
            before=float(a0[i]-a0[j])
            after=float(a1[i]-a1[j])
            if before==0 or after==0:
                continue
            valid+=1
            changed+=int(before*after<0)
    return float(changed/valid) if valid else 0.


def rank_alignment(gold,xp)->float:
    good=bad=0
    for i in range(5):
        for j in range(i+1,5):
            z=float((gold[i]-gold[j])*(xp[i]-xp[j]))
            good+=int(z>0)
            bad+=int(z<0)
    return (good-bad)/10.


def star_xp_share(gold,xp)->float:
    if len(gold)!=5 or len(xp)!=5:
        raise ValueError("Five players expected")
    denom=float(xp.sum())
    if denom<=0:
        return 0.
    leader=np.flatnonzero(gold==np.max(gold))
    return float(np.mean(xp[leader])/denom)


def one_snapshot(rg,dg,rx,dx,minute:int)->dict[str,float]:
    """All arrays (5 x times); suffix is explicitly never accessed."""
    a=[np.asarray(v,dtype=float) for v in (rg,dg,rx,dx)]
    if not isinstance(minute,(int,np.integer)) or minute<0:
        raise ValueError("Invalid minute")
    if (any(v.ndim!=2 or v.shape[0]!=5 or v.shape[1]<=minute for v in a)
        or any(np.any(v[:,:minute+1]<0) or not np.isfinite(v[:,:minute+1]).all() for v in a)):
        raise ValueError("Invalid source player prefix")
    rg,dg,rx,dx=a
    gr,gd=rg[:,minute],dg[:,minute]
    xr,xd=rx[:,minute],dx[:,minute]

    def flow_summary(g,now):
        if now==0:
            return 0.,0.,0.,0.
        before=g[:,max(0,now-5)]
        inc=np.maximum(0.,g[:,now]-before)
        return hhi(inc), max_share(inc), max_share(g[:,now]),float(inc.sum())

    rhhi,rmax,rstock,rtotal=flow_summary(rg,minute)
    dhhi,dmax,dstock,dtotal=flow_summary(dg,minute)

    if minute>=5:
        turnover=rank_flip(rg[:,minute-5],gr)-rank_flip(dg[:,minute-5],gd)
    else:
        turnover=0.

    # Empty flow has no role-funnel evidence even if initial earned gold is nonzero.
    funnel_r=(rmax-rstock) if rtotal>0 else 0.
    funnel_d=(dmax-dstock) if dtotal>0 else 0.

    sign=np.sign(float(gr.sum()-gd.sum()))
    leading_hhi=rhhi if sign>0 else (dhhi if sign<0 else 0.)
    leader_funnel=float(sign*(leading_hhi-0.2)) if minute>0 and (rtotal if sign>0 else dtotal)>0 else 0.

    out={
        "role_rank_turnover5":float(turnover),
        "flow_hhi5_gap":float(rhhi-dhhi),
        "flow_funnel_shift5_gap":float(funnel_r-funnel_d),
        "star_xp_share_gap":float(star_xp_share(gr,xr)-star_xp_share(gd,xd)),
        "gold_xp_rank_alignment_gap":float(rank_alignment(gr,xr)-rank_alignment(gd,xd)),
        "leader_flow_funnel":float(leader_funnel),
    }
    if tuple(out)!=ALL6 or not all(np.isfinite(v) and abs(v)<=2.000000001 for v in out.values()):
        raise AssertionError("Frozen role dynamics feature contract failed")
    return out


def asof_role_rows(match_id:int, raw:dict,minute_rows:list[int])->list[dict]:
    if int(raw.get("match_id",-1))!=int(match_id):
        raise AssertionError("Wrong match in player role history")
    r=team_array(raw,"gold_t",1)
    d=team_array(raw,"gold_t",-1)
    rx=team_array(raw,"xp_t",1)
    dx=team_array(raw,"xp_t",-1)
    if len({x.shape[1] for x in (r,d,rx,dx)})!=1:
        raise AssertionError("Raw player minute grids inconsistent")
    out=[]
    for t in minute_rows:
        val=one_snapshot(r,d,rx,dx,int(t))
        neg=one_snapshot(d,r,dx,rx,int(t))
        if not np.allclose(list(val.values()),-np.asarray(list(neg.values())),
                           atol=1e-12,rtol=0):
            raise AssertionError("Side inversion changes feature unexpectedly")
        out.append({"match_id":int(match_id),"minute":int(t),**val})
    return out


def add_train_role_features(train:pd.DataFrame,cache:Path=CACHE)->tuple[pd.DataFrame,dict]:
    if len(train)!=10675 or train.match_id.nunique()!=291 or set(train.partition)!={"train"}:
        raise AssertionError("Not frozen original March TRAIN")
    manifest=[]
    vals=[]
    for match,part in train.groupby("match_id",sort=True):
        path=cache/(source_key(int(match))+".json.gz")
        data=path.read_bytes()
        manifest.append([int(match),hashlib.sha256(data).hexdigest()])
        raw=json.loads(gzip.decompress(data))
        if int(raw["duration"])!=int(part.duration.iloc[0]):
            raise AssertionError("TRAIN source duration mismatch")
        ts=sorted(part.minute.astype(int).tolist())
        if ts!=list(range(len(part))):
            raise AssertionError("TRAIN source minute grid unexpected")
        vals.extend(asof_role_rows(int(match),raw,ts))
    aggregate=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    want=json.loads(PROVENANCE.read_text())["source_payload_bytes_sha256"]
    if aggregate!=want:
        raise AssertionError("March raw source aggregate SHA mismatch")
    features=pd.DataFrame(vals)
    result=train.merge(features,on=["match_id","minute"],how="left",validate="one_to_one",sort=False)
    if len(result)!=len(train) or result[list(ALL6)].isna().any().any():
        raise AssertionError("TRAIN player source join missing or duplicated")
    return result,{"games":291,"minute_features":len(vals),
                   "source_aggregate_sha256":aggregate,
                   "all_features_side_mirror_tested":len(vals)}
