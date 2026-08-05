import unittest

from src.rkf_recognition_repair import (
    RECOGNITION_REPAIR_THRESHOLD_KEV_PER_A,
    add_recognition_repair,
    recognition_repair_decision,
)


class RKFRecognitionRepairTests(unittest.TestCase):
    def test_coherent_sector_keeps_uam(self) -> None:
        decision = recognition_repair_decision(
            {"rkf_prediction_keV_per_a": 7001.0},
            {
                "guarded_blended_prediction_keV_per_a": 7000.0,
                "directional_disagreement_keV_per_a": 49.0,
            },
        )
        self.assertEqual(
            decision["recognition_repair_prediction_keV_per_a"], 7000.0
        )
        self.assertEqual(
            decision["recognition_repair_source"],
            "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
        )

    def test_seam_stressed_sector_uses_rkf(self) -> None:
        decision = recognition_repair_decision(
            {"rkf_prediction_keV_per_a": 7001.0},
            {
                "guarded_blended_prediction_keV_per_a": 7100.0,
                "directional_disagreement_keV_per_a": 50.0001,
            },
        )
        self.assertEqual(
            decision["recognition_repair_prediction_keV_per_a"], 7001.0
        )
        self.assertTrue(decision["recognition_repair_triggered"])

    def test_exact_boundary_remains_in_coherent_sector(self) -> None:
        decision = recognition_repair_decision(
            {"rkf_prediction_keV_per_a": 7001.0},
            {
                "guarded_blended_prediction_keV_per_a": 7000.0,
                "directional_disagreement_keV_per_a": RECOGNITION_REPAIR_THRESHOLD_KEV_PER_A,
            },
        )
        self.assertEqual(
            decision["recognition_repair_prediction_keV_per_a"], 7000.0
        )

    def test_frozen_uam_abstention_is_preserved(self) -> None:
        decision = recognition_repair_decision(
            {"rkf_prediction_keV_per_a": 7001.0},
            {
                "guarded_blended_prediction_keV_per_a": None,
                "directional_disagreement_keV_per_a": 500.0,
            },
        )
        self.assertIsNone(decision["recognition_repair_prediction_keV_per_a"])
        self.assertEqual(
            decision["recognition_repair_source"],
            "ABSTAIN_PRESERVE_FROZEN_UAM_COVERAGE",
        )

    def test_report_promotes_only_when_same_coverage_metrics_improve(self) -> None:
        base = {
            "report_type": "BASE",
            "status": "INCONCLUSIVE_BASE",
            "record_count": 2,
            "records": [
                {
                    "z": 1,
                    "n": 1,
                    "a": 2,
                    "entity": "A",
                    "actual_binding_energy_per_A_keV": 100.0,
                    "rkf_prediction_keV_per_a": 101.0,
                    "frozen_uam_guarded_prediction_keV_per_a": 150.0,
                },
                {
                    "z": 2,
                    "n": 2,
                    "a": 4,
                    "entity": "B",
                    "actual_binding_energy_per_A_keV": 200.0,
                    "rkf_prediction_keV_per_a": 201.0,
                    "frozen_uam_guarded_prediction_keV_per_a": 200.0,
                },
            ],
        }
        frozen = {
            "records": [
                {
                    "z": 1,
                    "n": 1,
                    "guarded_blended_prediction_keV_per_a": 150.0,
                    "directional_disagreement_keV_per_a": 100.0,
                },
                {
                    "z": 2,
                    "n": 2,
                    "guarded_blended_prediction_keV_per_a": 200.0,
                    "directional_disagreement_keV_per_a": 10.0,
                },
            ]
        }
        report = add_recognition_repair(base, frozen)
        self.assertEqual(
            report["status"],
            "PASS_EXPLORATORY_RECOGNITION_REPAIR_BEATS_FROZEN_UAM_V4_SAME_COVERAGE",
        )
        self.assertEqual(
            report["recognition_repair_metrics"]["prediction_count"], 2
        )


if __name__ == "__main__":
    unittest.main()
