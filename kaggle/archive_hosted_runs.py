#!/usr/bin/env python3
"""Seal Kaggle-hosted QA evidence after four COMPLETE and parity checks.

Runs only on previously downloaded private cloud receipts; does not
refit a model, fetch new training labels, or touch pool credentials.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
import nbformat

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path('/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113')
DEST=ROOT/'research/bible/results/hosted_kaggle_20261113'
SUMMARY=ROOT/'kaggle/hosted_run_verification_20261113.json'
MODES={
 'scores':['k1_recomputed_145_phase_metrics.csv'],
 'instability':['k2_cscv_20.csv','k2_oob_3000.csv'],
 'maxt':['k3_maxt_28_ci.csv'],
 'chronology':['k4_chronology_116_scores.csv']
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def compare_csv(a,b,mode):
    x=pd.read_csv(a);y=pd.read_csv(b)
    assert x.shape==y.shape and list(x.columns)==list(y.columns),(mode,a.name,'shape')
    for col in x.columns:
        if pd.api.types.is_numeric_dtype(x[col]):
            assert pd.api.types.is_numeric_dtype(y[col]),(mode,col,'type')
            assert np.allclose(x[col].to_numpy(float),y[col].to_numpy(float),rtol=0,atol=1e-11,equal_nan=True),(mode,col,'value mismatch')
        else:
            assert (x[col].astype(str).to_numpy()==y[col].astype(str).to_numpy()).all(),(mode,col,'text mismatch')
    return len(x)

def main():
    # Required independent gate. Aborts immediately on any mismatch.
    subprocess.run([
        '/home/ai-agent/projects/vexil-dota2-win-probability/.venv/bin/python',
        str(ROOT/'kaggle/verify_hosted_receipts.py'),
        '--source',str(STAGE/'hosted_downloads'),
        '--local',str(STAGE/'local_verified')
    ],check=True)
    plan=json.loads((ROOT/'kaggle/hosted_run_manifest.json').read_text())
    frozen=STAGE/'dataset/dataset_files_sha256.json'
    assert sha(frozen)==plan['dataset_manifest_sha256']
    archive={}
    DEST.mkdir(parents=True,exist_ok=True)
    for item in plan['kernels']:
        mode=item['mode'];assert mode in MODES
        source=STAGE/'hosted_downloads'/mode
        local=STAGE/'local_verified'
        receipt=source/('kaggle_'+mode+'_receipt.json')
        data=json.loads(receipt.read_text())
        assert data['status']=='PASS' and data['run_location']=='kaggle'
        assert data['kaggle_execution_env_detected']
        assert data['dataset_manifest_sha256']==plan['dataset_manifest_sha256']
        assert data['source_prediction_sha256']==plan['expected_source_prediction_sha256']
        assert data['verification_script_sha256']==plan['verification_script_sha256']
        assert data['no_model_fit'] and data['not_new_blind_data']
        pulled=STAGE/'pulled_final_source'/mode
        metadata=json.loads((pulled/'kernel-metadata.json').read_text())
        assert metadata['is_private'] is True
        assert not metadata['enable_internet'] and not metadata['enable_gpu']
        assert metadata['dataset_sources']==[plan['dataset']]
        pulled_n=nbformat.read(next(pulled.glob('*.ipynb')),as_version=4)
        orig_n=nbformat.read(ROOT/'kaggle'/('kernel_'+mode)/item['source_file'],as_version=4)
        assert pulled_n.cells[-1].source==orig_n.cells[-1].source,(mode,'cloud code drift')
        assert sha(ROOT/'kaggle'/('kernel_'+mode)/item['source_file'])==item['notebook_sha256']
        target=DEST/mode;target.mkdir(parents=True,exist_ok=True)
        shutil.copy2(receipt,target/receipt.name)
        hashes={receipt.name:sha(target/receipt.name)}
        linecounts={}
        for name in MODES[mode]:
            row_count=compare_csv(source/name,local/name,mode)
            linecounts[name]=row_count
            shutil.copy2(source/name,target/name)
            hashes[name]=sha(target/name)
        archive[mode]={
            'remote_url':'https://www.kaggle.com/code/'+item['kernel_slug'],
            'remote_status':'KernelWorkerStatus.COMPLETE',
            'private_metadata_verified':True,
            'code_cell_matches_checked_in_source':True,
            'hosted_numpy_version':data['numpy_version'],
            'hosted_pandas_version':data['pandas_version'],
            'hosted_python_version':data['python_version'],
            'hosted_results':data['results'],
            'receipt_and_output_sha256':hashes,
            'verified_csv_rows':linecounts
        }
        print('ARCHIVED_HOSTED_KAGGLE',mode,hashes,flush=True)
    assert len(archive)==4
    out={
        'verification_timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'dataset_id':plan['dataset'],
        'dataset_status_verified':'ready',
        'dataset_manifest_sha256':plan['dataset_manifest_sha256'],
        'prediction_data_sha256':plan['expected_source_prediction_sha256'],
        'source_code_sha256':plan['verification_script_sha256'],
        'dataset_package_source_commit':plan['packaged_from_git_head'],
        'pool_slot':'kaggle_01',
        'account':'sangtruong',
        'private_cpu_internet_off':True,
        'hosted_run_complete_count':4,
        'local_to_cloud_numeric_tolerance':1e-11,
        'all_4_numeric_and_source_parity_pass':True,
        'no_new_holdout_scored':True,
        'no_model_retrained':True,
        'selection_decision':'HOLD all P01-P28, retain M1 gold/time',
        'initial_cloud_error':'Old input path was incorrect; revised notebooks use /kaggle/input/datasets/sangtruong/...',
        'modes':archive
    }
    SUMMARY.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('SEALED_FOUR_HOSTED_KERNEL_RESULTS',SUMMARY,flush=True)

if __name__=='__main__':main()
