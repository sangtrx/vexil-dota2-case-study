# Private Kaggle QA kernels

These are research QA kernels, not the self-contained Vexil
submission notebook. Both are CPU-only, private, Internet OFF,
and use a private Kaggle dataset of only original 291 TRAIN
game cached OpenDota responses.

Dataset: sangtruong/vexil-redteam-train291-binary-20261113
Binary source archive file: qa_payload.bin
Archive SHA-256: 8d9c34c7a4547b6bc29587ffafb4ce34a939b7df90548328b92d5407760c3e8d

- vexil-binary-train-redteam-qa-20261113.ipynb:
  deterministic 12,063 train-only adversarial tests.
- vexil-binary-train-fullpit-qa-20261113.ipynb:
  every one of 10,683 train-minute prefix tests.

The first .tar.gz upload was auto-unpacked by Kaggle and
the corresponding kernels failed before performing any QA.
The fixed binary archive is preserved without automatic
unpacking. Both updated kernels verify SHA-256 and sources
before running. Do not count earlier errors as passes.

Hosted status and results must be checked against Kaggle's
actual COMPLETE status. No credentials are in these sources.
