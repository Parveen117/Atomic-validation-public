import unittest
from fractions import Fraction

from src.rkf_cut_graded import (
    add,
    aggregate_observer_gram,
    certificate_hash,
    certify_odd_nilpotent_flow,
    cut_loop_coefficients,
    direct_sum_observer_gram,
    grade_generator,
    identity,
    matrix,
    matrix_record,
    projected_component_gram,
    scale,
    zero,
)


class CutGradedCapstoneTests(unittest.TestCase):
    def test_unique_cut_grading_and_curvature(self) -> None:
        cut = matrix(((1, 0), (0, -1)))
        generator = matrix(((2, 3), (5, 7)))
        grading = grade_generator(cut, generator)
        self.assertEqual(grading.even, matrix(((2, 0), (0, 7))))
        self.assertEqual(grading.odd, matrix(((0, 3), (5, 0))))
        self.assertEqual(add(grading.even, grading.odd), generator)

        coefficients = cut_loop_coefficients(grading)
        self.assertEqual(coefficients.linear_memory, matrix(((4, 0), (0, 14))))
        self.assertEqual(coefficients.seam_curvature, matrix(((0, -15), (25, 0))))

    def test_exact_nilpotent_odd_flow_and_cut_square(self) -> None:
        cut = matrix(((1, 0), (0, -1)))
        generator = matrix(((0, 1), (0, 0)))
        certificate = certify_odd_nilpotent_flow(
            cut,
            generator,
            time=Fraction(3, 2),
            nilpotency_index=2,
        )
        self.assertTrue(certificate.bilateral_covariance)
        self.assertTrue(certificate.cut_square_holds)
        self.assertTrue(certificate.channel_product_commutes)
        self.assertEqual(certificate.cut_square_left, scale(identity(2), 4))
        self.assertEqual(certificate.u_plus, matrix(((1, Fraction(3, 2)), (0, 1))))
        self.assertEqual(certificate.u_minus, matrix(((1, Fraction(-3, 2)), (0, 1))))

    def test_complete_projection_family_preserves_gram(self) -> None:
        generator = matrix(((2, 3), (5, 7)))
        projections = (
            matrix(((1, 0), (0, 0))),
            matrix(((0, 0), (0, 1))),
        )
        self.assertEqual(
            projected_component_gram(generator, projections),
            matrix(((29, 41), (41, 58))),
        )

    def test_direct_sum_detects_aggregate_cancellation(self) -> None:
        component = matrix(((1, 2),))
        components = (component, scale(component, -1))
        self.assertEqual(aggregate_observer_gram(components), zero(2, 2))
        self.assertEqual(
            direct_sum_observer_gram(components),
            matrix(((2, 4), (4, 8))),
        )

    def test_invalid_cut_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            grade_generator(matrix(((1, 1), (0, -1))), matrix(((1, 0), (0, 1))))

    def test_certificate_hash_is_deterministic(self) -> None:
        payload = {
            "matrix": matrix_record(matrix(((1, Fraction(1, 2)), (0, -1)))),
            "status": "PASS",
        }
        self.assertEqual(certificate_hash(payload), certificate_hash(dict(payload)))


if __name__ == "__main__":
    unittest.main()
