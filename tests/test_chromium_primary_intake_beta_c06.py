from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALID_HASH_A = "a" * 64
VALID_HASH_B = "b" * 64
VALID_HASH_C = "c" * 64
VALID_HASH_D = "d" * 64
VALID_HASH_E = "e" * 64


def load_module():
    script = ROOT / "scripts" / "run_chromium_primary_intake_beta_c06.py"
    spec = importlib.util.spec_from_file_location("chromium_c06", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict:
    return json.loads(
        (
            ROOT
            / "protocols"
            / "C06_CHROMIUM_PRIMARY_INTAKE_BETA_INTERVAL.json"
        ).read_text(encoding="utf-8")
    )


def load_packet() -> dict:
    return json.loads(
        (
            ROOT
            / "data"
            / "manifests"
            / "C06_CHROMIUM_RESPONSE_PACKET.json"
        ).read_text(encoding="utf-8")
    )


def complete_packet() -> dict:
    packet = load_packet()
    packet["provenance"]["files"] = [
        {
            "original_filename": "chromium_primary_arrays.csv",
            "sha256": VALID_HASH_A,
            "byte_count": 4096,
            "source_route_id": "AUTHOR_DIRECT",
            "date_received": "2026-08-06",
            "rights_or_access_note": "Personal scholarly analysis copy",
            "media_type": "text/csv",
            "retained_location": "private-intake/chromium_primary_arrays.csv",
        }
    ]
    packet["sample_state"].update(
        {
            "sample_state_id": "SALAMON_1969_SPECIMEN_A",
            "same_specimen": True,
            "same_protocol": True,
        }
    )
    packet["transition_coordinate"].update(
        {
            "source_specific_tn": True,
            "universal_tn_used": False,
            "tn_K": "3114/10",
            "tn_uncertainty_K": "1/10",
            "tn_determination_rule": "predeclared simultaneous-channel centre",
        }
    )
    packet["bilateral_pairing"].update(
        {
            "both_sides_present": True,
            "accepted_pair_count": 12,
            "max_abs_tau_pair_mismatch": "1/10000",
            "tau_pair_tolerance": "1/1000",
            "pair_table_sha256": VALID_HASH_B,
        }
    )
    packet["channels"]["base"][0].update(
        {"array_sha256": VALID_HASH_C, "point_count": 40, "unit": "J mol^-1 K^-1"}
    )
    packet["channels"]["base"][1].update(
        {"array_sha256": VALID_HASH_D, "point_count": 40, "unit": "ohm m K^-1"}
    )
    packet["preprocessing"].update(
        {
            "baseline_rule_frozen_before_fit": True,
            "baseline_rule": "two-sided affine background outside the frozen core",
            "derivative_rule_frozen_before_fit": True,
            "derivative_rule": "symmetric local polynomial with fixed width",
            "target_selected_after_seeing_data": False,
        }
    )
    packet["metric"].update(
        {
            "covariance_source": "shared simultaneous-channel calibration covariance",
            "positive_support_certified": True,
            "whitening_applied": True,
            "whitened_observer_sha256": VALID_HASH_E,
        }
    )
    packet["observer"].update(
        {
            "tower_depth": 1,
            "visible_quotient_certified": True,
            "visible_basis_sha256": VALID_HASH_B,
            "target_visible": True,
        }
    )
    packet["target"].update(
        {
            "target_definition": "predeclared simultaneous Neel boundary row",
            "frozen_before_fit": True,
            "post_hoc_peak_target": False,
            "formula_sha256": VALID_HASH_C,
        }
    )
    packet["certified_bounds"].update(
        {
            "target_norm_lower": "1/2",
            "target_norm_upper": "1/2",
            "observer_norm_upper": "1",
            "visible_singular_lower": "1",
            "bilateral_defect_upper": "0",
            "bilateral_defect_tolerance": "0",
        }
    )
    return packet


class ChromiumPrimaryIntakeBetaC06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = load_contract()

    def test_empty_packet_is_fail_closed_data_required(self) -> None:
        result = self.module.audit(self.contract, load_packet(), ROOT)
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C06_ENGINE_FROZEN_PRIMARY_DATA_REQUIRED",
        )
        self.assertEqual(result["intake_file_count"], 0)
        self.assertFalse(result["readiness"]["ready_for_beta"])
        self.assertEqual(result["physical_classification"], "DATA_REQUIRED")

    def test_conservative_interval_formula(self) -> None:
        lower, upper = self.module.beta_interval_from_bounds(
            {
                "target_norm_lower": "1/2",
                "target_norm_upper": "3/4",
                "observer_norm_upper": "2",
                "visible_singular_lower": "1/2",
            }
        )
        self.assertEqual(lower, Fraction(1, 16))
        self.assertEqual(upper, Fraction(9, 4))

    def test_all_synthetic_classifications_are_frozen(self) -> None:
        controls = self.module.run_synthetic_controls(
            self.contract["synthetic_controls"]
        )
        for result in controls.values():
            self.assertEqual(
                result["classification"], result["expected_classification"]
            )

    def test_complete_packet_computes_strict_interval(self) -> None:
        result = self.module.audit(self.contract, complete_packet(), ROOT)
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C06_PHYSICAL_BETA_INTERVAL_COMPUTED",
        )
        self.assertTrue(result["readiness"]["ready_for_beta"])
        self.assertEqual(
            result["beta_interval"]["lower"],
            {"numerator": 1, "denominator": 4},
        )
        self.assertEqual(result["physical_classification"], "STRICT_NEEL_CUT_CLOSURE")

    def test_universal_tn_is_rejected(self) -> None:
        packet = complete_packet()
        packet["transition_coordinate"]["universal_tn_used"] = True
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT",
        )
        self.assertTrue(any("universal TN" in error for error in result["errors"]))

    def test_post_hoc_target_is_rejected(self) -> None:
        packet = complete_packet()
        packet["preprocessing"]["target_selected_after_seeing_data"] = True
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT",
        )
        self.assertTrue(any("post-hoc" in error for error in result["errors"]))

    def test_invalid_intake_hash_is_rejected(self) -> None:
        packet = complete_packet()
        packet["provenance"]["files"][0]["sha256"] = "not-a-hash"
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT",
        )
        self.assertTrue(any("sha256" in error for error in result["errors"]))

    def test_duplicate_intake_hashes_are_rejected(self) -> None:
        packet = complete_packet()
        duplicate = copy.deepcopy(packet["provenance"]["files"][0])
        duplicate["original_filename"] = "duplicate.csv"
        packet["provenance"]["files"].append(duplicate)
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT",
        )
        self.assertTrue(any("unique" in error for error in result["errors"]))

    def test_insufficient_pairing_keeps_beta_blocked(self) -> None:
        packet = complete_packet()
        packet["bilateral_pairing"]["accepted_pair_count"] = 7
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C06_ENGINE_FROZEN_PRIMARY_DATA_REQUIRED",
        )
        self.assertFalse(result["readiness"]["pairing_ready"])

    def test_open_seam_precedes_beta_classification(self) -> None:
        packet = complete_packet()
        packet["certified_bounds"]["bilateral_defect_upper"] = "1/10"
        packet["certified_bounds"]["bilateral_defect_tolerance"] = "1/100"
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(result["physical_classification"], "OPEN_SEAM_OR_WRONG_CUT")

    def test_invalid_singular_lower_bound_fails_closed(self) -> None:
        packet = complete_packet()
        packet["certified_bounds"]["visible_singular_lower"] = "0"
        result = self.module.audit(self.contract, packet, ROOT)
        self.assertEqual(
            result["status"],
            "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT",
        )
        self.assertTrue(any("singular" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
