from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rkf_cut_graded import (
    aggregate_observer_gram,
    certificate_hash,
    certify_odd_nilpotent_flow,
    cut_loop_coefficients,
    direct_sum_observer_gram,
    grade_generator,
    matrix,
    matrix_record,
    projected_component_gram,
    scale,
)

OUTPUT = ROOT / "releases" / "rkf-capstone-v5" / "exact_certificate.json"
SOURCE_COMMIT = "9f5792ee62ce3a1a71d9ed242ff9cb10e6745f3e"
EXPECTED_CERTIFICATE_SHA256 = "785e1010865b0fdeb0a119625ccb0b7a58eaecb5ae3c4d6412de107bfdc6d57a"


def main() -> None:
    cut = matrix(((1, 0), (0, -1)))
    generator = matrix(((2, 3), (5, 7)))
    grading = grade_generator(cut, generator)
    loop = cut_loop_coefficients(grading)

    odd_generator = matrix(((0, 1), (0, 0)))
    flow = certify_odd_nilpotent_flow(
        cut,
        odd_generator,
        time=Fraction(3, 2),
        nilpotency_index=2,
    )

    projections = (
        matrix(((1, 0), (0, 0))),
        matrix(((0, 0), (0, 1))),
    )
    projection_gram = projected_component_gram(generator, projections)

    observer_component = matrix(((1, 2),))
    cancelling_components = (observer_component, scale(observer_component, -1))
    direct_gram = direct_sum_observer_gram(cancelling_components)
    aggregate_gram = aggregate_observer_gram(cancelling_components)

    checks = {
        "grading_reconstructs": grading.generator == matrix(((2, 3), (5, 7))),
        "even_component_exact": grading.even == matrix(((2, 0), (0, 7))),
        "odd_component_exact": grading.odd == matrix(((0, 3), (5, 0))),
        "seam_curvature_exact": loop.seam_curvature == matrix(((0, -15), (25, 0))),
        "bilateral_flow_covariance": flow.bilateral_covariance,
        "exponential_cut_square": flow.cut_square_holds,
        "derived_channels_commute": flow.channel_product_commutes,
        "complete_component_gram": projection_gram == matrix(((29, 41), (41, 58))),
        "direct_sum_sees_cancellation": direct_gram != aggregate_gram,
    }

    payload = {
        "certificate_type": "ATOMIC_RKF_CAPSTONE_EXACT_CERTIFICATE_V1",
        "source_pin": {
            "repository": "Parveen117/Recognition-Kernel-Framework",
            "branch": "agent/cut-graded-lambda-jacobian-tower",
            "commit": SOURCE_COMMIT,
            "theorems": [
                "theorum/41_cut_graded_universal_generator_theorem.md",
                "theorum/42_cut_graded_lambda_jacobian_tower_theorem.md",
            ],
        },
        "scope": "FINITE_DIMENSIONAL_EXACT_RATIONAL_CORE",
        "grading": {
            "cut": matrix_record(grading.cut),
            "generator": matrix_record(grading.generator),
            "even": matrix_record(grading.even),
            "odd": matrix_record(grading.odd),
            "linear_memory": matrix_record(loop.linear_memory),
            "seam_curvature": matrix_record(loop.seam_curvature),
        },
        "odd_flow": flow.to_record(),
        "observer": {
            "complete_projection_gram": matrix_record(projection_gram),
            "cancelling_direct_sum_gram": matrix_record(direct_gram),
            "cancelling_aggregate_gram": matrix_record(aggregate_gram),
        },
        "checks": checks,
        "status": "PASS_ATOMIC_RKF_CAPSTONE_EXACT_CORE" if all(checks.values()) else "FAILED",
        "claim_boundary": {
            "physical_atomic_cut_identified": False,
            "unbounded_generator_domain_proved": False,
            "binding_energy_law_derived": False,
            "uam_v4_first_layer_adapter": False,
        },
    }
    payload["certificate_sha256"] = certificate_hash(payload)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if payload["status"] != "PASS_ATOMIC_RKF_CAPSTONE_EXACT_CORE":
        raise SystemExit(1)
    if payload["certificate_sha256"] != EXPECTED_CERTIFICATE_SHA256:
        raise SystemExit(
            "certificate hash changed: "
            f"{payload['certificate_sha256']} != {EXPECTED_CERTIFICATE_SHA256}"
        )


if __name__ == "__main__":
    main()
