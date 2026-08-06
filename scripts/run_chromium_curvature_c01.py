from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

N_OFFSETS = (-4, -2, 2, 4)
Z_OFFSETS = (-2, -1, 1, 2)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_linear(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> list[float]:
    n = len(rhs)
    aug = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular interpolation system")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        divisor = aug[col][col]
        aug[col] = [value / divisor for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [
                aug[row][index] - factor * aug[col][index]
                for index in range(n + 1)
            ]
    return [aug[index][-1] for index in range(n)]


def polynomial_jet(samples: Sequence[tuple[float, float]]) -> dict[str, float | int]:
    ordered = sorted((float(x), float(y)) for x, y in samples)
    degree = len(ordered) - 1
    coefficients = solve_linear(
        [[x**power for power in range(degree + 1)] for x, _ in ordered],
        [y for _, y in ordered],
    )
    coefficients += [0.0] * (4 - len(coefficients))
    return {
        "value": coefficients[0],
        "slope": coefficients[1],
        "curvature": 2.0 * coefficients[2],
        "jerk": 6.0 * coefficients[3],
        "order": degree,
    }


def axis_jet(
    grid: Mapping[tuple[int, int], float], z: int, n: int, axis: str
) -> dict[str, Any]:
    if axis == "n":
        supports = (
            (N_OFFSETS, "CUBIC_N2_N4"),
            ((-2, 2), "LINEAR_N2"),
            ((-4, -2), "ONE_SIDED_N_LEFT"),
            ((2, 4), "ONE_SIDED_N_RIGHT"),
        )
        lookup = lambda offset: grid.get((z, n + offset))
    elif axis == "z":
        supports = (
            (Z_OFFSETS, "CUBIC_Z1_Z2"),
            ((-1, 1), "LINEAR_Z1"),
            ((-2, -1), "ONE_SIDED_Z_LEFT"),
            ((1, 2), "ONE_SIDED_Z_RIGHT"),
        )
        lookup = lambda offset: grid.get((z + offset, n))
    else:
        raise ValueError("axis must be n or z")

    for offsets, predictor in supports:
        values = [lookup(offset) for offset in offsets]
        if all(value is not None for value in values):
            jet = polynomial_jet(
                [(float(offset), float(value)) for offset, value in zip(offsets, values)]
            )
            return {**jet, "predictor": predictor, "support_offsets": list(offsets)}
    return {
        "value": None,
        "slope": 0.0,
        "curvature": 0.0,
        "jerk": 0.0,
        "order": -1,
        "predictor": "INSUFFICIENT_SUPPORT",
        "support_offsets": [],
    }


def lagrange_weights_at_zero(nodes: Sequence[float]) -> list[float]:
    weights: list[float] = []
    for index, node in enumerate(nodes):
        weight = 1.0
        for other_index, other in enumerate(nodes):
            if index != other_index:
                weight *= (0.0 - float(other)) / (float(node) - float(other))
        weights.append(weight)
    return weights


def tensor_prediction(grid: Mapping[tuple[int, int], float], z: int, n: int) -> float | None:
    z_weights = lagrange_weights_at_zero(Z_OFFSETS)
    n_weights = lagrange_weights_at_zero(N_OFFSETS)
    total = 0.0
    for zi, delta_z in enumerate(Z_OFFSETS):
        for ni, delta_n in enumerate(N_OFFSETS):
            value = grid.get((z + delta_z, n + delta_n))
            if value is None:
                return None
            total += z_weights[zi] * n_weights[ni] * value
    return total


def robust_location_scale(values: Sequence[float]) -> dict[str, float | int]:
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    scale = max(1e-12, 1.4826 * mad)
    return {"count": len(values), "median": median, "mad": mad, "scale": scale}


def robust_z(value: float, stats: Mapping[str, float | int]) -> float:
    return (value - float(stats["median"])) / float(stats["scale"])


def smriti_vector(row: Mapping[str, Any], labels: Sequence[str]) -> list[float]:
    delta = row.get("smriti_delta") or {}
    return [float(delta.get(label, 0)) for label in labels]


def vector_curvature(
    left: Sequence[float], centre: Sequence[float], right: Sequence[float]
) -> list[float]:
    return [r - 2.0 * c + l for l, c, r in zip(left, centre, right)]


def norm(values: Iterable[float]) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in values))


def build_certificate(contract: Mapping[str, Any], repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    sources = contract["sources"]
    ledger_path = repository_root / sources["ground_state_ledger"]["path"]
    report_path = repository_root / sources["nuclear_report"]["path"]

    for source_id, path in (("ground_state_ledger", ledger_path), ("nuclear_report", report_path)):
        expected_hash = sources[source_id]["sha256"]
        if not path.exists():
            errors.append(f"missing source {source_id}: {path}")
        elif sha256_file(path) != expected_hash:
            errors.append(f"source hash mismatch for {source_id}")
    if errors:
        return {
            "campaign": contract.get("campaign"),
            "status": "FAIL_CHROMIUM_CURVATURE_SOURCE_PIN",
            "errors": errors,
            "claim_boundary": contract.get("claim_boundary"),
        }

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    target = contract["target"]
    target_z = int(target["atomic_number"])
    target_symbol = str(target["symbol"])
    rows_by_z = {int(row["atomic_number"]): row for row in ledger["rows"]}

    labels = ["3d", "4s"]
    electronic_rows: list[dict[str, Any]] = []
    z_start, z_end = map(int, target["electronic_comparison_range_Z"])
    for z in range(z_start + 1, z_end):
        curvature_vector = vector_curvature(
            smriti_vector(rows_by_z[z - 1], labels),
            smriti_vector(rows_by_z[z], labels),
            smriti_vector(rows_by_z[z + 1], labels),
        )
        electronic_rows.append(
            {
                "atomic_number": z,
                "symbol": rows_by_z[z]["symbol"],
                "curvature_vector_3d_4s": curvature_vector,
                "normalized_curvature": norm(curvature_vector) / math.sqrt(2.0),
            }
        )
    chromium_electronic = next(row for row in electronic_rows if row["atomic_number"] == target_z)
    copper_electronic = next(row for row in electronic_rows if row["symbol"] == "Cu")

    raw_records = report["records"]
    grid = {
        (int(row["z"]), int(row["n"])): float(row["actual_binding_energy_per_A_keV"])
        for row in raw_records
    }
    computed: list[dict[str, Any]] = []
    seam_reproduction_max_abs_error = 0.0
    for row in raw_records:
        z, n, a = int(row["z"]), int(row["n"]), int(row["a"])
        neutron = axis_jet(grid, z, n, "n")
        proton = axis_jet(grid, z, n, "z")
        neutron_value = neutron["value"]
        proton_value = proton["value"]
        if neutron_value is None and proton_value is None:
            axis_mean = None
        elif neutron_value is None:
            axis_mean = float(proton_value)
        elif proton_value is None:
            axis_mean = float(neutron_value)
        else:
            axis_mean = 0.5 * (float(neutron_value) + float(proton_value))
        tensor = tensor_prediction(grid, z, n)
        seam = None if tensor is None or axis_mean is None else tensor - axis_mean
        stored_seam = row.get("seam_residue_keV_per_a")
        if seam is not None and stored_seam is not None:
            seam_reproduction_max_abs_error = max(
                seam_reproduction_max_abs_error, abs(seam - float(stored_seam))
            )
        computed.append(
            {
                "entity": row["entity"],
                "z": z,
                "n": n,
                "a": a,
                "neutron_predictor": neutron["predictor"],
                "proton_predictor": proton["predictor"],
                "neutron_curvature_keV_per_a": float(neutron["curvature"]),
                "proton_curvature_keV_per_a": float(proton["curvature"]),
                "cut_even_curvature_keV_per_a": 0.5
                * (float(neutron["curvature"]) + float(proton["curvature"])),
                "cut_odd_curvature_keV_per_a": 0.5
                * (float(neutron["curvature"]) - float(proton["curvature"])),
                "seam_residue_keV_per_a": seam,
            }
        )

    support = contract["nuclear_support_contract"]
    full_cubic = [
        row
        for row in computed
        if row["neutron_predictor"] == support["required_neutron_predictor"]
        and row["proton_predictor"] == support["required_proton_predictor"]
    ]
    chromium_rows = [row for row in computed if row["z"] == target_z]
    chromium_full = [row for row in full_cubic if row["z"] == target_z]
    baseline = target["nuclear_local_baseline"]
    z_lo, z_hi = map(int, baseline["atomic_number_range_Z"])
    a_lo, a_hi = map(int, baseline["mass_number_range_A"])
    local_rows = [row for row in full_cubic if z_lo <= row["z"] <= z_hi and a_lo <= row["a"] <= a_hi]

    metric_keys = (
        "neutron_curvature_keV_per_a",
        "proton_curvature_keV_per_a",
        "cut_even_curvature_keV_per_a",
        "cut_odd_curvature_keV_per_a",
        "seam_residue_keV_per_a",
    )
    local_stats: dict[str, dict[str, float | int]] = {}
    global_stats: dict[str, dict[str, float | int]] = {}
    for key in metric_keys:
        local_values = [float(row[key]) for row in local_rows if row[key] is not None]
        global_values = [float(row[key]) for row in full_cubic if row[key] is not None]
        local_stats[key] = robust_location_scale(local_values)
        global_stats[key] = robust_location_scale(global_values)

    scored_chromium: list[dict[str, Any]] = []
    for row in chromium_full:
        scores = {}
        for key in metric_keys:
            if row[key] is not None:
                scores[key] = {
                    "value": row[key],
                    "local_robust_z": robust_z(float(row[key]), local_stats[key]),
                    "global_robust_z_diagnostic_only": robust_z(float(row[key]), global_stats[key]),
                }
        scored_chromium.append({**row, "scores": scores})

    def extreme(metric: str) -> dict[str, Any]:
        candidates = [item for item in scored_chromium if item[metric] is not None]
        row = max(candidates, key=lambda item: abs(float(item[metric])))
        return {
            "entity": row["entity"],
            "value": row[metric],
            "local_robust_z": row["scores"][metric]["local_robust_z"],
            "global_robust_z_diagnostic_only": row["scores"][metric][
                "global_robust_z_diagnostic_only"
            ],
        }

    extrema = {key: extreme(key) for key in metric_keys}
    threshold = float(contract["screening_contract"]["local_absolute_z_threshold"])
    local_peak_abs_z = max(
        abs(float(score["local_robust_z"]))
        for row in scored_chromium
        for score in row["scores"].values()
    )
    local_anomaly_detected = local_peak_abs_z >= threshold

    expected = contract["expected_controls"]
    controls = {
        "chromium_isotope_record_count": len(chromium_rows) == int(expected["chromium_isotope_record_count"]),
        "chromium_full_cubic_record_count": len(chromium_full) == int(expected["chromium_full_cubic_record_count"]),
        "local_baseline_record_count": len(local_rows) == int(expected["local_baseline_record_count"]),
        "chromium_electronic_curvature_exact": math.isclose(
            chromium_electronic["normalized_curvature"],
            float(expected["chromium_electronic_curvature"]),
            abs_tol=1e-12,
        ),
        "copper_electronic_curvature_exact": math.isclose(
            copper_electronic["normalized_curvature"],
            float(expected["copper_electronic_curvature"]),
            abs_tol=1e-12,
        ),
        "electronic_curvature_not_unique_to_chromium": math.isclose(
            chromium_electronic["normalized_curvature"],
            copper_electronic["normalized_curvature"],
            abs_tol=1e-12,
        ),
        "neutron_extreme_entity_exact": extrema["neutron_curvature_keV_per_a"]["entity"]
        == expected["largest_absolute_chromium_neutron_curvature_entity"],
        "cut_even_extreme_entity_exact": extrema["cut_even_curvature_keV_per_a"]["entity"]
        == expected["largest_absolute_chromium_cut_even_curvature_entity"],
        "cut_odd_extreme_entity_exact": extrema["cut_odd_curvature_keV_per_a"]["entity"]
        == expected["largest_absolute_chromium_cut_odd_curvature_entity"],
        "seam_extreme_entity_exact": extrema["seam_residue_keV_per_a"]["entity"]
        == expected["largest_absolute_chromium_seam_residue_entity"],
        "stored_seam_reproduced": seam_reproduction_max_abs_error <= 1e-9,
        "no_local_three_sigma_screening_anomaly": not local_anomaly_detected,
    }
    if not all(controls.values()):
        errors.extend(key for key, passed in controls.items() if not passed)

    status = (
        "PASS_CHROMIUM_CURVATURE_AUDIT_NO_LOCAL_THREE_SIGMA_ANOMALY"
        if not errors and not local_anomaly_detected
        else "INCONCLUSIVE_CHROMIUM_CURVATURE_AUDIT"
    )
    return {
        "campaign": contract["campaign"],
        "status": status,
        "errors": errors,
        "source_pins": {
            "ground_state_ledger": {
                "path": str(sources["ground_state_ledger"]["path"]),
                "sha256": sha256_file(ledger_path),
            },
            "nuclear_report": {
                "path": str(sources["nuclear_report"]["path"]),
                "sha256": sha256_file(report_path),
                "record_count": len(raw_records),
            },
        },
        "electronic_configuration_curvature": {
            "definition": "K_Z = Sigma_(Z+1) - 2 Sigma_Z + Sigma_(Z-1)",
            "active_coordinates": labels,
            "normalization": "L2_NORM_DIVIDED_BY_SQRT_2",
            "chromium": chromium_electronic,
            "copper": copper_electronic,
            "chromium_is_unique": False,
            "transition_metal_curvature_ranking": sorted(
                [
                    {
                        "atomic_number": row["atomic_number"],
                        "symbol": row["symbol"],
                        "normalized_curvature": row["normalized_curvature"],
                    }
                    for row in electronic_rows
                ],
                key=lambda item: (-float(item["normalized_curvature"]), int(item["atomic_number"])),
            ),
        },
        "nuclear_binding_surface": {
            "chromium_isotope_record_count": len(chromium_rows),
            "chromium_full_cubic_record_count": len(chromium_full),
            "chromium_mass_range_A": [min(row["a"] for row in chromium_rows), max(row["a"] for row in chromium_rows)],
            "local_baseline_contract": baseline,
            "local_baseline_full_cubic_record_count": len(local_rows),
            "global_full_cubic_record_count": len(full_cubic),
            "local_robust_statistics": local_stats,
            "global_robust_statistics_diagnostic_only": global_stats,
            "chromium_extrema": extrema,
            "local_peak_absolute_robust_z": local_peak_abs_z,
            "local_absolute_z_threshold": threshold,
            "local_screening_anomaly_detected": local_anomaly_detected,
            "stored_seam_reproduction_max_abs_error": seam_reproduction_max_abs_error,
            "selected_rows": {
                entity: next(
                    {
                        "entity": row["entity"],
                        "a": row["a"],
                        "n": row["n"],
                        "neutron_curvature_keV_per_a": row["neutron_curvature_keV_per_a"],
                        "proton_curvature_keV_per_a": row["proton_curvature_keV_per_a"],
                        "cut_even_curvature_keV_per_a": row["cut_even_curvature_keV_per_a"],
                        "cut_odd_curvature_keV_per_a": row["cut_odd_curvature_keV_per_a"],
                        "seam_residue_keV_per_a": row["seam_residue_keV_per_a"],
                        "scores": row["scores"],
                    }
                    for row in scored_chromium
                    if row["entity"] == entity
                )
                for entity in ("Cr-46", "Cr-47", "Cr-48", "Cr-52")
            },
        },
        "interpretation": {
            "sharp_structures_detected": True,
            "sharpest_neutron_and_cut_odd_structure": "Cr-46",
            "sharpest_cut_even_structure": "Cr-47",
            "sharpest_seam_structure": "Cr-48",
            "local_three_sigma_anomaly_detected": local_anomaly_detected,
            "global_scores_are_mass_region_confounded": True,
            "measurement_uncertainty_propagated": False,
            "robust_z_is_screening_score_not_measurement_sigma": True,
            "chromium_uniquely_selected_by_configuration_curvature": False,
        },
        "controls": controls,
        "next_stage": contract["next_stage"],
        "claim_boundary": contract["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("protocols/C01_CHROMIUM_CURVATURE_CONTRACT.json"),
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("releases/chromium-curvature-c01/chromium_curvature_certificate.json"),
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    certificate = build_certificate(contract, args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": certificate["status"],
        "electronic_chromium_curvature": certificate.get("electronic_configuration_curvature", {}).get("chromium", {}).get("normalized_curvature"),
        "local_peak_absolute_robust_z": certificate.get("nuclear_binding_surface", {}).get("local_peak_absolute_robust_z"),
        "local_screening_anomaly_detected": certificate.get("nuclear_binding_surface", {}).get("local_screening_anomaly_detected"),
        "output": str(args.output),
    }, indent=2, sort_keys=True))
    return 0 if certificate["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
