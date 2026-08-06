from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module():
    script = ROOT / "scripts" / "run_chromium_cp_resistivity_c03.py"
    spec = importlib.util.spec_from_file_location("chromium_c03", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict:
    path = ROOT / "protocols" / "C03_CHROMIUM_SIMULTANEOUS_CP_RESISTIVITY_DIGITIZATION.json"
    return json.loads(path.read_text(encoding="utf-8"))


class ChromiumCpResistivityC03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_current_contract_passes_acquisition_audit_but_blocks_digitization(self) -> None:
        result = self.module.audit(load_contract())
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C03_ACQUISITION_AUDIT_DIGITIZATION_BLOCKED",
        )
        self.assertTrue(result["source_metadata_verified"])
        self.assertFalse(result["digitization_ready"])
        self.assertFalse(result["curvature_allowed"])

    def test_same_specimen_channel_pair_is_frozen(self) -> None:
        result = self.module.audit(load_contract())
        self.assertTrue(result["same_specimen"])
        self.assertTrue(result["simultaneous_measurement"])
        self.assertTrue(result["common_temperature_calibration"])
        self.assertEqual(
            result["channels"],
            ["heat_capacity_Cp", "resistivity_temperature_coefficient_drho_dT"],
        )

    def test_modulation_branch_cannot_be_relabelled_as_heating_branch(self) -> None:
        contract = load_contract()
        contract["source_supported_experiment"]["thermal_branch_semantics"] = "HEATING"
        result = self.module.audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT")
        self.assertTrue(any("modulation branch" in error for error in result["errors"]))

    def test_abstract_cannot_supply_numeric_exponents(self) -> None:
        contract = load_contract()
        contract["source_supported_experiment"][
            "numeric_critical_exponents_available_from_verified_abstract"
        ] = True
        result = self.module.audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT")
        self.assertTrue(any("numeric critical exponents" in error for error in result["errors"]))

    def test_secondary_figure_proxy_is_forbidden(self) -> None:
        contract = load_contract()
        contract["acquisition_audit"][
            "secondary_thesis_or_review_may_be_used_as_primary_figure_proxy"
        ] = True
        result = self.module.audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT")
        self.assertTrue(any("secondary_thesis" in error for error in result["errors"]))

    def test_digitization_cannot_be_enabled_without_figure_axes_and_uncertainty(self) -> None:
        contract = load_contract()
        contract["current_digitization_state"]["digitization_allowed"] = True
        result = self.module.audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT")
        self.assertTrue(any("digitization cannot be allowed" in error for error in result["errors"]))

    def test_curvature_and_significance_remain_fail_closed(self) -> None:
        contract = load_contract()
        contract["current_digitization_state"]["derivative_or_curvature_allowed"] = True
        contract["current_digitization_state"]["anomaly_significance_allowed"] = True
        result = self.module.audit(contract)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT")
        self.assertTrue(any("curvature cannot be allowed" in error for error in result["errors"]))
        self.assertTrue(any("significance cannot be allowed" in error for error in result["errors"]))

    def test_primary_metadata_is_exact(self) -> None:
        result = self.module.audit(load_contract())
        self.assertEqual(result["primary_doi"], "10.1016/0038-1098(69)90464-5")
        self.assertEqual(result["primary_pii"], "0038109869904645")
        self.assertEqual(
            result["primary_authors"],
            ["M. B. Salamon", "D. S. Simons", "P. R. Garnier"],
        )
        self.assertEqual(result["primary_pages"], [1035, 1038])


if __name__ == "__main__":
    unittest.main()
