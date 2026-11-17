# Other proposed feature inputs: eligibility, not leaderboard scores

Examined exact SHA-matched 291 TRAIN cached OpenDota payloads. Never recorded message texts, players' names or IDs in this receipt.

- Chat events 12704, in 291 games. Types: {'chat': 2648, 'chatwheel': 10056}.
- Pregame chat events: 2166; post-duration chat events: 417.
- Hero ability-upgrade entries: 50783; entries bearing exact timestamps: 0.

**Decision:** Do not treat terminal hero upgrade arrays as a time-known level-up feature. Live chat availability also cannot be inferred from post-replay parse timestamps, and postgame/near-terminal announcements can give misleading outcome signals. These two source families are BLOCKED for honest live claims. They are **not** reported as experimentally underperforming models.

The separately scored BKB/Blink candidate is purchase-log first-event proxy only; it does not solve hero upgrade or live receipt provenance.
