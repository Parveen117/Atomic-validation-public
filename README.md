# Atomic Validation: Guarded Two-Axis Nuclear Binding-Energy Reconstruction

This repository is the publication-focused validation package for a guarded, uncertainty-weighted two-axis reconstruction method for nuclear binding energy per nucleon.

The repository is intentionally separated from the broader Atomic-model development repository. It contains only the material needed to inspect, reproduce, audit, and cite the empirical validation result.

## Primary result

On an AME/NUBASE-derived working dataset containing 3,558 evaluated nuclei, the guarded two-axis V4 response produced:

| Metric | Result |
|---|---:|
| Evaluated nuclei | 3,558 |
| Predictions retained | 3,514 |
| Abstentions | 44 |
| Coverage | 98.7634% |
| Mean absolute residual | 10.2147 keV/A |
| Median absolute residual | 0.9894 keV/A |
| 95th-percentile absolute residual | 36.9846 keV/A |
| 99th-percentile absolute residual | 165.2220 keV/A |
| RMSE | 54.7503 keV/A |
| Maximum retained absolute residual | 1,282.4164 keV/A |

The method combines independent neutron-direction and proton-direction local reconstructions using uncertainty-aware weighting. Directional disagreement and ultralight-state rules are used as prospective abstention signals.

## Scientific claim boundary

This repository supports the following empirical claim:

> A guarded combination of independent neutron-direction and proton-direction local reconstructions can recover nuclear binding energy per nucleon across most of the evaluated chart with explicit abstention and strongly reduced average residuals relative to either individual reconstruction axis.

This repository does **not** claim that the current result is:

- an externally validated universal nuclear law;
- a replacement for established global nuclear mass models;
- proof of a broader foundational physical framework;
- a temporally independent prediction of measurements released after model freezing.

Those stronger questions require additional comparison and external validation.

## Chromium anomaly campaign

The chromium campaign is developed on a separate branch and draft pull request so that its claim boundaries do not alter the frozen nuclear baseline.

### C01: electronic and isotope curvature

- chromium and copper both have normalized electronic-configuration curvature `2.0` on the active `(3d,4s)` Smriti coordinates;
- the source report contains 30 chromium isotopes, with 22 having complete neutron and proton cubic support;
- the strongest chromium structures occur at Cr-46, Cr-47 and Cr-48;
- the largest local robust screening score is `1.862842`, below the frozen threshold `3.0`.

Status:

`PASS_CHROMIUM_CURVATURE_AUDIT_NO_LOCAL_THREE_SIGMA_ANOMALY`

### C02: Neel-transition source pinning

C02 pins ten heat-capacity, transport, expansion, elastic, latent-heat and hysteresis sources. It types temperature, thermal branch and specimen state separately and forbids universal substitution of `311 K` across specimens and protocols.

Status:

`PASS_CHROMIUM_NEEL_SOURCE_PINNING_DATA_ACQUISITION_REQUIRED`

### C03: simultaneous Cp and resistivity acquisition audit

The primary 1969 experiment measures heat capacity and `drho/dT` simultaneously on one specimen using an AC modulation technique. Its official metadata and abstract are verified, but no publisher or author PDF, primary figure bitmap or machine-readable arrays are pinned.

The modulation response is not relabelled as a heating or cooling branch. An abstract relation between critical exponents is not converted into numerical exponent values or response curves.

Status:

`PASS_CHROMIUM_C03_ACQUISITION_AUDIT_DIGITIZATION_BLOCKED`

### C04: primary scan or author-data acquisition packet

C04 ranks five verified acquisition routes:

1. direct request to Myron B. Salamon using the contact on his official emeritus profile;
2. University of Illinois Archives series `11/14/818`, containing ARPA SD-131 annual technical reports;
3. University of Illinois Materials Research Laboratory legacy-record inquiry;
4. home-institution or public-library document delivery;
5. publisher access through the DOI landing page.

Prepared author, archive and library request documents are committed. No external message is marked as sent and no primary file has been received. Any future file must enter through an original-byte SHA-256 intake certificate before image extraction or digitization.

Status:

`PASS_CHROMIUM_C04_ACQUISITION_PACKET_READY_EXTERNAL_RESPONSE_REQUIRED`

### C05: Neel cut-square adapter and sharp beta burden

C05 transfers the Recognition Kernel cut-square architecture into a typed chromium adapter. It freezes:

```text
candidate cut       J_tau: tau -> -tau
observer tower      A_N = direct sum of admitted tau derivatives
response metric     H_Cr from covariance or compatibility whitening
Neel target         L_N frozen before fitting
sharp burden        beta_Cr,N
positive defect     A_N* H_Cr A_N - L_N* L_N
native curvature    [G_even,G_odd]
```

The exact proof gate is

```text
A_N* H_Cr A_N - L_N* L_N >= 0  iff  beta_Cr,N <= 1.
```

Exact rational implementation controls verify strict closure at beta `1/4`, the critical threshold at beta `1`, burden failure at beta `4`, and a target-blind case that requires a higher observer layer.

No physical chromium beta is computed. The candidate reduced-temperature cut is not admitted, no shared covariance is available, and a raw response second derivative is not promoted to native seam curvature.

Status:

`PASS_CHROMIUM_C05_CUT_SQUARE_ADAPTER_FROZEN_BETA_DATA_REQUIRED`

### C06: original-byte intake and outward beta interval

C06 freezes the primary-data packet that must populate the C05 theorem. The required order is:

```text
original bytes and SHA-256
-> source-specific TN with uncertainty
-> two-sided tau pairing
-> frozen baseline and derivative rules
-> covariance whitening
-> visible-quotient observer
-> target frozen before fitting
-> certified beta interval.
```

On the whitened visible quotient `W = H_Cr^(1/2) A_N`, C06 consumes outward bounds

```text
target_norm_lower <= ||L_N|| <= target_norm_upper,
||W|| <= observer_norm_upper,
sigma_min(W) >= visible_singular_lower > 0,
```

and returns the conservative enclosure

```text
beta_lower = (target_norm_lower / observer_norm_upper)^2,
beta_upper = (target_norm_upper / visible_singular_lower)^2.
```

The interval engine separately classifies strict closure, critical aligned closure, threshold uncertainty, burden failure, target blindness and an open or wrongly chosen cut. Eleven regression tests include a fully populated synthetic packet while the committed physical packet remains empty.

Current physical state:

```text
primary files admitted       0
source-specific TN frozen    false
bilateral pairs              0
metric and visible quotient  not certified
physical beta interval       not computed
physical classification      DATA_REQUIRED
```

Status:

`PASS_CHROMIUM_C06_ENGINE_FROZEN_PRIMARY_DATA_REQUIRED`

The next stage is `C07_CHROMIUM_BILATERAL_CUT_ADMISSION_AND_NATIVE_CURVATURE`. It starts after C06 produces an admitted physical response packet.

## Repository structure

```text
.
├── README.md
├── PUBLICATION_STATUS.md
├── docs/
│   ├── CLAIM_SCOPE.md
│   └── VALIDATION_PLAN.md
├── manuscript/
├── release/
│   └── uam_v4_publication/
├── src/
├── tests/
└── data/
    ├── manifests/
    └── processed/
```

The code, frozen report artefacts, dataset manifest, manuscript, figures, and complete reproduction command will be added in the next publication stages.

## Validation sequence

The publication package will preserve the progression that led to V4:

1. **V1:** common state and invariant architecture;
2. **V2:** same-chain response, uncertainty and abstention;
3. **V3:** leave-one-element-chain-out transfer;
4. **V3.1:** residual atlas and calibration;
5. **V3.2:** outlier diagnosis and prospective guards;
6. **V3.3:** nested chain-excluded abstention validation;
7. **V4:** guarded uncertainty-weighted two-axis response.

## Reproducibility target

A complete release must include:

- a frozen source revision;
- a dataset manifest and provenance statement;
- a deterministic configuration file;
- machine-readable metrics and predictions;
- an abstention ledger;
- hashes for all principal outputs;
- dependency and environment information;
- a single reproduction command;
- a clean automated test run.

## Current status

The core publication package and the chromium C01-C06 theorem-guided audit ladder are under active development. See [PUBLICATION_STATUS.md](PUBLICATION_STATUS.md) for the active gate checklist.
