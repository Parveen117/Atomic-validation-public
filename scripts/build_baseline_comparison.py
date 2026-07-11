from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "processed" / "ame_nubase_atomic_native.csv"
REPORT = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
OUT = ROOT / "releases" / "uam-v4" / "baseline_comparison"


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    w = pos - lo
    return ordered[lo] * (1 - w) + ordered[hi] * w


def metrics(rows, key):
    residuals = []
    for row in rows:
        prediction = row.get(key)
        actual = row.get("actual_binding_energy_per_A_keV")
        if prediction is not None and actual is not None:
            residuals.append(float(prediction) - float(actual))
    absolute = [abs(value) for value in residuals]
    count = len(rows)
    predicted = len(residuals)
    return {
        "count": count,
        "prediction_count": predicted,
        "coverage": predicted / count if count else None,
        "mae_keV_per_A": sum(absolute) / predicted if predicted else None,
        "median_abs_keV_per_A": statistics.median(absolute) if predicted else None,
        "p95_abs_keV_per_A": percentile(absolute, 0.95),
        "p99_abs_keV_per_A": percentile(absolute, 0.99),
        "rmse_keV_per_A": math.sqrt(sum(value * value for value in residuals) / predicted) if predicted else None,
        "mean_signed_keV_per_A": sum(residuals) / predicted if predicted else None,
        "max_abs_keV_per_A": max(absolute) if predicted else None,
    }


def solve_linear(matrix, vector):
    n = len(vector)
    aug = [list(map(float, matrix[i])) + [float(vector[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise RuntimeError("singular normal-equation matrix")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(n + 1)]
    return [aug[i][-1] for i in range(n)]


def semf_features(z, n, a):
    pairing = 0.0
    if a % 2 == 0:
        pairing = 1.0 if z % 2 == 0 and n % 2 == 0 else -1.0
    return [
        1.0,
        a ** (-1.0 / 3.0),
        z * (z - 1.0) / (a ** (4.0 / 3.0)),
        ((a - 2.0 * z) ** 2) / (a * a),
        pairing / (a ** 1.5),
    ]


def fit_semf(rows):
    p = 5
    gram = [[0.0] * p for _ in range(p)]
    rhs = [0.0] * p
    for row in rows:
        features = row["semf_features"]
        target = row["actual_binding_energy_per_A_keV"]
        for i in range(p):
            rhs[i] += features[i] * target
            for j in range(p):
                gram[i][j] += features[i] * features[j]
    return solve_linear(gram, rhs)


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def main():
    with DATASET.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    records = report["records"]
    grid = {}
    rows = []
    for source in source_rows:
        z, n, a = int(float(source["Z"])), int(float(source["N"])), int(float(source["A"]))
        actual = finite(source.get("binding_energy_per_A_keV"))
        if actual is None:
            continue
        item = {
            "z": z,
            "n": n,
            "a": a,
            "entity": f"{source.get('Symbol', 'X')}-{a}",
            "actual_binding_energy_per_A_keV": actual,
            "semf_features": semf_features(z, n, a),
            "fold": (31 * z + 17 * n + a) % 5,
        }
        rows.append(item)
        grid[(z, n)] = actual

    record_map = {(int(r["z"]), int(r["n"])): r for r in records}
    fold_coefficients = {}
    for fold in range(5):
        training = [row for row in rows if row["fold"] != fold]
        fold_coefficients[str(fold)] = fit_semf(training)

    output_rows = []
    for row in rows:
        z, n = row["z"], row["n"]
        neighbours = [
            grid.get((z, n - 2)), grid.get((z, n + 2)),
            grid.get((z - 1, n)), grid.get((z + 1, n)),
        ]
        available = [value for value in neighbours if value is not None]
        local_prediction = sum(available) / len(available) if available else None
        source_record = record_map[(z, n)]
        n_prediction = source_record.get("n_prediction_keV_per_a")
        z_prediction = source_record.get("z_prediction_keV_per_a")
        if n_prediction is not None and z_prediction is not None:
            equal_blend = 0.5 * (float(n_prediction) + float(z_prediction))
        elif n_prediction is not None:
            equal_blend = float(n_prediction)
        elif z_prediction is not None:
            equal_blend = float(z_prediction)
        else:
            equal_blend = None
        coefficients = fold_coefficients[str(row["fold"])]
        output_rows.append({
            **row,
            "local_neighbour_prediction_keV_per_A": local_prediction,
            "equal_axis_blend_prediction_keV_per_A": equal_blend,
            "semf_5fold_prediction_keV_per_A": dot(coefficients, row["semf_features"]),
            "uam_v4_guarded_prediction_keV_per_A": source_record.get("guarded_blended_prediction_keV_per_a"),
        })

    comparison = {
        "LOCAL_NEIGHBOUR_MEAN": metrics(output_rows, "local_neighbour_prediction_keV_per_A"),
        "EQUAL_AXIS_BLEND": metrics(output_rows, "equal_axis_blend_prediction_keV_per_A"),
        "SEMF_5FOLD_OUT_OF_FOLD": metrics(output_rows, "semf_5fold_prediction_keV_per_A"),
        "UAM_V4_GUARDED": metrics(output_rows, "uam_v4_guarded_prediction_keV_per_A"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    fields = [
        "entity", "z", "n", "a", "fold", "actual_binding_energy_per_A_keV",
        "local_neighbour_prediction_keV_per_A", "equal_axis_blend_prediction_keV_per_A",
        "semf_5fold_prediction_keV_per_A", "uam_v4_guarded_prediction_keV_per_A",
    ]
    with (OUT / "baseline_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    with (OUT / "baseline_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        metric_fields = ["model", *next(iter(comparison.values())).keys()]
        writer = csv.DictWriter(handle, fieldnames=metric_fields)
        writer.writeheader()
        for model, values in comparison.items():
            writer.writerow({"model": model, **values})
    summary = {
        "status": "BASELINE_COMPARISON_BUILT",
        "comparison": comparison,
        "semf_design": {
            "validation": "deterministic five-fold out-of-fold prediction",
            "fold_rule": "(31*Z + 17*N + A) mod 5",
            "feature_order": [
                "constant", "A^(-1/3)", "Z(Z-1)/A^(4/3)",
                "(A-2Z)^2/A^2", "pairing/A^(3/2)",
            ],
            "fold_coefficients_keV_per_A": fold_coefficients,
        },
        "local_neighbour_definition": "Mean of available leakage-safe neighbours at N±2 within the element and Z±1 at fixed N; the target row is never used.",
        "equal_axis_definition": "Unweighted mean of available V4 neutron- and proton-direction predictions before calibration and guarding.",
        "limitations": [
            "The SEMF coefficients are fitted on this dataset but evaluated out of fold; this is not temporal or external validation.",
            "The local-neighbour baseline has variable coverage because some nuclei lack nearby support.",
            "Recognised external mass-model tables remain a separate comparison task.",
        ],
    }
    (OUT / "baseline_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "models": comparison}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
