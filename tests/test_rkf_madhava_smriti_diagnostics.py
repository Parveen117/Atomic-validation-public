import unittest

from src.rkf_madhava_smriti_diagnostics import add_honest_v6_diagnostics


def record(
    *,
    actual: float,
    v5: float,
    strict: float | None,
    fallback: float | None,
    order_selected: float | None,
    classification: str,
    source: str = "RKF_CROSS_FITTED_TAIL_REPAIR",
    burden: float = 0.2,
    burden_pass: bool = True,
    ratio: float | None = 0.5,
    uam: float | None = 7.0,
) -> dict:
    return {
        "z": 10,
        "n": 12,
        "actual_binding_energy_per_A_keV": actual,
        "recognition_repair_prediction_keV_per_a": v5,
        "frozen_uam_guarded_prediction_keV_per_a": uam,
        "rkf_level3_prediction_keV_per_a": v5,
        "v6_strict_prediction_keV_per_a": strict,
        "v6_fallback_prediction_keV_per_a": fallback,
        "v6_order_selected_prediction_keV_per_a": order_selected,
        "recognition_repair_source": source,
        "madhava_refinement_classification": classification,
        "madhava_refinement_ratio": ratio,
        "rkf_level3_decoder_burden": burden,
        "rkf_level3_burden_guard_pass": burden_pass,
    }


class MadhavaSmritiDiagnosticsTests(unittest.TestCase):
    def test_strict_gain_is_identified_as_abstention_not_prediction_change(self) -> None:
        records = [
            record(
                actual=10.0,
                v5=10.2,
                strict=10.2,
                fallback=10.2,
                order_selected=10.2,
                classification="CONTRACTIVE_MEMORY",
            ),
            record(
                actual=10.0,
                v5=14.0,
                strict=None,
                fallback=16.0,
                order_selected=15.0,
                classification="OPEN_REFINEMENT",
                burden=2.0,
                burden_pass=False,
            ),
            record(
                actual=12.0,
                v5=12.1,
                strict=12.1,
                fallback=12.1,
                order_selected=12.1,
                classification="CONTRACTIVE_MEMORY",
            ),
        ]
        report = add_honest_v6_diagnostics(
            {
                "status": "PASS_MADHAVA_SMRITI_NUCLEAR_ADAPTER_IDENTITIES",
                "records": records,
                "claim_boundary": {},
            }
        )
        strict = report["same_support_audit"]["v6_strict"]
        self.assertTrue(strict["identical_to_v5_1_on_support"])
        self.assertEqual(
            strict["maximum_prediction_difference_from_v5_1_keV_per_a"],
            0.0,
        )
        self.assertEqual(
            report["same_support_audit"]["strict_new_abstention_count"],
            1,
        )
        self.assertEqual(
            report["performance_status"],
            "PASS_IDENTITIES_V5_1_REMAINS_BEST_SAME_COVERAGE_RATIO_NOT_PROMOTED",
        )
        self.assertEqual(
            report["promotion_decision"]["best_same_coverage_predictor"],
            "RECOGNITION_REPAIR_V5_1",
        )

    def test_refinement_ratio_is_not_promoted_as_error_score(self) -> None:
        records = [
            record(
                actual=10.0,
                v5=11.0,
                strict=11.0,
                fallback=11.0,
                order_selected=11.0,
                classification="CONTRACTIVE_MEMORY",
                ratio=0.2,
                burden=0.1,
            ),
            record(
                actual=10.0,
                v5=14.0,
                strict=None,
                fallback=15.0,
                order_selected=15.0,
                classification="OPEN_REFINEMENT",
                ratio=2.0,
                burden=1.5,
                burden_pass=False,
            ),
            record(
                actual=10.0,
                v5=10.5,
                strict=10.5,
                fallback=10.5,
                order_selected=10.5,
                classification="CONTRACTIVE_MEMORY",
                ratio=0.8,
                burden=0.2,
            ),
        ]
        report = add_honest_v6_diagnostics(
            {
                "status": "PASS_MADHAVA_SMRITI_NUCLEAR_ADAPTER_IDENTITIES",
                "records": records,
                "claim_boundary": {},
            }
        )
        proxy = report["refinement_proxy_audit"]
        self.assertFalse(proxy["refinement_ratio_promoted_as_risk_score"])
        self.assertIn(
            "CONTRACTIVE_MEMORY",
            proxy["seam_stressed_metrics_by_refinement_class"],
        )
        self.assertEqual(
            proxy["seam_stressed_metrics_by_level3_burden_guard"]["FAIL"][
                "record_count"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
