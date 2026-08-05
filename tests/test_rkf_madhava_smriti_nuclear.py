import unittest

from src.rkf_madhava_smriti_nuclear import (
    bilateral_reconstruction_defect,
    build_madhava_record,
    classify_refinement,
)


def observer_record() -> dict:
    return {
        "z": 10,
        "n": 12,
        "cut_even_jet": {
            "value": 10.0,
            "slope": 2.0,
            "curvature": 1.0,
            "jerk": 0.5,
        },
        "cut_odd_jet": {
            "value": 2.0,
            "slope": -1.0,
            "curvature": 0.25,
            "jerk": -0.5,
        },
        "neutron_jet": {
            "value": 12.0,
            "slope": 1.0,
            "curvature": 1.25,
            "jerk": 0.0,
        },
        "proton_jet": {
            "value": 8.0,
            "slope": 3.0,
            "curvature": 0.75,
            "jerk": 1.0,
        },
    }


def level_record(prediction: float, guard: bool = True, burden: float = 0.1) -> dict:
    return {
        "z": 10,
        "n": 12,
        "rkf_prediction_keV_per_a": prediction,
        "burden_guard_pass": guard,
        "decoder_burden": burden,
    }


def v5_record(
    prediction: float,
    actual: float = 10.0,
    source: str = "RKF_CROSS_FITTED_TAIL_REPAIR",
    v5_prediction: float | None = None,
    uam: float | None = 7.0,
    guard: bool = True,
) -> dict:
    return {
        "entity": "E10-22",
        "z": 10,
        "n": 12,
        "a": 22,
        "actual_binding_energy_per_A_keV": actual,
        "rkf_prediction_keV_per_a": prediction,
        "recognition_repair_prediction_keV_per_a": (
            prediction if v5_prediction is None else v5_prediction
        ),
        "recognition_repair_source": source,
        "frozen_uam_guarded_prediction_keV_per_a": uam,
        "burden_guard_pass": guard,
        "decoder_burden": 0.2,
    }


class MadhavaSmritiNuclearTests(unittest.TestCase):
    def test_bilateral_axis_reconstruction(self) -> None:
        self.assertEqual(bilateral_reconstruction_defect(observer_record()), 0.0)

    def test_wrong_axis_packet_opens_bilateral_seam(self) -> None:
        bad = observer_record()
        bad["proton_jet"] = dict(bad["proton_jet"])
        bad["proton_jet"]["value"] = 9.0
        defect = bilateral_reconstruction_defect(bad)
        self.assertEqual(defect, 1.0)
        self.assertEqual(
            classify_refinement(8.0, 9.0, 9.5, defect),
            "OPEN_BILATERAL_SEAM",
        )

    def test_exact_smriti_transfer_and_contractive_gate(self) -> None:
        record = build_madhava_record(
            observer_record(),
            level_record(8.0),
            level_record(9.0),
            v5_record(9.5, actual=10.0),
        )
        self.assertEqual(record["madhava_correction_q2_keV_per_a"], 1.0)
        self.assertEqual(record["madhava_correction_q3_keV_per_a"], 0.5)
        self.assertEqual(record["madhava_refinement_ratio"], 0.5)
        self.assertEqual(record["madhava_refinement_classification"], "CONTRACTIVE_MEMORY")
        self.assertEqual(
            record["validation_smriti_tail_keV_per_a"],
            {"level1": 2.0, "level2": 1.0, "level3": 0.5},
        )
        self.assertAlmostEqual(
            record["validation_transfer_defect_keV_per_a"]["level1_to_level2"],
            0.0,
        )
        self.assertAlmostEqual(
            record["validation_transfer_defect_keV_per_a"]["level2_to_level3"],
            0.0,
        )
        self.assertTrue(record["capstone_gate_pass"])
        self.assertEqual(record["v6_strict_prediction_keV_per_a"], 9.5)

    def test_expansive_third_correction_uses_level_two_ablation(self) -> None:
        record = build_madhava_record(
            observer_record(),
            level_record(8.0),
            level_record(8.5),
            v5_record(10.0, actual=11.0, uam=7.0),
        )
        self.assertEqual(record["madhava_refinement_classification"], "OPEN_REFINEMENT")
        self.assertFalse(record["capstone_gate_pass"])
        self.assertIsNone(record["v6_strict_prediction_keV_per_a"])
        self.assertEqual(record["v6_fallback_prediction_keV_per_a"], 7.0)
        self.assertEqual(record["v6_order_selected_prediction_keV_per_a"], 8.5)
        self.assertEqual(
            record["v6_order_selected_source"],
            "RKF_LEVEL2_BEFORE_EXPANSIVE_THIRD_CORRECTION",
        )

    def test_coherent_uam_sector_remains_frozen(self) -> None:
        record = build_madhava_record(
            observer_record(),
            level_record(8.0),
            level_record(9.0),
            v5_record(
                9.5,
                source="FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
                v5_prediction=7.25,
                uam=7.25,
            ),
        )
        self.assertEqual(record["v6_strict_prediction_keV_per_a"], 7.25)
        self.assertEqual(record["v6_fallback_prediction_keV_per_a"], 7.25)
        self.assertEqual(record["v6_order_selected_prediction_keV_per_a"], 7.25)

    def test_prospective_gate_does_not_use_actual_target(self) -> None:
        first = build_madhava_record(
            observer_record(),
            level_record(8.0),
            level_record(9.0),
            v5_record(9.5, actual=10.0),
        )
        second = build_madhava_record(
            observer_record(),
            level_record(8.0),
            level_record(9.0),
            v5_record(9.5, actual=1000.0),
        )
        for key in (
            "madhava_refinement_classification",
            "madhava_refinement_ratio",
            "capstone_gate_pass",
            "v6_strict_prediction_keV_per_a",
            "v6_fallback_prediction_keV_per_a",
            "v6_order_selected_prediction_keV_per_a",
        ):
            self.assertEqual(first[key], second[key])
        self.assertNotEqual(
            first["validation_smriti_tail_keV_per_a"],
            second["validation_smriti_tail_keV_per_a"],
        )

    def test_exact_refinement_stability(self) -> None:
        self.assertEqual(
            classify_refinement(5.0, 5.0, 5.0, 0.0),
            "EXACT_REFINEMENT_STABLE",
        )


if __name__ == "__main__":
    unittest.main()
