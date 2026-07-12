# Universal Atomic Model: Halo and Drip-Line Evidence Study V10.1

## Status

This directory stages the public, reproducible release of the halo and drip-line evidence layer developed in the private `Atomic-model` research repository.

UAM V4 remains frozen and unchanged. V10.1 is a separate experimental release rather than a retrospective modification of the V4 publication object.

## Scientific question

The study asks whether externally identified halo-nucleus candidates show unusual local nuclear mass-surface behaviour after comparison with nuclei from similar mass regions and similar operational drip-line classes.

The current evidence layer uses binding energy per nucleon and one- and two-nucleon separation energies. Halo labels are external benchmark annotations and are not used to construct predictions.

## Claim boundary

This release may support the following bounded claim:

> Externally annotated halo candidates can be tested for unusual local mass-surface behaviour using leakage-safe same-parity reconstruction, threshold-sensitive drip-line classification, and matched non-halo controls.

This release does not by itself establish spatial halo structure. Direct halo discrimination requires additional observables such as matter radii, charge radii, reaction cross sections, momentum distributions, or spectroscopic information.

## Predictor hierarchy

For each target isotope, the strongest available same-parity predictor is selected in this order:

1. `SAME_PARITY_CUBIC_N2_N4`
2. `SAME_PARITY_LINEAR_N2`
3. `ONE_SIDED_SAME_PARITY_LEFT`
4. `ONE_SIDED_SAME_PARITY_RIGHT`
5. `INSUFFICIENT_SAME_PARITY_SUPPORT`

Predictor classes are reported separately because their residual distributions are not assumed to be interchangeable.

## Drip-line sensitivity

Operational classifications are evaluated at multiple declared thresholds, initially:

- 500 keV
- 1000 keV
- 1500 keV
- 2000 keV

This threshold sweep distinguishes robust boundary proximity from classifications that depend strongly on one arbitrary cutoff.

## Matched controls

Each external halo candidate is compared with non-halo controls selected from the same broad mass region and the same 1000 keV drip classification. Ranking uses proximity in mass number, proton number, one-neutron separation energy, and two-neutron separation energy.

External halo labels do not enter prediction or distance scoring.

## Intended public package

```text
release/uam_halo_v10_1/
├── README.md
├── PUBLICATION_GATE.md
├── release_manifest.json
├── config/
├── data/
│   ├── manifests/
│   └── processed/
├── figures/
├── reports/
├── src/
└── tests/
```

## Reproduction target

The completed release will provide one documented command that regenerates the machine-readable report, summary tables, figures, and reproduction certificate from a frozen public input dataset.

## Current migration phase

The first migration phase establishes the public claim boundary and file manifest. Private-only imports, annotations, datasets, and internal naming must be audited before executable code or generated outputs are copied into this repository.
