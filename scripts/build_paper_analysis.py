from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
DATASET = ROOT / "data" / "processed" / "ame_nubase_atomic_native.csv"
OUT = ROOT / "releases" / "uam-v4" / "paper_analysis"
MAGIC = {2, 8, 20, 28, 50, 82, 126}


def percentile(values: list[float], q: float) -> float | None:
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


def metrics(rows: list[dict], prediction_key: str = "guarded_blended_prediction_keV_per_a") -> dict:
    residuals = []
    total_residuals = []
    for row in rows:
        pred = row.get(prediction_key)
        actual = row.get("actual_binding_energy_per_A_keV")
        if pred is None or actual is None:
            continue
        residual = float(pred) - float(actual)
        residuals.append(residual)
        total_residuals.append(residual * int(row["a"]))
    absolute = [abs(x) for x in residuals]
    total_abs = [abs(x) for x in total_residuals]
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
        "rmse_keV_per_A": math.sqrt(sum(x * x for x in residuals) / predicted) if predicted else None,
        "mean_signed_keV_per_A": sum(residuals) / predicted if predicted else None,
        "max_abs_keV_per_A": max(absolute) if predicted else None,
        "mae_total_keV": sum(total_abs) / predicted if predicted else None,
        "median_abs_total_keV": statistics.median(total_abs) if predicted else None,
        "p95_abs_total_keV": percentile(total_abs, 0.95),
        "rmse_total_keV": math.sqrt(sum(x * x for x in total_residuals) / predicted) if predicted else None,
        "mae_total_MeV": (sum(total_abs) / predicted / 1000.0) if predicted else None,
    }


def shell_class(z: int, n: int) -> str:
    if z in MAGIC or n in MAGIC:
        return "AT_MAGIC_Z_OR_N"
    if any(abs(z - m) <= 2 or abs(n - m) <= 2 for m in MAGIC):
        return "WITHIN_2_OF_MAGIC_Z_OR_N"
    return "AWAY_FROM_MAGIC_NUMBERS"


def stable_class(row: dict) -> str:
    raw = str(row.get("half_life_raw", "")).strip().upper()
    if "STABLE" in raw:
        return "STABLE"
    seconds = row.get("half_life_s")
    try:
        if seconds not in (None, "") and math.isfinite(float(seconds)):
            return "RADIOACTIVE_WITH_NUMERIC_HALF_LIFE"
    except (TypeError, ValueError):
        pass
    return "RADIOACTIVE_OR_UNRESOLVED_HALF_LIFE"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    with DATASET.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    source = {(int(float(r["Z"])), int(float(r["N"]))): r for r in source_rows}
    records = report["records"]
    OUT.mkdir(parents=True, exist_ok=True)

    enriched = []
    for record in records:
        row = dict(record)
        src = source.get((int(row["z"]), int(row["n"])), {})
        row["stability_class"] = stable_class(src)
        row["shell_class"] = shell_class(int(row["z"]), int(row["n"]))
        pred = row.get("guarded_blended_prediction_keV_per_a")
        actual = row.get("actual_binding_energy_per_A_keV")
        if pred is not None and actual is not None:
            residual = float(pred) - float(actual)
            row["signed_residual_keV_per_A"] = residual
            row["absolute_residual_keV_per_A"] = abs(residual)
            row["signed_residual_total_keV"] = residual * int(row["a"])
            row["absolute_residual_total_keV"] = abs(residual * int(row["a"]))
        enriched.append(row)

    extreme = sorted(
        [r for r in enriched if r.get("absolute_residual_keV_per_A") is not None],
        key=lambda r: float(r["absolute_residual_keV_per_A"]),
        reverse=True,
    )[:50]
    extreme_fields = [
        "entity", "z", "n", "a", "mass_region", "shell_class", "stability_class",
        "actual_binding_energy_per_A_keV", "guarded_blended_prediction_keV_per_a",
        "signed_residual_keV_per_A", "absolute_residual_keV_per_A",
        "signed_residual_total_keV", "absolute_residual_total_keV",
        "directional_disagreement_keV_per_a", "n_predictor", "z_predictor",
    ]
    write_csv(OUT / "extreme_retained_residuals_top50.csv", extreme, extreme_fields)

    shell_groups: dict[str, list[dict]] = defaultdict(list)
    stability_groups: dict[str, list[dict]] = defaultdict(list)
    region_groups: dict[str, list[dict]] = defaultdict(list)
    for row in enriched:
        shell_groups[row["shell_class"]].append(row)
        stability_groups[row["stability_class"]].append(row)
        region_groups[row["mass_region"]].append(row)

    shell_rows = [{"group": key, **metrics(rows)} for key, rows in sorted(shell_groups.items())]
    stability_rows = [{"group": key, **metrics(rows)} for key, rows in sorted(stability_groups.items())]
    region_rows = [{"group": key, **metrics(rows)} for key, rows in sorted(region_groups.items())]
    metric_fields = list(shell_rows[0].keys())
    write_csv(OUT / "shell_closure_metrics.csv", shell_rows, metric_fields)
    write_csv(OUT / "stability_metrics.csv", stability_rows, metric_fields)
    write_csv(OUT / "mass_region_metrics_extended.csv", region_rows, metric_fields)

    raw_available = [
        r for r in enriched
        if r.get("raw_blended_prediction_keV_per_a") is not None
        and r.get("actual_binding_energy_per_A_keV") is not None
    ]
    ranked = sorted(
        raw_available,
        key=lambda r: (
            float(r.get("directional_disagreement_keV_per_a") or -1.0),
            float(r.get("n_robust_sigma_keV_per_a") or -1.0) + float(r.get("z_robust_sigma_keV_per_a") or -1.0),
        ),
    )
    curve = []
    for target in (1.00, 0.995, 0.99, 0.9875, 0.98, 0.95, 0.90, 0.80, 0.70, 0.50):
        keep = max(1, min(len(ranked), round(len(ranked) * target)))
        retained = ranked[:keep]
        result = metrics(retained, "raw_blended_prediction_keV_per_a")
        curve.append({
            "target_retained_fraction": target,
            "retained_count": keep,
            "available_raw_prediction_count": len(ranked),
            **result,
            "maximum_retained_directional_disagreement_keV_per_A": max(
                float(r.get("directional_disagreement_keV_per_a") or 0.0) for r in retained
            ),
        })
    write_csv(OUT / "coverage_error_curve.csv", curve, list(curve[0].keys()))

    summary = {
        "status": "PAPER_ANALYSIS_BUILT",
        "record_count": len(enriched),
        "retained_prediction_count": report["guarded_prediction_count"],
        "abstention_count": report["guarded_abstention_count"],
        "overall_guarded_metrics_with_total_energy": metrics(enriched),
        "axis_comparison": {
            "neutron_direction": report["n_direction_metrics"],
            "proton_direction": report["z_direction_metrics"],
            "raw_blend": report["raw_blended_metrics"],
            "guarded_blend": report["guarded_blended_metrics"],
        },
        "shell_closure_metrics": shell_rows,
        "stability_metrics": stability_rows,
        "mass_region_metrics": region_rows,
        "coverage_error_curve_definition": (
            "Records with raw blended predictions are ranked by directional disagreement, then combined robust sigma; "
            "the highest-risk tail is abstained to obtain each retained fraction."
        ),
        "extreme_residual_file": "extreme_retained_residuals_top50.csv",
        "limitations": [
            "Stable-versus-unstable grouping uses the processed half_life_raw and half_life_s fields.",
            "Shell-closure grouping is descriptive and uses conventional magic numbers 2, 8, 20, 28, 50, 82 and 126.",
            "Coverage-error curves are in-sample diagnostics and are not external validation.",
        ],
    }
    (OUT / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": summary["status"],
        "outputs": sorted(p.name for p in OUT.iterdir()),
        "top_extreme_entity": extreme[0]["entity"] if extreme else None,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
