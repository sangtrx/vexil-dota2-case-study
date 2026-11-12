# Kaggle private QA — 4/4 hosted COMPLETE

**Verified on 13 November 2026.** Four independent Kaggle executions
reproduced the pre-existing, previously inspected Vexil development
predictions. All four have `KernelWorkerStatus.COMPLETE`, actual
Kaggle-generated output receipts, and numerical/source parity with
local. See [`hosted_run_verification_20261113.json`](hosted_run_verification_20261113.json)
and [`docs/QUANT_BIBLE_APPLIED_RESULTS.md`](../docs/QUANT_BIBLE_APPLIED_RESULTS.md).

The research is **NOT** new blind evidence or a live betting strategy.
It is deterministic cross-environment QA for a fixed negative-model-
selection archive. No candidate is promoted; original M1 remains.

## Runs

| Private kernel | Work performed |
|---|---|
| `vexil-bible-proper-scores-20261113` | All 29 models' loss/Brier, 145 phase/calibration rows |
| `vexil-bible-selection-instability-20261113` | 20 directional splits (10 complementary pairs), 3,000 grouped OOB selections |
| `vexil-bible-familywise-audit-20261113` | All 28 simultaneous max-t CI scores, 5,000 draws |
| `vexil-bible-chronology-audit-20261113` | Four approximately disjoint intervals, 4/5 six-bucket overlaps, 116 scores |

All four are private, CPU-only and Kaggle Internet OFF.
Dataset: `sangtruong/vexil-bible-development-qa-20261113` (private;
Kaggle API reported `ready`). The actual Kaggle mount is:

```text
/kaggle/input/datasets/sangtruong/vexil-bible-development-qa-20261113
```

Early kernel versions failed because they used the legacy abbreviated
mount path. The corrected versions were repushed and all passed.

## Credential management: use the existing 25-slot pool

Do **not** run `kaggle auth login` and do **not** copy/paste an API key.
The authorized BigLinux `ai-agent` has existing access to:

```text
/srv/ai/repos/woodsbot-system/.local/kaggle/credentials.json
/srv/ai/repos/woodsbot-system/scripts/kaggle_research_loop.py
```

The checked `kaggle_01` account is `sangtruong`; the credential
pool file is mode `0600`. `pool_gateway.py` calls the pool's existing
credential loader and passes the selected key only as a subprocess
environment variable. Neither source control nor Kaggle input contains
secrets. GitHub author `sangtrx` is a separate account.

To re-check **without re-running** any Kaggle kernel:

```bash
sudo -u ai-agent -H /home/ai-agent/projects/vexil-dota2-win-probability/.venv/bin/python \
  /home/ai-agent/projects/vexil-dota2-bible-audit/kaggle/pool_gateway.py --action verify
```

This checks all four statuses, downloads cloud outputs again and checks
input/source hashes and numerical parity. The hosted JSON and CSV
outputs are also committed in `research/bible/results/hosted_kaggle_20261113/`.

**Repush only when intentionally creating a new version:**

```bash
sudo -u ai-agent -H /home/ai-agent/projects/vexil-dota2-win-probability/.venv/bin/python \
  /home/ai-agent/projects/vexil-dota2-bible-audit/kaggle/pool_gateway.py --action push
```

The private dataset already exists. Do not create it again or use
`--public`. `prepare_private_runs.py` preserves the uploaded manifest
SHA-256 and refuses changed dataset files without explicit versioning.
An already verified run retains its status on re-preparation only if
all four notebook hashes, code and dataset source hashes are unchanged.

## Source lineage and limitations

- Private dataset manifest SHA-256: `c9155ee8820fac43f4432ac1f1362226c6c16af7868080b105bd45b30767dc8b`.
- Frozen prediction CSV SHA-256: `aebc0cccce1b4c7ed7591bafa3dd2cd52fc1f8de50aa7c79fcba5b2faf3532d4`.
- Cloud NumPy 2.1.3; local NumPy 2.2.6; pandas 2.3.3 in both environments.
- Four receipts and five output CSVs pass checks, with max numerical difference within `1e-11` tolerance.
- No independent later-match cohort, executable betting prices, or market PnL was tested.
- The original Vexil take-home notebook and report in Draft PR #3 remain untouched.
