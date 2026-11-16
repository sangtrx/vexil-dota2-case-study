# Fresh-kernel, no-network 500-match notebook parity check

Design frozen on 15 November 2026 before this author-controlled full-replay QA.

**Goal:** The candidate repository carries a self-contained, executed
500-game OpenDota notebook; 70+ unit tests alone cannot certify that
the current notebook runs from top to bottom. Re-execute ALL 14 code
cells in a fresh Python kernel and disposable working directory, using
only previously captured /matches JSON payloads corresponding to the
500 *frozen* match IDs. No model or cohort reselection.

**Source rules:** The raw JSON cache exists externally on the author's
BigLinux machine, is **not** bundled or sent. Copy only 500 matches
with exact SHA-256 keys used by notebook OpenDota class. Verify
every cached payload matches requested ID and minimum parsed
eligibility; fail closed on missing, malformed or mismatched raw data,
never query OpenDota or silently fall back. Verify frozen manifest
ID/time/patch identity inside the notebook and required 250/250 patch
composition. Input payloads can be reparsed over time; compare
source-lineage fingerprint against the saved 15 Nov Colab provenance.

**Execution:** Original notebook code & cells unchanged. Run its
unchanged source with nbclient/Jupyter in a new disposable kernel from the repository's pinned Python scientific environment. Kernel
launcher is resolved against the controller interpreter, to prevent
accidental global-Python substitution. 500 cached match hits and
zero successful OpenDota HTTP responses are checked; dead proxy
environment blocks normal requests, but this is **NOT OS-level network
isolation or a general proof of zero outbound network traffic**.
The executed notebook must have **14/14** code cells completed with
no errors. Produce its own artifacts in the disposable working
directory. No TEST labels are used for model fitting or selection.

**Reproduction gates:** Exact 500/291/103/106 match counts,
18,292/10,675/3,781/3,836 forecast-row counts derived from
source match durations and the frozen split manifest, M1 selected on
validation, original 3,836 row TEST predictions in exact original
order and SHA-256, same original notebook scientific source SHA,
all thirteen expected notebook CSV/PNG/JSON outputs, and matching canonical
source model-input, outcome-label and metadata fingerprints from
the cold Colab receipt. Recompute all four validation model log
loss/Brier scores and original overall held-out scores within 1e-9
of the frozen expected values, and no temporary raw files in the recruiter ZIP.

**Performance boundary:** This is an author-controlled no-network
replay from *previously cached* raw OpenDota payloads. It is a
reproducibility/lineage test, **NOT** fresh future-event validation,
new independent data or a cold API test. The separate Colab 15 Nov
fresh API receipt remains the only observed zero-cache cloud run,
with cloud-export CSV byte comparison explicitly unavailable.

**Governance:** Do not change original model, science code, 500
match IDs or TEST predictions to make this check pass. If it fails,
document the failure; fix only a real execution bug on a new branch
without selecting a better model on TEST. No hosted CI, no
recruiter email, no GitHub access grant, no merge or release.
