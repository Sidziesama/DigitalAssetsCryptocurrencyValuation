import tempfile
import unittest
from pathlib import Path

from src.pipeline.bnb_monetary_activity import normalize_rows, validate


def specification(days=2):
    return {"schema_version":1,"asset_id":"crypto_bnb","provider":"dune","api_base":"https://api.dune.com/api/v1",
            "api_source":"https://docs.dune.com/x","start_date":"2026-01-01","end_date":f"2026-01-0{days}",
            "expected_days":days,"sql":'SELECT bnb.transactions, COUNT(DISTINCT address), transaction_count, active_addresses'}


class BnbMonetaryActivityTests(unittest.TestCase):
    def test_normalizes_exact_consecutive_window(self):
        spec=specification(); validate(spec)
        payload={"result":{"rows":[{"date":"2026-01-02 00:00:00.000 UTC","active_addresses":"12","transaction_count":30},
                                   {"date":"2026-01-01","active_addresses":10,"transaction_count":"20"}]}}
        rows=normalize_rows(payload,spec)
        self.assertEqual([row["date"] for row in rows],["2026-01-01","2026-01-02"])
        self.assertEqual(rows[0]["active_addresses"],10)

    def test_rejects_missing_day_and_new_address_substitute(self):
        spec=specification()
        with self.assertRaisesRegex(ValueError,"exactly 2 consecutive"):
            normalize_rows({"result":{"rows":[{"date":"2026-01-01","active_addresses":10,"transaction_count":20}]}},spec)
        bad=dict(spec); bad["sql"]='SELECT bnb.transactions, new_addresses, transaction_count, active_addresses'
        with self.assertRaisesRegex(ValueError,"COUNT"):
            validate(bad)


if __name__ == "__main__": unittest.main()
