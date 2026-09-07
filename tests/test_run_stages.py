import unittest
from pathlib import Path

from src.pipeline.run_stages import load, plan, validate

REPO = Path(__file__).resolve().parents[1]


class RunStagesTests(unittest.TestCase):
    def test_stage_map_covers_every_module_exactly_once(self):
        validate(load(REPO), REPO)

    def test_offline_plan_orders_commands(self):
        spec = load(REPO)
        steps = plan(spec, ["crypto_classification", "reporting"], REPO)
        self.assertEqual(steps[0]["module"], "crypto_research_scope")
        self.assertEqual(steps[-1]["module"], "checkpoint_readiness")
        self.assertIn("--repo", steps[0]["argv"])

    def test_unknown_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown stages"):
            plan(load(REPO), ["nope"], REPO)

    def test_duplicate_module_is_rejected(self):
        spec = load(REPO)
        spec["stages"][1]["commands"].append({"module": "checkpoint_readiness", "args": []})
        with self.assertRaisesRegex(ValueError, "appears in both"):
            validate(spec, REPO)


if __name__ == "__main__": unittest.main()
