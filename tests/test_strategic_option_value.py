"""Independent PIT, sign-equivariance, and window-edge tests (offline)."""
from __future__ import annotations
import copy
import math
import unittest
from research.strategic_option_value import option_snapshot,option_prefix_truncated
from tests.test_notebook_contracts import match_fixture


class StrategicOptionsContracts(unittest.TestCase):
    def game(self):
        x=match_fixture()
        x['radiant_gold_adv']=[2000.]*36
        x['objectives']=[
            {'time': 599,'type':'CHAT_MESSAGE_AEGIS','player_slot':0},
            {'time': 600,'type':'building_kill','key':'npc_dota_goodguys_tower1_mid'},
            {'time': 601,'type':'CHAT_MESSAGE_AEGIS','player_slot':131},
            {'time': 1800,'type':'building_kill','key':'npc_dota_badguys_melee_rax_mid'},
        ]
        for p in x['players']:
            p['buyback_log']=[]
            p['purchase_log']=[{'time':-20,'key':'tango'},{'time':2200,'key':'blink'}]
        x['players'][0]['buyback_log']=[{'time':600}, {'time':601}]
        x['players'][6]['buyback_log']=[{'time':599}]
        return x

    def test_exact_cutoff_and_linear_event_age(self):
        x=self.game()
        before=option_snapshot(x,9)
        at=option_snapshot(x,10)
        next_min=option_snapshot(x,11)
        five_after=option_snapshot(x,16)
        self.assertEqual(before['aegis_claim5'],0)
        self.assertAlmostEqual(at['aegis_claim5'],1.-1/300)
        self.assertAlmostEqual(next_min['aegis_claim5'],1.-61/300- (1.-59/300))
        self.assertEqual(five_after['aegis_claim5'],0)
        self.assertAlmostEqual(at['buyback_commitment5'],1+(0)-(1.-1/300))
        self.assertEqual(at['unconverted_gold_k'],2.)

    def test_future_gold_and_labels_do_not_change_present_snapshot(self):
        x=self.game()
        before=option_snapshot(x,10)
        y=copy.deepcopy(x)
        y['radiant_gold_adv']=y['radiant_gold_adv'][:11]+[99999999]*25
        y['radiant_win']=not x['radiant_win']
        y['duration']=0
        y['players'][0]['net_worth']=999999999
        y['players'][1]['buyback_log'].append({'time':3600})
        y['objectives'].append({'time':4000,'type':'CHAT_MESSAGE_AEGIS','player_slot':128})
        self.assertEqual(before,option_snapshot(y,10))
        self.assertEqual(before,option_snapshot(option_prefix_truncated(y,10),10))

    def test_historical_prefix_fully_truncates_option_logs(self):
        x=self.game()
        p=option_prefix_truncated(x,10)
        self.assertEqual(len(p['objectives']),2)
        self.assertEqual(len(p['players'][0]['buyback_log']),1)
        self.assertEqual(len(p['players'][0]['purchase_log']),1)
        self.assertFalse(p['radiant_win']==x['radiant_win'])
        self.assertEqual(len(p['radiant_gold_adv']),11)
        self.assertEqual(option_snapshot(x,10),option_snapshot(p,10))

    def test_radiant_dire_sign_equivariance(self):
        x=self.game();a=option_snapshot(x,10);y=copy.deepcopy(x)
        y['radiant_gold_adv']=[-g for g in x['radiant_gold_adv']]
        for p in y['players']:
            old=p['player_slot'];p['player_slot']=old+128 if old<128 else old-128
        for event in y['objectives']:
            if event['type']=='CHAT_MESSAGE_AEGIS':
                old=event['player_slot'];event['player_slot']=old+128 if old<128 else old-128
            elif event['type']=='building_kill':
                key=event['key']
                event['key']=key.replace('goodguys','GOODTEMP').replace('badguys','goodguys').replace('GOODTEMP','badguys')
        b=option_snapshot(y,10)
        for name in a:
            self.assertAlmostEqual(a[name],-b[name],msg=name)

    def test_missing_optional_logs_are_nan_not_zero(self):
        x=self.game();x['objectives']=None
        a=option_snapshot(x,10)
        self.assertTrue(math.isnan(a['aegis_claim5']))
        self.assertTrue(math.isnan(a['unconverted_gold_k']))
        x=self.game();x['players'][0]['buyback_log']=None
        self.assertTrue(math.isnan(option_snapshot(x,10)['buyback_commitment5']))

    def test_invalid_slots_or_malformed_event_times_fail_closed(self):
        x=self.game();x['players'][0]['player_slot']=x['players'][1]['player_slot']
        self.assertTrue(math.isnan(option_snapshot(x,10)['buyback_commitment5']))
        x=self.game();x['objectives'][0]['time']=None
        self.assertTrue(math.isnan(option_snapshot(x,10)['aegis_claim5']))
        x=self.game();x['players'][0]['buyback_log'][0]['time']=None
        self.assertTrue(math.isnan(option_snapshot(x,10)['buyback_commitment5']))

    def test_reject_noninteger_game_clock(self):
        with self.assertRaises(ValueError): option_snapshot(self.game(),10.5)
        with self.assertRaises(ValueError): option_snapshot(self.game(),-1)

if __name__=='__main__':unittest.main()
