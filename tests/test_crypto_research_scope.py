import copy
import json
import unittest
from pathlib import Path

from src.pipeline.crypto_research_scope import validate


class CryptoResearchScopeTests(unittest.TestCase):
    def setUp(self):
        repo = Path(__file__).resolve().parents[1]
        self.scope = json.loads((repo / "config/research_scope.json").read_text(encoding="utf-8"))

    def test_active_crypto_scope_and_deferred_stablecoins(self):
        result = validate(self.scope)
        self.assertEqual(result["active_hypotheses"], ["H1", "H2", "H3", "H4", "H8"])
        self.assertEqual(result["deferred_hypotheses"], ["H5", "H6", "H7"])
        self.assertFalse(result["stablecoin_work_is_active_gate"])

    def test_stablecoins_cannot_silently_reenter_active_gate(self):
        scope = copy.deepcopy(self.scope)
        scope["deferred_phase"]["status"] = "active"
        with self.assertRaisesRegex(ValueError, "deferred non-gating"):
            validate(scope)


if __name__ == "__main__":
    unittest.main()
