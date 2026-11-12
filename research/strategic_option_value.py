"""Registered two-timescale point-in-time event features for research only.

No model training, outcomes, final-state fields, API access or feature tuning.
Aegis is a *recent claim*, never an assertion that a hero still holds it.
"""
from __future__ import annotations
import copy
import math
from collections.abc import Mapping

FEATURES = ("aegis_claim5", "buyback_commitment5", "unconverted_gold_k")


def _clock(event):
    if not isinstance(event, Mapping):
        return None
    value = event.get("time")
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def _team_sign(slot):
    if type(slot) is not int:
        return None
    if 0 <= slot < 5:
        return 1
    if 128 <= slot < 133:
        return -1
    return None


def _gold_at(match, minute):
    values = match.get("radiant_gold_adv")
    if not isinstance(values, list):
        return float("nan")
    for i in range(min(minute, len(values)-1), -1, -1):
        x = values[i]
        if type(x) in (int,float) and math.isfinite(x):
            return float(x)
    return float("nan")


def _window(time_second, horizon_second):
    age = horizon_second - time_second
    return max(0., 1. - age/300.) if 0 <= age <= 300 else 0.


def option_snapshot(match, minute):
    """Only per-minute gold and timestamped objectives/buybacks through t.

    NaN signals absent optional payloads; do NOT fabricate a zero log.
    """
    if type(minute) is not int or minute < 0:
        raise ValueError("Nonnegative integer minute required")
    cutoff = 60 * minute
    objectives = match.get("objectives")
    players = match.get("players")
    aegis = float("nan")
    control = float("nan")
    buyback = float("nan")
    if isinstance(objectives, list):
        aegis = 0.
        structural = 0.
        unknown = False
        for event in objectives:
            if not isinstance(event, Mapping):
                unknown = True
                continue
            typ = event.get("type")
            if typ not in ("CHAT_MESSAGE_AEGIS", "building_kill"):
                continue
            ts = _clock(event)
            if ts is None:
                unknown = True
                continue
            if ts > cutoff:
                continue
            if typ == "CHAT_MESSAGE_AEGIS":
                sign = _team_sign(event.get("player_slot"))
                if sign is None:
                    unknown = True
                else:
                    aegis += sign * _window(ts, cutoff)
            else:
                key = str(event.get("key") or "").lower()
                sign = +1 if "badguys" in key else -1 if "goodguys" in key else 0
                if "tower" in key:
                    structural += sign
                elif "rax" in key or "barracks" in key:
                    structural += 2 * sign
        gold = _gold_at(match, minute)
        control = gold/1000. * float(gold * structural < 0) if math.isfinite(gold) else float("nan")
        if unknown:
            aegis = float("nan")
            control = float("nan")
    if isinstance(players, list) and len(players) == 10:
        signs = [_team_sign(p.get("player_slot")) if isinstance(p,dict) else None for p in players]
        slots = [p.get("player_slot") if isinstance(p,dict) else None for p in players]
        if all(s is not None for s in signs) and len(set(slots)) == 10 and all(
            isinstance(p.get("buyback_log"),list) for p in players
        ):
            buyback = 0.
            unknown = False
            for p,sign in zip(players,signs):
                for e in p["buyback_log"]:
                    ts = _clock(e)
                    if ts is None:
                        unknown = True
                    elif ts <= cutoff:
                        buyback += sign * _window(ts,cutoff)
            if unknown: buyback = float("nan")
    return {"aegis_claim5":aegis,
            "buyback_commitment5":buyback,
            "unconverted_gold_k":control}


def option_prefix_truncated(match, minute):
    """Red-team transform: remove *all* future arrays, event logs and labels."""
    if type(minute) is not int or minute < 0:
        raise ValueError("minute must be nonnegative integer")
    cutoff=60*minute
    game=copy.deepcopy(match)
    for key in ("radiant_gold_adv", "radiant_xp_adv"):
        if isinstance(game.get(key),list): game[key]=game[key][:minute+1]
    if isinstance(game.get("objectives"),list):
        game["objectives"]=[e for e in game["objectives"]
                           if _clock(e) is not None and _clock(e)<=cutoff]
    for player in game.get("players") or []:
        for field in ("gold_t", "xp_t", "lh_t", "times"):
            if isinstance(player.get(field),list): player[field]=player[field][:minute+1]
        for field in ("kills_log", "purchase_log", "buyback_log"):
            if isinstance(player.get(field),list):
                player[field]=[e for e in player[field]
                               if _clock(e) is not None and _clock(e)<=cutoff]
        for field in ("net_worth", "kills", "deaths", "assists", "level",
                      "total_gold", "gold_per_min", "xp_per_min"):
            player[field]=-9999999
    game["radiant_win"] = not bool(game.get("radiant_win"))
    game["duration"] = -9999999
    return game
