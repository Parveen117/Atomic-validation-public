from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence


EXPECTED_FRAMEWORK_REPOSITORY = "Parveen117/Recognition-Kernel-Framework"
EXPECTED_FRAMEWORK_BRANCH = "agent/thermodynamic-cut-square-theorem"
EXPECTED_FRAMEWORK_COMMIT = "97ab70eb3663840aa5161ccddcbb70fafe75a80b"
EXPECTED_FRAMEWORK_FILES = [
    (
        "theorum/thermodynamics/10_thermodynamic_cut_square_response_decomposition.md",
        "b4ab0dcfb22bad997b5c1fe259e3b2940e0ec200",
        "THERMODYNAMIC_CUT_SQUARE_AND_SHARP_BURDEN",
    ),
    (
        "theorum/43_bilateral_jet_flow_recognition_capstone_theorem.md",
        "95a83b98f79005cc00a2d718f717bad575196af3",
        "JET_OBSERVER_AND_BETA_ADMISSIBILITY",
    ),
    (
        "theorum/42_cut_graded_lambda_jacobian_tower_theorem.md",
        "b7850a2b059dfc0e072f9c423fefacff5233c287",
        "HIGHER_LAYER_TARGET_REPAIR",
    ),
    (
        "theorum/41_cut_graded_universal_generator_theorem.md",
        "2fd898a5ffa26f0a5fbbed4ca1223dad3c230266",
        "CUT_LOOP_SEAM_CURVATURE",
    ),
    (
        "theorum/thermodynamics/04_projection_defect_and_source_overlap.md",
        "3acb5751711ff5754186077f74426332050ded9a",
        "PROJECTION_DEFECT_AND_GRAM_POSITIVITY",
    ),
    (
        "papers/rkf_completed_weil_endpoint/main.tex",
        "875757b5f43dda265924c89c70cd51691f1fd3a4",
        "RH_ARCHITECTURE_REFERENCE_ONLY",
    ),
]
EXPECTED_BASE_CHANNELS = [
    "heat_capacity_Cp_anomaly",
    "resistivity_temperature_coefficient_drho_dT_anomaly",
]


def fraction(value: int | float | str | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    return Fraction(value)


def matrix(values: Sequence[Sequence[int | float | str | Fraction]]) -> list[list[Fraction]]:
    rows = [[fraction(value) for value in row] for row in values]
    if rows and any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("matrix rows must have equal length")
    return rows


def transpose(a: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    if not a:
        return []
    return [list(column) for column in zip(*a)]


def matmul(
    a: Sequence[Sequence[Fraction]], b: Sequence[Sequence[Fraction]]
) -> list[list[Fraction]]:
    if not a or not b:
        return []
    if len(a[0]) != len(b):
        raise ValueError("matrix dimensions do not align")
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, column)) for column in bt] for row in a]


def rref(
    values: Sequence[Sequence[int | float | str | Fraction]],
) -> tuple[list[list[Fraction]], list[int]]:
    a = matrix(values)
    if not a:
        return [], []
    row_count = len(a)
    column_count = len(a[0])
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(column_count):
        candidate = next(
            (row for row in range(pivot_row, row_count) if a[row][column] != 0),
            None,
        )
        if candidate is None:
            continue
        a[pivot_row], a[candidate] = a[candidate], a[pivot_row]
        divisor = a[pivot_row][column]
        a[pivot_row] = [value / divisor for value in a[pivot_row]]
        for row in range(row_count):
            if row == pivot_row:
                continue
            coefficient = a[row][column]
            if coefficient:
                a[row] = [
                    value - coefficient * pivot_value
                    for value, pivot_value in zip(a[row], a[pivot_row])
                ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == row_count:
            break
    return a, pivot_columns


def solve_square(
    coefficients: Sequence[Sequence[int | float | str | Fraction]],
    rhs: Sequence[int | float | str | Fraction],
) -> list[Fraction]:
    a = matrix(coefficients)
    b = [fraction(value) for value in rhs]
    n = len(a)
    if n == 0 or any(len(row) != n for row in a) or len(b) != n:
        raise ValueError("solve_square requires an n by n system")
    augmented = [row[:] + [b[index]] for index, row in enumerate(a)]
    reduced, pivots = rref(augmented)
    if pivots[:n] != list(range(n)):
        raise ValueError("system is singular")
    return [reduced[index][-1] for index in range(n)]


def row_space_factorization(
    observer: Sequence[Sequence[int | float | str | Fraction]],
) -> tuple[list[list[Fraction]], list[int], list[list[Fraction]]]:
    a = matrix(observer)
    reduced, pivots = rref(a)
    rank = len(pivots)
    row_basis = [row for row in reduced if any(value != 0 for value in row)][:rank]
    column_factor = [[row[pivot] for pivot in pivots] for row in a]
    return row_basis, pivots, column_factor


def sharp_burden(
    observer: Sequence[Sequence[int | float | str | Fraction]],
    metric: Sequence[Sequence[int | float | str | Fraction]],
    target: Sequence[int | float | str | Fraction],
) -> dict[str, Any]:
    a = matrix(observer)
    h = matrix(metric)
    ell = [fraction(value) for value in target]
    if not a or len(ell) != len(a[0]):
        raise ValueError("target dimension must match observer domain")
    if len(h) != len(a) or any(len(row) != len(a) for row in h):
        raise ValueError("metric dimension must match observer codomain")

    row_basis, pivots, column_factor = row_space_factorization(a)
    coordinates = [ell[pivot] for pivot in pivots]
    reconstructed = [
        sum(coordinates[index] * row_basis[index][column] for index in range(len(pivots)))
        for column in range(len(ell))
    ]
    if reconstructed != ell:
        return {
            "visible": False,
            "classification": "TARGET_BLIND_ADD_HIGHER_LAYER",
            "beta": None,
            "rank": len(pivots),
        }

    gram = matmul(matmul(transpose(column_factor), h), column_factor)
    solution = solve_square(gram, coordinates)
    beta = sum(coordinate * value for coordinate, value in zip(coordinates, solution))
    return {
        "visible": True,
        "classification": classify_exact_beta(beta),
        "beta": beta,
        "rank": len(pivots),
    }


def classify_exact_beta(beta: Fraction, transverse_zero: bool = False) -> str:
    if beta < 1:
        return "STRICT_NEEL_CUT_CLOSURE"
    if beta > 1:
        return "BURDEN_EXCEEDS_ONE"
    if transverse_zero:
        return "CRITICAL_ALIGNED_CLOSURE"
    return "THRESHOLD_INCONCLUSIVE"


def classify_beta_interval(
    lower: int | float | str | Fraction | None,
    upper: int | float | str | Fraction | None,
    *,
    transverse_zero: bool = False,
) -> str:
    if lower is None or upper is None:
        return "DATA_REQUIRED"
    lo, hi = fraction(lower), fraction(upper)
    if lo > hi:
        raise ValueError("beta interval lower bound exceeds upper bound")
    if hi < 1:
        return "STRICT_NEEL_CUT_CLOSURE"
    if lo > 1:
        return "BURDEN_EXCEEDS_ONE"
    if lo == hi == 1 and transverse_zero:
        return "CRITICAL_ALIGNED_CLOSURE"
    return "THRESHOLD_INCONCLUSIVE"


def fraction_json(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def synthetic_controls() -> dict[str, Any]:
    identity = [[1, 0], [0, 1]]
    metric_identity = [[1, 0], [0, 1]]
    strict = sharp_burden(identity, metric_identity, ["1/2", 0])
    critical = sharp_burden(identity, metric_identity, [1, 0])
    exceeds = sharp_burden(identity, metric_identity, [2, 0])
    blind = sharp_burden([[1, 0]], [[1]], [0, 1])
    return {
        "strict": {
            "beta": fraction_json(strict["beta"]),
            "classification": strict["classification"],
        },
        "critical_without_alignment_certificate": {
            "beta": fraction_json(critical["beta"]),
            "classification": critical["classification"],
        },
        "critical_with_alignment_certificate": {
            "beta": fraction_json(critical["beta"]),
            "classification": classify_exact_beta(critical["beta"], transverse_zero=True),
        },
        "exceeds": {
            "beta": fraction_json(exceeds["beta"]),
            "classification": exceeds["classification"],
        },
        "blind": {
            "beta": None,
            "classification": blind["classification"],
        },
    }


def audit(contract: dict[str, Any], repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    pins = contract.get("framework_source_pins", {})
    upstream = contract.get("upstream_local_certificates", {})
    physical = contract.get("physical_state_contract", {})
    observer = contract.get("observer_contract", {})
    metric_contract = contract.get("metric_contract", {})
    target = contract.get("target_contract", {})
    burden = contract.get("sharp_burden_contract", {})
    seam = contract.get("seam_curvature_contract", {})
    state = contract.get("current_state", {})

    if pins.get("repository") != EXPECTED_FRAMEWORK_REPOSITORY:
        errors.append("framework repository pin changed")
    if pins.get("branch") != EXPECTED_FRAMEWORK_BRANCH:
        errors.append("framework branch pin changed")
    if pins.get("commit") != EXPECTED_FRAMEWORK_COMMIT:
        errors.append("framework commit pin changed")
    actual_files = [
        (item.get("path"), item.get("blob_sha"), item.get("role"))
        for item in pins.get("files", [])
    ]
    if actual_files != EXPECTED_FRAMEWORK_FILES:
        errors.append("framework theorem file pins changed")

    c03_path = repository_root / str(upstream.get("c03_path", ""))
    c04_path = repository_root / str(upstream.get("c04_path", ""))
    if not c03_path.is_file():
        errors.append("C03 certificate missing")
        c03: dict[str, Any] = {}
    else:
        c03 = load_json(c03_path)
    if not c04_path.is_file():
        errors.append("C04 certificate missing")
        c04: dict[str, Any] = {}
    else:
        c04 = load_json(c04_path)
    if c03.get("status") != upstream.get("c03_required_status"):
        errors.append("C03 prerequisite status changed")
    if c04.get("status") != upstream.get("c04_required_status"):
        errors.append("C04 prerequisite status changed")
    for key in ("same_specimen", "simultaneous_measurement", "common_temperature_calibration"):
        if c03 and c03.get(key) is not True:
            errors.append(f"C03 physical gate {key} must remain true")
    if c03 and c03.get("channels") != [
        "heat_capacity_Cp",
        "resistivity_temperature_coefficient_drho_dT",
    ]:
        errors.append("C03 same-specimen channel pair changed")
    if c04 and int(c04.get("primary_files_acquired", -1)) != 0:
        errors.append("C04 primary files must remain zero before C06 intake")

    required_true_physical = (
        "same_specimen_required",
        "simultaneous_measurement_required",
        "common_temperature_calibration_required",
        "modulation_branch_is_not_heating_or_cooling",
        "universal_TN_K_forbidden",
        "source_specific_TN_required",
    )
    for key in required_true_physical:
        if physical.get(key) is not True:
            errors.append(f"physical gate {key} must remain true")
    if physical.get("measurement_mode") != "AC_MODULATION_NEAR_EQUILIBRIUM":
        errors.append("measurement mode changed")
    if physical.get("candidate_cut") != "J_tau:tau->-tau":
        errors.append("candidate reduced-temperature cut changed")
    if physical.get("candidate_cut_admitted") is not False:
        errors.append("candidate cut cannot be admitted before two-sided data and covariance")

    if observer.get("base_channels") != EXPECTED_BASE_CHANNELS:
        errors.append("base response channel pair changed")
    for key in (
        "raw_channel_units_must_not_be_wedged",
        "baseline_rule_must_be_predeclared",
        "higher_layers_allowed_only_from_admitted_raw_curves",
    ):
        if observer.get(key) is not True:
            errors.append(f"observer gate {key} must remain true")
    if int(observer.get("current_admitted_point_count_per_channel", -1)) != 0:
        errors.append("admitted point count must remain zero")
    if observer.get("observer_instantiated") is not False:
        errors.append("observer cannot be instantiated before admitted response data")

    for key in (
        "positive_metric_required",
        "compatibility_gram_whitening_allowed",
        "unlike_units_require_whitening",
        "singular_covariance_requires_support_restriction",
    ):
        if metric_contract.get(key) is not True:
            errors.append(f"metric gate {key} must remain true")
    if metric_contract.get("metric_instantiated") is not False:
        errors.append("metric cannot be instantiated before covariance is admitted")
    if metric_contract.get("shared_covariance_available") is not False:
        errors.append("shared covariance cannot be marked available")

    for key in (
        "target_formula_must_be_frozen_before_data_fit",
        "post_hoc_peak_picking_forbidden",
        "abstract_exponent_relation_is_not_numeric_target",
    ):
        if target.get(key) is not True:
            errors.append(f"target gate {key} must remain true")
    if target.get("target_instantiated") is not False:
        errors.append("Neel target cannot be instantiated before a source-locked formula")

    if burden.get("positive_defect_equivalence") != "A^* H A-L^*L>=0 iff beta<=1":
        errors.append("cut-square burden equivalence changed")
    for key in ("beta_interval_required", "outward_uncertainty_required"):
        if burden.get(key) is not True:
            errors.append(f"burden gate {key} must remain true")
    if burden.get("beta_computed") is not False:
        errors.append("physical chromium beta cannot be marked computed")
    if burden.get("beta_lower") is not None or burden.get("beta_upper") is not None:
        errors.append("physical chromium beta interval must remain null")
    current_classification = classify_beta_interval(
        burden.get("beta_lower"), burden.get("beta_upper")
    )
    if burden.get("classification") != current_classification:
        errors.append("physical beta classification must remain DATA_REQUIRED")

    if seam.get("raw_second_derivative_is_not_native_seam_curvature") is not True:
        errors.append("raw second derivative cannot be promoted to native seam curvature")
    if seam.get("generator_instantiated") is not False:
        errors.append("protocol generator cannot be instantiated before a physical adapter")
    if seam.get("curvature_computed") is not False:
        errors.append("native seam curvature cannot be marked computed")

    for key in (
        "primary_scan_or_author_arrays_acquired",
        "response_packet_admitted",
        "candidate_cut_admitted",
        "observer_instantiated",
        "metric_instantiated",
        "target_instantiated",
        "beta_computed",
        "curvature_computed",
        "fit_allowed",
        "anomaly_significance_allowed",
    ):
        if state.get(key) is not False:
            errors.append(f"current state {key} must remain false")

    template_path = repository_root / str(contract.get("response_packet_template_path", ""))
    template_present = template_path.is_file()
    if not template_present:
        errors.append("response packet template missing")
        template: dict[str, Any] = {}
    else:
        template = load_json(template_path)
    if template and template.get("temperature_K") != []:
        errors.append("unpopulated template temperature array must remain empty")
    if template and template.get("target", {}).get("frozen_before_fit") is not False:
        errors.append("unpopulated template target cannot be frozen")
    if template and template.get("cut", {}).get("admitted") is not False:
        errors.append("unpopulated template cut cannot be admitted")

    adapter_ready = not errors
    status = (
        "PASS_CHROMIUM_C05_CUT_SQUARE_ADAPTER_FROZEN_BETA_DATA_REQUIRED"
        if adapter_ready
        else "FAIL_CHROMIUM_C05_CUT_SQUARE_ADAPTER_CONTRACT"
    )
    controls = synthetic_controls()
    return {
        "campaign": contract.get("campaign"),
        "status": status,
        "errors": errors,
        "framework_repository": pins.get("repository"),
        "framework_branch": pins.get("branch"),
        "framework_commit": pins.get("commit"),
        "framework_theorem_pin_count": len(actual_files),
        "upstream_c03_status": c03.get("status"),
        "upstream_c04_status": c04.get("status"),
        "same_specimen": bool(c03.get("same_specimen")),
        "simultaneous_measurement": bool(c03.get("simultaneous_measurement")),
        "common_temperature_calibration": bool(c03.get("common_temperature_calibration")),
        "measurement_mode": physical.get("measurement_mode"),
        "candidate_cut": physical.get("candidate_cut"),
        "candidate_cut_admitted": bool(physical.get("candidate_cut_admitted")),
        "base_channels": observer.get("base_channels"),
        "observer_tower": observer.get("observer_tower"),
        "observer_instantiated": bool(observer.get("observer_instantiated")),
        "metric_symbol": metric_contract.get("metric_symbol"),
        "metric_instantiated": bool(metric_contract.get("metric_instantiated")),
        "target_symbol": target.get("target_symbol"),
        "target_instantiated": bool(target.get("target_instantiated")),
        "beta_definition": burden.get("definition"),
        "positive_defect_equivalence": burden.get("positive_defect_equivalence"),
        "beta_interval": {"lower": burden.get("beta_lower"), "upper": burden.get("beta_upper")},
        "beta_computed": bool(burden.get("beta_computed")),
        "beta_classification": current_classification,
        "native_seam_curvature": seam.get("native_seam_curvature"),
        "curvature_computed": bool(seam.get("curvature_computed")),
        "response_packet_template_path": contract.get("response_packet_template_path"),
        "response_packet_template_present": template_present,
        "synthetic_exact_controls": controls,
        "physical_result": {
            "beta_bound_proved": False,
            "strict_closure_proved": False,
            "critical_closure_proved": False,
            "burden_exceeds_one_proved": False,
            "target_blindness_proved": False,
            "native_curvature_proved": False,
            "data_required": True,
        },
        "decisive_reasons": [
            "The framework theorem pins establish the exact cut-square, target-repair, projection-defect and seam-curvature architecture.",
            "The 1969 experiment supplies the intended same-specimen Cp and drho/dT channel types, but no admitted pointwise arrays or shared covariance are present.",
            "The reduced-temperature involution tau -> -tau remains a candidate cut until source-specific TN, two-sided support and bilateral closure are certified.",
            "The Neel target formula must be frozen before fitting; an abstract exponent relation or post-hoc peak is not an admissible target.",
            "Therefore the physical sharp burden beta_Cr,N and native seam curvature remain uncomputed while the adapter itself is reproducibly frozen."
        ],
        "next_stage": contract.get("next_stage"),
        "claim_boundary": contract.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path("protocols/C05_CHROMIUM_NEEL_CUT_SQUARE_ADAPTER.json"),
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("releases/chromium-neel-c05/chromium_cut_square_adapter_certificate.json"),
    )
    args = parser.parse_args()
    result = audit(load_json(args.contract), args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
