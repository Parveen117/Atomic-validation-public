# RKF Recognition Repair V5.1

## Result

The first cross-fitted RKF nuclear jet decoder did not replace UAM-V4 as a universal point predictor. It produced a stronger tail distribution but a weaker central mean absolute error.

That failure exposed a sharper physical decomposition.

The frozen UAM-V4 directional disagreement already contains a declared minimum coherence boundary of `50 keV/A`. The Recognition Repair predictor therefore uses the fixed rule

```text
if frozen UAM-V4 abstains:
    preserve abstention
elif directional disagreement <= 50 keV/A:
    use frozen UAM-V4 guarded prediction
else:
    use leave-one-element-chain-out RKF prediction
```

The numerical value `50 keV/A` was inherited from the frozen UAM-V4 prospective guard and was not optimized over the RKF results.

## Whole-chart comparison

Both predictors retain exactly 3,514 predictions from 3,558 evaluated nuclei.

| Metric | Frozen UAM-V4 | Recognition Repair | Relative improvement |
|---|---:|---:|---:|
| Coverage | 98.7634% | 98.7634% | same |
| MAE (keV/A) | 10.2147 | 7.5174 | 26.41% |
| Median absolute residual (keV/A) | 0.9894 | 0.9878 | 0.16% |
| p95 absolute residual (keV/A) | 36.9846 | 35.3138 | 4.52% |
| p99 absolute residual (keV/A) | 165.2220 | 100.7613 | 39.01% |
| RMSE (keV/A) | 54.7503 | 29.3292 | 46.43% |
| Maximum absolute residual (keV/A) | 1,282.4164 | 794.3589 | 38.06% |
| Residuals >= 100 keV/A | 68 | 37 | 45.59% fewer |
| Residuals >= 250 keV/A | 22 | 7 | 68.18% fewer |
| Residuals >= 500 keV/A | 8 | 2 | 75.00% fewer |
| Residuals >= 1,000 keV/A | 3 | 0 | eliminated |

The generated report status is

```text
PASS_EXPLORATORY_RECOGNITION_REPAIR_BEATS_FROZEN_UAM_V4_SAME_COVERAGE
```

and its deterministic report hash is

```text
7b10f2a786d1b8ece797b89330a77d865a2ce66877b5c35708b075844bae93d8
```

## Sector explanation

### Coherent sector

There are 3,154 retained nuclei with directional disagreement at or below 50 keV/A.

Frozen UAM-V4 is the correct decoder in this sector:

| Metric | UAM-V4 | RKF |
|---|---:|---:|
| MAE (keV/A) | 3.0685 | 9.4069 |
| p95 (keV/A) | 12.2154 | 24.2920 |
| RMSE (keV/A) | 8.8409 | 14.5176 |

The local two-axis interpolation remains highly coherent here. Replacing it with the global RKF decoder would destroy information rather than add it.

### Seam-stressed sector

There are 360 retained nuclei with directional disagreement above 50 keV/A.

The RKF decoder becomes the better response in this sector:

| Metric | UAM-V4 | RKF repair |
|---|---:|---:|
| MAE (keV/A) | 72.8236 | 46.4946 |
| p95 (keV/A) | 299.2679 | 133.3643 |
| p99 (keV/A) | 907.4401 | 338.3114 |
| RMSE (keV/A) | 169.0417 | 87.8164 |
| Maximum (keV/A) | 1,282.4164 | 794.3589 |
| Residuals >= 1,000 keV/A | 3 | 0 |

Thus the directional disagreement is not merely an empirical confidence feature. It acts as a recognition-seam coordinate separating two lawful decoder regimes.

## Why this is a Recognition Kernel result

The result is not a weighted average of two predictors. It is a target-free observer-selection law:

```text
coherent local observer
    -> retain the sharp UAM decoder

open recognition seam
    -> transport to the cross-fitted RKF decoder
```

The RKF decoder is built from cut-even and cut-odd neutron/proton response jets, local curvature and jerk, the mixed tensor seam, asymmetry, pairing, surface and Coulomb coordinates, and magic-number proximity. Every target element chain is excluded from its decoder fit.

The same observable that declares loss of local coherence decides when the second decoder is needed. The framework therefore predicts a value and records why that value came from a different recognition regime.

## Validation boundary

This is a strong exploratory result, not yet an external predictive validation.

Important limitations remain:

- the repair architecture was formulated after inspecting the first RKF tail audit, although the numerical 50 keV/A boundary itself was inherited unchanged from frozen UAM-V4;
- frozen UAM-V4 uncertainty scales were internally calibrated on the same historical dataset;
- the RKF correction is leave-one-element-chain-out, not temporally future-blind;
- no claim is made that the response-axis exchange is the unique fundamental nuclear involution;
- no claim is made that Recognition Repair replaces established global nuclear mass models.

The next decisive test is to freeze V5.1 completely and evaluate it without modification on a later or independently held-out mass table.
