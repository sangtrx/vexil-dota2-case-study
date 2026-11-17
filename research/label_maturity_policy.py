"""As-of outcome eligibility, independent of model and historic TEST data.

For real-time claims require a verified outcome received-at timestamp.
A game-end proxy is permitted only in explicitly retrospective audits.
This function cannot establish the arrival of in-game feature events.
"""
from __future__ import annotations

from numbers import Integral


def outcome_known_by(
    *, start_time: int, duration: int, fit_time: int,
    received_at: int | None = None,
    require_received_at: bool = True,
    availability_lag_seconds: int = 0,
) -> bool:
    """Whether a final match label could have been known by fit_time.

    The conservative availability time is max(game_end, received_at) plus
    any declared ingest/verification lag. Never substitute an unobserved
    received-at time for a production claim. Explicit
    require_received_at=False uses a historical end-time proxy ONLY.
    """
    times = (start_time, duration, fit_time, availability_lag_seconds)
    if any(isinstance(x, bool) or not isinstance(x, Integral) for x in times):
        raise TypeError("All time fields must be integer Unix seconds")
    if start_time < 0 or fit_time < 0 or duration <= 0 or availability_lag_seconds < 0:
        raise ValueError("Invalid time, match duration or availability lag")
    if received_at is None:
        if require_received_at:
            raise ValueError("received_at required for live as-of eligibility")
        availability = start_time + duration
    else:
        if isinstance(received_at, bool) or not isinstance(received_at, Integral):
            raise TypeError("received_at must be an integer Unix timestamp")
        if received_at < start_time:
            raise ValueError("Outcome cannot arrive before match start")
        availability = max(start_time + duration, received_at)
    return availability + availability_lag_seconds <= fit_time
