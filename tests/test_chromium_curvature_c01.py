from __future__ import annotations

import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def load_module():
    path = ROOT / "scripts" / "run_chromium_curvature_c01.py"
    spec = importlib.util.spec_from_file_location("chromium_c01", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChromiumCurvatureC01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = json.loads(
            (ROOT / "protocols" / "C01_CHROMIUM_CURVATURE_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        cls.certificate = cls.module.build_certificate(cls.contract, ROOT)

    def test_audit_passes_without_local_three_sigma_detection(self) -> None:
        self.assertEqual(
            self.certificate["status"],
            "PASS_CHROMIUM_CURVATURE_AUDIT_NO_LOCAL_THREE_SIGMA_ANOMALY",
        )
        self.assertFalse(
            self.certificate["nuclear_binding_surface"]["local_screening_anomaly_detected"]
        )

    def test_configuration_curvature_ties_chromium_and_copper(self) -> None:
        electronic = self.certificate["electronic_configuration_curvature"]
        self.assertTrue(math.isclose(electronic["chromium"]["normalized_curvature"], 2.0))
        self.assertTrue(math.isclose(electronic["copper"]["normalized_curvature"], 2.0))
        self.assertFalse(electronic["chromium_is_unique"])

    def test_chromium_chain_and_support_counts_are_frozen(self) -> None:
        nuclear = self.certificate["nuclear_binding_surface"]
        self.assertEqual(nuclear["chromium_isotope_record_count"], 30)
        self.assertEqual(nuclear["chromium_full_cubic_record_count"], 22)
        self.assertEqual(nuclear["local_baseline_full_cubic_record_count"], 185)

    def test_stored_seam_is_reproduced(self) -> None:
        error = self.certificate["nuclear_binding_surface"][
            "stored_seam_reproduction_max_abs_error"
        ]
        self.assertLessEqual(error, 1e-9)

    def test_chromium_extrema_are_frozen(self) -> None:
        extrema = self.certificate["nuclear_binding_surface"]["chromium_extrema"]
        self.assertEqual(extrema["neutron_curvature_keV_per_a"]["entity"], "Cr-46")
        self.assertEqual(extrema["cut_even_curvature_keV_per_a"]["entity"], "Cr-47")
        self.assertEqual(extrema["cut_odd_curvature_keV_per_a"]["entity"], "Cr-46")
        self.assertEqual(extrema["seam_residue_keV_per_a"]["entity"], "Cr-48")

    def test_global_score_is_not_used_as_detection_gate(self) -> None:
        neutron = self.certificate["nuclear_binding_surface"]["chromium_extrema"][
            "neutron_curvature_keV_per_a"
        ]
        self.assertGreater(abs(neutron["global_robust_z_diagnostic_only"]), 20.0)
        self.assertLess(abs(neutron["local_robust_z"]), 3.0)
        self.assertTrue(
            self.certificate["interpretation"]["global_scores_are_mass_region_confounded"]
        )

    def test_source_hash_change_fails_closed(self) -> None:
        contract = json.loads(json.dumps(self.contract))
        contract["sources"]["nuclear_report"]["sha256"] = "0" * 64
        certificate = self.module.build_certificate(contract, ROOT)
        self.assertEqual(certificate["status"], "FAIL_CHROMIUM_CURVATURE_SOURCE_PIN")


if __name__ == "__main__":
    unittest.main()
