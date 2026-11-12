"""Deterministic one-page methodological cards for ALL registered hypotheses."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from research.proposal_factory_registry import BASE, SPECS,SEED,PRACTICAL_IMPROVEMENT,BOOTSTRAP_REPS

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"research/proposals"
DEST.mkdir(parents=True,exist_ok=True)

def main():
    cards=[]
    for ident,family,name,features,mechanism,null,algorithm in SPECS:
        relative=Path("research/proposals")/(ident+"_"+family+".md")
        text=f"""# {ident}: {name}

**Status:** Registered for this finite, exploratory factory run.
Several individual signal ideas (gold velocity, relative wealth, Aegis,
buyback, structural mismatch) were already explored in earlier
research branches; this is NOT an independent first test of them.

**Scientific mechanism.** {mechanism}

**Falsifiable null.** {null}

**Feature definition.** New columns: {', '.join(features) if features else 'none; changed model shape only'}. Existing fixed M1 columns: {', '.join(BASE)}. The production data contract permits only OpenDota /proMatches and /matches/{{match_id}}, with per-minute array entries through t and dated events at seconds <=60t.

**Algorithm.** {algorithm}; see the frozen, shared experiment runner. No candidate-specific hyperparameter tuning, external data, hero stats from validation games, or answer-dependent feature selection.

**Controls.** (i) mandatory logistic gold-only M0; (ii) currently selected M1 gold×time. Any gain must be incremental over M1; comparisons to M0 alone do not count. Equal weights for minute forecasts, with equal-match sensitivity and chronological series-safe folds.

**Falsification and decision.** A candidate must improve the already-inspected 103 validation matches over M1 by >=0.005 absolute log loss, have a non-positive Brier difference, improve in at least 2/3 original-train-only forward folds, and have upper familywise 95% series-cluster interval <0 after simultaneous correction across all {len(SPECS)} candidates. This is only a DEVELOPMENT SCREEN, not confirmatory evidence. A new matched/series-disjoint chronologically later cohort is necessary to claim a reproducible edge. A failure means STOP, not tune phase cutoffs or cite a lucky p-value.

**Result policy.** Keep a numerical receipt for this proposal whether better or worse; never discard or selectively report negative candidates. Do not merge an unvalidated model into original Vexil submission.
"""
        (ROOT/relative).write_text(text)
        cards.append({"id":ident,"file":str(relative),"family":family,"model":algorithm,
                      "new_features":list(features),"null":null})
    registry=ROOT/"research/proposal_factory_registry.py"
    features=ROOT/"research/proposal_factory_features.py"
    manifest={
        "proposal_count":len(cards),
        "registration_status":"registered BEFORE scored development experiments",
        "original_train_games":291,
        "previously_inspected_validation_games":103,
        "consumed_test_games_reserved_as_not_new":106+200+200,
        "candidate_familywise_test_count":len(cards),
        "seed":SEED,"bootstrap_replicates":BOOTSTRAP_REPS,
        "minimum_required_logloss_gain":PRACTICAL_IMPROVEMENT,
        "registry_sha256":hashlib.sha256(registry.read_bytes()).hexdigest(),
        "feature_source_sha256":hashlib.sha256(features.read_bytes()).hexdigest(),
        "cards":cards
    }
    (ROOT/"research/proposal_registry_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("PRE-REGISTERED_PROPOSAL_CARDS",len(cards),manifest["registry_sha256"],
          "FEAT_SOURCE",manifest["feature_source_sha256"])

if __name__=="__main__":main()
