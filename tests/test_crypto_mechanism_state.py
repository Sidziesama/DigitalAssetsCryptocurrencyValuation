import unittest

from src.pipeline.crypto_economic_design import CODES
from src.pipeline.crypto_mechanism_state import resolve


def design(protocol=0):
    codes=[0]*10; codes[CODES.index("VA_PROTOCOL")]=protocol
    return {"assets":[{"asset_id":"crypto_x","codes":codes}]}


class CryptoMechanismStateTests(unittest.TestCase):
    def test_latest_effective_event_wins(self):
        spec={"schema_version":1,"as_of":"2026-08-22","events":[
            {"asset_id":"crypto_x","code":"VA_PROTOCOL","effective_from":"2026-01-01","value":1,"source_url":"https://example.org/on","rationale":"on"},
            {"asset_id":"crypto_x","code":"VA_PROTOCOL","effective_from":"2026-04-01","value":0,"source_url":"https://example.org/off","rationale":"off"}]}
        rows,summary=resolve(spec,design(0))
        self.assertEqual(rows[0]["value"],0); self.assertEqual(summary["status"],"pass")

    def test_future_event_does_not_backfill(self):
        spec={"schema_version":1,"as_of":"2026-01-01","events":[{"asset_id":"crypto_x","code":"VA_PROTOCOL","effective_from":"2026-02-01","value":1,"source_url":"https://example.org","rationale":"future"}]}
        rows,_=resolve(spec,design(0)); self.assertEqual(rows,[])

    def test_mismatch_blocks_state(self):
        spec={"schema_version":1,"as_of":"2026-01-02","events":[{"asset_id":"crypto_x","code":"VA_PROTOCOL","effective_from":"2026-01-01","value":1,"source_url":"https://example.org","rationale":"on"}]}
        _,summary=resolve(spec,design(0)); self.assertEqual(summary["status"],"blocked_design_state_mismatch")


if __name__=="__main__": unittest.main()
