"""Offline feature contracts for 28 finite hypothesis cards; no model scores."""
from __future__ import annotations
import copy
import math
import unittest
import numpy as np
from research.proposal_factory_features import (
    build_match_events, make_snapshot, prefix_poison, HERO_COLUMNS
)
from research.proposal_factory_registry import SPECS,BASE,FEATURE_SET
from tests.test_notebook_contracts import N,match_fixture

class ProposalFactoryFeatureContracts(unittest.TestCase):
    def fixture(self):
        x=match_fixture()
        x['objectives']=[e for e in x['objectives'] if isinstance(e.get('time'),(int,float))]
        x['objectives'].append({'time':601,'type':'CHAT_MESSAGE_AEGIS','player_slot':0})
        x['objectives'].append({'time':700,'type':'CHAT_MESSAGE_AEGIS','player_slot':128})
        for i,p in enumerate(x['players']):
            p['hero_id']=i+1
            p['purchase_log']=[]
            p['buyback_log']=[]
        x['players'][0]['buyback_log']=[{'time':600},{'time':601}]
        x['players'][5]['buyback_log']=[{'time':601}]
        x['players'][0]['purchase_log']=[
            {'time':-30,'key':'branches'},
            {'time':601,'key':'blink'},
            {'time':602,'key':'black_king_bar'},
            {'time':3600,'key':'manta'}]
        return x

    def test_registry_count_unique_explicit_features(self):
        self.assertEqual(len(SPECS),28)
        self.assertEqual(len({s[0] for s in SPECS}),28)
        x=self.fixture()
        f=make_snapshot(x,10,N['snapshot_features'])
        self.assertTrue(all(k in f for k in FEATURE_SET))
        self.assertTrue(all(k in f for k in BASE))
        self.assertEqual(len(HERO_COLUMNS),160)

    def test_cutoff_and_future_poison(self):
        x=self.fixture()
        for t in (0,1,9,10,11,20,30):
            a=make_snapshot(x,t,N['snapshot_features'])
            shortened=prefix_poison(x,t)
            b=make_snapshot(shortened,t,N['snapshot_features'])
            for name in a:
                if math.isnan(a[name]):
                    self.assertTrue(math.isnan(b[name]),(t,name))
                else:
                    self.assertAlmostEqual(a[name],b[name],places=9,msg=(t,name))
        self.assertEqual(make_snapshot(x,10,N['snapshot_features'])['aegis_claim5'],0)
        self.assertGreater(make_snapshot(x,11,N['snapshot_features'])['aegis_claim5'],0)

    def test_frozen_hero_pick_symmetry(self):
        x=self.fixture()
        a=make_snapshot(x,10,N['snapshot_features'])
        y=copy.deepcopy(x)
        y['radiant_gold_adv']=[-v for v in x['radiant_gold_adv']]
        y['radiant_xp_adv']=[-v for v in x['radiant_xp_adv']]
        for p in y['players']:
            p['player_slot']=p['player_slot']+128 if p['player_slot']<128 else p['player_slot']-128
        for e in y['objectives']:
            if e['type']=='building_kill':
                e['key']=e['key'].replace('badguys','temp').replace('goodguys','badguys').replace('temp','goodguys')
            if e['type']=='CHAT_MESSAGE_AEGIS':
                e['player_slot']=e['player_slot']+128 if e['player_slot']<128 else e['player_slot']-128
            if e['type']=='CHAT_MESSAGE_ROSHAN_KILL':
                e['team']=5-e['team']  # 2->3 and 3->2
        b=make_snapshot(y,10,N['snapshot_features'])
        for k in ('relative_gold','relative_xp','carry_gold_diff_k',
                  'top2_share_gap','bottom3_gold_diff_k','lh_diff10',
                  'gold_gini_gap','roshan_recent10','tower_tier_delta',
                  'tower_recent10','buyback_commitment5','major_item_diff',
                  'unconverted_gold_k'):
            self.assertAlmostEqual(a[k],-b[k],places=8,msg=k)
        for col in HERO_COLUMNS:
            self.assertEqual(a[col],-b[col])

    def test_sparse_events_and_unknown_payload(self):
        x=self.fixture()
        a=make_snapshot(x,11,N['snapshot_features'])
        self.assertGreater(a['major_item_diff'],0)
        self.assertGreater(a['major_recent5'],0)
        self.assertGreater(a['purchasing_breadth5'],0)
        self.assertGreater(a['blink_bkb_diff'],0)
        x=self.fixture();x['objectives']=None
        a=make_snapshot(x,11,N['snapshot_features'])
        for col in ('tower_tier_delta','aegis_claim5','roshan_recent10',
                    'unconverted_gold_k'):
            self.assertTrue(math.isnan(a[col]))
        x=self.fixture();x['players'][0]['purchase_log']=None
        a=make_snapshot(x,11,N['snapshot_features'])
        self.assertTrue(math.isnan(a['major_item_diff']))
        self.assertTrue(math.isnan(a['major_recent5']))

    def test_reject_fractional_or_negative_time(self):
        x=self.fixture()
        with self.assertRaises(ValueError):make_snapshot(x,11.1,N['snapshot_features'])
        with self.assertRaises(ValueError):prefix_poison(x,-1)

if __name__=='__main__':unittest.main()
