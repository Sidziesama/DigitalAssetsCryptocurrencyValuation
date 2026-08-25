import unittest

from src.pipeline.stablecoin_evidence import build_audit, validate


def asset_config():
    return {"schema_version": 1, "as_of": "2026-01-01", "assets": [{"asset_id": f"stable_{i}", "symbol": f"S{i}", "name": f"Stable {i}", "universe": "stablecoin", "tier": "x", "coingecko_id": f"s{i}", "defillama_id": str(i)} for i in range(8)]}


def plan(status="candidate_unextracted"):
    classes = ["reserve"]
    return {"schema_version": 1, "selected_assets": [f"stable_{i}" for i in range(8)], "required_evidence_classes": classes, "allowed_extraction_statuses": ["candidate_unextracted", "verified_extracted"], "assets": [{"asset_id": f"stable_{i}", "design_type": "x", "sources": [{"url": "https://example.test", "publication_or_effective_date": "2026-01-01", "evidence_classes": classes, "extraction_status": status}]} for i in range(8)]}


class StablecoinEvidenceTests(unittest.TestCase):
    def test_plan_requires_exactly_eight_assets(self):
        value = plan(); value["selected_assets"].pop()
        with self.assertRaisesRegex(ValueError, "exactly eight"): validate(value, asset_config())

    def test_candidate_source_is_not_verified_evidence(self):
        matrix, summary = build_audit(plan())
        self.assertEqual(matrix[0]["candidate_coverage"], 1)
        self.assertEqual(matrix[0]["verified_coverage"], 0)
        self.assertEqual(summary[0]["point_in_time_score_ready"], 0)

    def test_verified_dated_extraction_passes(self):
        value = plan()
        extraction = {"schema_version": 1, "extractions": [{
            "asset_id": "stable_0", "evidence_class": "reserve",
            "source_url": "https://example.test", "source_title": "Official report",
            "publication_or_effective_date": "2026-01-01", "locator": "p. 1",
            "evidence_summary": "Dated reserve evidence.",
            "verification_status": "verified_extracted", "verified_by": "researcher",
            "verification_date": "2026-01-02",
        }]}
        validate(value, asset_config(), extraction)
        matrix, summary = build_audit(value, extraction)
        self.assertEqual(matrix[0]["status"], "pass")
        self.assertEqual(summary[0]["point_in_time_score_ready"], 1)

    def test_unregistered_extraction_source_is_rejected(self):
        extraction = {"schema_version": 1, "extractions": [{
            "asset_id": "stable_0", "evidence_class": "reserve",
            "source_url": "https://unregistered.test", "source_title": "Report",
            "publication_or_effective_date": "2026-01-01", "locator": "p. 1",
            "evidence_summary": "Evidence.", "verification_status": "verified_extracted",
            "verified_by": "researcher", "verification_date": "2026-01-02",
        }]}
        with self.assertRaisesRegex(ValueError, "not registered"):
            validate(plan(), asset_config(), extraction)


if __name__ == "__main__":
    unittest.main()
