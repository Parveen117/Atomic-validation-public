import unittest

from release.uam_halo_v10_1.src.uam_halo_v10_1 import analyze_rows, prediction_with_fallback


class UAMHaloV101Tests(unittest.TestCase):
    def row(self, z, n, binding, symbol="X", **extra):
        payload = {
            "Z": z,
            "N": n,
            "A": z + n,
            "Symbol": symbol,
            "binding_energy_per_A_keV": binding,
            "S_n_keV": 800.0,
            "S_2n_keV": 1600.0,
            "S_p_keV": 3000.0,
            "S_2p_keV": 6000.0,
        }
        payload.update(extra)
        return payload

    def test_cubic_predictor_is_preferred(self):
        by_n = {0: self.row(2, 0, 10.0), 2: self.row(2, 2, 20.0), 6: self.row(2, 6, 40.0), 8: self.row(2, 8, 50.0)}
        predicted, name, offsets = prediction_with_fallback(by_n, 4)
        self.assertEqual(name, "SAME_PARITY_CUBIC_N2_N4")
        self.assertEqual(offsets, [-4, -2, 2, 4])
        self.assertAlmostEqual(predicted, 30.0)

    def test_linear_and_one_sided_fallbacks(self):
        predicted, name, _ = prediction_with_fallback({2: self.row(2, 2, 20.0), 6: self.row(2, 6, 40.0)}, 4)
        self.assertEqual(name, "SAME_PARITY_LINEAR_N2")
        self.assertAlmostEqual(predicted, 30.0)
        predicted, name, _ = prediction_with_fallback({2: self.row(2, 2, 20.0), 4: self.row(2, 4, 30.0)}, 0)
        self.assertEqual(name, "ONE_SIDED_SAME_PARITY_RIGHT")
        self.assertAlmostEqual(predicted, 10.0)

    def test_insufficient_support_abstains(self):
        predicted, name, offsets = prediction_with_fallback({2: self.row(2, 2, 20.0)}, 4)
        self.assertIsNone(predicted)
        self.assertEqual(name, "INSUFFICIENT_SAME_PARITY_SUPPORT")
        self.assertEqual(offsets, [])

    def test_halo_label_does_not_change_prediction(self):
        rows = [self.row(2, n, 100.0 + n) for n in range(0, 10, 2)]
        without = analyze_rows(rows, halo_candidates=set())
        entity = without["records"][2]["entity"]
        labelled = analyze_rows(rows, halo_candidates={entity})
        first = next(row for row in without["records"] if row["entity"] == entity)
        second = next(row for row in labelled["records"] if row["entity"] == entity)
        self.assertEqual(first["predicted_binding_energy_per_A_keV"], second["predicted_binding_energy_per_A_keV"])

    def test_threshold_sensitivity(self):
        report = analyze_rows([self.row(2, 2, 100.0, S_n_keV=750.0, S_2n_keV=1500.0)], thresholds_keV=(500.0, 1000.0))
        record = report["records"][0]
        self.assertEqual(record["threshold_sweep"]["500"], "BOUND_AWAY_FROM_DECLARED_THRESHOLD")
        self.assertEqual(record["threshold_sweep"]["1000"], "NEAR_NEUTRON_DRIP_BOUNDARY")

    def test_matched_controls_exclude_halo_labels(self):
        rows = [self.row(z, n, 100.0 + z + n) for z in (2, 3) for n in range(0, 12, 2)]
        report = analyze_rows(rows, halo_candidates={"X-6"}, controls_per_halo=2)
        for match in report["matched_halo_controls"]:
            self.assertNotIn(match["halo_entity"], match["control_entities"])

    def test_report_hash_is_deterministic(self):
        rows = [self.row(2, n, 100.0 + n) for n in range(0, 12, 2)]
        self.assertEqual(analyze_rows(rows)["report_hash"], analyze_rows(rows)["report_hash"])


if __name__ == "__main__":
    unittest.main()
