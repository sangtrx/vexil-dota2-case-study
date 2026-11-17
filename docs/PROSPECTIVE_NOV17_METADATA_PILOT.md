# Metadata-only window feasibility checkpoint (17 Nov 2026)

This is **not** a model evaluation. The initially committed protocol
`40f36f9` fixed a start-time window
`[2026-11-16T00:00Z,2026-11-17T09:00Z)`.
The first OpenDota `/proMatches` discovery returned 2 pages/200 rows
containing only **16** IDs in that window (listing SHA256
`cb1bf12006e32c7f567a77b0b60b96faca81db00c3bb2179e6c8ddb5b17c18d8`).
This count is **before** the strict parse/clock eligibility check.

**No /matches/{id} detail calls, winner inspection for selection, model
predictions or outcome scores occurred under this initial cohort.**
Raw `/proMatches` pages can contain `radiant_win` even when selection code
does not access that field; this is therefore metadata-guided sample size
planning, *not* a human-blinded experiment. The original 16-game listing
and two raw page hashes are retained without retroactively rewriting the
protocol.

Because 16 listed games is far below the predeclared 50-game/30-cluster
minimum for even provisional inference, a separate explicitly dated
**pre-outcome protocol amendment** may broaden the population and record
the changed estimand. It must be committed before any match detail
download or model scoring. Do not mix the original tiny-window cohort
with an amended one and pretend the original rules were met.
