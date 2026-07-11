from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Optional


def certificate_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite(row: Optional[Mapping[str, object]], key: str) -> Optional[float]:
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


def mass_region(a: int) -> str:
    if a < 40:
        return "LIGHT_A_LT_40"
    if a < 100:
        return "MEDIUM_40_TO_99"
    if a < 180:
        return "HEAVY_100_TO_179"
    return "VERY_HEAVY_A_GE_180"


def _same_chain_prediction(by_n: Mapping[int, Mapping[str, object]], n: int):
    m4 = _finite(by_n.get(n - 4), "binding_energy_per_A_keV")
    m2 = _finite(by_n.get(n - 2), "binding_energy_per_A_keV")
    p2 = _finite(by_n.get(n + 2), "binding_energy_per_A_keV")
    p4 = _finite(by_n.get(n + 4), "binding_energy_per_A_keV")
    if all(value is not None for value in (m4, m2, p2, p4)):
        return (2.0 / 3.0) * (m2 + p2) - (1.0 / 6.0) * (m4 + p4), "SAME_PARITY_CUBIC_N2_N4", [-4, -2, 2, 4]
    if m2 is not None and p2 is not None:
        return (m2 + p2) / 2.0, "SAME_PARITY_LINEAR_N2", [-2, 2]
    if m4 is not None and m2 is not None:
        return 2.0 * m2 - m4, "ONE_SIDED_SAME_PARITY_LEFT", [-4, -2]
    if p2 is not None and p4 is not None:
        return 2.0 * p2 - p4, "ONE_SIDED_SAME_PARITY_RIGHT", [2, 4]
    return None, "INSUFFICIENT_SAME_PARITY_SUPPORT", []


def _cross_element_prediction(grid: Mapping[tuple[int, int], Mapping[str, object]], z: int, n: int):
    m2 = _finite(grid.get((z - 2, n)), "binding_energy_per_A_keV")
    m1 = _finite(grid.get((z - 1, n)), "binding_energy_per_A_keV")
    p1 = _finite(grid.get((z + 1, n)), "binding_energy_per_A_keV")
    p2 = _finite(grid.get((z + 2, n)), "binding_energy_per_A_keV")
    if all(value is not None for value in (m2, m1, p1, p2)):
        return (2.0 / 3.0) * (m1 + p1) - (1.0 / 6.0) * (m2 + p2), "CROSS_ELEMENT_CUBIC_Z1_Z2", [-2, -1, 1, 2]
    if m1 is not None and p1 is not None:
        return (m1 + p1) / 2.0, "CROSS_ELEMENT_LINEAR_Z1", [-1, 1]
    if m2 is not None and m1 is not None:
        return 2.0 * m1 - m2, "CROSS_ELEMENT_ONE_SIDED_LEFT", [-2, -1]
    if p1 is not None and p2 is not None:
        return 2.0 * p1 - p2, "CROSS_ELEMENT_ONE_SIDED_RIGHT", [1, 2]
    return None, "ABSTAIN_INSUFFICIENT_CROSS_ELEMENT_SUPPORT", []


def _percentile(values: list[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower, upper = int(math.floor(position)), int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _metrics(records: Iterable[Mapping[str, object]], prediction_key: str) -> dict:
    rows = list(records)
    residuals = [float(r[prediction_key]) - float(r["actual_binding_energy_per_A_keV"]) for r in rows if r.get(prediction_key) is not None and r.get("actual_binding_energy_per_A_keV") is not None]
    absolute = [abs(value) for value in residuals]
    if not residuals:
        return {"count": len(rows), "prediction_count": 0, "coverage": 0.0 if rows else None, "mean_absolute_residual_keV_per_a": None, "median_absolute_residual_keV_per_a": None, "p95_absolute_residual_keV_per_a": None, "p99_absolute_residual_keV_per_a": None, "max_absolute_residual_keV_per_a": None, "root_mean_square_residual_keV_per_a": None, "mean_signed_residual_keV_per_a": None}
    return {"count": len(rows), "prediction_count": len(residuals), "coverage": len(residuals) / len(rows), "mean_absolute_residual_keV_per_a": sum(absolute) / len(absolute), "median_absolute_residual_keV_per_a": statistics.median(absolute), "p95_absolute_residual_keV_per_a": _percentile(absolute, 0.95), "p99_absolute_residual_keV_per_a": _percentile(absolute, 0.99), "max_absolute_residual_keV_per_a": max(absolute), "root_mean_square_residual_keV_per_a": math.sqrt(sum(v * v for v in residuals) / len(residuals)), "mean_signed_residual_keV_per_a": sum(residuals) / len(residuals)}


def _calibrate(records: list[dict], direction: str) -> dict:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in records:
        residual = record.get(f"{direction}_signed_residual_keV_per_a")
        if residual is not None:
            groups[(str(record[f"{direction}_predictor"]), str(record["mass_region"]))].append(float(residual))
    output = {}
    for (predictor, region), values in sorted(groups.items()):
        centre = statistics.median(values)
        mad = statistics.median(abs(value - centre) for value in values)
        output[f"{predictor}|{region}"] = {"predictor": predictor, "mass_region": region, "sample_count": len(values), "median_signed_residual_keV_per_a": centre, "robust_sigma_keV_per_a": max(1e-9, 1.4826 * mad)}
    return output


def _sigma(record: Mapping[str, object], calibration: Mapping[str, dict], direction: str) -> Optional[float]:
    entry = calibration.get(f"{record[f'{direction}_predictor']}|{record['mass_region']}")
    if entry is None or int(entry.get("sample_count", 0)) < 8:
        return None
    return float(entry["robust_sigma_keV_per_a"])


def _is_z_eligible(record: Mapping[str, object]) -> bool:
    return record.get("z_prediction_keV_per_a") is not None and "ONE_SIDED" not in str(record["z_predictor"]) and int(record["a"]) >= 8


def _blend_record(record: dict, n_calibration: Mapping[str, dict], z_calibration: Mapping[str, dict], disagreement_sigma: float) -> dict:
    item = dict(record)
    n_prediction, z_prediction = item.get("n_prediction_keV_per_a"), item.get("z_prediction_keV_per_a")
    n_sigma = _sigma(item, n_calibration, "n") if n_prediction is not None else None
    z_sigma = _sigma(item, z_calibration, "z") if _is_z_eligible(item) else None
    item["n_robust_sigma_keV_per_a"], item["z_robust_sigma_keV_per_a"] = n_sigma, z_sigma
    item["directional_disagreement_keV_per_a"] = abs(float(n_prediction) - float(z_prediction)) if n_prediction is not None and z_prediction is not None else None
    raw_blend = weight_n = weight_z = None
    if n_prediction is not None and z_prediction is not None and n_sigma is not None and z_sigma is not None:
        pn, pz = 1.0 / (n_sigma * n_sigma), 1.0 / (z_sigma * z_sigma)
        weight_n, weight_z = pn / (pn + pz), pz / (pn + pz)
        raw_blend = weight_n * float(n_prediction) + weight_z * float(z_prediction)
    elif n_prediction is not None:
        raw_blend, weight_n, weight_z = float(n_prediction), 1.0, 0.0
    elif _is_z_eligible(item):
        raw_blend, weight_n, weight_z = float(z_prediction), 0.0, 1.0
    item["raw_blended_prediction_keV_per_a"], item["weight_n"], item["weight_z"] = raw_blend, weight_n, weight_z
    reasons = []
    if int(item["a"]) < 8:
        reasons.append("ULTRALIGHT_A_LT_8")
    if n_prediction is None and not _is_z_eligible(item):
        reasons.append("NO_ELIGIBLE_DIRECTION")
    disagreement = item.get("directional_disagreement_keV_per_a")
    if disagreement is not None and n_sigma is not None and z_sigma is not None:
        threshold = max(50.0, float(disagreement_sigma) * math.sqrt(n_sigma * n_sigma + z_sigma * z_sigma))
        item["directional_disagreement_threshold_keV_per_a"] = threshold
        if float(disagreement) > threshold:
            reasons.append("EXCESSIVE_DIRECTIONAL_DISAGREEMENT")
    else:
        item["directional_disagreement_threshold_keV_per_a"] = None
    item["guard_reasons"] = reasons
    item["guarded_blended_prediction_keV_per_a"] = None if reasons else raw_blend
    item["guard_decision"] = "ABSTAIN" if reasons else "PREDICT"
    return item


def build_report(rows: Iterable[Mapping[str, object]], source: str, disagreement_sigma: float = 3.0) -> dict:
    raw_rows = [dict(row) for row in rows]
    valid, rejected = [], []
    for index, row in enumerate(raw_rows):
        try:
            z, n = _int_field(row, "Z"), _int_field(row, "N")
            a = _int_field(row, "A") if row.get("A") not in (None, "") else z + n
            item = dict(row)
            item.update({"_z": z, "_n": n, "_a": a, "_entity": _entity(row, z, a)})
            valid.append(item)
        except (TypeError, ValueError) as exc:
            rejected.append({"row_index": index, "error": str(exc), "row": row})
    grid = {(item["_z"], item["_n"]): item for item in valid}
    chains: dict[int, list[dict]] = defaultdict(list)
    for item in valid:
        chains[item["_z"]].append(item)
    provisional = []
    for _, chain in chains.items():
        chain.sort(key=lambda item: item["_n"])
        by_n = {item["_n"]: item for item in chain}
        for item in chain:
            z, n, a = item["_z"], item["_n"], item["_a"]
            npred, npredictor, noffsets = _same_chain_prediction(by_n, n)
            zpred, zpredictor, zoffsets = _cross_element_prediction(grid, z, n)
            actual = _finite(item, "binding_energy_per_A_keV")
            provisional.append({"record_type": "UNIVERSAL_ATOMIC_TWO_AXIS_RECORD_V4", "entity": item["_entity"], "z": z, "n": n, "a": a, "mass_region": mass_region(a), "actual_binding_energy_per_A_keV": actual, "n_prediction_keV_per_a": npred, "n_predictor": npredictor, "n_support_offsets": noffsets, "n_signed_residual_keV_per_a": npred - actual if npred is not None and actual is not None else None, "z_prediction_keV_per_a": zpred, "z_predictor": zpredictor, "z_support_offsets": zoffsets, "z_signed_residual_keV_per_a": zpred - actual if zpred is not None and actual is not None else None})
    provisional.sort(key=lambda row: (row["z"], row["n"]))
    n_calibration, z_calibration = _calibrate(provisional, "n"), _calibrate(provisional, "z")
    records = [_blend_record(record, n_calibration, z_calibration, disagreement_sigma) for record in provisional]
    guard_counts, disagreement_values = Counter(), []
    error_by_band: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        guard_counts.update(record["guard_reasons"])
        disagreement = record.get("directional_disagreement_keV_per_a")
        if disagreement is not None:
            disagreement_values.append(float(disagreement))
            if record.get("raw_blended_prediction_keV_per_a") is not None and record.get("actual_binding_energy_per_A_keV") is not None:
                band = "LT_10" if disagreement < 10 else "10_TO_49" if disagreement < 50 else "50_TO_199" if disagreement < 200 else "GE_200"
                error_by_band[band].append(record)
        record["record_hash"] = certificate_hash(record)
    payload = {"report_type": "UNIVERSAL_ATOMIC_GUARDED_TWO_AXIS_REPORT_V4", "source": source, "rows_read": len(raw_rows), "rows_valid": len(records), "rows_rejected": len(rejected), "declared_disagreement_sigma": disagreement_sigma, "n_direction_metrics": _metrics(records, "n_prediction_keV_per_a"), "z_direction_metrics": _metrics(records, "z_prediction_keV_per_a"), "raw_blended_metrics": _metrics(records, "raw_blended_prediction_keV_per_a"), "guarded_blended_metrics": _metrics(records, "guarded_blended_prediction_keV_per_a"), "guard_reason_counts": dict(sorted(guard_counts.items())), "guarded_prediction_count": sum(r["guard_decision"] == "PREDICT" for r in records), "guarded_abstention_count": sum(r["guard_decision"] == "ABSTAIN" for r in records), "directional_disagreement_summary_keV_per_a": {"count": len(disagreement_values), "median": statistics.median(disagreement_values) if disagreement_values else None, "p90": _percentile(disagreement_values, 0.90), "p95": _percentile(disagreement_values, 0.95), "p99": _percentile(disagreement_values, 0.99), "maximum": max(disagreement_values) if disagreement_values else None}, "error_by_directional_disagreement_band": {key: _metrics(value, "raw_blended_prediction_keV_per_a") for key, value in sorted(error_by_band.items())}, "n_calibration": n_calibration, "z_calibration": z_calibration, "records": records, "rejected": rejected, "scientific_status": "GUARDED_IN_SAMPLE_TWO_AXIS_RESPONSE_NOT_EXTERNAL_VALIDATION", "calibration_note": "Axis uncertainties and disagreement thresholds are calibrated on leakage-safe residuals from this dataset; external or nested validation remains required."}
    payload["report_hash"] = certificate_hash(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-label", default="data/processed/ame_nubase_atomic_native.csv")
    parser.add_argument("--disagreement-sigma", type=float, default=3.0)
    parser.add_argument("--expected-hash")
    args = parser.parse_args()
    with Path(args.input).open("r", encoding="utf-8-sig", newline="") as handle:
        report = build_report(csv.DictReader(handle), args.source_label, args.disagreement_sigma)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.expected_hash and report["report_hash"] != args.expected_hash:
        raise SystemExit(f"hash mismatch: {report['report_hash']} != {args.expected_hash}")
    print(json.dumps({"report_hash": report["report_hash"], "guarded_blended_metrics": report["guarded_blended_metrics"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
