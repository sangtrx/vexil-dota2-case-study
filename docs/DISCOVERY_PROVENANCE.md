# Discovery provenance: how the 500-game cohort was selected

**Reviewer question:** Why does a fresh notebook `Run all` call `/matches/{match_id}` for a fixed list rather than page a changing `/proMatches` feed? **Answer:** `/proMatches` was the *discovery* source on 13 November 2026; the selected IDs were then frozen in Git before the original held-out comparison. Fresh runs fetch the same 500 games, so results are not confounded by newly appearing pro matches.

## Historical procedure and source evidence

| Step | Evidence and reproducibility boundary |
| --- | --- |
| Preflight | The original 13 Nov research log recorded a **30-page** `/proMatches` scan; the sampled pages were still patch 60. A recent-500 shortcut would not have covered the desired transition. This is a recorded observation, **not** a saved raw-page archive. |
| Discover patch change | `collect_matches(api, frozen=())` in the original notebook paginates `/proMatches?less_than_match_id=<cursor>`, checks monotone cursor progress, probes at most **3** candidate `/matches/{id}` payloads per page for parsed patch IDs, and stops at the first observed transition (recorded around **page 93**, patch **59 -> 60**). `MAX_PRO_PAGES=110` is a bounded failure limit, not 110 pages actually consumed. |
| Select without outcomes | The source chooses the closest **250 usable games on each side** of that boundary, requiring a parsed gold series and duration >=600 seconds. No winner or model score is used in the eligibility/selection predicate. The original 13 Nov log recorded **705 API calls**, **49 cache hits** and **46 excluded candidates** (45 wrong-patch; 1 unparsed/short). These counts describe that recorded discovery, **not** the current rerun. |
| Freeze | Original commit [`3258a762`](https://github.com/sangtrx/vexil-dota2-case-study/commit/3258a762a5e31cbca131389a1a4b28389099130a) from **13 Nov 2026, 01:41 ICT** embedded the ordered 500 `FROZEN_MATCH_IDS` into the notebook. Their original `SHA256(json.dumps(list(ids)))` is **`f2be53e16ae29df1f62aa9907187fdba846d9af9fb7a3f69e7dd7504be43b776`**. This digest is reproduced from both the archived original scientific notebook and the current reviewer notebook. |
| Reuse exactly that cohort | `collect_matches(api, FROZEN_MATCH_IDS)` fetches `/matches/{id}` for every frozen ID, fails on wrong IDs/unusable records/patch imbalance and checks the canonical match-ID/start-time/patch SHA **`e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea`**. **500 distinct games**: patch 59 (250) and patch 60 (250), played **21–26 March 2026**. A fresh 16-cell Google Colab CPU Run All (19 Nov) used **508 API calls**, **0 cache hits**, loaded the same 500 games and reproduced the TEST-row count and rounded headline scores; see [current-source cloud receipt](COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json). An older 16 Nov receipt is preserved only in the private research repository. |

**What can be inspected with ZIP access alone:** the included notebook contains the frozen 500 IDs and the discovery/replay functions (`frozen=()` and `frozen=FROZEN_MATCH_IDS`), with source checksums. The historical original commit, mirrored `history/actual-*` branches, 14-cell scientific source and old decision log are in the private Git repository and **not contained in this ZIP**. Those private materials support the original discovery chronology; the raw source pages were not archived.

## What the evidence does *not* prove

- The 13 Nov original raw `/proMatches` response pages and network-level request timestamps **are not bundled**. Page-93 location, API-call/exclusion counts, and outcome-blind chronology are traceable to historical source and author records, not independently notarized request logs.
- The patch-balanced, parsed-match sample is **purposive**, not randomly representative of current professional Dota 2, all leagues, or an unseen later patch. TRAIN includes some patch-60 games; VALIDATION and TEST are both patch 60.
- Frozen IDs prevent changes in *which games* are scored; OpenDota may **reparse payloads** for the same game. The notebook hashes source manifest/content and fails closed on identity drift. A source hash or successful Colab rerun is **not** proof of live event receipt times, an untouched second TEST or cloud-export CSV byte equality.
- The 12 exact-end-row corrections were made **after the original TEST was inspected**. They are not reframed as a new blind sample.

**Why this design:** step 1 of the brief required a patch-spanning `/proMatches` collection. That discovery was recorded in the original research sequence. The later fixed-ID default protects the *same* cohort's reproducibility for a recruiter clicking `Run all`, without silently changing the evaluation population.
