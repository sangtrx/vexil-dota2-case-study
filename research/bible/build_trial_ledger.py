#!/usr/bin/env python3
"""Inventory of known Vexil experiments from prior branches.

This is not an estimate of independent trials and cannot capture unlogged
manual/source-selection choices. All 38 entries are KNOWN evaluation
attempts; repeated families across cohorts count as separate exposures.
"""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research/bible/results"
repo="https://github.com/sangtrx/vexil-dota2-win-probability"

def make_rows():
    rows=[]
    def add(identifier,family,source,cohort,status,note):
        rows.append({
            "trial_id":identifier,"family":family,"source":source,
            "cohort":cohort,"status":status,"note":note
        })
    for name in ("M0_gold_only","M1_time_value","M2_momentum_xp","M3_objective_conversion"):
        add(name,"initial_models",repo+"/pull/3",
            "original_291_train_103_validation",
            "M1_selected_on_development_only" if name=="M1_time_value" else "not_selected",
            "Four original fixed candidates; M0 as null, M1 as proposed model")
    for name in ("S1_relative_economy","S2_top_two_allocation","S3_gold_persistence_shocks","S4_combined"):
        add(name,"structural_exploration",repo+"/pull/4",
            "original_train_only_folds_plus_103_validation","screen_failed",
            "Mechanistic structural features, no robust incremental gain")
    add("M4_option_value","event_option_state",repo+"/pull/5",
        "original_291_train_103_validation","screen_failed",
        "Aegis pickup proxy, recent buyback, structural mismatch, 0.520596 > M1")
    add("G1_fixed_stage_gate","temporal_gate",repo+"/pull/4",
        "third_independent_200_after_first_forward_200","confirmatory_HOLD",
        "Frozen gate failed prespecified gain and confidence criterion")
    src=ROOT/"research/proposal_factory_registry.py"
    txt=src.read_text()
    import ast
    mod=ast.parse(txt)
    assignment=next(node for node in mod.body if isinstance(node,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=="SPECS" for t in node.targets))
    specs=ast.literal_eval(assignment.value)
    assert len(specs)==28
    for ident,family,title,extras,mechanism,null,alg in specs:
        add(ident,family,repo+"/pull/6",
            "original_291_train_103_previously_examined_validation",
            "screen_failed","Fixed factory candidate; one 28-way family correction, not global trial-count")
    assert len(rows)==38 and len({r["trial_id"] for r in rows})==38
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=make_rows()
    with (OUT/"known_trial_ledger.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    summary={
        "documented_trial_evaluation_records":len(rows),
        "independent_trials_estimated":None,
        "unknown_unrecorded_trials":True,
        "not_a_closed_search_family":True,
        "disclaimer":"Includes overlapping/repeated families and reused validation. Not an estimate of N_eff; does not certify all historical attempts.",
        "sources":[r["source"] for r in rows if r["trial_id"] in
                   ["M1_time_value","S2_top_two_allocation","M4_option_value","G1_fixed_stage_gate","P20"]],
    }
    (OUT/"trial_ledger_receipt.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("KNOWN_TRIAL_LEDGER",json.dumps(summary,sort_keys=True))

if __name__=="__main__":main()
