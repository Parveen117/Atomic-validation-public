from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Mapping, Optional, Sequence

from src.rkf_nuclear_prediction import (
    build_observer_records,
    certificate_hash,
    cross_fitted_predictions,
    prediction_metrics,
)

REFINEMENT_TOLERANCE_KEV_PER_A = 1.0e-9
BILATERAL_TOLERANCE_KEV_PER_A = 1.0e-8


def _finite(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _index(records: Iterable[Mapping[str, object]]) -> dict[tuple[int, int], Mapping[str, object]]:
    return {
        (int(record["z"]), int(record["n"])): record
        for record in records
    }


def bilateral_reconstruction_defect(record: Mapping[str, object]) -> float:
    """Return the largest neutron/proton reconstruction defect.

    The declared nuclear cut exchanges the neutron and proton response axes.
    The cut-even and cut-odd packets must reconstruct both axis jets at every
    available derivative order.
    """
    even = record.get("cut_even_jet", {})
    odd = record.get("cut_odd_jet", {})
    neutron = record.get("neutron_jet", {})
    proton = record.get("proton_jet", {})
    defects: list[float] = []
    for key in ("value", "slope", "curvature", "jerk"):
        try:
            e = float(even[key])
            o = float(odd[key])
            n = float(neutron[key])
            p = float(proton[key])
        except (KeyError, TypeError, ValueError):
            continue
        defects.append(abs((e + o) - n))
        defects.append(abs((e - o) - p))
    return max(defects, default=float("inf"))


def classify_refinement(
    p1: Optional[float],
    p2: Optional[float],
    p3: Optional[float],
    bilateral_defect: float,
    tolerance: float = REFINEMENT_TOLERANCE_KEV_PER_A,
) -> str:
    if bilateral_defect > BILATERAL_TOLERANCE_KEV_PER_A:
        return "OPEN_BILATERAL_SEAM"
    if p1 is None or p2 is None or p3 is None:
        return "ABSTAIN_MISSING_JET_LEVEL"
    q2 = p2 - p1
    q3 = p3 - p2
    if abs(q2) <= tolerance and abs(q3) <= tolerance:
        return "EXACT_REFINEMENT_STABLE"
    if abs(q3) <= abs(q2) + tolerance:
        return "CONTRACTIVE_MEMORY"
    return "OPEN_REFINEMENT"


def _prediction_decisions(
    *,
    v5_source: str,
    v5_prediction: Optional[float],
    frozen_uam: Optional[float],
    p1: Optional[float],
    p2: Optional[float],
    p3: Optional[float],
    level1_guard: bool,
    level2_guard: bool,
    level3_guard: bool,
    refinement_classification: str,
) -> dict[str, object]:
    stable = refinement_classification in {
        "CONTRACTIVE_MEMORY",
        "EXACT_REFINEMENT_STABLE",
    }
    capstone_pass = stable and level3_guard

    if v5_prediction is None:
        return {
            "capstone_gate_pass": False,
            "v6_strict_prediction_keV_per_a": None,
            "v6_strict_source": "ABSTAIN_PRESERVE_FROZEN_COVERAGE",
            "v6_fallback_prediction_keV_per_a": None,
            "v6_fallback_source": "ABSTAIN_PRESERVE_FROZEN_COVERAGE",
            "v6_order_selected_prediction_keV_per_a": None,
            "v6_order_selected_source": "ABSTAIN_PRESERVE_FROZEN_COVERAGE",
        }

    if v5_source == "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR":
        return {
            "capstone_gate_pass": True,
            "v6_strict_prediction_keV_per_a": v5_prediction,
            "v6_strict_source": "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
            "v6_fallback_prediction_keV_per_a": v5_prediction,
            "v6_fallback_source": "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
            "v6_order_selected_prediction_keV_per_a": v5_prediction,
            "v6_order_selected_source": "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
        }

    strict = p3 if capstone_pass else None
    strict_source = (
        "RKF_LEVEL3_MADHAVA_CAPSTONE_PASS"
        if capstone_pass
        else "ABSTAIN_OPEN_OR_HIGH_BURDEN_SMRITI"
    )

    fallback = p3 if capstone_pass else frozen_uam
    fallback_source = (
        "RKF_LEVEL3_MADHAVA_CAPSTONE_PASS"
        if capstone_pass
        else "FROZEN_UAM_V4_FAIL_CLOSED_FALLBACK"
    )

    if capstone_pass:
        order_selected = p3
        order_source = "RKF_LEVEL3_MADHAVA_CAPSTONE_PASS"
    elif refinement_classification == "OPEN_REFINEMENT" and level2_guard and p2 is not None:
        order_selected = p2
        order_source = "RKF_LEVEL2_BEFORE_EXPANSIVE_THIRD_CORRECTION"
    elif level1_guard and p1 is not None and frozen_uam is None:
        order_selected = p1
        order_source = "RKF_LEVEL1_LAST_GUARDED_BODY"
    else:
        order_selected = frozen_uam
        order_source = "FROZEN_UAM_V4_FAIL_CLOSED_FALLBACK"

    return {
        "capstone_gate_pass": capstone_pass,
        "v6_strict_prediction_keV_per_a": strict,
        "v6_strict_source": strict_source,
        "v6_fallback_prediction_keV_per_a": fallback,
        "v6_fallback_source": fallback_source,
        "v6_order_selected_prediction_keV_per_a": order_selected,
        "v6_order_selected_source": order_source,
    }


def build_madhava_record(
    observer_record: Mapping[str, object],
    level1_record: Mapping[str, object],
    level2_record: Mapping[str, object],
    v5_record: Mapping[str, object],
) -> dict:
    actual = _finite(v5_record.get("actual_binding_energy_per_A_keV"))
    p1 = _finite(level1_record.get("rkf_prediction_keV_per_a"))
    p2 = _finite(level2_record.get("rkf_prediction_keV_per_a"))
    p3 = _finite(v5_record.get("rkf_prediction_keV_per_a"))
    bilateral_defect = bilateral_reconstruction_defect(observer_record)
    classification = classify_refinement(p1, p2, p3, bilateral_defect)

    q2 = None if p1 is None or p2 is None else p2 - p1
    q3 = None if p2 is None or p3 is None else p3 - p2
    if q2 is None or q3 is None:
        ratio = None
    elif abs(q2) <= REFINEMENT_TOLERANCE_KEV_PER_A:
        ratio = 0.0 if abs(q3) <= REFINEMENT_TOLERANCE_KEV_PER_A else None
    else:
        ratio = abs(q3) / abs(q2)

    tails = {
        "level1": None if actual is None or p1 is None else actual - p1,
        "level2": None if actual is None or p2 is None else actual - p2,
        "level3": None if actual is None or p3 is None else actual - p3,
    }
    closure_defects = {
        "level1": None if tails["level1"] is None else (p1 + tails["level1"] - actual),
        "level2": None if tails["level2"] is None else (p2 + tails["level2"] - actual),
        "level3": None if tails["level3"] is None else (p3 + tails["level3"] - actual),
    }
    transfer_defects = {
        "level1_to_level2": (
            None
            if tails["level1"] is None or tails["level2"] is None or q2 is None
            else tails["level2"] - (tails["level1"] - q2)
        ),
        "level2_to_level3": (
            None
            if tails["level2"] is None or tails["level3"] is None or q3 is None
            else tails["level3"] - (tails["level2"] - q3)
        ),
    }
    tail_descent = {
        "level1_to_level2": (
            None
            if tails["level1"] is None or tails["level2"] is None
            else abs(tails["level2"]) <= abs(tails["level1"])
        ),
        "level2_to_level3": (
            None
            if tails["level2"] is None or tails["level3"] is None
            else abs(tails["level3"]) <= abs(tails["level2"])
        ),
    }

    v5_prediction = _finite(v5_record.get("recognition_repair_prediction_keV_per_a"))
    frozen_uam = _finite(v5_record.get("frozen_uam_guarded_prediction_keV_per_a"))
    decisions = _prediction_decisions(
        v5_source=str(v5_record.get("recognition_repair_source", "")),
        v5_prediction=v5_prediction,
        frozen_uam=frozen_uam,
        p1=p1,
        p2=p2,
        p3=p3,
        level1_guard=bool(level1_record.get("burden_guard_pass")),
        level2_guard=bool(level2_record.get("burden_guard_pass")),
        level3_guard=bool(v5_record.get("burden_guard_pass")),
        refinement_classification=classification,
    )

    output = dict(v5_record)
    output.update(
        {
            "record_type": "RKF_MADHAVA_SMRITI_NUCLEAR_RECORD_V6",
            "rkf_level1_prediction_keV_per_a": p1,
            "rkf_level2_prediction_keV_per_a": p2,
            "rkf_level3_prediction_keV_per_a": p3,
            "rkf_level1_decoder_burden": _finite(level1_record.get("decoder_burden")),
            "rkf_level2_decoder_burden": _finite(level2_record.get("decoder_burden")),
            "rkf_level3_decoder_burden": _finite(v5_record.get("decoder_burden")),
            "rkf_level1_burden_guard_pass": bool(level1_record.get("burden_guard_pass")),
            "rkf_level2_burden_guard_pass": bool(level2_record.get("burden_guard_pass")),
            "rkf_level3_burden_guard_pass": bool(v5_record.get("burden_guard_pass")),
            "madhava_correction_q2_keV_per_a": q2,
            "madhava_correction_q3_keV_per_a": q3,
            "madhava_refinement_ratio": ratio,
            "madhava_refinement_classification": classification,
            "bilateral_reconstruction_defect_keV_per_a": bilateral_defect,
            "validation_smriti_tail_keV_per_a": tails,
            "validation_closure_defect_keV_per_a": closure_defects,
            "validation_transfer_defect_keV_per_a": transfer_defects,
            "validation_tail_descent": tail_descent,
            "validation_smriti_state": (
                "ABSTAIN_UNTYPED_TAIL"
                if tails["level3"] is None
                else (
                    "EXACT_FINITE_CLOSURE"
                    if abs(tails["level3"]) <= REFINEMENT_TOLERANCE_KEV_PER_A
                    else "MEMORY_CLOSED_VALIDATION"
                )
            ),
            **decisions,
        }
    )
    output["prediction_hash"] = certificate_hash(
        {key: value for key, value in output.items() if key != "prediction_hash"}
    )
    return output


def _fraction_true(values: Sequence[object]) -> Optional[float]:
    usable = [value for value in values if value is not None]
    if not usable:
        return None
    return sum(bool(value) for value in usable) / len(usable)


def _max_abs_nested(records: Sequence[Mapping[str, object]], field: str) -> Optional[float]:
    values: list[float] = []
    for record in records:
        nested = record.get(field, {})
        if not isinstance(nested, Mapping):
            continue
        for value in nested.values():
            number = _finite(value)
            if number is not None:
                values.append(abs(number))
    return max(values) if values else None


def _improvement(candidate: Mapping[str, object], baseline: Mapping[str, object], key: str) -> Optional[float]:
    left = _finite(candidate.get(key))
    right = _finite(baseline.get(key))
    if left is None or right in (None, 0.0):
        return None
    return (right - left) / right


def _comparison(candidate: Mapping[str, object], baseline: Mapping[str, object]) -> dict:
    return {
        "same_prediction_count": candidate.get("prediction_count") == baseline.get("prediction_count"),
        "mae_improvement_fraction": _improvement(
            candidate, baseline, "mean_absolute_residual_keV_per_a"
        ),
        "p95_improvement_fraction": _improvement(
            candidate, baseline, "p95_absolute_residual_keV_per_a"
        ),
        "p99_improvement_fraction": _improvement(
            candidate, baseline, "p99_absolute_residual_keV_per_a"
        ),
        "rmse_improvement_fraction": _improvement(
            candidate, baseline, "root_mean_square_residual_keV_per_a"
        ),
        "maximum_improvement_fraction": _improvement(
            candidate, baseline, "max_absolute_residual_keV_per_a"
        ),
    }


def build_madhava_smriti_report(
    rows: Iterable[Mapping[str, object]],
    frozen_report: Mapping[str, object],
    v5_report: Mapping[str, object],
    source: str,
    ridge: float = 1.0,
) -> dict:
    observer_records = build_observer_records(rows)
    level1 = cross_fitted_predictions(observer_records, level=1, ridge=ridge)
    level2 = cross_fitted_predictions(observer_records, level=2, ridge=ridge)
    observers = _index(observer_records)
    level1_index = _index(level1)
    level2_index = _index(level2)
    v5_index = _index(v5_report.get("records", []))

    records: list[dict] = []
    for key in sorted(v5_index):
        if key not in observers or key not in level1_index or key not in level2_index:
            continue
        records.append(
            build_madhava_record(
                observers[key],
                level1_index[key],
                level2_index[key],
                v5_index[key],
            )
        )

    classifications = Counter(
        str(record["madhava_refinement_classification"]) for record in records
    )
    source_counts = {
        field: dict(Counter(str(record.get(field)) for record in records))
        for field in (
            "v6_strict_source",
            "v6_fallback_source",
            "v6_order_selected_source",
        )
    }

    metrics = {
        "frozen_uam_v4": prediction_metrics(records, "frozen_uam_guarded_prediction_keV_per_a"),
        "recognition_repair_v5_1": prediction_metrics(
            records, "recognition_repair_prediction_keV_per_a"
        ),
        "rkf_level1": prediction_metrics(records, "rkf_level1_prediction_keV_per_a"),
        "rkf_level2": prediction_metrics(records, "rkf_level2_prediction_keV_per_a"),
        "rkf_level3": prediction_metrics(records, "rkf_level3_prediction_keV_per_a"),
        "v6_strict": prediction_metrics(records, "v6_strict_prediction_keV_per_a"),
        "v6_fallback": prediction_metrics(records, "v6_fallback_prediction_keV_per_a"),
        "v6_order_selected": prediction_metrics(
            records, "v6_order_selected_prediction_keV_per_a"
        ),
    }

    max_bilateral = max(
        (float(record["bilateral_reconstruction_defect_keV_per_a"]) for record in records),
        default=float("inf"),
    )
    max_closure = _max_abs_nested(records, "validation_closure_defect_keV_per_a")
    max_transfer = _max_abs_nested(records, "validation_transfer_defect_keV_per_a")
    identities_pass = (
        max_bilateral <= BILATERAL_TOLERANCE_KEV_PER_A
        and (max_closure is not None and max_closure <= BILATERAL_TOLERANCE_KEV_PER_A)
        and (max_transfer is not None and max_transfer <= BILATERAL_TOLERANCE_KEV_PER_A)
    )

    report = {
        "report_type": "RKF_MADHAVA_SMRITI_NUCLEAR_ADAPTER_REPORT_V6",
        "source": source,
        "source_theorems": {
            "recognition_kernel_framework_commit": "60b8bba2b4579d75c691af6589b00a764f24622b",
            "bilateral_jet_flow_capstone_certificate_sha256": "4f0f31183c6de9b354fbc90134cfcd14c8d6f55270f41c1e286f719c0e06b091",
            "madhava_smriti_certificate_sha256": "2dc970d0b180e6ae0c679879ac9d0aabbb138c9315942f8bc8d2565e1a539c35",
        },
        "adapter": {
            "declared_nuclear_cut": "NEUTRON_PROTON_RESPONSE_AXIS_EXCHANGE",
            "finite_chandas_bodies": "LEAVE_ONE_ELEMENT_OUT_RKF_LEVELS_1_2_3",
            "correction_transfers": ["P2_MINUS_P1", "P3_MINUS_P2"],
            "prospective_smriti_proxy": "ABS_Q3_OVER_ABS_Q2_WITH_ZERO_DENOMINATOR_GUARD",
            "validation_smriti_tail": "HELD_OUT_ACTUAL_MINUS_LEVEL_PREDICTION",
            "target_used_in_prediction_gate": False,
            "frozen_uam_v4_modified": False,
            "recognition_repair_v5_1_modified": False,
        },
        "record_count": len(records),
        "refinement_classification_counts": dict(classifications),
        "prediction_source_counts": source_counts,
        "identity_audit": {
            "maximum_bilateral_reconstruction_defect_keV_per_a": max_bilateral,
            "maximum_validation_closure_defect_keV_per_a": max_closure,
            "maximum_validation_transfer_defect_keV_per_a": max_transfer,
            "all_exact_identities_within_tolerance": identities_pass,
        },
        "convergence_audit": {
            "prospective_contractive_or_stable_fraction": (
                sum(
                    classifications[name]
                    for name in ("CONTRACTIVE_MEMORY", "EXACT_REFINEMENT_STABLE")
                )
                / len(records)
                if records
                else None
            ),
            "validation_tail_descent_level1_to_level2_fraction": _fraction_true(
                [record["validation_tail_descent"]["level1_to_level2"] for record in records]
            ),
            "validation_tail_descent_level2_to_level3_fraction": _fraction_true(
                [record["validation_tail_descent"]["level2_to_level3"] for record in records]
            ),
            "capstone_gate_pass_fraction": (
                sum(bool(record["capstone_gate_pass"]) for record in records) / len(records)
                if records
                else None
            ),
        },
        "metrics": metrics,
        "comparisons_to_v5_1": {
            "v6_strict": _comparison(metrics["v6_strict"], metrics["recognition_repair_v5_1"]),
            "v6_fallback": _comparison(metrics["v6_fallback"], metrics["recognition_repair_v5_1"]),
            "v6_order_selected": _comparison(
                metrics["v6_order_selected"], metrics["recognition_repair_v5_1"]
            ),
        },
        "claim_boundary": {
            "theorem_identities_applied_to_nuclear_response_jets": True,
            "historical_mass_values_used_only_for_validation_smriti": True,
            "prospective_gate_uses_actual_target": False,
            "external_future_mass_table_validation": False,
            "fundamental_nuclear_generator_identified": False,
            "prediction_improvement_claimed_before_report": False,
        },
        "records": records,
    }
    report["status"] = (
        "PASS_MADHAVA_SMRITI_NUCLEAR_ADAPTER_IDENTITIES"
        if identities_pass and len(records) == int(v5_report.get("record_count", -1))
        else "INCONCLUSIVE_MADHAVA_SMRITI_NUCLEAR_ADAPTER"
    )
    report["performance_status"] = (
        "PASS_V6_ORDER_SELECTED_BEATS_V5_1_ON_MAE"
        if (
            metrics["v6_order_selected"].get("mean_absolute_residual_keV_per_a") is not None
            and metrics["recognition_repair_v5_1"].get("mean_absolute_residual_keV_per_a") is not None
            and float(metrics["v6_order_selected"]["mean_absolute_residual_keV_per_a"])
            < float(metrics["recognition_repair_v5_1"]["mean_absolute_residual_keV_per_a"])
        )
        else "INCONCLUSIVE_V6_PERFORMANCE_NOT_PROMOTED"
    )
    report["report_hash"] = certificate_hash(report)
    return report
