from __future__ import annotations

import argparse
import json
import re
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping


EXPECTED_C04_STATUS = (
    "PASS_CHROMIUM_C04_ACQUISITION_PACKET_READY_EXTERNAL_RESPONSE_REQUIRED"
)
EXPECTED_C05_STATUS = (
    "PASS_CHROMIUM_C05_CUT_SQUARE_ADAPTER_FROZEN_BETA_DATA_REQUIRED"
)
EXPECTED_CHANNELS = [
    "heat_capacity_Cp_anomaly",
    "resistivity_temperature_coefficient_drho_dT_anomaly",
]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def as_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError(f"unsupported rational value: {value!r}")


def fraction_json(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def beta_interval_from_bounds(
    bounds: Mapping[str, Any],
) -> tuple[Fraction, Fraction]:
    target_lower = as_fraction(bounds["target_norm_lower"])
    target_upper = as_fraction(bounds["target_norm_upper"])
    observer_upper = as_fraction(bounds["observer_norm_upper"])
    visible_singular_lower = as_fraction(bounds["visible_singular_lower"])

    if target_lower < 0 or target_upper < target_lower:
        raise ValueError("target norm bounds are invalid")
    if observer_upper <= 0:
        raise ValueError("observer norm upper bound must be positive")
    if visible_singular_lower <= 0:
        raise ValueError("visible singular lower bound must be positive")

    lower = target_lower**2 / observer_upper**2
    upper = target_upper**2 / visible_singular_lower**2
    if lower > upper:
        raise ValueError("computed beta interval is inverted")
    return lower, upper


def classify_beta_interval(
    lower: Fraction | None,
    upper: Fraction | None,
    *,
    target_visible: bool,
    bilateral_defect_upper: Fraction | None,
    bilateral_defect_tolerance: Fraction,
    alignment_certified: bool,
) -> str:
    if not target_visible:
        return "TARGET_BLIND_ADD_HIGHER_LAYER"
    if bilateral_defect_upper is None:
        return "DATA_REQUIRED"
    if bilateral_defect_upper > bilateral_defect_tolerance:
        return "OPEN_SEAM_OR_WRONG_CUT"
    if lower is None or upper is None:
        return "DATA_REQUIRED"
    if upper < 1:
        return "STRICT_NEEL_CUT_CLOSURE"
    if lower > 1:
        return "BURDEN_EXCEEDS_ONE"
    if lower == upper == 1 and alignment_certified:
        return "CRITICAL_ALIGNED_CLOSURE"
    return "THRESHOLD_INCONCLUSIVE"


def validate_intake_file(
    record: Mapping[str, Any], allowed_routes: set[str]
) -> list[str]:
    errors: list[str] = []
    required_text = (
        "original_filename",
        "source_route_id",
        "date_received",
        "rights_or_access_note",
        "media_type",
        "retained_location",
    )
    for key in required_text:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"intake file missing {key}")

    digest = record.get("sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        errors.append("intake file sha256 must be lowercase hexadecimal")
    if int(record.get("byte_count", 0)) <= 0:
        errors.append("intake file byte_count must be positive")
    if record.get("source_route_id") not in allowed_routes:
        errors.append("intake file source route is not admitted by C04")

    received = record.get("date_received")
    if isinstance(received, str) and ISO_DATE_RE.fullmatch(received):
        try:
            date.fromisoformat(received)
        except ValueError:
            errors.append("intake file date_received is invalid")
    elif received:
        errors.append("intake file date_received must be ISO YYYY-MM-DD")
    return errors


def run_synthetic_controls(
    controls: list[Mapping[str, Any]],
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for control in controls:
        control_id = str(control["id"])
        if control.get("target_visible") is False:
            lower = upper = None
        else:
            lower, upper = beta_interval_from_bounds(
                control["certified_bounds"]
            )
        classification = classify_beta_interval(
            lower,
            upper,
            target_visible=bool(control.get("target_visible", True)),
            bilateral_defect_upper=as_fraction(
                control.get("bilateral_defect_upper", "0")
            ),
            bilateral_defect_tolerance=as_fraction(
                control.get("bilateral_defect_tolerance", "0")
            ),
            alignment_certified=bool(
                control.get("alignment_certified", False)
            ),
        )
        results[control_id] = {
            "beta_lower": fraction_json(lower),
            "beta_upper": fraction_json(upper),
            "classification": classification,
            "expected_classification": control.get(
                "expected_classification"
            ),
        }
    return results


def _read_status(path: Path) -> str | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("status")


def audit(
    contract: dict[str, Any],
    packet: dict[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    upstream = contract.get("upstream_certificates", {})
    c04_status = _read_status(repository_root / upstream.get("c04_path", ""))
    c05_status = _read_status(repository_root / upstream.get("c05_path", ""))
    if c04_status != EXPECTED_C04_STATUS:
        errors.append("C04 upstream certificate missing or changed")
    if c05_status != EXPECTED_C05_STATUS:
        errors.append("C05 upstream certificate missing or changed")

    if packet.get("campaign") != contract.get("campaign"):
        errors.append("response packet campaign mismatch")
    if packet.get("schema_version") != "C06_CHROMIUM_RESPONSE_PACKET_V0_1":
        errors.append("response packet schema version changed")

    allowed_routes = set(
        contract.get("intake_contract", {}).get(
            "allowed_source_route_ids", []
        )
    )
    files = list(packet.get("provenance", {}).get("files", []))
    intake_errors = [
        error
        for record in files
        for error in validate_intake_file(record, allowed_routes)
    ]
    if len({record.get("sha256") for record in files}) != len(files):
        intake_errors.append("intake file hashes must be unique")
    errors.extend(intake_errors)
    intake_ready = bool(files) and not intake_errors

    sample = packet.get("sample_state", {})
    sample_ready = (
        isinstance(sample.get("sample_state_id"), str)
        and bool(sample.get("sample_state_id"))
        and sample.get("same_specimen") is True
        and sample.get("same_protocol") is True
        and sample.get("measurement_mode")
        == "AC_MODULATION_NEAR_EQUILIBRIUM"
    )

    coordinate = packet.get("transition_coordinate", {})
    if coordinate.get("universal_tn_used") is True:
        errors.append("universal TN is forbidden")
    coordinate_ready = (
        coordinate.get("source_specific_tn") is True
        and coordinate.get("universal_tn_used") is False
        and coordinate.get("tn_K") is not None
        and coordinate.get("tn_uncertainty_K") is not None
        and as_fraction(str(coordinate.get("tn_uncertainty_K"))) > 0
    )

    pairing = packet.get("bilateral_pairing", {})
    minimum_pairs = int(
        contract.get("pairing_contract", {}).get("minimum_pairs", 8)
    )
    pairing_ready = (
        pairing.get("both_sides_present") is True
        and int(pairing.get("accepted_pair_count", 0)) >= minimum_pairs
        and pairing.get("max_abs_tau_pair_mismatch") is not None
        and pairing.get("tau_pair_tolerance") is not None
        and as_fraction(str(pairing["max_abs_tau_pair_mismatch"]))
        <= as_fraction(str(pairing["tau_pair_tolerance"]))
        and isinstance(pairing.get("pair_table_sha256"), str)
        and SHA256_RE.fullmatch(pairing.get("pair_table_sha256", ""))
        is not None
    )

    channels = packet.get("channels", {})
    base = list(channels.get("base", []))
    base_ids = [item.get("channel_id") for item in base]
    channel_hashes_valid = all(
        isinstance(item.get("array_sha256"), str)
        and SHA256_RE.fullmatch(item.get("array_sha256", "")) is not None
        and int(item.get("point_count", 0)) > 0
        and isinstance(item.get("unit"), str)
        and bool(item.get("unit"))
        for item in base
    )
    channels_ready = (
        base_ids == EXPECTED_CHANNELS
        and channel_hashes_valid
        and channels.get("raw_unlike_unit_wedge_forbidden") is True
    )

    preprocessing = packet.get("preprocessing", {})
    if preprocessing.get("target_selected_after_seeing_data") is True:
        errors.append("post-hoc target selection is forbidden")
    preprocessing_ready = (
        preprocessing.get("baseline_rule_frozen_before_fit") is True
        and isinstance(preprocessing.get("baseline_rule"), str)
        and bool(preprocessing.get("baseline_rule"))
        and preprocessing.get("derivative_rule_frozen_before_fit") is True
        and isinstance(preprocessing.get("derivative_rule"), str)
        and bool(preprocessing.get("derivative_rule"))
        and preprocessing.get("target_selected_after_seeing_data") is False
    )

    metric = packet.get("metric", {})
    metric_ready = (
        metric.get("metric_symbol") == "H_Cr"
        and metric.get("positive_support_certified") is True
        and metric.get("whitening_applied") is True
        and isinstance(metric.get("covariance_source"), str)
        and bool(metric.get("covariance_source"))
        and isinstance(metric.get("whitened_observer_sha256"), str)
        and SHA256_RE.fullmatch(
            metric.get("whitened_observer_sha256", "")
        )
        is not None
    )

    observer = packet.get("observer", {})
    target_visible = bool(observer.get("target_visible", False))
    observer_ready = (
        observer.get("visible_quotient_certified") is True
        and observer.get("tower_depth") is not None
        and int(observer.get("tower_depth")) >= 0
        and isinstance(observer.get("visible_basis_sha256"), str)
        and SHA256_RE.fullmatch(observer.get("visible_basis_sha256", ""))
        is not None
    )

    target = packet.get("target", {})
    target_ready = (
        target.get("target_symbol") == "L_N"
        and target.get("frozen_before_fit") is True
        and target.get("post_hoc_peak_target") is False
        and isinstance(target.get("target_definition"), str)
        and bool(target.get("target_definition"))
        and isinstance(target.get("formula_sha256"), str)
        and SHA256_RE.fullmatch(target.get("formula_sha256", ""))
        is not None
    )

    bounds = packet.get("certified_bounds", {})
    bound_names = contract.get("interval_contract", {}).get(
        "required_certified_bounds", []
    )
    bounds_ready = bool(bound_names) and all(
        bounds.get(name) is not None for name in bound_names
    )

    readiness = {
        "intake_ready": intake_ready,
        "sample_ready": sample_ready,
        "coordinate_ready": coordinate_ready,
        "pairing_ready": pairing_ready,
        "channels_ready": channels_ready,
        "preprocessing_ready": preprocessing_ready,
        "metric_ready": metric_ready,
        "observer_ready": observer_ready,
        "target_ready": target_ready,
        "bounds_ready": bounds_ready,
    }
    ready_for_beta = all(readiness.values())
    readiness["ready_for_beta"] = ready_for_beta

    beta_lower: Fraction | None = None
    beta_upper: Fraction | None = None
    physical_classification = "DATA_REQUIRED"
    if ready_for_beta:
        try:
            beta_lower, beta_upper = beta_interval_from_bounds(bounds)
            physical_classification = classify_beta_interval(
                beta_lower,
                beta_upper,
                target_visible=target_visible,
                bilateral_defect_upper=as_fraction(
                    bounds["bilateral_defect_upper"]
                ),
                bilateral_defect_tolerance=as_fraction(
                    bounds["bilateral_defect_tolerance"]
                ),
                alignment_certified=bool(
                    packet.get("cut_square_alignment", {}).get(
                        "alignment_certified", False
                    )
                ),
            )
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"physical beta interval failed: {exc}")

    synthetic = run_synthetic_controls(
        contract.get("synthetic_controls", [])
    )
    for control_id, result in synthetic.items():
        if result["classification"] != result["expected_classification"]:
            errors.append(f"synthetic control {control_id} failed")

    if errors:
        status = "FAIL_CHROMIUM_C06_INTAKE_OR_BETA_INTERVAL_CONTRACT"
    elif ready_for_beta:
        status = "PASS_CHROMIUM_C06_PHYSICAL_BETA_INTERVAL_COMPUTED"
    else:
        status = "PASS_CHROMIUM_C06_ENGINE_FROZEN_PRIMARY_DATA_REQUIRED"

    return {
        "campaign": contract.get("campaign"),
        "status": status,
        "errors": errors,
        "upstream_statuses": {"C04": c04_status, "C05": c05_status},
        "response_packet_path": contract.get("response_packet_path"),
        "intake_file_count": len(files),
        "readiness": readiness,
        "beta_interval": {
            "lower": fraction_json(beta_lower),
            "upper": fraction_json(beta_upper),
        },
        "physical_classification": physical_classification,
        "interval_formula": {
            "lower": "(target_norm_lower/observer_norm_upper)^2",
            "upper": "(target_norm_upper/visible_singular_lower)^2",
        },
        "synthetic_controls": synthetic,
        "next_stage": contract.get("next_stage"),
        "claim_boundary": contract.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(
            "protocols/C06_CHROMIUM_PRIMARY_INTAKE_BETA_INTERVAL.json"
        ),
    )
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path("data/manifests/C06_CHROMIUM_RESPONSE_PACKET.json"),
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "releases/chromium-neel-c06/"
            "chromium_intake_beta_interval_certificate.json"
        ),
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    result = audit(contract, packet, args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
