from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from typing import Iterable, Mapping, Optional, Sequence

MAGIC_NUMBERS = (2, 8, 20, 28, 50, 82, 126)
N_CUBIC_OFFSETS = (-4, -2, 2, 4)
Z_CUBIC_OFFSETS = (-2, -1, 1, 2)
DEFAULT_RIDGE = 1.0
BURDEN_RETENTION_QUANTILE = 0.9875


def certificate_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite(row: Optional[Mapping[str, object]], key: str = "binding_energy_per_A_keV") -> Optional[float]:
    if row is None:
        return None
    value = row.get(key)
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _int_field(row: Mapping[str, object], key: str) -> int:
    value = row.get(key)
    if value in (None, ""):
        raise ValueError(f"missing {key}")
    return int(float(value))


def _entity(row: Mapping[str, object], z: int, a: int) -> str:
    for key in ("entity", "Entity", "nuclide", "Nuclide", "isotope", "Isotope"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    symbol = str(row.get("Symbol", row.get("symbol", ""))).strip()
    return f"{symbol}-{a}" if symbol else f"Z{z}-A{a}"


def _percentile(values: Sequence[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _solve_linear_system(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> list[float]:
    n = len(rhs)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square and match rhs")
    augmented = [list(map(float, matrix[index])) + [float(rhs[index])] for index in range(n)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular linear system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                augmented[row][index] - factor * augmented[column][index]
                for index in range(n + 1)
            ]
    return [augmented[index][-1] for index in range(n)]


def _invert_matrix(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    augmented = [
        list(map(float, matrix[row])) + [1.0 if row == column else 0.0 for column in range(n)]
        for row in range(n)
    ]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                augmented[row][index] - factor * augmented[column][index]
                for index in range(2 * n)
            ]
    return [row[n:] for row in augmented]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(float(a) * float(b) for a, b in zip(left, right))


def _matvec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    return [_dot(row, vector) for row in matrix]


def polynomial_jet(samples: Sequence[tuple[float, float]]) -> dict:
    """Recover value and first three derivative coefficients at the target cut x=0."""
    if len(samples) < 2 or len(samples) > 4:
        raise ValueError("jet requires between two and four samples")
    ordered = sorted((float(x), float(y)) for x, y in samples)
    if len({x for x, _ in ordered}) != len(ordered):
        raise ValueError("sample coordinates must be distinct")
    degree = len(ordered) - 1
    matrix = [[x**power for power in range(degree + 1)] for x, _ in ordered]
    coefficients = _solve_linear_system(matrix, [y for _, y in ordered])
    coefficients += [0.0] * (4 - len(coefficients))
    return {
        "value": coefficients[0],
        "slope": coefficients[1],
        "curvature": 2.0 * coefficients[2],
        "jerk": 6.0 * coefficients[3],
        "order": degree,
        "coefficients": coefficients[:4],
    }


def lagrange_weights_at_zero(nodes: Sequence[float]) -> list[float]:
    nodes = [float(node) for node in nodes]
    if len(set(nodes)) != len(nodes):
        raise ValueError("nodes must be distinct")
    weights = []
    for index, node in enumerate(nodes):
        weight = 1.0
        for other_index, other in enumerate(nodes):
            if index != other_index:
                weight *= (0.0 - other) / (node - other)
        weights.append(weight)
    return weights


def axis_jet(
    grid: Mapping[tuple[int, int], Mapping[str, object]],
    z: int,
    n: int,
    axis: str,
) -> dict:
    if axis == "n":
        supports = (
            (N_CUBIC_OFFSETS, "CUBIC_N2_N4"),
            ((-2, 2), "LINEAR_N2"),
            ((-4, -2), "ONE_SIDED_N_LEFT"),
            ((2, 4), "ONE_SIDED_N_RIGHT"),
        )

        def value(offset: int) -> Optional[float]:
            return _finite(grid.get((z, n + offset)))

    elif axis == "z":
        supports = (
            (Z_CUBIC_OFFSETS, "CUBIC_Z1_Z2"),
            ((-1, 1), "LINEAR_Z1"),
            ((-2, -1), "ONE_SIDED_Z_LEFT"),
            ((1, 2), "ONE_SIDED_Z_RIGHT"),
        )

        def value(offset: int) -> Optional[float]:
            return _finite(grid.get((z + offset, n)))

    else:
        raise ValueError("axis must be 'n' or 'z'")

    for offsets, predictor in supports:
        samples = [(offset, value(offset)) for offset in offsets]
        if all(sample is not None for _, sample in samples):
            jet = polynomial_jet([(offset, float(sample)) for offset, sample in samples])
            jet.update(
                {
                    "axis": axis,
                    "predictor": predictor,
                    "support_offsets": list(offsets),
                }
            )
            return jet
    return {
        "axis": axis,
        "predictor": "INSUFFICIENT_SUPPORT",
        "support_offsets": [],
        "value": None,
        "slope": 0.0,
        "curvature": 0.0,
        "jerk": 0.0,
        "order": -1,
        "coefficients": [0.0, 0.0, 0.0, 0.0],
    }


def tensor_cubic_prediction(
    grid: Mapping[tuple[int, int], Mapping[str, object]],
    z: int,
    n: int,
) -> Optional[float]:
    z_weights = lagrange_weights_at_zero(Z_CUBIC_OFFSETS)
    n_weights = lagrange_weights_at_zero(N_CUBIC_OFFSETS)
    total = 0.0
    for z_index, delta_z in enumerate(Z_CUBIC_OFFSETS):
        for n_index, delta_n in enumerate(N_CUBIC_OFFSETS):
            observed = _finite(grid.get((z + delta_z, n + delta_n)))
            if observed is None:
                return None
            total += z_weights[z_index] * n_weights[n_index] * observed
    return total


def _parity_channel(z: int, n: int) -> int:
    if z % 2 == 0 and n % 2 == 0:
        return 1
    if z % 2 == 1 and n % 2 == 1:
        return -1
    return 0


def _nearest_magic_distance(value: int) -> int:
    return min(abs(value - magic) for magic in MAGIC_NUMBERS)


def build_observer_records(rows: Iterable[Mapping[str, object]]) -> list[dict]:
    valid = []
    for index, row in enumerate(rows):
        try:
            z = _int_field(row, "Z")
            n = _int_field(row, "N")
            a = _int_field(row, "A") if row.get("A") not in (None, "") else z + n
        except (TypeError, ValueError):
            continue
        actual = _finite(row)
        if actual is None or a <= 0:
            continue
        item = dict(row)
        item.update(
            {
                "_row_index": index,
                "_z": z,
                "_n": n,
                "_a": a,
                "_entity": _entity(row, z, a),
                "_actual": actual,
            }
        )
        valid.append(item)

    grid = {(item["_z"], item["_n"]): item for item in valid}
    output = []
    for item in valid:
        z, n, a = item["_z"], item["_n"], item["_a"]
        neutron = axis_jet(grid, z, n, "n")
        proton = axis_jet(grid, z, n, "z")
        tensor = tensor_cubic_prediction(grid, z, n)
        neutron_value = neutron.get("value")
        proton_value = proton.get("value")
        if neutron_value is None and proton_value is None:
            axis_mean = None
        elif neutron_value is None:
            axis_mean = float(proton_value)
        elif proton_value is None:
            axis_mean = float(neutron_value)
        else:
            axis_mean = 0.5 * (float(neutron_value) + float(proton_value))

        even = {}
        odd = {}
        for key in ("value", "slope", "curvature", "jerk"):
            neutron_component = 0.0 if neutron_value is None else float(neutron[key])
            proton_component = 0.0 if proton_value is None else float(proton[key])
            even[key] = 0.5 * (neutron_component + proton_component)
            odd[key] = 0.5 * (neutron_component - proton_component)

        asymmetry = (n - z) / a
        record = {
            "record_type": "RKF_NUCLEAR_OBSERVER_RECORD_V5",
            "entity": item["_entity"],
            "z": z,
            "n": n,
            "a": a,
            "actual_binding_energy_per_A_keV": item["_actual"],
            "neutron_jet": neutron,
            "proton_jet": proton,
            "axis_mean_prediction_keV_per_a": axis_mean,
            "tensor_cubic_prediction_keV_per_a": tensor,
            "seam_residue_keV_per_a": (
                None if tensor is None or axis_mean is None else float(tensor) - float(axis_mean)
            ),
            "cut_even_jet": even,
            "cut_odd_jet": odd,
            "asymmetry": asymmetry,
            "surface_coordinate": a ** (-1.0 / 3.0),
            "coulomb_coordinate": z * (z - 1) / (a ** (4.0 / 3.0)),
            "pairing_coordinate": _parity_channel(z, n) / (a**1.5),
            "n_magic_distance": _nearest_magic_distance(n),
            "z_magic_distance": _nearest_magic_distance(z),
        }
        record["observer_hash"] = certificate_hash(record)
        output.append(record)
    return sorted(output, key=lambda row: (int(row["z"]), int(row["n"])))


def feature_vector(record: Mapping[str, object], level: int = 3) -> tuple[list[str], list[float]] | None:
    if level not in (1, 2, 3):
        raise ValueError("level must be 1, 2, or 3")
    if record.get("axis_mean_prediction_keV_per_a") is None:
        return None
    even = record["cut_even_jet"]
    odd = record["cut_odd_jet"]
    seam = record.get("seam_residue_keV_per_a")
    tensor = record.get("tensor_cubic_prediction_keV_per_a")
    names = [
        "odd_value",
        "absolute_odd_value",
        "asymmetry",
        "asymmetry_square",
        "surface_coordinate",
        "coulomb_coordinate",
        "pairing_coordinate",
        "neutron_jet_order",
        "proton_jet_order",
    ]
    values = [
        float(odd["value"]),
        abs(float(odd["value"])),
        float(record["asymmetry"]),
        float(record["asymmetry"]) ** 2,
        float(record["surface_coordinate"]),
        float(record["coulomb_coordinate"]),
        float(record["pairing_coordinate"]),
        float(record["neutron_jet"]["order"]),
        float(record["proton_jet"]["order"]),
    ]
    if level >= 2:
        names.extend(
            [
                "even_slope",
                "odd_slope",
                "even_curvature",
                "odd_curvature",
                "seam_residue",
                "tensor_available",
                "n_magic_proximity",
                "z_magic_proximity",
            ]
        )
        values.extend(
            [
                float(even["slope"]),
                float(odd["slope"]),
                float(even["curvature"]),
                float(odd["curvature"]),
                0.0 if seam is None else float(seam),
                0.0 if tensor is None else 1.0,
                1.0 / (1.0 + float(record["n_magic_distance"])),
                1.0 / (1.0 + float(record["z_magic_distance"])),
            ]
        )
    if level >= 3:
        names.extend(
            [
                "even_jerk",
                "odd_jerk",
                "odd_value_times_asymmetry",
                "odd_curvature_times_asymmetry",
                "seam_times_asymmetry",
            ]
        )
        values.extend(
            [
                float(even["jerk"]),
                float(odd["jerk"]),
                float(odd["value"]) * float(record["asymmetry"]),
                float(odd["curvature"]) * float(record["asymmetry"]),
                (0.0 if seam is None else float(seam)) * float(record["asymmetry"]),
            ]
        )
    return names, values


def fit_minimum_burden_decoder(
    records: Sequence[Mapping[str, object]],
    level: int = 3,
    ridge: float = DEFAULT_RIDGE,
) -> dict:
    if ridge < 0.0:
        raise ValueError("ridge must be non-negative")
    raw_features = []
    targets = []
    names: list[str] | None = None
    for record in records:
        packet = feature_vector(record, level)
        base = record.get("axis_mean_prediction_keV_per_a")
        actual = record.get("actual_binding_energy_per_A_keV")
        if packet is None or base is None or actual is None:
            continue
        names, values = packet
        raw_features.append(values)
        targets.append(float(actual) - float(base))
    if not raw_features or names is None:
        raise ValueError("no complete training records")

    feature_count = len(raw_features[0])
    means = [
        sum(row[column] for row in raw_features) / len(raw_features)
        for column in range(feature_count)
    ]
    scales = []
    for column in range(feature_count):
        variance = sum(
            (row[column] - means[column]) ** 2 for row in raw_features
        ) / max(1, len(raw_features) - 1)
        scales.append(math.sqrt(variance) if variance > 1e-18 else 1.0)

    design = [
        [1.0]
        + [
            (row[column] - means[column]) / scales[column]
            for column in range(feature_count)
        ]
        for row in raw_features
    ]
    dimension = feature_count + 1
    gram = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    rhs = [0.0 for _ in range(dimension)]
    for row, target in zip(design, targets):
        for left in range(dimension):
            rhs[left] += row[left] * target
            for right in range(left, dimension):
                gram[left][right] += row[left] * row[right]
    for left in range(dimension):
        for right in range(left):
            gram[left][right] = gram[right][left]
        if left > 0:
            gram[left][left] += ridge

    inverse_gram = _invert_matrix(gram)
    coefficients = _matvec(inverse_gram, rhs)
    training_residuals = [
        target - _dot(row, coefficients) for row, target in zip(design, targets)
    ]
    centre = statistics.median(training_residuals)
    mad = statistics.median(abs(value - centre) for value in training_residuals)
    robust_sigma = max(1e-9, 1.4826 * mad)
    burdens = [_dot(row, _matvec(inverse_gram, row)) for row in design]

    return {
        "decoder_type": "RKF_MINIMUM_BURDEN_RIDGE_DECODER_V5",
        "level": level,
        "ridge": ridge,
        "feature_names": names,
        "feature_means": means,
        "feature_scales": scales,
        "coefficients": coefficients,
        "inverse_gram": inverse_gram,
        "training_robust_sigma_keV_per_a": robust_sigma,
        "burden_threshold": _percentile(burdens, BURDEN_RETENTION_QUANTILE),
        "training_count": len(design),
        "training_z_values": sorted({int(record["z"]) for record in records}),
    }


def apply_decoder(model: Mapping[str, object], record: Mapping[str, object]) -> dict | None:
    level = int(model["level"])
    packet = feature_vector(record, level)
    base = record.get("axis_mean_prediction_keV_per_a")
    if packet is None or base is None:
        return None
    _, raw = packet
    means = [float(value) for value in model["feature_means"]]
    scales = [float(value) for value in model["feature_scales"]]
    standardized = [1.0] + [
        (float(raw[index]) - means[index]) / scales[index]
        for index in range(len(raw))
    ]
    correction = _dot(standardized, model["coefficients"])
    burden = _dot(standardized, _matvec(model["inverse_gram"], standardized))
    sigma = float(model["training_robust_sigma_keV_per_a"])
    return {
        "prediction_keV_per_a": float(base) + correction,
        "correction_keV_per_a": correction,
        "decoder_burden": burden,
        "predicted_uncertainty_keV_per_a": sigma * math.sqrt(1.0 + max(0.0, burden)),
        "burden_guard_pass": (
            int(record["a"]) >= 8
            and burden <= float(model["burden_threshold"])
        ),
    }


def cross_fitted_predictions(
    records: Sequence[Mapping[str, object]],
    level: int = 3,
    ridge: float = DEFAULT_RIDGE,
) -> list[dict]:
    by_z: dict[int, list[Mapping[str, object]]] = defaultdict(list)
    for record in records:
        by_z[int(record["z"])].append(record)
    output = []
    all_records = list(records)
    for held_out_z in sorted(by_z):
        training = [record for record in all_records if int(record["z"]) != held_out_z]
        model = fit_minimum_burden_decoder(training, level=level, ridge=ridge)
        if held_out_z in set(model["training_z_values"]):
            raise AssertionError("held-out element leaked into decoder training")
        for record in by_z[held_out_z]:
            applied = apply_decoder(model, record)
            item = {
                "entity": record["entity"],
                "z": record["z"],
                "n": record["n"],
                "a": record["a"],
                "actual_binding_energy_per_A_keV": record["actual_binding_energy_per_A_keV"],
                "axis_mean_prediction_keV_per_a": record["axis_mean_prediction_keV_per_a"],
                "tensor_cubic_prediction_keV_per_a": record["tensor_cubic_prediction_keV_per_a"],
                "seam_residue_keV_per_a": record["seam_residue_keV_per_a"],
                "held_out_z": held_out_z,
                "decoder_training_count": model["training_count"],
                "decoder_level": level,
            }
            if applied is None:
                item.update(
                    {
                        "rkf_prediction_keV_per_a": None,
                        "rkf_guarded_prediction_keV_per_a": None,
                        "rkf_correction_keV_per_a": None,
                        "decoder_burden": None,
                        "predicted_uncertainty_keV_per_a": None,
                        "burden_guard_pass": False,
                    }
                )
            else:
                item.update(
                    {
                        "rkf_prediction_keV_per_a": applied["prediction_keV_per_a"],
                        "rkf_guarded_prediction_keV_per_a": (
                            applied["prediction_keV_per_a"]
                            if applied["burden_guard_pass"]
                            else None
                        ),
                        "rkf_correction_keV_per_a": applied["correction_keV_per_a"],
                        "decoder_burden": applied["decoder_burden"],
                        "predicted_uncertainty_keV_per_a": applied["predicted_uncertainty_keV_per_a"],
                        "burden_guard_pass": applied["burden_guard_pass"],
                    }
                )
            item["prediction_hash"] = certificate_hash(item)
            output.append(item)
    return sorted(output, key=lambda row: (int(row["z"]), int(row["n"])))


def prediction_metrics(records: Iterable[Mapping[str, object]], prediction_key: str) -> dict:
    rows = list(records)
    residuals = [
        float(record[prediction_key]) - float(record["actual_binding_energy_per_A_keV"])
        for record in rows
        if record.get(prediction_key) is not None
        and record.get("actual_binding_energy_per_A_keV") is not None
    ]
    absolute = [abs(value) for value in residuals]
    if not residuals:
        return {
            "count": len(rows),
            "prediction_count": 0,
            "coverage": 0.0 if rows else None,
            "mean_absolute_residual_keV_per_a": None,
            "median_absolute_residual_keV_per_a": None,
            "p95_absolute_residual_keV_per_a": None,
            "p99_absolute_residual_keV_per_a": None,
            "max_absolute_residual_keV_per_a": None,
            "root_mean_square_residual_keV_per_a": None,
            "mean_signed_residual_keV_per_a": None,
            "tail_counts": {},
        }
    return {
        "count": len(rows),
        "prediction_count": len(residuals),
        "coverage": len(residuals) / len(rows),
        "mean_absolute_residual_keV_per_a": sum(absolute) / len(absolute),
        "median_absolute_residual_keV_per_a": statistics.median(absolute),
        "p95_absolute_residual_keV_per_a": _percentile(absolute, 0.95),
        "p99_absolute_residual_keV_per_a": _percentile(absolute, 0.99),
        "max_absolute_residual_keV_per_a": max(absolute),
        "root_mean_square_residual_keV_per_a": math.sqrt(
            sum(value * value for value in residuals) / len(residuals)
        ),
        "mean_signed_residual_keV_per_a": sum(residuals) / len(residuals),
        "tail_counts": {
            str(threshold): sum(value >= threshold for value in absolute)
            for threshold in (100.0, 250.0, 500.0, 1000.0)
        },
    }


def _pearson(pairs: Sequence[tuple[float, float]]) -> Optional[float]:
    if len(pairs) < 3:
        return None
    left = [float(pair[0]) for pair in pairs]
    right = [float(pair[1]) for pair in pairs]
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right)
    )
    left_scale = math.sqrt(sum((x - left_mean) ** 2 for x in left))
    right_scale = math.sqrt(sum((y - right_mean) ** 2 for y in right))
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    return numerator / (left_scale * right_scale)


def explainability_summary(records: Sequence[Mapping[str, object]]) -> dict:
    burden_pairs = []
    seam_pairs = []
    uncertainty_pairs = []
    eligible = []
    for record in records:
        prediction = record.get("rkf_prediction_keV_per_a")
        actual = record.get("actual_binding_energy_per_A_keV")
        if prediction is None or actual is None:
            continue
        absolute_error = abs(float(prediction) - float(actual))
        eligible.append((float(record["decoder_burden"]), absolute_error, record))
        burden_pairs.append((float(record["decoder_burden"]), absolute_error))
        uncertainty_pairs.append((float(record["predicted_uncertainty_keV_per_a"]), absolute_error))
        if record.get("seam_residue_keV_per_a") is not None:
            seam_pairs.append((abs(float(record["seam_residue_keV_per_a"])), absolute_error))

    burden_values = [item[0] for item in eligible]
    cut_points = [_percentile(burden_values, q) for q in (0.25, 0.50, 0.75)] if burden_values else []
    bands: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for burden, _, record in eligible:
        if not cut_points:
            band = "Q1"
        elif burden <= float(cut_points[0]):
            band = "Q1_LOW"
        elif burden <= float(cut_points[1]):
            band = "Q2"
        elif burden <= float(cut_points[2]):
            band = "Q3"
        else:
            band = "Q4_HIGH"
        bands[band].append(record)

    return {
        "absolute_error_correlation_with_decoder_burden": _pearson(burden_pairs),
        "absolute_error_correlation_with_predicted_uncertainty": _pearson(uncertainty_pairs),
        "absolute_error_correlation_with_absolute_seam_residue": _pearson(seam_pairs),
        "metrics_by_burden_quartile": {
            band: prediction_metrics(values, "rkf_prediction_keV_per_a")
            for band, values in sorted(bands.items())
        },
    }


def attach_frozen_uam(
    predictions: Sequence[dict],
    frozen_report: Mapping[str, object],
) -> list[dict]:
    frozen = {
        (int(record["z"]), int(record["n"])): record
        for record in frozen_report.get("records", [])
    }
    output = []
    for prediction in predictions:
        item = dict(prediction)
        baseline = frozen.get((int(item["z"]), int(item["n"])), {})
        item["frozen_uam_raw_prediction_keV_per_a"] = baseline.get(
            "raw_blended_prediction_keV_per_a"
        )
        item["frozen_uam_guarded_prediction_keV_per_a"] = baseline.get(
            "guarded_blended_prediction_keV_per_a"
        )
        item["frozen_uam_guard_decision"] = baseline.get("guard_decision")
        output.append(item)
    return output


def common_support_comparison(records: Sequence[Mapping[str, object]]) -> dict:
    common = [
        record
        for record in records
        if record.get("rkf_guarded_prediction_keV_per_a") is not None
        and record.get("frozen_uam_guarded_prediction_keV_per_a") is not None
    ]
    rkf = prediction_metrics(common, "rkf_guarded_prediction_keV_per_a")
    uam = prediction_metrics(common, "frozen_uam_guarded_prediction_keV_per_a")
    rkf_mae = rkf.get("mean_absolute_residual_keV_per_a")
    uam_mae = uam.get("mean_absolute_residual_keV_per_a")
    rkf_p95 = rkf.get("p95_absolute_residual_keV_per_a")
    uam_p95 = uam.get("p95_absolute_residual_keV_per_a")
    return {
        "common_count": len(common),
        "rkf": rkf,
        "frozen_uam_v4": uam,
        "mae_improvement_fraction": (
            None
            if rkf_mae is None or uam_mae in (None, 0.0)
            else (float(uam_mae) - float(rkf_mae)) / float(uam_mae)
        ),
        "p95_improvement_fraction": (
            None
            if rkf_p95 is None or uam_p95 in (None, 0.0)
            else (float(uam_p95) - float(rkf_p95)) / float(uam_p95)
        ),
        "beats_frozen_uam_v4_on_mae": (
            rkf_mae is not None and uam_mae is not None and float(rkf_mae) < float(uam_mae)
        ),
        "beats_frozen_uam_v4_on_p95": (
            rkf_p95 is not None and uam_p95 is not None and float(rkf_p95) < float(uam_p95)
        ),
    }


def build_experiment_report(
    rows: Iterable[Mapping[str, object]],
    frozen_report: Mapping[str, object],
    source: str,
    level: int = 3,
    ridge: float = DEFAULT_RIDGE,
) -> dict:
    observer_records = build_observer_records(rows)
    predictions = cross_fitted_predictions(observer_records, level=level, ridge=ridge)
    attached = attach_frozen_uam(predictions, frozen_report)
    comparison = common_support_comparison(attached)
    report = {
        "report_type": "RKF_CROSS_FITTED_NUCLEAR_JET_PREDICTION_REPORT_V5",
        "source": source,
        "physical_adapter": {
            "declared_response_cut": "NEUTRON_PROTON_AXIS_EXCHANGE",
            "cut_even_interpretation": "ISOSCALAR_RESPONSE_PACKET",
            "cut_odd_interpretation": "ISOVECTOR_RESPONSE_PACKET",
            "first_layer": "TWO_AXIS_TARGET_FREE_LOCAL_PREDICTIONS",
            "higher_layers": "LOCAL_SLOPE_CURVATURE_JERK_AND_TENSOR_SEAM",
            "decoder_validation": "LEAVE_ONE_ELEMENT_CHAIN_OUT",
        },
        "decoder": {
            "level": level,
            "ridge": ridge,
            "burden_retention_quantile": BURDEN_RETENTION_QUANTILE,
        },
        "record_count": len(attached),
        "axis_mean_metrics": prediction_metrics(attached, "axis_mean_prediction_keV_per_a"),
        "tensor_cubic_metrics": prediction_metrics(attached, "tensor_cubic_prediction_keV_per_a"),
        "rkf_cross_fitted_metrics": prediction_metrics(attached, "rkf_prediction_keV_per_a"),
        "rkf_burden_guarded_metrics": prediction_metrics(
            attached, "rkf_guarded_prediction_keV_per_a"
        ),
        "frozen_uam_v4_metrics": prediction_metrics(
            attached, "frozen_uam_guarded_prediction_keV_per_a"
        ),
        "common_support_comparison": comparison,
        "explainability": explainability_summary(attached),
        "claim_boundary": {
            "exploratory_physical_prediction": True,
            "target_values_excluded_from_local_observers": True,
            "held_out_element_excluded_from_decoder_training": True,
            "external_future_mass_table_validation": False,
            "fundamental_nuclear_law_claimed": False,
        },
        "records": attached,
    }
    report["status"] = (
        "PASS_EXPLORATORY_RKF_BEATS_FROZEN_UAM_V4_COMMON_SUPPORT"
        if comparison["beats_frozen_uam_v4_on_mae"]
        else "INCONCLUSIVE_EXPLORATORY_RKF_DOES_NOT_BEAT_FROZEN_UAM_V4_COMMON_SUPPORT"
    )
    report["report_hash"] = certificate_hash(report)
    return report
