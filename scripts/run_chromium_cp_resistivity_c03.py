from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_SOURCE_ID = "SIMULTANEOUS_CP_DRHODT_1969"
EXPECTED_DOI = "10.1016/0038-1098(69)90464-5"
EXPECTED_PII = "0038109869904645"
EXPECTED_AUTHORS = ["M. B. Salamon", "D. S. Simons", "P. R. Garnier"]
EXPECTED_CHANNELS = ["heat_capacity_Cp", "resistivity_temperature_coefficient_drho_dT"]
EXPECTED_MODE = "AC_MODULATION_NEAR_EQUILIBRIUM"
EXPECTED_BRANCH = "MODULATION_BRANCH_NOT_HEATING_COOLING_BRANCH"


def audit(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    source = contract.get("primary_source", {})
    experiment = contract.get("source_supported_experiment", {})
    acquisition = contract.get("acquisition_audit", {})
    digitization = contract.get("digitization_contract", {})
    state = contract.get("current_digitization_state", {})

    if source.get("source_id") != EXPECTED_SOURCE_ID:
        errors.append("primary source id changed")
    if source.get("doi") != EXPECTED_DOI:
        errors.append("primary DOI changed")
    if source.get("pii") != EXPECTED_PII:
        errors.append("primary PII changed")
    if source.get("authors") != EXPECTED_AUTHORS:
        errors.append("primary author sequence changed")
    if source.get("pages") != [1035, 1038]:
        errors.append("primary page range changed")
    if source.get("official_landing_page_verified") is not True:
        errors.append("official landing page must remain verified")
    if source.get("official_abstract_verified") is not True:
        errors.append("official abstract must remain verified")

    if experiment.get("measurement_mode") != EXPECTED_MODE:
        errors.append("measurement mode must remain AC modulation")
    if experiment.get("thermal_branch_semantics") != EXPECTED_BRANCH:
        errors.append("modulation branch cannot be relabeled as heating or cooling")
    if experiment.get("channels") != EXPECTED_CHANNELS:
        errors.append("same-specimen channel pair changed")
    for key in ("same_specimen", "simultaneous_measurement", "common_temperature_calibration"):
        if experiment.get(key) is not True:
            errors.append(f"experiment gate {key} must remain true")
    if experiment.get("numeric_critical_exponents_available_from_verified_abstract") is not False:
        errors.append("numeric critical exponents cannot be promoted from the abstract")

    expected_false_acquisition = (
        "official_full_text_pdf_acquired",
        "official_or_author_figure_bitmap_acquired",
        "primary_figure_page_number_verified",
        "primary_figure_identifier_verified",
        "author_machine_readable_arrays_acquired",
        "repository_or_library_exact_primary_file_found",
        "public_machine_readable_curve_found",
        "secondary_thesis_or_review_may_be_used_as_primary_figure_proxy",
    )
    for key in expected_false_acquisition:
        if acquisition.get(key) is not False:
            errors.append(f"acquisition state {key} must remain false until evidence is pinned")
    if acquisition.get("figure_bytes_sha256") is not None:
        errors.append("figure hash cannot exist before figure acquisition")
    if acquisition.get("full_text_pdf_sha256") is not None:
        errors.append("PDF hash cannot exist before PDF acquisition")

    required_true = (
        "primary_figure_bytes_required",
        "figure_hash_required",
        "axis_scale_type_required",
        "panel_bounds_required",
        "curve_identity_and_marker_style_required",
        "pixel_pick_uncertainty_required",
        "axis_tick_uncertainty_required",
        "temperature_calibration_uncertainty_required",
        "branch_or_modulation_label_required",
        "no_abstract_to_curve_conversion",
        "no_secondary_figure_proxy",
        "no_numeric_exponent_inference_from_later_papers",
        "no_curvature_before_digitization_certificate",
    )
    for key in required_true:
        if digitization.get(key) is not True:
            errors.append(f"digitization gate {key} must remain true")
    if digitization.get("minimum_points_per_channel") != 20:
        errors.append("minimum point count per channel must remain twenty")
    if digitization.get("x_axis_calibration_points_required") != 2:
        errors.append("x-axis calibration requires two points")
    if digitization.get("y_axis_calibration_points_required_per_panel") != 2:
        errors.append("each y-axis requires two calibration points")

    expected_false_state = (
        "x_axis_calibrated",
        "heat_capacity_y_axis_calibrated",
        "drho_dT_y_axis_calibrated",
        "pixel_uncertainty_frozen",
        "temperature_uncertainty_frozen",
        "shared_calibration_covariance_frozen",
        "digitization_allowed",
        "derivative_or_curvature_allowed",
        "anomaly_significance_allowed",
    )
    for key in expected_false_state:
        if state.get(key) is not False:
            errors.append(f"current digitization state {key} must remain false")
    if int(state.get("heat_capacity_point_count", -1)) != 0:
        errors.append("heat-capacity point count must remain zero")
    if int(state.get("drho_dT_point_count", -1)) != 0:
        errors.append("drho/dT point count must remain zero")

    figure_ready = bool(
        acquisition.get("official_or_author_figure_bitmap_acquired")
        and acquisition.get("figure_bytes_sha256")
        and acquisition.get("primary_figure_page_number_verified")
        and acquisition.get("primary_figure_identifier_verified")
    )
    axes_ready = bool(
        state.get("x_axis_calibrated")
        and state.get("heat_capacity_y_axis_calibrated")
        and state.get("drho_dT_y_axis_calibrated")
    )
    uncertainty_ready = bool(
        state.get("pixel_uncertainty_frozen")
        and state.get("temperature_uncertainty_frozen")
        and state.get("shared_calibration_covariance_frozen")
    )
    points_ready = (
        int(state.get("heat_capacity_point_count", 0))
        >= int(digitization.get("minimum_points_per_channel", 20))
        and int(state.get("drho_dT_point_count", 0))
        >= int(digitization.get("minimum_points_per_channel", 20))
    )
    computed_digitization_ready = figure_ready and axes_ready and uncertainty_ready and points_ready

    if state.get("digitization_allowed") is True and not computed_digitization_ready:
        errors.append("digitization cannot be allowed before all figure, axis, uncertainty and point gates pass")
    if state.get("derivative_or_curvature_allowed") is True and not computed_digitization_ready:
        errors.append("curvature cannot be allowed before digitization is complete")
    if state.get("anomaly_significance_allowed") is True and not uncertainty_ready:
        errors.append("significance cannot be allowed without uncertainty and covariance")

    if errors:
        status = "FAIL_CHROMIUM_C03_DIGITIZATION_CONTRACT"
    elif computed_digitization_ready:
        status = "PASS_CHROMIUM_C03_DIGITIZATION_READY"
    else:
        status = "PASS_CHROMIUM_C03_ACQUISITION_AUDIT_DIGITIZATION_BLOCKED"

    return {
        "campaign": contract.get("campaign"),
        "status": status,
        "errors": errors,
        "primary_source_id": source.get("source_id"),
        "primary_doi": source.get("doi"),
        "primary_pii": source.get("pii"),
        "primary_authors": source.get("authors"),
        "primary_pages": source.get("pages"),
        "source_metadata_verified": (
            source.get("official_landing_page_verified") is True
            and source.get("official_abstract_verified") is True
        ),
        "measurement_mode": experiment.get("measurement_mode"),
        "thermal_branch_semantics": experiment.get("thermal_branch_semantics"),
        "same_specimen": bool(experiment.get("same_specimen")),
        "simultaneous_measurement": bool(experiment.get("simultaneous_measurement")),
        "common_temperature_calibration": bool(experiment.get("common_temperature_calibration")),
        "channels": experiment.get("channels"),
        "abstract_supported_relation": experiment.get("abstract_supported_relation"),
        "numeric_critical_exponents_available": bool(
            experiment.get("numeric_critical_exponents_available_from_verified_abstract")
        ),
        "search_attempt_count": len(acquisition.get("search_attempts", [])),
        "full_text_pdf_acquired": bool(acquisition.get("official_full_text_pdf_acquired")),
        "primary_figure_acquired": bool(
            acquisition.get("official_or_author_figure_bitmap_acquired")
        ),
        "author_arrays_acquired": bool(acquisition.get("author_machine_readable_arrays_acquired")),
        "figure_ready": figure_ready,
        "axes_ready": axes_ready,
        "uncertainty_ready": uncertainty_ready,
        "points_ready": points_ready,
        "heat_capacity_point_count": int(state.get("heat_capacity_point_count", 0)),
        "drho_dT_point_count": int(state.get("drho_dT_point_count", 0)),
        "digitization_ready": computed_digitization_ready,
        "digitization_allowed": bool(state.get("digitization_allowed")),
        "curvature_allowed": bool(state.get("derivative_or_curvature_allowed")),
        "anomaly_significance_allowed": bool(state.get("anomaly_significance_allowed")),
        "decisive_reasons": [
            "The official publisher metadata and abstract verify a simultaneous same-specimen AC-modulation experiment with Cp and drho/dT channels.",
            "The verified abstract provides only a relation between critical exponents, not numeric exponent values or pointwise curves.",
            "No publisher or author PDF, primary figure bitmap, or machine-readable arrays are pinned.",
            "Axis calibration, pixel uncertainty, temperature uncertainty and shared calibration covariance therefore remain unavailable.",
            "Digitization, curvature and anomaly significance remain fail-closed until the primary figure or author arrays are acquired."
        ],
        "required_acquisition_package": contract.get("required_acquisition_package", []),
        "next_stage": contract.get("next_stage"),
        "claim_boundary": contract.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path("protocols/C03_CHROMIUM_SIMULTANEOUS_CP_RESISTIVITY_DIGITIZATION.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("releases/chromium-neel-c03/chromium_cp_resistivity_certificate.json"),
    )
    args = parser.parse_args()
    result = audit(json.loads(args.contract.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
