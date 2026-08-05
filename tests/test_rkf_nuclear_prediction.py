import copy
import unittest

from src.rkf_nuclear_prediction import (
    apply_decoder,
    build_observer_records,
    cross_fitted_predictions,
    fit_minimum_burden_decoder,
    polynomial_jet,
    tensor_cubic_prediction,
)


def row(z: int, n: int, binding: float) -> dict:
    return {
        "Z": z,
        "N": n,
        "A": z + n,
        "Symbol": f"E{z}",
        "binding_energy_per_A_keV": binding,
    }


class RKFNuclearPredictionTests(unittest.TestCase):
    def test_cubic_jet_recovers_derivatives(self) -> None:
        def polynomial(x: float) -> float:
            return 7.0 + 3.0 * x + 2.0 * x * x + x**3

        jet = polynomial_jet([(x, polynomial(x)) for x in (-4, -2, 2, 4)])
        self.assertAlmostEqual(jet["value"], 7.0)
        self.assertAlmostEqual(jet["slope"], 3.0)
        self.assertAlmostEqual(jet["curvature"], 4.0)
        self.assertAlmostEqual(jet["jerk"], 6.0)

    def test_tensor_cubic_recovers_bivariate_surface(self) -> None:
        grid = {}
        target_z, target_n = 10, 20
        for z in range(7, 14):
            for n in range(15, 26):
                value = (
                    1000.0
                    + 3.0 * z
                    + 2.0 * n
                    + 0.1 * z * n
                    + 0.05 * z**2
                    + 0.02 * n**2
                    + 0.001 * z**3
                    - 0.0002 * n**3
                )
                grid[(z, n)] = row(z, n, value)
        expected = grid[(target_z, target_n)]["binding_energy_per_A_keV"]
        self.assertAlmostEqual(tensor_cubic_prediction(grid, target_z, target_n), expected)

    def test_target_value_does_not_enter_observer(self) -> None:
        rows = [
            row(z, n, float(1000 + z**2 + n**2 + 0.1 * z * n))
            for z in range(4, 14)
            for n in range(8, 28)
        ]
        changed = copy.deepcopy(rows)
        for item in changed:
            if item["Z"] == 9 and item["N"] == 18:
                item["binding_energy_per_A_keV"] = 999999.0
        first = {
            (item["z"], item["n"]): item for item in build_observer_records(rows)
        }[(9, 18)]
        second = {
            (item["z"], item["n"]): item for item in build_observer_records(changed)
        }[(9, 18)]
        for key in (
            "axis_mean_prediction_keV_per_a",
            "tensor_cubic_prediction_keV_per_a",
            "seam_residue_keV_per_a",
            "cut_even_jet",
            "cut_odd_jet",
        ):
            self.assertEqual(first[key], second[key])

    def test_cut_even_odd_reconstruct_axis_jets(self) -> None:
        rows = [
            row(z, n, float(1000 + 2 * z + 3 * n + 0.2 * z * n))
            for z in range(4, 14)
            for n in range(8, 28)
        ]
        record = {
            (item["z"], item["n"]): item for item in build_observer_records(rows)
        }[(9, 18)]
        for key in ("value", "slope", "curvature", "jerk"):
            even = record["cut_even_jet"][key]
            odd = record["cut_odd_jet"][key]
            self.assertAlmostEqual(even + odd, record["neutron_jet"][key])
            self.assertAlmostEqual(even - odd, record["proton_jet"][key])

    def test_decoder_recovers_declared_residual_law(self) -> None:
        records = []
        for z in range(4, 12):
            for n in range(8, 20):
                base = 7000.0 + 2.0 * z + 3.0 * n
                odd = float(n - z)
                asymmetry = (n - z) / (n + z)
                correction = 1.5 * odd + 20.0 * asymmetry
                records.append(
                    {
                        "entity": f"E{z}-{z+n}",
                        "z": z,
                        "n": n,
                        "a": z + n,
                        "actual_binding_energy_per_A_keV": base + correction,
                        "axis_mean_prediction_keV_per_a": base,
                        "tensor_cubic_prediction_keV_per_a": None,
                        "seam_residue_keV_per_a": None,
                        "cut_even_jet": {"value": base, "slope": 0.0, "curvature": 0.0, "jerk": 0.0},
                        "cut_odd_jet": {"value": odd, "slope": 0.0, "curvature": 0.0, "jerk": 0.0},
                        "asymmetry": asymmetry,
                        "surface_coordinate": (z + n) ** (-1.0 / 3.0),
                        "coulomb_coordinate": z * (z - 1) / ((z + n) ** (4.0 / 3.0)),
                        "pairing_coordinate": 0.0,
                        "n_magic_distance": 1,
                        "z_magic_distance": 1,
                        "neutron_jet": {"order": 3},
                        "proton_jet": {"order": 3},
                    }
                )
        model = fit_minimum_burden_decoder(records, level=1, ridge=1e-9)
        applied = apply_decoder(model, records[10])
        self.assertIsNotNone(applied)
        self.assertAlmostEqual(
            applied["prediction_keV_per_a"],
            records[10]["actual_binding_energy_per_A_keV"],
            places=5,
        )

    def test_cross_fit_excludes_held_out_element(self) -> None:
        rows = [
            row(z, n, float(1000 + z**2 + n**2 + 0.1 * z * n))
            for z in range(4, 14)
            for n in range(8, 28)
        ]
        records = build_observer_records(rows)
        predictions = cross_fitted_predictions(records, level=1, ridge=1.0)
        self.assertEqual(len(predictions), len(records))
        self.assertTrue(all(item["held_out_z"] == item["z"] for item in predictions))


if __name__ == "__main__":
    unittest.main()
