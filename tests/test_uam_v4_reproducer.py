import unittest

from src.uam_v4_reproducer import _blend_record, build_report


def row(z: int, n: int, binding: float) -> dict:
    return {
        "Z": z,
        "N": n,
        "A": z + n,
        "Symbol": f"E{z}",
        "binding_energy_per_A_keV": binding,
    }


class UAMV4ReproducerTests(unittest.TestCase):
    def test_cubic_surface_is_recovered(self) -> None:
        rows = [
            row(z, n, float(z**3 + n**3 + 2 * z + 3 * n + 1000))
            for z in range(2, 10)
            for n in range(2, 14)
        ]
        report = build_report(rows, "in-memory")
        target = next(r for r in report["records"] if r["z"] == 5 and r["n"] == 7)
        self.assertAlmostEqual(target["n_prediction_keV_per_a"], target["actual_binding_energy_per_A_keV"])
        self.assertAlmostEqual(target["z_prediction_keV_per_a"], target["actual_binding_energy_per_A_keV"])

    def test_target_value_does_not_enter_axis_predictions(self) -> None:
        rows = [row(z, n, float(z**2 + n**2 + 1000)) for z in range(2, 9) for n in range(2, 12)]
        changed = [dict(item) for item in rows]
        for item in changed:
            if item["Z"] == 5 and item["N"] == 7:
                item["binding_energy_per_A_keV"] = 999999.0
        first = build_report(rows, "in-memory")
        second = build_report(changed, "in-memory")
        a = next(r for r in first["records"] if r["z"] == 5 and r["n"] == 7)
        b = next(r for r in second["records"] if r["z"] == 5 and r["n"] == 7)
        self.assertEqual(a["n_prediction_keV_per_a"], b["n_prediction_keV_per_a"])
        self.assertEqual(a["z_prediction_keV_per_a"], b["z_prediction_keV_per_a"])

    def test_ultralight_abstention(self) -> None:
        record = {
            "a": 6,
            "mass_region": "LIGHT_A_LT_40",
            "n_prediction_keV_per_a": 10.0,
            "z_prediction_keV_per_a": 11.0,
            "n_predictor": "SAME_PARITY_CUBIC_N2_N4",
            "z_predictor": "CROSS_ELEMENT_CUBIC_Z1_Z2",
        }
        calibration = {
            "SAME_PARITY_CUBIC_N2_N4|LIGHT_A_LT_40": {"sample_count": 100, "robust_sigma_keV_per_a": 2.0},
            "CROSS_ELEMENT_CUBIC_Z1_Z2|LIGHT_A_LT_40": {"sample_count": 100, "robust_sigma_keV_per_a": 2.0},
        }
        result = _blend_record(record, calibration, calibration, 3.0)
        self.assertEqual(result["guard_decision"], "ABSTAIN")
        self.assertIn("ULTRALIGHT_A_LT_8", result["guard_reasons"])

    def test_report_hash_is_deterministic(self) -> None:
        rows = [row(z, n, float(z + n + 1000)) for z in range(2, 8) for n in range(2, 10)]
        self.assertEqual(build_report(rows, "in-memory")["report_hash"], build_report(rows, "in-memory")["report_hash"])


if __name__ == "__main__":
    unittest.main()
