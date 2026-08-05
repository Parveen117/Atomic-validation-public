from __future__ import annotations

from typing import Mapping, Sequence

from src.rkf_nuclear_prediction import certificate_hash, prediction_metrics

RECOGNITION_REPAIR_THRESHOLD_KEV_PER_A = 50.0


def _indexed_frozen_records(frozen_report: Mapping[str, object]) -> dict[tuple[int, int], Mapping[str, object]]:
    return {
        (int(record["z"]), int(record["n"])): record
        for record in frozen_report.get("records", [])
    }


def recognition_repair_decision(
    record: Mapping[str, object],
    frozen_record: Mapping[str, object],
    threshold_keV_per_a: float = RECOGNITION_REPAIR_THRESHOLD_KEV_PER_A,
) -> dict:
    """Select UAM in its coherence band and RKF only in the seam-stressed band.

    The 50 keV/A boundary is inherited from the frozen UAM-V4 prospective
    disagreement rule. It is not fitted to the RKF experiment outcomes.
    """
    uam = frozen_record.get("guarded_blended_prediction_keV_per_a")
    rkf = record.get("rkf_prediction_keV_per_a")
    disagreement = frozen_record.get("directional_disagreement_keV_per_a")

    if uam is None:
        return {
            "recognition_repair_prediction_keV_per_a": None,
            "recognition_repair_source": "ABSTAIN_PRESERVE_FROZEN_UAM_COVERAGE",
            "recognition_repair_triggered": False,
            "recognition_repair_reason": "FROZEN_UAM_V4_ABSTAINED",
        }

    seam_stressed = (
        disagreement is not None
        and float(disagreement) > float(threshold_keV_per_a)
    )
    if seam_stressed and rkf is not None:
        return {
            "recognition_repair_prediction_keV_per_a": float(rkf),
            "recognition_repair_source": "RKF_CROSS_FITTED_TAIL_REPAIR",
            "recognition_repair_triggered": True,
            "recognition_repair_reason": "DIRECTIONAL_DISAGREEMENT_ABOVE_PREDECLARED_50_KEV_PER_A",
        }

    return {
        "recognition_repair_prediction_keV_per_a": float(uam),
        "recognition_repair_source": "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
        "recognition_repair_triggered": False,
        "recognition_repair_reason": "WITHIN_PREDECLARED_COHERENCE_BAND",
    }


def _improvement_fraction(candidate: Mapping[str, object], baseline: Mapping[str, object], key: str) -> float | None:
    candidate_value = candidate.get(key)
    baseline_value = baseline.get(key)
    if candidate_value is None or baseline_value in (None, 0.0):
        return None
    return (float(baseline_value) - float(candidate_value)) / float(baseline_value)


def _source_metrics(records: Sequence[Mapping[str, object]], source: str, prediction_key: str) -> dict:
    selected = [record for record in records if record.get("recognition_repair_source") == source]
    return {
        "record_count": len(selected),
        "candidate_metrics": prediction_metrics(selected, prediction_key),
        "frozen_uam_v4_metrics": prediction_metrics(
            selected, "frozen_uam_guarded_prediction_keV_per_a"
        ),
        "rkf_metrics": prediction_metrics(selected, "rkf_prediction_keV_per_a"),
    }


def add_recognition_repair(
    report: Mapping[str, object],
    frozen_report: Mapping[str, object],
    threshold_keV_per_a: float = RECOGNITION_REPAIR_THRESHOLD_KEV_PER_A,
) -> dict:
    """Add the fixed-boundary Recognition Repair predictor to an RKF report."""
    frozen = _indexed_frozen_records(frozen_report)
    records = []
    for original in report.get("records", []):
        item = dict(original)
        frozen_record = frozen.get((int(item["z"]), int(item["n"])), {})
        item["frozen_uam_directional_disagreement_keV_per_a"] = frozen_record.get(
            "directional_disagreement_keV_per_a"
        )
        item["frozen_uam_directional_disagreement_threshold_keV_per_a"] = frozen_record.get(
            "directional_disagreement_threshold_keV_per_a"
        )
        item.update(
            recognition_repair_decision(
                item,
                frozen_record,
                threshold_keV_per_a=threshold_keV_per_a,
            )
        )
        item["prediction_hash"] = certificate_hash(
            {key: value for key, value in item.items() if key != "prediction_hash"}
        )
        records.append(item)

    candidate = prediction_metrics(records, "recognition_repair_prediction_keV_per_a")
    baseline = prediction_metrics(records, "frozen_uam_guarded_prediction_keV_per_a")
    same_coverage = candidate.get("prediction_count") == baseline.get("prediction_count")
    beats_mae = (
        candidate.get("mean_absolute_residual_keV_per_a") is not None
        and baseline.get("mean_absolute_residual_keV_per_a") is not None
        and float(candidate["mean_absolute_residual_keV_per_a"])
        < float(baseline["mean_absolute_residual_keV_per_a"])
    )
    beats_p95 = (
        candidate.get("p95_absolute_residual_keV_per_a") is not None
        and baseline.get("p95_absolute_residual_keV_per_a") is not None
        and float(candidate["p95_absolute_residual_keV_per_a"])
        < float(baseline["p95_absolute_residual_keV_per_a"])
    )
    beats_max = (
        candidate.get("max_absolute_residual_keV_per_a") is not None
        and baseline.get("max_absolute_residual_keV_per_a") is not None
        and float(candidate["max_absolute_residual_keV_per_a"])
        < float(baseline["max_absolute_residual_keV_per_a"])
    )

    output = dict(report)
    output.pop("report_hash", None)
    output["base_rkf_status"] = report.get("status")
    output["report_type"] = "RKF_RECOGNITION_REPAIR_NUCLEAR_PREDICTION_REPORT_V5_1"
    output["recognition_repair_rule"] = {
        "threshold_keV_per_a": float(threshold_keV_per_a),
        "threshold_provenance": "FROZEN_UAM_V4_MINIMUM_DIRECTIONAL_DISAGREEMENT_BOUNDARY",
        "coherent_sector_action": "USE_FROZEN_UAM_V4_GUARDED_PREDICTION",
        "seam_stressed_sector_action": "USE_LEAVE_ONE_ELEMENT_OUT_RKF_PREDICTION",
        "abstention_action": "PRESERVE_FROZEN_UAM_V4_ABSTENTION",
        "post_hoc_threshold_fit": False,
    }
    output["recognition_repair_metrics"] = candidate
    output["recognition_repair_comparison"] = {
        "frozen_uam_v4_metrics": baseline,
        "same_prediction_count": same_coverage,
        "mae_improvement_fraction": _improvement_fraction(
            candidate, baseline, "mean_absolute_residual_keV_per_a"
        ),
        "p95_improvement_fraction": _improvement_fraction(
            candidate, baseline, "p95_absolute_residual_keV_per_a"
        ),
        "p99_improvement_fraction": _improvement_fraction(
            candidate, baseline, "p99_absolute_residual_keV_per_a"
        ),
        "rmse_improvement_fraction": _improvement_fraction(
            candidate, baseline, "root_mean_square_residual_keV_per_a"
        ),
        "maximum_improvement_fraction": _improvement_fraction(
            candidate, baseline, "max_absolute_residual_keV_per_a"
        ),
        "beats_frozen_uam_v4_on_mae": beats_mae,
        "beats_frozen_uam_v4_on_p95": beats_p95,
        "beats_frozen_uam_v4_on_maximum": beats_max,
    }
    output["recognition_repair_sector_audit"] = {
        "coherent_sector": _source_metrics(
            records,
            "FROZEN_UAM_V4_COHERENT_LOCAL_PREDICTOR",
            "recognition_repair_prediction_keV_per_a",
        ),
        "seam_stressed_sector": _source_metrics(
            records,
            "RKF_CROSS_FITTED_TAIL_REPAIR",
            "recognition_repair_prediction_keV_per_a",
        ),
        "abstained_sector_count": sum(
            record.get("recognition_repair_prediction_keV_per_a") is None
            for record in records
        ),
    }
    output["records"] = records
    output["status"] = (
        "PASS_EXPLORATORY_RECOGNITION_REPAIR_BEATS_FROZEN_UAM_V4_SAME_COVERAGE"
        if same_coverage and beats_mae and beats_p95 and beats_max
        else "INCONCLUSIVE_EXPLORATORY_RECOGNITION_REPAIR_GATE"
    )
    output["report_hash"] = certificate_hash(output)
    return output
