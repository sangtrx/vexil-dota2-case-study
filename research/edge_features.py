#!/usr/bin/env python3
"""Pure PIT feature functions for a finite Dota 2 research family.

Never imports labels, final player state, match duration or endpoints.
The event clock is defined by the source notebook, while these additions
use only gold-advantage and ten per-player cumulative gold_t histories
at or before minute t.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


STRUCTURAL_COLUMNS = (
    "econ_share_gap",
    "top2_share_gap",
    "core_gold_gap_share",
    "relative_shock5",
    "signed_lead_persistence10",
)
BASE_M1 = ("gold_k", "minute10", "gold_x_time")
SPECS = {
    "M1_time_value": BASE_M1,
    "S1_econ_leverage": BASE_M1 + ("econ_share_gap",),
    "S2_core_allocation": BASE_M1 + ("top2_share_gap", "core_gold_gap_share"),
    "S3_lead_fragility": BASE_M1 + ("relative_shock5", "signed_lead_persistence10"),
    "S4_joint_state": BASE_M1 + (
        "econ_share_gap", "top2_share_gap", "relative_shock5"
    ),
}


def _finite_at(series, t):
    if not isinstance(series, list) or len(series) <= t:
        return None
    x = series[t]
    return float(x) if isinstance(x, (float, int)) and math.isfinite(x) else None


def _sided_player_gold(match: Mapping, t: int):
    """Return two 5-player gold histories strictly as of t or None."""
    players = match.get("players")
    if not isinstance(players, list) or len(players) != 10:
        return None
    radiant, dire, slots = [], [], set()
    for player in players:
        if not isinstance(player, dict):
            return None
        slot = player.get("player_slot")
        if not isinstance(slot, int) or slot in slots or slot < 0:
            return None
        slots.add(slot)
        value = _finite_at(player.get("gold_t"), t)
        if value is None or value < 0:
            return None
        if slot < 128:
            radiant.append(value)
        else:
            dire.append(value)
    if len(radiant) != 5 or len(dire) != 5:
        return None
    return radiant, dire


def _past_gold_at(match, t):
    """No missing future fill: only past observed finite points."""
    gold = match.get("radiant_gold_adv")
    if not isinstance(gold, list) or not gold:
        return float("nan")
    for i in range(min(t, len(gold)-1), -1, -1):
        v=gold[i]
        if isinstance(v, (int,float)) and math.isfinite(v):
            return float(v)
    return float("nan")


def structural_snapshot(match: Mapping, t: int) -> dict[str, float]:
    """Feature values as of minute t, no result or duration inputs."""
    if not isinstance(t,int) or t<0:
        raise ValueError("minute t must be a nonnegative integer")
    nan=float("nan")
    out={key:nan for key in STRUCTURAL_COLUMNS}
    gold=_past_gold_at(match,t)
    if not math.isfinite(gold):
        return out
    sided=_sided_player_gold(match,t)
    if sided is not None:
        r,d=sided
        rsum,dsum=sum(r),sum(d)
        out["econ_share_gap"]=100. * (rsum-dsum)/(rsum+dsum+1000.)
        if rsum>0 and dsum>0:
            top_r=sum(sorted(r,reverse=True)[:2])
            top_d=sum(sorted(d,reverse=True)[:2])
            out["top2_share_gap"]=top_r/rsum - top_d/dsum
            out["core_gold_gap_share"]=(top_r-top_d)/(rsum+dsum+1000.)
    old=_past_gold_at(match,max(0,t-5))
    if math.isfinite(old):
        out["relative_shock5"]=(gold-old)/(abs(gold)+3000.)
    past=[]
    for minute in range(max(0,t-9),t+1):
        observed=_past_gold_at(match,minute)
        if math.isfinite(observed):
            past.append(float(np.sign(observed)))
    if past:
        out["signed_lead_persistence10"]=float(np.mean(past))
    return out


def structural_rows(games: list[dict], baseline_snapshot):
    """Create match-minute table without using a future label as a feature."""
    rows=[]
    for game in games:
        game_id=int(game["match_id"])
        for minute in range(int(game["duration"])//60+1):
            a=baseline_snapshot(game,minute)
            b=structural_snapshot(game,minute)
            rows.append(dict(match_id=game_id,minute=minute,
                             radiant_win=int(game["radiant_win"]),**a,**b))
    out=pd.DataFrame.from_records(rows)
    assert out[["match_id","minute"]].duplicated().sum()==0
    return out
