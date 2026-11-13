"""Re-run the same fixed adversarial families with a second random stream.

This is sensitivity of the QA cases, not an independent model experiment
or new professional-game outcome evidence. Does not overwrite seed-20261113.
"""
from __future__ import annotations
import json
import random
from pathlib import Path
import research.adversarial_cases as qa

def main(seed=20261114):
    assert seed!=20261113 and seed>0
    qa.SEED=seed
    qa.GEN=random.Random(seed)
    qa.CATEGORIES={}
    qa.NOTES={}
    qa.OUT=Path(__file__).resolve().parents[1]/'research/results'/f'adversarial_seed_{seed}'
    qa.main()
    receipt=json.loads((qa.OUT/'adversarial_qa_receipt.json').read_text())
    assert receipt['seed']==seed
    assert receipt['total_case_assertions']==12063
    assert receipt['real_http_calls']==0
    assert receipt['validation_103_labels_scored']==0
    assert receipt['heldout_106_labels_scored']==0
    print('SECOND_SEED_12063_CASES_PASS',json.dumps(receipt,sort_keys=True),flush=True)

if __name__=='__main__':main()
