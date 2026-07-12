from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Optional

DEFAULT_THRESHOLDS_KEV = (500.0, 1000.0, 1500.0, 2000.0)


def _finite(value: object) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _entity(row: Mapping[str, object]) -> str:
    symbol = str(row.get("Symbol") or row.get("symbol") or "X").strip()
    return f"{symbol}-{int(row['A'])}"


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _binding(by_n: Mapping[int, Mapping[str, object]], n: int) -> Optional[float]:
    row = by_n.get(n)
    return None if row is None else _finite(row.get("binding_energy_per_A_keV"))


def prediction_with_fallback(
    by_n: Mapping[int, Mapping[str, object]], n: int
) -> tuple[Optional[float], str, list[int]]:
    m4, m2 = _binding(by_n, n - 4), _binding(by_n, n - 2)
    p2, p4 = _binding(by_n, n + 2), _binding(by_n, n + 4)
    if all(value is not None for value in (m4, m2, p2, p4)):
        return (2.0 / 3.0) * (m2 + p2) - (1.0 / 6.0) * (m4 + p4), "SAME_PARITY_CUBIC_N2_N4", [-4, -2, 2, 4]
    if m2 is not None and p2 is not None:
        return (m2 + p2) / 2.0, "SAME_PARITY_LINEAR_N2", [-2, 2]
    if m4 is not None and m2 is not None:
        return 2.0 * m2 - m4, "ONE_SIDED_SAME_PARITY_LEFT", [-4, -2]
    if p2 is not None and p4 is not None:
        return 2.0 * p2 - p4, "ONE_SIDED_SAME_PARITY_RIGHT", [2, 4]
    return None, "INSUFFICIENT_SAME_PARITY_SUPPORT", []


def _drip_class(row: Mapping[str, object], threshold: float) -> tuple[str, dict[str, Optional[float]]]:
    values = {key: _finite(row.get(key)) for key in ("S_n_keV", "S_2n_keV", "S_p_keV", "S_2p_keV")}
    neutron = [values["S_n_keV"], values["S_2n_keV"]]
    proton = [values["S_p_keV"], values["S_2p_keV"]]
    if any(value is not None and value <= 0 for value in neutron):
        name = "NEUTRON_DRIP_OR_UNBOUND"
    elif any(value is not None and value <= 0 for value in proton):
        name = "PROTON_DRIP_OR_UNBOUND"
    elif any(value is not None and value <= threshold for value in neutron):
        name = "NEAR_NEUTRON_DRIP_BOUNDARY"
    elif any(value is not None and value <= threshold for value in proton):
        name = "NEAR_PROTON_DRIP_BOUNDARY"
    else:
        name = "BOUND_AWAY_FROM_DECLARED_THRESHOLD"
    return name, values


def _mass_region(a: int) -> str:
    if a < 20:
        return "ULTRALIGHT"
    if a < 60:
        return "LIGHT"
    if a < 140:
        return "MEDIUM"
    return "HEAVY"


def _metric_summary(records: list[dict]) -> dict:
    residuals = [float(row["signed_residual_keV_per_a"]) for row in records if row.get("signed_residual_keV_per_a") is not None]
    if not residuals:
        return {"count": len(records), "residual_count": 0, "mean_absolute_residual_keV_per_a": None, "root_mean_square_residual_keV_per_a": None, "mean_signed_residual_keV_per_a": None}
    return {
        "count": len(records),
        "residual_count": len(residuals),
        "mean_absolute_residual_keV_per_a": sum(abs(x) for x in residuals) / len(residuals),
        "root_mean_square_residual_keV_per_a": math.sqrt(sum(x * x for x in residuals) / len(residuals)),
        "mean_signed_residual_keV_per_a": sum(residuals) / len(residuals),
    }


def _distance(a: dict, b: dict) -> float:
    distance = abs(a["a"] - b["a"]) + 2.0 * abs(a["z"] - b["z"])
    for key in ("S_n_keV", "S_2n_keV"):
        av, bv = a["separation_energy_keV"].get(key), b["separation_energy_keV"].get(key)
        distance += 2.0 if av is None or bv is None else min(5.0, abs(av - bv) / 1000.0)
    return distance


def analyze_rows(
    rows: Iterable[Mapping[str, object]],
    halo_candidates: Optional[set[str]] = None,
    thresholds_keV: tuple[float, ...] = DEFAULT_THRESHOLDS_KEV,
    controls_per_halo: int = 3,
    source: str = "in-memory",
) -> dict:
    candidates = set(halo_candidates or set())
    thresholds = tuple(sorted({float(x) for x in thresholds_keV}))
    if not thresholds or any(x <= 0 for x in thresholds):
        raise ValueError("all thresholds must be positive")

    chains: dict[int, list[dict]] = defaultdict(list)
    rejected: list[dict] = []
    for index, raw in enumerate(rows):
        row = dict(raw)
        try:
            z, n, a = int(row["Z"]), int(row["N"]), int(row["A"])
            if a != z + n:
                raise ValueError("A must equal Z + N")
            row.update({"_z": z, "_n": n, "_a": a, "_entity": _entity(row)})
            chains[z].append(row)
        except (KeyError, TypeError, ValueError) as exc:
            rejected.append({"row_index": index, "error": str(exc), "row": row})

    records: list[dict] = []
    for chain in chains.values():
        chain.sort(key=lambda item: item["_n"])
        by_n = {item["_n"]: item for item in chain}
        for row in chain:
            actual = _finite(row.get("binding_energy_per_A_keV"))
            predicted, predictor, offsets = prediction_with_fallback(by_n, row["_n"])
            residual = None if actual is None or predicted is None else predicted - actual
            sweep = {}
            reference_values = None
            for threshold in thresholds:
                label, values = _drip_class(row, threshold)
                sweep[str(int(threshold) if threshold.is_integer() else threshold)] = label
                if threshold == 1000.0 or reference_values is None:
                    reference_values = values
            reference_key = "1000" if "1000" in sweep else next(iter(sweep))
            record = {
                "record_type": "ATOMIC_EULER_EXOTIC_EVIDENCE_RECORD_V10_1_PUBLIC",
                "entity": row["_entity"], "z": row["_z"], "n": row["_n"], "a": row["_a"],
                "mass_region": _mass_region(row["_a"]),
                "external_halo_candidate": row["_entity"] in candidates,
                "predictor": predictor, "support_offsets": offsets,
                "actual_binding_energy_per_A_keV": actual,
                "predicted_binding_energy_per_A_keV": predicted,
                "signed_residual_keV_per_a": residual,
                "absolute_residual_keV_per_a": None if residual is None else abs(residual),
                "separation_energy_keV": reference_values,
                "drip_class": sweep[reference_key],
                "threshold_sweep": sweep,
            }
            record["record_hash"] = _hash(record)
            records.append(record)

    records.sort(key=lambda item: (item["z"], item["n"]))
    halo_records = [row for row in records if row["external_halo_candidate"]]
    matched = []
    for halo in halo_records:
        controls = [row for row in records if not row["external_halo_candidate"] and row["mass_region"] == halo["mass_region"] and row["drip_class"] == halo["drip_class"] and row["signed_residual_keV_per_a"] is not None]
        controls.sort(key=lambda row: (_distance(halo, row), row["z"], row["n"]))
        controls = controls[: max(0, int(controls_per_halo))]
        matched.append({
            "halo_entity": halo["entity"],
            "halo_predictor": halo["predictor"],
            "halo_absolute_residual_keV_per_a": halo["absolute_residual_keV_per_a"],
            "control_entities": [row["entity"] for row in controls],
            "control_predictors": [row["predictor"] for row in controls],
            "control_absolute_residuals_keV_per_a": [row["absolute_residual_keV_per_a"] for row in controls],
        })

    predictor_groups: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        predictor_groups[row["predictor"]].append(row)
    report = {
        "report_type": "ATOMIC_EULER_HALO_AND_DRIP_EVIDENCE_REPORT_V10_1_PUBLIC",
        "source": source,
        "rows_read": sum(len(chain) for chain in chains.values()) + len(rejected),
        "rows_valid": len(records), "rows_rejected": len(rejected),
        "thresholds_keV": list(thresholds),
        "halo_candidates_present": [row["entity"] for row in halo_records],
        "halo_candidate_metrics": _metric_summary(halo_records),
        "predictor_metrics": {name: _metric_summary(group) for name, group in sorted(predictor_groups.items())},
        "matched_halo_controls": matched,
        "records": records,
        "external_annotation_note": "Halo labels are external benchmark metadata and never enter prediction values or control-distance scoring.",
        "scientific_boundary": "This report screens mass-surface behaviour and does not alone establish spatial halo structure.",
        "rejected": rejected,
    }
    report["report_hash"] = _hash(report)
    return report


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_annotations(path: Optional[Path]) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("halo_candidates", []) if isinstance(payload, dict) else payload
    return {str(value) for value in values}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the public UAM halo and drip-line V10.1 evidence report")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--annotations")
    parser.add_argument("--thresholds-keV", nargs="+", type=float, default=list(DEFAULT_THRESHOLDS_KEV))
    parser.add_argument("--controls-per-halo", type=int, default=3)
    args = parser.parse_args()
    report = analyze_rows(_read_csv(Path(args.input)), _read_annotations(Path(args.annotations)) if args.annotations else set(), tuple(args.thresholds_keV), args.controls_per_halo, args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("rows_read", "rows_valid", "rows_rejected", "halo_candidates_present", "predictor_metrics", "report_hash")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
