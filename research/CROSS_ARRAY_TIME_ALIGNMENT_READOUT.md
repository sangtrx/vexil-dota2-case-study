# Cross-array time-axis check on the original 291 TRAIN matches

- Player minute vectors: **2910** checked, all exactly [0,60,120,...] by index.
- Historical game snapshots: **10685**.
- Team gold and XP advantages equal their respective five-player Radiant-minus-Dire sums at all 10685 raw sampled indices, with zero mismatches.
- Raw slots at or beyond stated terminal duration: 10; original TRAIN 10,675 decision rows were already filtered before termination.

**Scope limit:** Same OpenDota replay parser can generate both player times and gold arrays. Thus exact agreement is a strong internal invariance and catches a shifted one-array index or inconsistent team sum, but is not an independent proof that each raw time was actually observed and delivered at exactly that minute. Received-at is still unavailable. Do not extrapolate to a different Zenodo cohort's excluded matches.

No model fitting, TEST/VAL outcomes, applicant submission or raw mutation.
