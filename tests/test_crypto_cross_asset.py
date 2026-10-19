import copy
import json
import math
import unittest
from datetime import date,timedelta
from pathlib import Path

from src.pipeline.crypto_cross_asset import PRIMARY, block_interval, corr, matched, prepare, performance, build
from src.pipeline.cross_asset_market_data import normalize


class Tests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((Path(__file__).parents[1]/'config/crypto_cross_asset.json').read_text())
        self.spec['window']={'start':'2026-01-05','end':'2026-05-10'}
        self.spec['minimum_weekly_pairs']=10
        self.spec['uncertainty']['draws']=30

    def test_weekend_returns_are_compounded_not_discarded(self):
        self.spec['window']={'start':'2026-01-05','end':'2026-01-05'}
        daily={'BTC':{'2026-01-03':.1,'2026-01-04':.1,'2026-01-05':.1}}
        benchmarks={'SPY':{'2026-01-02':100,'2026-01-05':101}}
        rows=matched(self.spec,daily,benchmarks,False)
        self.assertAlmostEqual(rows[0]['BTC'],1.1**3-1)
        self.assertAlmostEqual(rows[0]['SPY'],.01)

    def test_missing_crypto_calendar_day_is_not_filled(self):
        self.spec['window']={'start':'2026-01-05','end':'2026-01-05'}
        daily={'BTC':{'2026-01-03':.1,'2026-01-05':.1}}
        rows=matched(self.spec,daily,{'SPY':{'2026-01-02':100,'2026-01-05':101}},False)
        self.assertNotIn('BTC',rows[0])

    def test_shift_moves_crypto_endpoints_only(self):
        self.spec['window']={'start':'2026-01-05','end':'2026-01-05'}
        daily={'BTC':{'2026-01-03':.1,'2026-01-04':.2,'2026-01-05':.3,'2026-01-06':.4}}
        benchmark={'SPY':{'2026-01-02':100,'2026-01-05':101}}
        base=matched(self.spec,daily,benchmark,False)[0]
        shifted=matched(self.spec,daily,benchmark,False,1)[0]
        self.assertEqual(base['SPY'],shifted['SPY'])
        self.assertAlmostEqual(shifted['BTC'],1.2*1.3*1.4-1)

    def test_bootstrap_resamples_pairs_reproducibly(self):
        x=[float(i) for i in range(40)]; y=[2*v+3 for v in x]
        self.assertAlmostEqual(corr(x,y),1)
        interval=block_interval(x,y,self.spec['uncertainty'])
        self.assertEqual(interval,block_interval(x,y,self.spec['uncertainty']))
        self.assertAlmostEqual(interval[0],1)

    def test_us_session_timestamp_is_not_utc_calendar_date(self):
        # A UTC timestamp on Jan 6 is still Jan 5 in New York.
        payload={'chart':{'result':[{'meta':{'currency':'USD'},'timestamp':[1767661200],'indicators':{'adjclose':[{'adjclose':[123.0]}]}}],'error':None}}
        rows=normalize(payload,'SPY')
        self.assertEqual(rows[0]['date'],'2026-01-05')

    def test_invalid_benchmark_currency_rejected(self):
        payload={'chart':{'result':[{'meta':{'currency':'EUR'},'timestamp':[1767661200],'indicators':{'adjclose':[{'adjclose':[123.0]}]}}],'error':None}}
        with self.assertRaises(ValueError):normalize(payload,'SPY')

    def test_long_missing_week_is_not_bridged(self):
        self.spec['window']={'start':'2026-01-01','end':'2026-02-01'}
        rows=matched(self.spec,{}, {'SPY':{'2026-01-02':100,'2026-01-23':110}}, True)
        self.assertEqual(rows,[])

    def fixture(self):
        profiles=[{'asset_id':f'a{i}','symbol':['BTC','ETH'][i] if i<2 else f'C{i}','classification_status':'complete_human_verified','bundle_holder_capture':'1' if i%2 else '0'} for i in range(23)]
        prices=[]; benchmark=[]
        for j in range(132):
            day=date(2025,12,30)+timedelta(days=j)
            for i in range(23):
                prices.append({'asset_id':f'a{i}','date':day.isoformat(),'close_usdt':100*math.exp(.001*j+.02*math.sin(j/5+i))})
            if day.weekday()<5:
                for i,b in enumerate(['GLD','SPY','IWM']):benchmark.append({'symbol':b,'date':day.isoformat(),'adjusted_close_usd':100*math.exp(.0005*j+.01*math.cos(j/4+i))})
        return profiles,prices,benchmark

    def test_missing_constituent_does_not_change_basket_weights(self):
        profiles,prices,_=self.fixture()
        prices=[r for r in prices if not (r['asset_id']=='a2' and r['date']=='2026-01-15')]
        daily,coverage,members=prepare(self.spec,profiles,prices)
        self.assertEqual(sum(r['eligible'] for r in coverage),23)
        self.assertNotIn('2026-01-15',daily[PRIMARY])
        self.assertNotIn('2026-01-16',daily[PRIMARY])
        self.assertEqual(len(members[PRIMARY]),23)

    def test_build_preserves_universe_and_all_scenarios(self):
        profiles,prices,benchmark=self.fixture()
        result,weekly,rolling=build(self.spec,profiles,prices,benchmark)
        self.assertEqual(sum(r['eligible'] for r in result['coverage']),23)
        primary=[r for r in result['correlations'] if r['series']==PRIMARY]
        self.assertEqual(len(primary),3)
        self.assertTrue(all(r['pairs']>=10 for r in primary))
        self.assertEqual(len({r['scenario'] for r in result['robustness']}),5)
        self.assertTrue(rolling)

    def test_total_return_compounds_instead_of_summing(self):
        rows=[{'date':'2026-01-09','previous_date':'2026-01-02','X':.1},{'date':'2026-01-16','previous_date':'2026-01-09','X':-.1}]
        self.assertAlmostEqual(performance(rows,'X')['total_return'],-.01)


if __name__=='__main__':unittest.main()
