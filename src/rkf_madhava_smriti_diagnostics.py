from __future__ import annotations

import math
from typing import Mapping, Optional, Sequence

from src.rkf_nuclear_prediction import certificate_hash, prediction_metrics


def _finite(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _pearson(pairs: Sequence[tuple[float, float]]) -> Optional[float]:
    if len(pairs) < 3:
        return None
    left = [pair[0] for pair in pairs]
    right = [pair[1] for pair in pairs]
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right)
    )
    left_scale = math.sqrt(sum((x - left_mean) ** 2 for x in left))
    right_scale = math.sqrt(sum((y - right_mean) ** 2 for y in right))
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    return numerator / (left_scale * right_scale)


def _same_support_audit(
    records: Sequence[Mapping[str, object]],
    candidate_key: str,
    baseline_key: str,
) -> dict:
    support = [record for record in records if record.get(candidate_key) is not None]
    candidate = prediction_metrics(support, candidate_key)
    baseline = prediction_metrics(support, baseline_key)
    differences = [
        abs(float(record[candidate_key]) - float(record[baseline_key]))
        for record in support
        if record.get(baseline_key) is not None
    ]
    return {
        "support_count": len(support),
        "candidate_metrics": candidate,
        "v5_1_same_support_metrics": baseline,
        "maximum_prediction_difference_from_v5_1_keV_per_a": (
            max(differences) if differences else None
        ),
        "identical_to_v5_1_on_support": (
            bool(differences) and max(differences) <= 1.0e-12
        ),
    }


def _classification_metrics(
    records: Sequence[Mapping[str, object]],
    classification: str,
) -> dict:
    selected = [
        record
        for record in records
        if record.get("recognition_repair_source") == "RKF_CROSS_FITTED_TAIL_REPAIR"
        and record.get("madhava_refinement_classification") == classification
    ]
    return {
        "record_count": len(selected),
        "rkf_level3_metrics": prediction_metrics(
            selected, "rkf_level3_prediction_keV_per_a"
        ),
        "v5_1_metrics": prediction_metrics(
            selected, "recognition_repair_prediction_keV_per_a"
        ),
    }


def _burden_metrics(
    records: Sequence[Mapping[str, object]],
    burden_pass: bool,
) -> dict:
    selected = [
        record
        for record in records
        if record.get("recognition_repair_source") == "RKF_CROSS_FITTED_TAIL_REPAIR"
        and bool(record.get("rkf_level3_burden_guard_pass")) is burden_pass
    ]
    return {
        "record_count": len(selected),
        "rkf_level3_metrics": prediction_metrics(
            selected, "rkf_level3_prediction_keV_per_a"
        ),
    }


def add_honest_v6_diagnostics(report: Mapping[str, object]) -> dict:
    """Add same-support and proxy diagnostics without changing predictions."""
    output = dict(report)
    output.pop("report_hash", None)
    records = [dict(record) for record in report.get("records", [])]

    strict_support = _same_support_audit(
        records,
        "v6_strict_prediction_keV_per_a",
        "recognition_repair_prediction_keV_per_a",
    )
    fallback_support = _same_support_audit(
        records,
        "v6_fallback_prediction_keV_per_a",
        "recognition_repair_prediction_keV_per_a",
    )
    order_support = _same_support_audit(
        records,
        "v6_order_selected_prediction_keV_per_a",
        "recognition_repair_prediction_keV_per_a",
    )

    newly_abstained = [
        record
        for record in records
        if record.get("recognition_repair_prediction_keV_per_a") is not None
        and record.get("v6_strict_prediction_keV_per_a") is None
    ]

    ratio_error_pairs: list[tuple[float, float]] = []
    burden_error_pairs: list[tuple[float, float]] = []
    for record in records:
        if record.get("recognition_repair_source") != "RKF_CROSS_FITTED_TAIL_REPAIR":
            continue
        prediction = _finite(record.get("rkf_level3_prediction_keV_per_a"))
        actual = _finite(record.get("actual_binding_energy_per_A_keV"))
        if prediction is None or actual is None:
            continue
        absolute_error = abs(prediction - actual)
        ratio = _finite(record.get("madhava_refinement_ratio"))
        burden = _finite(record.get("rkf_level3_decoder_burden"))
        if ratio is not None:
            ratio_error_pairs.append((ratio, absolute_error))
        if burden is not None:
            burden_error_pairs.append((burden, absolute_error))

    output["same_support_audit"] = {
        "v6_strict": strict_support,
        "v6_fallback": fallback_support,
        "v6_order_selected": order_support,
        "strict_new_abstention_count": len(newly_abstained),
        "strict_newly_abstained_v5_1_metrics": prediction_metrics(
            newly_abstained, "recognition_repair_prediction_keV_per_a"
        ),
        "strict_newly_abstained_frozen_uam_metrics": prediction_metrics(
            newly_abstained, "frozen_uam_guarded_prediction_keV_per_a"
        ),
    }
    output["refinement_proxy_audit"] = {
        "seam_stressed_metrics_by_refinement_class": {
            "CONTRACTIVE_MEMORY": _classification_metrics(
                records, "CONTRACTIVE_MEMORY"
            ),
            "OPEN_REFINEMENT": _classification_metrics(
                records, "OPEN_REFINEMENT"
            ),
            "EXACT_REFINEMENT_STABLE": _classification_metrics(
                records, "EXACT_REFINEMENT_STABLE"
            ),
        },
        "seam_stressed_metrics_by_level3_burden_guard": {
            "PASS": _burden_metrics(records, True),
            "FAIL": _burden_metrics(records, False),
        },
        "absolute_error_correlation_with_refinement_ratio": _pearson(
            ratio_error_pairs
        ),
        "absolute_error_correlation_with_level3_decoder_burden": _pearson(
            burden_error_pairs
        ),
        "refinement_ratio_promoted_as_risk_score": False,
        "reason": (
            "The correction-ratio ordering is an algebraic refinement audit, "
            "not a validated prospective error ranking on this chart."
        ),
    }

    strict_identical = bool(strict_support["identical_to_v5_1_on_support"])
    fallback_mae = _finite(
        fallback_support["candidate_metrics"].get(
            "mean_absolute_residual_keV_per_a"
        )
    )
    fallback_v5_mae = _finite(
        fallback_support["v5_1_same_support_metrics"].get(
            "mean_absolute_residual_keV_per_a"
        )
    )
    order_mae = _finite(
        order_support["candidate_metrics"].get(
            "mean_absolute_residual_keV_per_a"
        )
    )
    order_v5_mae = _finite(
        order_support["v5_1_same_support_metrics"].get(
            "mean_absolute_residual_keV_per_a"
        )
    )
    no_same_coverage_improvement = (
        fallback_mae is not None
        and fallback_v5_mae is not None
        and order_mae is not None
        and order_v5_mae is not None
        and fallback_mae >= fallback_v5_mae
        and order_mae >= order_v5_mae
    )

    output["performance_status"] = (
        "PASS_IDENTITIES_V5_1_REMAINS_BEST_SAME_COVERAGE_RATIO_NOT_PROMOTED"
        if strict_identical and no_same_coverage_improvement
        else "INCONCLUSIVE_V6_DIAGNOSTIC_STATUS"
    )
    output["promotion_decision"] = {
        "best_same_coverage_predictor": "RECOGNITION_REPAIR_V5_1",
        "v6_strict_interpretation": (
            "SELECTIVE_ABSTENTION_AUDIT; NOT A NEW POINT PREDICTOR"
        ),
        "v6_fallback_promoted": False,
        "v6_order_selected_promoted": False,
        "madhava_smriti_adapter_promoted_for": [
            "BILATERAL_IDENTITY_AUDIT",
            "CORRECTION_TO_TAIL_TRANSFER_AUDIT",
            "OBSERVER_DEPTH_ABLATION",
        ],
    }
    output["claim_boundary"] = dict(output.get("claim_boundary", {}))
    output["claim_boundary"].update(
        {
            "strict_metric_gain_is_same_support_prediction_gain": False,
            "strict_metric_gain_is_selective_abstention": True,
            "v5_1_retained_as_best_same_coverage_predictor": True,
            "refinement_ratio_validated_as_error_score": False,
        }
    )
    output["records"] = records
    output["report_hash"] = certificate_hash(output)
    return output
