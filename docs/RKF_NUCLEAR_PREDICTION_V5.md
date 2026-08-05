# RKF Nuclear Prediction V5: Cross-Fitted Cut-Graded Jet Experiment

## Purpose

This experiment is the first bridge from the exact finite-dimensional Recognition Kernel capstone to measured nuclear binding energy per nucleon.

It does not assume in advance that the new predictor beats UAM-V4. It constructs a target-free physical observer, tests it by held-out-element transfer, and records either improvement or failure.

## Target-free nuclear observer

For a target nucleus `(Z,N)`, the target binding value is removed from every observer component.

The neutron-direction packet is reconstructed from same-parity neighbours at offsets

```text
N - 4, N - 2, N + 2, N + 4
```

when available. The proton-direction packet uses

```text
Z - 2, Z - 1, Z + 1, Z + 2.
```

Each complete direction supplies the local cubic jet at the missing target:

```text
value, slope, curvature, jerk.
```

Fallback linear jets are used when the cubic packet is incomplete.

## Declared response cut

The first physical adapter declares neutron/proton response-axis exchange as the cut:

```text
J(B_N, B_Z) = (B_Z, B_N).
```

This gives the exact response decomposition

```text
cut-even jet = (neutron jet + proton jet) / 2
cut-odd jet  = (neutron jet - proton jet) / 2.
```

The even packet is interpreted as an isoscalar response shadow. The odd packet is interpreted as an isovector response shadow. This is a response-fibre cut, not yet a theorem identifying a universal nuclear-state involution.

## Mixed tensor seam

When all sixteen surrounding nuclei are present, a tensor-product cubic reconstruction is evaluated on the rectangle

```text
Delta Z in {-2,-1,+1,+2}
Delta N in {-4,-2,+2,+4}.
```

The mixed seam residue is

```text
R_seam = B_tensor - (B_N + B_Z)/2.
```

It measures information present in the two-dimensional neighbourhood that is invisible to the separate axis average. No target value enters this quantity.

## Minimum-burden decoder

The decoder predicts the residual relative to the target-free axis mean from:

```text
cut-even and cut-odd jet coefficients;
local mixed seam residue;
neutron excess;
surface and Coulomb coordinates;
pairing coordinate;
magic-number proximity;
jet support order.
```

Features are standardized on the training set only. A fixed ridge of `1.0` stabilizes the finite Gram inverse. The associated quadratic form supplies a decoder-burden score and a training-defined burden guard.

## Validation rule

For every proton number `Z0`:

```text
train decoder on all records with Z != Z0;
predict every eligible record with Z = Z0.
```

Thus the target element chain never enters its decoder fit. Neighbouring measured nuclei may still enter the target's local observer, matching the intended task of predicting a missing nuclear mass from surrounding measurements.

The final report compares:

```text
axis mean;
tensor cubic prediction;
all cross-fitted RKF predictions;
burden-guarded RKF predictions;
frozen UAM-V4 guarded predictions;
RKF and UAM-V4 on identical common support.
```

## Explanation test

The report measures whether absolute prediction error rises with:

```text
decoder burden;
predicted decoder uncertainty;
absolute mixed seam residue.
```

It also reports error by burden quartile. Improvement without such structure would be a numerical result; improvement accompanied by ordered burden/error bands would begin to explain why the observer works and where it becomes blind.

## Claim boundary

This experiment does not yet establish:

```text
a fundamental nuclear binding-energy law;
a universal physical atomic cut;
future mass-table validation;
a replacement for established global mass models;
a proof that the Recognition Kernel must beat UAM-V4.
```

The result is promoted only if the generated common-support report actually earns it.
