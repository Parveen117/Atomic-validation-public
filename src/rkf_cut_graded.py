from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence

Scalar = int | Fraction
Matrix = tuple[tuple[Fraction, ...], ...]


def matrix(rows: Iterable[Iterable[Scalar]]) -> Matrix:
    result = tuple(tuple(Fraction(value) for value in row) for row in rows)
    if not result or not result[0]:
        raise ValueError("matrix must be non-empty")
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise ValueError("matrix rows must have equal length")
    return result


def shape(value: Matrix) -> tuple[int, int]:
    return len(value), len(value[0])


def zero(rows: int, columns: int) -> Matrix:
    if rows <= 0 or columns <= 0:
        raise ValueError("matrix dimensions must be positive")
    return tuple(tuple(Fraction(0) for _ in range(columns)) for _ in range(rows))


def identity(size: int) -> Matrix:
    if size <= 0:
        raise ValueError("identity size must be positive")
    return tuple(
        tuple(Fraction(1 if row == column else 0) for column in range(size))
        for row in range(size)
    )


def add(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("matrix shapes do not match")
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(len(left[0])))
        for row in range(len(left))
    )


def subtract(left: Matrix, right: Matrix) -> Matrix:
    return add(left, scale(right, -1))


def scale(value: Matrix, factor: Scalar) -> Matrix:
    factor = Fraction(factor)
    return tuple(tuple(factor * entry for entry in row) for row in value)


def multiply(left: Matrix, right: Matrix) -> Matrix:
    left_rows, left_columns = shape(left)
    right_rows, right_columns = shape(right)
    if left_columns != right_rows:
        raise ValueError("matrix shapes are not composable")
    return tuple(
        tuple(
            sum(
                (left[row][index] * right[index][column] for index in range(left_columns)),
                Fraction(0),
            )
            for column in range(right_columns)
        )
        for row in range(left_rows)
    )


def transpose(value: Matrix) -> Matrix:
    rows, columns = shape(value)
    return tuple(tuple(value[row][column] for row in range(rows)) for column in range(columns))


def power(value: Matrix, exponent: int) -> Matrix:
    rows, columns = shape(value)
    if rows != columns:
        raise ValueError("matrix power requires a square matrix")
    if exponent < 0:
        raise ValueError("negative powers are not supported")
    result = identity(rows)
    factor = value
    remaining = exponent
    while remaining:
        if remaining % 2:
            result = multiply(result, factor)
        factor = multiply(factor, factor)
        remaining //= 2
    return result


def commutator(left: Matrix, right: Matrix) -> Matrix:
    return subtract(multiply(left, right), multiply(right, left))


def matrix_sum(values: Sequence[Matrix]) -> Matrix:
    if not values:
        raise ValueError("at least one matrix is required")
    result = zero(*shape(values[0]))
    for value in values:
        result = add(result, value)
    return result


def gram(value: Matrix) -> Matrix:
    return multiply(transpose(value), value)


def conjugate_by_cut(cut: Matrix, value: Matrix) -> Matrix:
    return multiply(multiply(cut, value), cut)


def validate_cut(cut: Matrix) -> None:
    rows, columns = shape(cut)
    if rows != columns:
        raise ValueError("cut must be square")
    if transpose(cut) != cut:
        raise ValueError("cut must be self-adjoint in the real exact model")
    if multiply(cut, cut) != identity(rows):
        raise ValueError("cut must be an involution")


@dataclass(frozen=True)
class CutGrading:
    cut: Matrix
    generator: Matrix
    even: Matrix
    odd: Matrix

    def verify(self) -> None:
        if add(self.even, self.odd) != self.generator:
            raise AssertionError("cut grading does not reconstruct the generator")
        if conjugate_by_cut(self.cut, self.even) != self.even:
            raise AssertionError("even component is not cut even")
        if conjugate_by_cut(self.cut, self.odd) != scale(self.odd, -1):
            raise AssertionError("odd component is not cut odd")


@dataclass(frozen=True)
class CutLoopCoefficients:
    linear_memory: Matrix
    seam_curvature: Matrix


@dataclass(frozen=True)
class OddFlowCertificate:
    time: Fraction
    u_plus: Matrix
    u_minus: Matrix
    join_channel: Matrix
    cut_channel: Matrix
    cut_square_left: Matrix
    cut_square_right: Matrix
    bilateral_covariance: bool
    cut_square_holds: bool
    channel_product_commutes: bool

    def to_record(self) -> dict:
        return {
            "certificate_type": "ATOMIC_RKF_EXACT_ODD_FLOW_V1",
            "time": fraction_text(self.time),
            "u_plus": matrix_record(self.u_plus),
            "u_minus": matrix_record(self.u_minus),
            "join_channel": matrix_record(self.join_channel),
            "cut_channel": matrix_record(self.cut_channel),
            "cut_square_left": matrix_record(self.cut_square_left),
            "cut_square_right": matrix_record(self.cut_square_right),
            "bilateral_covariance": self.bilateral_covariance,
            "cut_square_holds": self.cut_square_holds,
            "channel_product_commutes": self.channel_product_commutes,
        }


def grade_generator(cut: Matrix, generator: Matrix) -> CutGrading:
    validate_cut(cut)
    if shape(cut) != shape(generator):
        raise ValueError("cut and generator must have the same square shape")
    conjugate = conjugate_by_cut(cut, generator)
    grading = CutGrading(
        cut=cut,
        generator=generator,
        even=scale(add(generator, conjugate), Fraction(1, 2)),
        odd=scale(subtract(generator, conjugate), Fraction(1, 2)),
    )
    grading.verify()
    return grading


def cut_loop_coefficients(grading: CutGrading) -> CutLoopCoefficients:
    grading.verify()
    return CutLoopCoefficients(
        linear_memory=scale(grading.even, 2),
        seam_curvature=commutator(grading.even, grading.odd),
    )


def nilpotent_exponential(generator: Matrix, time: Scalar, nilpotency_index: int) -> Matrix:
    rows, columns = shape(generator)
    if rows != columns:
        raise ValueError("generator must be square")
    if nilpotency_index <= 0:
        raise ValueError("nilpotency index must be positive")
    if power(generator, nilpotency_index) != zero(rows, rows):
        raise ValueError("declared nilpotency index is not valid")
    time = Fraction(time)
    result = zero(rows, rows)
    for order in range(nilpotency_index):
        coefficient = time**order / math.factorial(order)
        result = add(result, scale(power(generator, order), coefficient))
    return result


def certify_odd_nilpotent_flow(
    cut: Matrix,
    generator: Matrix,
    time: Scalar,
    nilpotency_index: int,
) -> OddFlowCertificate:
    grading = grade_generator(cut, generator)
    if grading.even != zero(*shape(generator)):
        raise ValueError("generator must be cut odd")
    time = Fraction(time)
    u_plus = nilpotent_exponential(generator, time, nilpotency_index)
    u_minus = nilpotent_exponential(generator, -time, nilpotency_index)
    join_channel = add(u_plus, u_minus)
    cut_channel = subtract(u_plus, u_minus)
    left = subtract(power(join_channel, 2), power(cut_channel, 2))
    right = scale(identity(shape(generator)[0]), 4)
    return OddFlowCertificate(
        time=time,
        u_plus=u_plus,
        u_minus=u_minus,
        join_channel=join_channel,
        cut_channel=cut_channel,
        cut_square_left=left,
        cut_square_right=right,
        bilateral_covariance=conjugate_by_cut(cut, u_plus) == u_minus,
        cut_square_holds=left == right,
        channel_product_commutes=(
            multiply(join_channel, cut_channel) == multiply(cut_channel, join_channel)
        ),
    )


def direct_sum_observer_gram(components: Sequence[Matrix]) -> Matrix:
    if not components:
        raise ValueError("at least one observer component is required")
    first_shape = shape(components[0])
    if any(shape(component) != first_shape for component in components):
        raise ValueError("observer components must have the same shape")
    return matrix_sum([gram(component) for component in components])


def aggregate_observer_gram(components: Sequence[Matrix]) -> Matrix:
    return gram(matrix_sum(components))


def validate_projection_family(projections: Sequence[Matrix]) -> None:
    if not projections:
        raise ValueError("at least one projection is required")
    rows, columns = shape(projections[0])
    if rows != columns:
        raise ValueError("projections must be square")
    if any(shape(projection) != (rows, rows) for projection in projections):
        raise ValueError("projection shapes do not match")
    for projection in projections:
        if transpose(projection) != projection:
            raise ValueError("projection must be self-adjoint")
        if multiply(projection, projection) != projection:
            raise ValueError("projection must be idempotent")
    for left_index, left in enumerate(projections):
        for right in projections[left_index + 1 :]:
            if multiply(left, right) != zero(rows, rows):
                raise ValueError("projections must be pairwise orthogonal")
    if matrix_sum(list(projections)) != identity(rows):
        raise ValueError("projection family must be complete")


def projected_component_gram(generator: Matrix, projections: Sequence[Matrix]) -> Matrix:
    validate_projection_family(projections)
    components = [multiply(projection, generator) for projection in projections]
    result = direct_sum_observer_gram(components)
    expected = gram(generator)
    if result != expected:
        raise AssertionError("complete orthogonal components did not preserve the Gram operator")
    return result


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def matrix_record(value: Matrix) -> list[list[str]]:
    return [[fraction_text(entry) for entry in row] for row in value]


def certificate_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
