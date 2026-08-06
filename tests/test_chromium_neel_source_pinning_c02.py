from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def load_module():
    path = ROOT / "scripts" / "run_chromium_neel_source_pinning_c02.py"
    spec = importlib.util.spec_from_file_location("chromium_c02", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict:
    return json.loads(
        (ROOT / "protocols" / "C02_CHROMIUM_NEEL_SOURCE_PINNING.json").read_text(
            encoding="utf-8"
        )
    )


class ChromiumNeelSourcePinningC02Tests(unittest.TestCase):
    def test_current_contract_passes_source_pinning_only(self) -> None:
        result = load_module().audit(load_contract())
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_NEEL_SOURCE_PINNING_DATA_ACQUISITION_REQUIRED",
        )
        self.assertEqual(result["source_count"], 10)
        self.assertEqual(result["machine_readable_curve_source_count"], 0)
        self.assertFalse(result["four_channel_common_specimen_ready"])
        self.assertFalse(result["curvature_computed"])
        self.assertFalse(result["anomaly_significance_computed"])

    def test_primary_pair_remains_same_specimen_heat_and_resistivity(self) -> None:
        result = load_module().audit(load_contract())
        self.assertEqual(
            result["primary_same_specimen_source_id"],
            "SIMULTANEOUS_CP_DRHODT_1969",
        )
        self.assertEqual(
            result["primary_same_specimen_channels"],
            ["heat_capacity_Cp", "resistivity_temperature_coefficient_drho_dT"],
        )

    def test_311K_cannot_be_promoted_to_universal_coordinate(self) -> None:
        contract = load_contract()
        contract["target"]["nominal_reference_is_not_universal"] = False
        result = load_module().audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_NEEL_SOURCE_PINNING")
        self.assertTrue(any("non-universal" in error for error in result["errors"]))

    def test_branch_and_specimen_gates_cannot_be_removed(self) -> None:
        contract = load_contract()
        contract["qualification_contract"][
            "heating_cooling_or_modulation_branch_required"
        ] = False
        contract["qualification_contract"]["same_specimen_flag_required"] = False
        result = load_module().audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_NEEL_SOURCE_PINNING")
        self.assertGreaterEqual(len(result["errors"]), 2)

    def test_machine_readable_claim_fails_closed(self) -> None:
        contract = load_contract()
        contract["source_registry"][0]["curve_machine_readable_verified"] = True
        result = load_module().audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_NEEL_SOURCE_PINNING")
        self.assertTrue(any("machine-readable" in error for error in result["errors"]))

    def test_cross_paper_curvature_cannot_be_enabled(self) -> None:
        contract = load_contract()
        contract["admission_decision"]["cross_paper_curvature_allowed"] = True
        result = load_module().audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_NEEL_SOURCE_PINNING")
        self.assertTrue(any("cross-paper" in error for error in result["errors"]))

    def test_direct_latent_heat_scalar_is_frozen(self) -> None:
        result = load_module().audit(load_contract())
        self.assertEqual(
            result["direct_latent_heat_scalar"],
            {"value_cal_per_mol": 0.47, "uncertainty_cal_per_mol": 0.1},
        )
        self.assertEqual(result["first_order_witness_count"], 3)

    def test_missing_source_pin_fails_closed(self) -> None:
        contract = load_contract()
        contract["source_registry"] = contract["source_registry"][:-1]
        result = load_module().audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_NEEL_SOURCE_PINNING")
        self.assertTrue(any("missing source pins" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
