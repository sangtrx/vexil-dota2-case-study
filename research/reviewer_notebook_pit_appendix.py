# APPEND-ONLY reviewer QA, written AFTER the frozen original TEST was opened.
# This cell audits point-in-time features; it does not change data, model,
# selection, probabilities or any original held-out result.
def reviewer_feature_prefix(match, minute):
    """Only fields actually used by snapshot_features, clipped to cutoff."""
    seconds = 60 * minute
    def safe_events(events):
        if not isinstance(events, list):
            return events
        return [e for e in events if isinstance(e, dict)
                and type(e.get("time")) in (int, float)
                and math.isfinite(e["time"]) and e["time"] <= seconds]
    return {
        "radiant_gold_adv": (match["radiant_gold_adv"][:minute+1]
                             if isinstance(match.get("radiant_gold_adv"), list)
                             else match.get("radiant_gold_adv")),
        "radiant_xp_adv": (match["radiant_xp_adv"][:minute+1]
                           if isinstance(match.get("radiant_xp_adv"), list)
                           else match.get("radiant_xp_adv")),
        "objectives": safe_events(match.get("objectives")),
        "players": [
            {"player_slot": player.get("player_slot"),
             "kills_log": safe_events(player.get("kills_log"))}
            for player in match.get("players", [])
        ],
        "radiant_win": not bool(match.get("radiant_win")),
        "duration": -999999,
    }

reviewer_pit_count = {"train": 0, "validation": 0, "test": 0}
reviewer_pre_full_window = 0
reviewer_split_lookup = dict(zip(manifest.match_id.astype(int),
                                 manifest.partition.astype(str)))
for reviewer_game in matches:
    mid = int(reviewer_game["match_id"])
    original_partition = reviewer_split_lookup[mid]
    # Original notebook already verified all player-clock axes against team
    # economy; verify EVERY admissible minute against deliberately poisoned
    # terminal outcome and future economy/objective/kill information.
    for minute in range((int(reviewer_game["duration"]) - 1)//60 + 1):
        current = snapshot_features(reviewer_game, minute)
        truncated = snapshot_features(reviewer_feature_prefix(reviewer_game, minute), minute)
        assert_same_features(current, truncated)
        reviewer_pit_count[original_partition] += 1
        reviewer_pre_full_window += int(minute < 5)
assert reviewer_pit_count == {
    "train": 10675, "validation": 3781, "test": 3836}
assert sum(reviewer_pit_count.values()) == 18292
assert reviewer_pre_full_window == 2500
print("REVIEWER FULL PIT: 18,292/18,292 forecast snapshots PASS "
      "(TRAIN 10,675, VAL 3,781, TEST 3,836).")
print("Feature-timing qualification: 2,500 first-five-minute rows "
      "use 0–4 minutes of history rather than a full five-minute window. "
      "Retrospective event timestamps cannot establish live received-at.")
