# C06 Chromium primary-file intake, response packet and beta interval

## Purpose

C06 consumes the theorem adapter frozen in C05. It does not search for a visually impressive curvature peak. It defines the exact data packet required to evaluate the chromium Neel cut-square burden.

The dependency order is

```text
primary original bytes
-> provenance and rights intake
-> source-specific TN
-> reduced-temperature bilateral pairing
-> baseline and derivative rules
-> covariance whitening
-> visible-quotient observer
-> predeclared target
-> outward beta interval
-> fail-closed classification.
```

No primary article scan or author-supplied arrays are currently admitted. The committed response packet is deliberately empty.

## Original-byte intake

Every primary file must record:

- original filename;
- original-byte SHA-256;
- byte count;
- C04 acquisition route;
- date received;
- rights or access note;
- media type;
- retained location.

OCR text cannot be used as numerical response data. A secondary redrawing cannot be relabelled as the primary experiment. Duplicate hashes are rejected so the same bytes cannot masquerade as independent evidence, a surprisingly necessary precaution whenever humans meet spreadsheets.

## Source-specific transition coordinate

For the admitted specimen and protocol, C06 uses

```text
tau = (T - TN_source_sample) / TN_source_sample.
```

The source-specific `TN` and its uncertainty must be frozen before bilateral pairing. Universal substitution of `311 K` is forbidden.

At least eight two-sided pairs are required. A pair `(tau_plus,tau_minus)` is admitted only when

```text
abs(tau_plus + tau_minus) <= certified_tau_pair_tolerance.
```

The pair table receives its own SHA-256.

## Response packet

The base same-specimen channels are

```text
heat_capacity_Cp_anomaly
resistivity_temperature_coefficient_drho_dT_anomaly
```

Higher layers are added through the C05 observer tower

```text
A_N = direct_sum_(k=0)^N Q_k D_tau^k y.
```

The baseline rule, derivative rule and Neel target formula must all be frozen before fitting. A largest observed peak is not an admissible target definition.

## Whitening and visible quotient

Raw channels have unlike physical units and cannot be wedged directly. Let

```text
W = H_Cr^(1/2) A_N
```

be the whitened observer on the declared visible quotient. C06 requires:

- positive-support certification for `H_Cr`;
- a hash of the whitened observer;
- a hash of the visible basis;
- a positive lower bound on the smallest visible singular value;
- a separate target-visibility decision.

Visibility and burden remain different obligations. A target can be invisible even when several response columns exist; adding duplicated rows does not cure blindness.

## Conservative outward beta interval

On the visible quotient, write the target row as `L_N` and define

```text
beta = sup_(W x != 0) |L_N x|^2 / ||W x||^2.
```

Suppose outward certificates give

```text
target_norm_lower <= ||L_N|| <= target_norm_upper,
||W|| <= observer_norm_upper,
sigma_min(W) >= visible_singular_lower > 0.
```

Then

```text
beta_lower = (target_norm_lower / observer_norm_upper)^2,
beta_upper = (target_norm_upper / visible_singular_lower)^2.
```

Indeed,

```text
||L_N|| <= sqrt(beta) ||W||
```

gives the lower bound, while

```text
sqrt(beta) <= ||L_N|| / sigma_min(W)
```

gives the upper bound. The interval is conservative and may be wide. It is nevertheless an outward enclosure rather than a fitted central value dressed in ceremonial decimals.

## Classification order

C06 classifies in the following order:

```text
target invisible
    TARGET_BLIND_ADD_HIGHER_LAYER

bilateral defect above tolerance
    OPEN_SEAM_OR_WRONG_CUT

beta_upper < 1
    STRICT_NEEL_CUT_CLOSURE

beta_lower > 1
    BURDEN_EXCEEDS_ONE

beta_lower = beta_upper = 1 and transverse alignment certified
    CRITICAL_ALIGNED_CLOSURE

otherwise the interval intersects the threshold
    THRESHOLD_INCONCLUSIVE
```

The bilateral cut gate precedes the beta conclusion. A low burden under a wrong cut does not certify the physical transition.

## Exact controls

The executable controls freeze:

```text
beta = 1/4                    STRICT_NEEL_CUT_CLOSURE
beta = 1 with alignment       CRITICAL_ALIGNED_CLOSURE
[0.9801, 1.0201]              THRESHOLD_INCONCLUSIVE
beta = 4                      BURDEN_EXCEEDS_ONE
invisible target              TARGET_BLIND_ADD_HIGHER_LAYER
large bilateral defect        OPEN_SEAM_OR_WRONG_CUT
```

These controls test the interval engine. They are not chromium measurements.

## Current result

```text
primary files admitted          0
source-specific TN              not frozen
bilateral pairs                 0
channel arrays                  not admitted
metric whitening                not instantiated
visible quotient                not certified
Neel target                     not instantiated
physical beta interval          not computed
physical classification         DATA_REQUIRED
```

Status:

```text
PASS_CHROMIUM_C06_ENGINE_FROZEN_PRIMARY_DATA_REQUIRED
```

## Next stage

`C07_CHROMIUM_BILATERAL_CUT_ADMISSION_AND_NATIVE_CURVATURE`

C07 begins after C06 produces a physical packet. It will decide whether `tau -> -tau` is an admitted cut, then construct a cut-covariant protocol generator and test the native seam curvature `[G_even,G_odd]`. A raw second temperature derivative will not be promoted to that operator curvature without the adapter.
