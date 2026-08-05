# RKF Madhava–Smriti Nuclear Adapter V6

## Purpose

This experiment applies the bounded Recognition theorems without altering the
frozen UAM-V4 or Recognition Repair V5.1 predictors.

```text
Theorem 43: bilateral jet-flow capstone
Theorem 44: Madhava–Smriti correction/tail closure
                         ↓
neutron/proton nuclear response jets
                         ↓
level-1 / level-2 / level-3 cross-fitted prediction bodies
                         ↓
correction transfer, convergence audit and fail-closed ablations
```

The adapter is an exploratory held-out validation. It is not an external future
mass-table test and does not identify a fundamental nuclear Hamiltonian.

## Nuclear theorem map

For each nucleus, the local neutron and proton response packets are reconstructed
from the cut-even and cut-odd jets:

\[
J_N=J_+ + J_-,
\qquad
J_Z=J_+ - J_-.
\]

Their numerical reconstruction defect is the bilateral seam audit.

Let \(p_1,p_2,p_3\) be leave-one-element-chain-out RKF predictions built from
feature levels 1, 2 and 3. They are the successive finite Chandas bodies. Define

\[
q_2=p_2-p_1,
\qquad
q_3=p_3-p_2.
\]

The prospective refinement audit is target-free:

```text
EXACT_REFINEMENT_STABLE   |q2| and |q3| are numerically zero
CONTRACTIVE_MEMORY        |q3| <= |q2|
OPEN_REFINEMENT           |q3| > |q2|
OPEN_BILATERAL_SEAM       neutron/proton reconstruction fails
ABSTAIN_MISSING_JET_LEVEL one or more prediction bodies are unavailable
```

The held-out measured value \(y\) is used only for validation. Its empirical
Smriti tails are

\[
T_r=y-p_r.
\]

They obey the exact transfer identities

\[
p_r+T_r=y,
\qquad
T_2=T_1-q_2,
\qquad
T_3=T_2-q_3.
\]

These identities certify the adapter wiring. Whether the absolute tail decreases
is an empirical question and is reported, not assumed.

## Frozen decision structure

The predeclared 50 keV/A Recognition Repair boundary remains unchanged.

```text
coherent UAM sector:
    keep frozen UAM-V4

seam-stressed sector:
    audit level-1/2/3 RKF correction transfer
```

Three ablations are reported:

1. `v6_strict`: use level 3 only when refinement is stable/contractive and the
   existing level-3 burden guard passes; otherwise abstain.
2. `v6_fallback`: use level 3 on the same capstone pass; otherwise fall back to
   frozen UAM-V4.
3. `v6_order_selected`: use level 3 on a capstone pass; when the third correction
   is expansive but level 2 is guarded, stop at level 2; otherwise fall back to
   frozen UAM-V4.

No variant examines the target residual when selecting a prediction.

## Full-chart result

The theorem identities pass on all 3,558 evaluated nuclei:

```text
maximum bilateral reconstruction defect    1.8189894035458565e-12 keV/A
maximum validation closure defect          0
maximum correction-to-tail transfer defect 0
```

The refinement classification is:

```text
CONTRACTIVE_MEMORY  2,578 nuclei
OPEN_REFINEMENT       980 nuclei
```

The held-out absolute tail decreases from level 1 to level 2 for about 73.27%
of nuclei and from level 2 to level 3 for about 80.83%. Thus the deeper observer
usually repairs the tail, but not monotonically for every nucleus.

### Prediction conclusion

Recognition Repair V5.1 remains the best same-coverage predictor.

```text
V5.1                  3,514 predictions, MAE 7.5174 keV/A
V6 fallback           3,514 predictions, MAE 8.9778 keV/A
V6 order-selected     3,514 predictions, MAE 9.2109 keV/A
```

The strict V6 audit retains 3,370 predictions and reports MAE 5.9481 keV/A, but
its retained prediction values are exactly the same as V5.1 on those same 3,370
nuclei. The apparent improvement comes entirely from 144 additional abstentions.
It is therefore a selective-risk audit, not a new point predictor.

The correction ratio \(|q_3|/|q_2|\) is not promoted as a prospective error
score. In the seam-stressed sector its correlation with absolute level-3 error
is approximately 0.00027, effectively zero. The level-3 decoder burden is more
informative, with correlation about 0.24; the small burden-fail sector has much
larger errors. This motivates a future cross-fitted Smriti-risk decoder rather
than a hand-written ratio threshold.

## Theorem source pins

```text
Recognition-Kernel-Framework commit
60b8bba2b4579d75c691af6589b00a764f24622b

Bilateral jet-flow capstone certificate
4f0f31183c6de9b354fbc90134cfcd14c8d6f55270f41c1e286f719c0e06b091

Madhava–Smriti closure certificate
2dc970d0b180e6ae0c679879ac9d0aabbb138c9315942f8bc8d2565e1a539c35
```

## Promotion decision

```text
THEOREM IDENTITY ADAPTER                         PROMOTE
CORRECTION-TO-TAIL AND DEPTH ABLATION            PROMOTE
RECOGNITION REPAIR V5.1 SAME-COVERAGE PREDICTOR  RETAIN
V6 STRICT                                        SELECTIVE ABSTENTION AUDIT ONLY
V6 FALLBACK                                      DO NOT PROMOTE
V6 ORDER-SELECTED                                DO NOT PROMOTE
REFINEMENT RATIO AS ERROR SCORE                  DO NOT PROMOTE
```

## Claim boundary

```text
BILATERAL NEUTRON/PROTON JET RECONSTRUCTION     TESTED
MADHAVA CORRECTION-TO-TAIL IDENTITIES           TESTED
TARGET-FREE REFINEMENT CLASSIFICATION           IMPLEMENTED AND AUDITED
FROZEN UAM-V4 AND V5.1 PRESERVATION             ENFORCED
FULL-DATA ABLATION REPORT                        GENERATED BY CI

EXTERNAL FUTURE-BLIND VALIDATION                 NOT YET DONE
FUNDAMENTAL NUCLEAR GENERATOR                    NOT IDENTIFIED
UNIVERSAL IMPROVEMENT                            NOT CLAIMED
81/100 SPECTRAL TAIL SPECIALIZATION              NOT USED
```

The numerical report is generated at
`releases/rkf-nuclear-v6/madhava_smriti_report.json`.
