#!/usr/bin/env python3
"""Authorized Kaggle pool launcher and hosted-result verifier.

Uses the existing ai-agent-owned 25-slot pool via its established loader.
No credential bytes are printed, copied, written or committed by this code.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POOL=Path('/srv/ai/repos/woodsbot-system/.local/kaggle/credentials.json')
LOADER=Path('/srv/ai/repos/woodsbot-system/scripts/kaggle_research_loop.py')
STAGE=Path('/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113')
ACCOUNT='sangtruong'
SLOT='kaggle_01'
DATASET=ACCOUNT+'/vexil-bible-development-qa-20261113'


def authorized():
    # Pool loader's Kaggle subprocess must find the account-local CLI;
    # do not require an interactive OAuth login or any copied key file.
    os.environ['PATH']='/home/ai-agent/.local/bin'+os.pathsep+os.environ.get('PATH','')
    assert LOADER.is_file() and POOL.is_file(), 'Existing approved pool missing'
    spec=importlib.util.spec_from_file_location('kaggle_pool_loader',LOADER)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    slots=mod.load_credential_slots(argparse.Namespace(credentials_json=str(POOL),credentials_csv=None))
    slot=mod.select_slot(slots,SLOT)
    assert slot.get('username')==ACCOUNT, 'Pool ownership changed; refuse wrong-account upload'
    env=mod.kaggle_env(slot)
    return mod,env


def manifest():
    p=ROOT/'kaggle/hosted_run_manifest.json'
    m=json.loads(p.read_text())
    assert len(m['kernels'])==4 and m['private']
    assert m['dataset']==DATASET and not m['enable_gpu'] and not m['enable_internet']
    return m


def kaggle(mod,env,args,timeout=60):
    result=mod.run_kaggle(args,env,timeout=timeout)
    if result.returncode!=0:
        err=(result.stderr or result.stdout or '').strip()
        raise RuntimeError(f'Kaggle command {args[:2]!r} failed ({result.returncode}): {err[:550]}')
    return (result.stdout or result.stderr or '').strip()


def status(mod,env,record):
    response=kaggle(mod,env,['kernels','status',record['kernel_slug']],timeout=28)
    return response


def push(mod,env,m):
    check=kaggle(mod,env,['datasets','status',DATASET])
    assert check.lower().strip()=='ready', f'Private Kaggle dataset not ready: {check}'
    import hashlib
    for record in m['kernels']:
        folder=ROOT/'kaggle'/('kernel_'+record['mode'])
        meta=json.loads((folder/'kernel-metadata.json').read_text())
        assert meta['id']==record['kernel_slug']
        assert meta['dataset_sources']==[DATASET]
        assert str(meta['is_private']).lower()=='true'
        assert str(meta['enable_internet']).lower()=='false'
        assert str(meta['enable_gpu']).lower()=='false'
        notebook=folder/record['source_file']
        assert hashlib.sha256(notebook.read_bytes()).hexdigest()==record['notebook_sha256']
        print('PRIVATE_POOL_KERNEL_PUSH',record['mode'],flush=True)
        response=kaggle(mod,env,['kernels','push','-p',str(folder)],timeout=100)
        print('PUSH_OK',record['mode'],response[-400:],flush=True)


def verify(mod,env,m):
    for record in m['kernels']:
        response=status(mod,env,record)
        print('HOSTED_STATUS',record['mode'],response,flush=True)
        assert 'KernelWorkerStatus.COMPLETE' in response, 'Kernel not COMPLETE; no numerical-parity claim'
    for record in m['kernels']:
        folder=STAGE/'hosted_downloads'/record['mode']
        folder.mkdir(parents=True,exist_ok=True)
        response=kaggle(mod,env,['kernels','output',record['kernel_slug'],'-p',str(folder)],timeout=110)
        receipt=folder/('kaggle_'+record['mode']+'_receipt.json')
        assert receipt.is_file(),f'Missing actual hosted numeric receipt: {receipt} ({response[-350:]})'
        print('DOWNLOADED_HOSTED_RECEIPT',record['mode'],receipt.stat().st_size,flush=True)
    runner=ROOT/'kaggle/verify_hosted_receipts.py'
    subprocess.run([sys.executable,str(runner),'--source',str(STAGE/'hosted_downloads'),
                    '--local',str(STAGE/'local_verified')],check=True)
    print('FOUR_PRIVATE_POOL_KERNELS_VERIFIED_NUMERICALLY',flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--action',required=True,choices=('push','status','verify'))
    args=p.parse_args()
    m=manifest()
    module,env=authorized()
    if args.action=='push':push(module,env,m)
    elif args.action=='verify':verify(module,env,m)
    else:
        for record in m['kernels']:
            print('HOSTED_STATUS',record['mode'],status(module,env,record))

if __name__=='__main__':main()
