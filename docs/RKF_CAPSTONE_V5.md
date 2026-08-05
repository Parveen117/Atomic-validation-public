# Atomic RKF Capstone V5

## Purpose

This development introduces the first theorem-native Recognition Kernel core into the public Atomic validation repository. It does not replace the empirical UAM-V4 predictor and does not yet claim a physical atomic cut or a universal nuclear generator.

The immediate objective is narrower and rigorous:

```text
exact finite-dimensional state packet
-> declared self-adjoint involutive cut
-> unique cut-even / cut-odd generator grading
-> cut-loop memory and seam-curvature coefficients
-> exact bilateral nilpotent Euler flow
-> exponential cut-square certificate
-> faithful direct-sum observer energy
```

## Source pin

The implementation is pinned to Recognition Kernel Framework commit:

```text
9f5792ee62ce3a1a71d9ed242ff9cb10e6745f3e
```

on branch:

```text
agent/cut-graded-lambda-jacobian-tower
```

The imported theorem interfaces are:

- `theorum/41_cut_graded_universal_generator_theorem.md`
- `theorum/42_cut_graded_lambda_jacobian_tower_theorem.md`

The source is consumed as a mathematical interface. No claim is made that the current two-dimensional certificate identifies the physical atomic state space.

## Exact core

For a declared cut `J` and generator `G`, the implementation constructs

\[
G_{\mathrm e}=\frac12(G+JGJ),
\qquad
G_{\mathrm o}=\frac12(G-JGJ).
\]

It verifies exactly that

\[
G=G_{\mathrm e}+G_{\mathrm o},
\quad
JG_{\mathrm e}J=G_{\mathrm e},
\quad
JG_{\mathrm o}J=-G_{\mathrm o}.
\]

The cut-loop coefficients are represented by

\[
2G_{\mathrm e}
\]

for linear memory and

\[
[G_{\mathrm e},G_{\mathrm o}]
\]

for the first noncommutative seam-curvature term.

For an exactly nilpotent cut-odd generator, the finite exponential series is evaluated over `fractions.Fraction`. The certificate checks

\[
JU_tJ=U_{-t}
\]

and

\[
(U_t+U_{-t})^2-(U_t-U_{-t})^2=4I.
\]

No floating point, NumPy, fitted transform or post-hoc Gram factor is used.

## Observer discipline

The module distinguishes a direct-sum observer from a simple aggregate. Two components may cancel in their aggregate while their direct-sum Gram energy remains nonzero. Complete orthogonal projection components are also checked to preserve the generator Gram operator exactly.

This matters for the existing neutron-direction and proton-direction UAM observers: agreement or cancellation must not be confused with faithful recognition.

## Deterministic certificate

Run:

```bash
python scripts/certify_rkf_capstone.py
```

Expected status:

```text
PASS_ATOMIC_RKF_CAPSTONE_EXACT_CORE
```

Expected certificate SHA-256:

```text
785e1010865b0fdeb0a119625ccb0b7a58eaecb5ae3c4d6412de107bfdc6d57a
```

## Claim boundary

Proved or exactly verified in this slice:

- finite-dimensional rational matrix algebra;
- valid self-adjoint involutive cut checks;
- unique cut grading;
- exact linear-memory and seam-curvature extraction;
- exact nilpotent odd Euler flow;
- exponential cut-square identity for the certified packet;
- complete orthogonal component Gram preservation;
- aggregate-cancellation negative control.

Still open:

- derivation of the physical atomic cut `J_A`;
- construction and domain proof for an unbounded atomic generator;
- adapter from UAM-V4 directional responses to a lawful direct-sum observer;
- identification of seam curvature with a measured nuclear response quantity;
- lambda-Jacobian tower on the AME/NUBASE state bundle;
- derivation of binding energy or separation energies from the capstone core.

## Next development

The next atomic theorem should construct the UAM-V4 first-layer observer

\[
\mathcal A_1=(A_N,A_Z)
\]

without collapsing the two axes into a scalar blend, then test whether a higher response layer reduces the target-relevant blind kernel on the guarded residual tail.
