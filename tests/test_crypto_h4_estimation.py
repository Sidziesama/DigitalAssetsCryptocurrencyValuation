import json
import math
import unittest
from datetime import date,timedelta
from pathlib import Path

from src.pipeline.crypto_h4_estimation import build,index_rows


class Tests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).parents[1]
        self.spec=json.loads((root/'config/crypto_h4_estimation.json').read_text())
        self.design=json.loads((root/'config/crypto_h4_analysis.json').read_text())
        self.design.update(study_start='2026-03-01',study_end='2026-04-09',minimum_common_days=30)
        self.market=[];self.prices=[];self.eth=[];self.bnb=[]
        assets=self.design['primary_sample']['consensus_staking_assets']+self.design['primary_sample']['structural_nonstaking_controls']
        start=date(2026,3,1)
        for j,asset in enumerate(assets):
            for t in range(-100,40):
                d=(start+timedelta(days=t)).isoformat()
                price=100*math.exp(.001*t+.05*math.sin(t/4+j))
                cap=1e8*math.exp(.02*j+.01*math.cos(t/7+j)+.001*t)
                self.prices.append({'asset_id':asset,'date':d,'price_usd':price})
                if t>=-1:
                    self.market.append({'asset_id':asset,'date':d,'price_usd':price,'market_cap_usd':cap,'volume_24h_usd':cap*(.1+.01*math.cos(t/3+j))})
                    if asset in ['crypto_eth','crypto_bnb']:
                        share=.2+.01*math.sin(t/8+j)
                        row={'asset_id':asset,'date':d,'total_staked_native_units':share*cap/price,'measurement_role':'consensus_active_effective_balance' if asset=='crypto_eth' else 'consensus_stake_all_validator_pools'}
                        (self.eth if asset=='crypto_eth' else self.bnb).append(row)

    def test_missing_eth_never_estimated_or_filled_with_zero(self):
        panel,result=build(self.spec,self.design,self.market,self.prices,[],self.bnb)
        self.assertFalse(result['estimation_allowed']);self.assertEqual(result['results'],[]);self.assertEqual(panel,[])
        self.assertEqual(result['common_market_and_price_days_excluding_stake'],40)

    def test_partial_eth_still_blocks(self):
        _,result=build(self.spec,self.design,self.market,self.prices,self.eth[:-1],self.bnb)
        self.assertFalse(result['estimation_allowed'])

    def test_balanced_synthetic_panel_has_three_tests_and_absorbed_btc(self):
        panel,result=build(self.spec,self.design,self.market,self.prices,self.eth,self.bnb)
        self.assertEqual(result['status'],'h4_exploratory_estimation_complete')
        self.assertEqual(len(panel),5*40);self.assertEqual(len(result['results']),3)
        self.assertNotIn('crypto_aave',{r['asset_id'] for r in panel})
        self.assertIn('btc_log_return',result['absorbed_controls'])
        for row in result['results']:
            self.assertEqual(row['bootstrap_assignments'],32)
            self.assertEqual(row['clusters'],5)
            self.assertGreaterEqual(row['bh_q_value'],row['wild_cluster_bootstrap_p_two_sided']-1e-12)
        self.assertTrue(all(r['staked_share_lag1']==0 for r in panel if r['asset_id']=='crypto_btc'))

    def test_lag_uses_previous_day_not_current_stake(self):
        panel,_=build(self.spec,self.design,self.market,self.prices,self.eth,self.bnb)
        first=next(r for r in panel if r['asset_id']=='crypto_eth')
        previous=next(r for r in self.market if r['asset_id']=='crypto_eth' and r['date']=='2026-02-28')
        stake=next(r for r in self.eth if r['date']=='2026-02-28')
        self.assertAlmostEqual(first['staked_share_lag1'],stake['total_staked_native_units']/(previous['market_cap_usd']/previous['price_usd']))

    def test_missing_price_in_warmup_blocks_common_sample(self):
        prices=[r for r in self.prices if r['date']!='2026-02-15']
        _,result=build(self.spec,self.design,self.market,prices,self.eth,self.bnb)
        self.assertEqual(result['status'],'h4_estimation_blocked_insufficient_common_days')
        self.assertEqual(result['results'],[])

    def test_wrong_stake_measure_rejected(self):
        self.eth[0]['measurement_role']='validator_count_times_32'
        with self.assertRaises(ValueError):build(self.spec,self.design,self.market,self.prices,self.eth,self.bnb)

    def test_duplicate_dates_are_not_extra_coverage(self):
        with self.assertRaises(ValueError):index_rows([self.market[0],self.market[0]],['price_usd'])


if __name__=='__main__':unittest.main()
