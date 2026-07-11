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

The repository is under construction and remains private while the publication package is assembled. See [PUBLICATION_STATUS.md](PUBLICATION_STATUS.md) for the active gate checklist.
