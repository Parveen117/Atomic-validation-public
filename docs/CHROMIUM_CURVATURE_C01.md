# C01 Chromium curvature audit

## Question

Does chromium's known electronic-configuration exception correspond to a uniquely large and data-supported curvature anomaly?

C01 separates two claims that are easy to blur:

1. the exact neutral-ground-state configuration Smriti across the first transition series;
2. curvature and seam structure across the measured chromium isotope chain.

## Electronic configuration result

The NIST-grounded ledger gives chromium the promotion vector

```text
3d  +1
4s  -1
```

relative to the frozen Madelung baseline. On the active `(3d,4s)` coordinates C01 uses

```text
K_Z = Sigma_(Z+1) - 2 Sigma_Z + Sigma_(Z-1)
```

and normalizes its Euclidean norm by `sqrt(2)`. Chromium has curvature `2.0`, but copper also has curvature `2.0`. Configuration curvature therefore detects the isolated promotion pattern but does not uniquely select chromium.

## Nuclear binding-surface result

The source report contains 3,558 nuclei and 30 chromium isotopes, Cr-41 through Cr-70. Twenty-two chromium isotopes have the complete neutron and proton cubic support required by the primary gate.

The strongest chromium structures are:

```text
Cr-46  neutron curvature       -30.405250 keV/A
Cr-46  cut-odd curvature       -22.018592 keV/A
Cr-47  cut-even curvature      -20.090667 keV/A
Cr-48  seam residue            -32.650214 keV/A
```

The global all-mass robust score for Cr-46 neutron curvature is approximately `-23.07`, but that comparison is confounded by the much sharper curvature scale of light nuclei. C01 therefore freezes a local same-support reference set with `20 <= Z <= 28` and `40 <= A <= 70`.

Against that local reference, the largest absolute chromium screening score is approximately `1.86`, below the frozen threshold `3.0`. The result is:

```text
PASS_CHROMIUM_CURVATURE_AUDIT_NO_LOCAL_THREE_SIGMA_ANOMALY
```

`PASS` means the audit and controls reproduced. It does not mean a chromium anomaly was detected.

## Claim boundary

- Robust z-scores are screening scores, not measurement sigma values.
- Experimental covariance is not available in the source report and is not invented.
- Chromium shows sharp local structures, but C01 does not establish a unique electronic or nuclear curvature anomaly.
- The thermal and magnetic anomaly near chromium's antiferromagnetic transition is a separate C02 source-data campaign.
