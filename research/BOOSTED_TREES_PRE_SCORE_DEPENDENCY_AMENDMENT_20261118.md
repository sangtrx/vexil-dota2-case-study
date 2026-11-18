# Dependency pin amendment PRIOR to any boosted fit/score (18 Nov ICT)

The original prior-to-model benchmark protocol at commit 6ff70a493a85614e94e0dada3ea1285deb208ce9 fixed xgboost==3.4.2 and lightgbm==4.7.0. BigLinux epic pinned Python 3.12.3 pip index **does not provide xgboost 3.4.2** (pip reported max xgboost==3.4.1), so the first installation failed with exit 1. The isolated target directory did not exist afterward; **NO boosted-model fit/score had occurred**. Verify this history; never claim the first pin was used.

The explicit single practical correction is to set **xgboost==3.4.1** and keep **lightgbm==4.7.0**. The 4 candidate model families, parameter sets, March TRAIN source, immutable fold cuts, labels maturity rules, comparators, per-minute primary metric, 5000 grouped bootstrap, 99.375% screen-local intervals, and research-only status are EXACTLY unchanged. Future runs MUST match these revised version pins; do not optimize/tune anything after seeing results.

This is a transparent reproducibility/environment amendment, **not** a new prospective pre-registration or an independent holdout. This amendment is committed before any model fit or evaluation. Original applicant notebook/PDF/ZIP/pinned dependencies remain unchanged.
