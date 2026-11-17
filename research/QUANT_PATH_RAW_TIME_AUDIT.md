# OpenDota array time-axis audit: structural compatibility only

Read the exact existing 291 TRAIN raw payloads, requiring the previously committed aggregate payload SHA256. No outcomes, VAL, TEST or employer artifacts enter the audit.

- Raw games: 291; player streams: 2910.
- Arrays shorter than duration-derived minute grid: 0.
- Arrays longer than duration-derived minute grid: 84 (two matches each with two team and 40 per-player extra terminal slots).
- Mismatched match IDs or durations: 0.
- Team arrays exactly matching duration grid: gold=289/291; XP=289/291.

**Scientific status: INDETERMINATE for actual sample timestamps and feed arrival.** Duration matching cannot prove actual array index-to-minute alignment. Some arrays contain additional trailing sample slots and source does not supply trustworthy per-sample arrival timestamps. This audit neither detects an OpenDota leak nor certifies the live PIT model.

Motivation: a separate 2026 professional Dota dataset, Zenodo DOI 10.5281/zenodo.23166182, removed 1,849 different matches because per-minute arrays could be shifted or sampled irregularly. Do not copy that count to this sample.

Read-only QA; no original TEST, notebook, ZIP or report change.
