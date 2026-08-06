from __future__ import annotations

import importlib.util
import json
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module():
    path = ROOT / "scripts" / "run_chromium_neel_cut_square_c05.py"
    spec = importlib.util.spec_from_file_location("chromium_c05", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict:
    return json.loads(
        (ROOT / "protocols" / "C05_CHROMIUM_NEEL_CUT_SQUARE_ADAPTER.json").read_text(
            encoding="utf-8"
        )
    )


class ChromiumNeelCutSquareC05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_adapter_is_frozen_but_physical_beta_requires_data(self) -> None:
        result = self.module.audit(load_contract(), ROOT)
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C05_CUT_SQUARE_ADAPTER_FROZEN_BETA_DATA_REQUIRED",
        )
        self.assertEqual(result["beta_classification"], "DATA_REQUIRED")
        self.assertFalse(result["beta_computed"])
        self.assertFalse(result["curvature_computed"])
        self.assertTrue(result["physical_result"]["data_required"])

    def test_strict_exact_control_has_beta_one_quarter(self) -> None:
        result = self.module.sharp_burden(
            [[1, 0], [0, 1]], [[1, 0], [0, 1]], ["1/2", 0]
        )
        self.assertTrue(result["visible"])
        self.assertEqual(result["beta"], Fraction(1, 4))
        self.assertEqual(result["classification"], "STRICT_NEEL_CUT_CLOSURE")

    def test_critical_control_needs_alignment_certificate(self) -> None:
        result = self.module.sharp_burden(
            [[1, 0], [0, 1]], [[1, 0], [0, 1]], [1, 0]
        )
        self.assertEqual(result["beta"], Fraction(1, 1))
        self.assertEqual(result["classification"], "THRESHOLD_INCONCLUSIVE")
        self.assertEqual(
            self.module.classify_exact_beta(result["beta"], transverse_zero=True),
            "CRITICAL_ALIGNED_CLOSURE",
        )

    def test_burden_exceeds_one_control(self) -> None:
        result = self.module.sharp_burden(
            [[1, 0], [0, 1]], [[1, 0], [0, 1]], [2, 0]
        )
        self.assertEqual(result["beta"], Fraction(4, 1))
        self.assertEqual(result["classification"], "BURDEN_EXCEEDS_ONE")

    def test_blind_target_requires_higher_layer(self) -> None:
        result = self.module.sharp_burden([[1, 0]], [[1]], [0, 1])
        self.assertFalse(result["visible"])
        self.assertIsNone(result["beta"])
        self.assertEqual(result["classification"], "TARGET_BLIND_ADD_HIGHER_LAYER")

    def test_redundant_observer_rows_preserve_exact_burden(self) -> None:
        result = self.module.sharp_burden(
            [[1, 0], [0, 1], [1, 1]],
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [1, 0],
        )
        self.assertEqual(result["beta"], Fraction(2, 3))
        self.assertEqual(result["classification"], "STRICT_NEEL_CUT_CLOSURE")

    def test_interval_classification_is_fail_closed(self) -> None:
        self.assertEqual(
            self.module.classify_beta_interval("9/10", "99/100"),
            "STRICT_NEEL_CUT_CLOSURE",
        )
        self.assertEqual(
            self.module.classify_beta_interval("99/100", "101/100"),
            "THRESHOLD_INCONCLUSIVE",
        )
        self.assertEqual(
            self.module.classify_beta_interval("101/100", "11/10"),
            "BURDEN_EXCEEDS_ONE",
        )

    def test_candidate_cut_cannot_be_promoted_without_data(self) -> None:
        contract = load_contract()
        contract["physical_state_contract"]["candidate_cut_admitted"] = True
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT")
        self.assertTrue(any("candidate cut" in error for error in result["errors"]))

    def test_post_hoc_peak_target_is_forbidden(self) -> None:
        contract = load_contract()
        contract["target_contract"]["post_hoc_peak_picking_forbidden"] = False
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT")
        self.assertTrue(any("post_hoc_peak" in error for error in result["errors"]))

    def test_raw_second_derivative_is_not_native_curvature(self) -> None:
        contract = load_contract()
        contract["seam_curvature_contract"][
            "raw_second_derivative_is_not_native_seam_curvature"
        ] = False
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT")
        self.assertTrue(any("raw second derivative" in error for error in result["errors"]))

    def test_framework_pin_change_fails_closed(self) -> None:
        contract = load_contract()
        contract["framework_source_pins"]["commit"] = "0" * 40
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT")
        self.assertTrue(any("framework commit" in error for error in result["errors"]))

    def test_universal_TN_cannot_be_enabled(self) -> None:
        contract = load_contract()
        contract["physical_state_contract"]["universal_TN_K_forbidden"] = False
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT")
        self.assertTrue(any("universal_TN" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
