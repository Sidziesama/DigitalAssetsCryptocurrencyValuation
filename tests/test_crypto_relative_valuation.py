import copy
import json
import math
import unittest
from pathlib import Path

from src.pipeline.crypto_relative_valuation import build, collect, fit_predict, peer_multiples


class Tests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((Path(__file__).parents[1]/'config/crypto_relative_valuation.json').read_text())
        self.spec['window']={'start':'2026-01-01','end':'2026-01-03','minimum_coverage_share':1.0}
        self.profiles=[]; self.market=[]; self.fees=[]
        for i in range(23):
            a=f'a{i}'
            self.profiles.append({'asset_id':a,'symbol':a,'classification_status':'complete_human_verified','raw_function_breadth':'3',**{g:'1' for g in self.spec['groups']}})
            for day in ['2026-01-01','2026-01-02','2026-01-03']:
                self.market.append({'asset_id':a,'date':day,'market_cap_usd':str((i+1)*1000000),'volume_24h_usd':str((i+1)*1000)})
                self.fees.append({'asset_id':a,'date':day,'fees_usd_lag1':str(i+1),'holders_revenue_usd_lag1':'1','fee_scope':'chain'})

    def test_target_outcome_is_never_used_by_fit(self):
        train=[{'x':float(i),'mean_log_market_cap_usd':float(i)} for i in range(5)]
        target={'x':100.0,'mean_log_market_cap_usd':-100.0}
        before=fit_predict(train,target,['x'],10)
        target['mean_log_market_cap_usd']=1e20
        self.assertEqual(before,fit_predict(train,target,['x'],10))
        self.assertTrue(math.isfinite(before))

    def test_mean_benchmark_is_training_mean_and_constant_features_are_safe(self):
        train=[{'x':1.0,'mean_log_market_cap_usd':float(i)} for i in range(4)]
        self.assertAlmostEqual(fit_predict(train,{'x':1.0},[],10),1.5)
        self.assertAlmostEqual(fit_predict(train,{'x':1.0},['x'],10),1.5)

    def test_duplicate_dates_do_not_manufacture_coverage(self):
        market=[r for r in self.market if r['date']=='2026-01-01']*10
        rows,coverage=collect(self.spec,self.profiles,market,self.fees)
        self.assertEqual(rows,[])
        self.assertEqual(coverage[0]['cap_days'],1)

    def test_peers_exclude_target_and_match_scope(self):
        rows,_=collect(self.spec,self.profiles,self.market,self.fees)
        rows[1]['fee_scope']='application_protocol'
        peers=peer_multiples(self.spec,rows)
        target=next(r for r in peers if r['asset_id']=='a0' and r['metric']=='fees')
        self.assertNotIn('a0',target['peers'].split('|'))
        self.assertNotIn('a1',target['peers'].split('|'))
        self.assertEqual(target['state'],'measured')

    def test_held_out_residuals_do_not_use_own_outcome(self):
        first=build(self.spec,self.profiles,self.market,self.fees)
        changed=copy.deepcopy(self.market)
        for r in changed:
            if r['asset_id']=='a0': r['market_cap_usd']=str(1e12)
        second=build(self.spec,self.profiles,changed,self.fees)
        for model in ['identity_mean','identity_breadth','identity_groups','fundamentals_capture']:
            a=next(r for r in first['asset_estimates'] if r['asset_id']=='a0' and r['model_id']==model)
            b=next(r for r in second['asset_estimates'] if r['asset_id']=='a0' and r['model_id']==model)
            self.assertAlmostEqual(a['held_out_implied_cap_usd'],b['held_out_implied_cap_usd'])
            self.assertAlmostEqual(a['empirical_band_low_usd'],b['empirical_band_low_usd'])
        self.assertEqual(len(first['models']),6)


if __name__=='__main__': unittest.main()
