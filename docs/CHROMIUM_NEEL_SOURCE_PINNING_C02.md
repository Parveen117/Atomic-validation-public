# C02 Chromium thermal-magnetic Néel source pinning

## Purpose

C01 found sharp electronic and isotope curvature but no local three-sigma nuclear anomaly. C02 therefore moves to the macroscopic chromium transition near room temperature and freezes the source and state-variable contract before any curve fitting.

The nominal search window is

```text
293 K <= T <= 323 K
```

but `311 K` is only a reference landmark. It is not a universal coordinate because reported transition temperatures depend on specimen purity, strain, annealing, alloying, crystal state, thermal branch and measurement protocol.

## Typed state

Every admitted point must carry:

```text
equilibrium_sample_temperature_K
thermal_branch
sample_state_id
```

The sample state must preserve purity, crystal orientation or polycrystalline state, strain or pressure, annealing history, interstitial contamination, scan rate and thermal lag.

## Primary same-specimen anchor

The 1969 experiment `10.1016/0038-1098(69)90464-5` measured anomalous heat capacity and the temperature coefficient of resistivity simultaneously near the Néel transition. It is the strongest acquisition target because both channels share one specimen and one temperature calibration.

```text
heat_capacity_Cp
resistivity_temperature_coefficient_drho_dT
```

This gives a valid two-channel starting packet, not a four-channel curvature experiment.

## Additional pinned sources

Heat capacity and strain dependence:

- `10.1088/0305-4608/9/3/007`
- reported transition temperature approximately 311.4 K;
- reported magnetic entropy 35 mJ mol^-1 K^-1;
- reported latent heat 1.4 J mol^-1;
- strained and annealed specimens must not be merged.

Thermal expansion and magnetoelastic response:

- `10.1143/JPSJ.27.786`, single-crystal expansion at the transition;
- `10.1088/0305-4608/16/4/009`, Cr and CrV expansion from 2 to 700 K with Cr95V5 as a paramagnetic reference;
- `10.1103/PhysRev.129.1063`, elastic constants and expansion from 77 to 500 K with anomalies near 310 K and 120 K.

Electrical transport:

- `10.1103/PhysRevB.18.3665`, resistivity of antiferromagnetic chromium near the transition.

First-order and branch witnesses:

- `10.1016/0375-9601(71)90719-5`, latent heat `0.47 +/- 0.1 cal mol^-1`;
- `10.1103/PhysRevLett.27.1523`, first-order transition witness;
- `10.1088/0305-4608/5/10/019`, calorimetric comparison of pure Cr and Cr alloys;
- `10.1088/0305-4608/10/11/026`, heating/cooling hysteresis target.

## Admission result

Ten sources are pinned. Eight contain more than one observable or protocol-level quantity on the same specimen, but only the simultaneous heat-capacity/resistivity paper supplies the primary same-specimen response pair required for the next numerical step.

No pinned source currently provides a verified public machine-readable curve with pointwise uncertainty and shared calibration covariance.

```text
source pinning                     PASS
machine-readable curve sources     0
four-channel common specimen       false
cross-paper curvature              forbidden
curvature computed                 false
anomaly significance computed      false
```

Official status:

```text
PASS_CHROMIUM_NEEL_SOURCE_PINNING_DATA_ACQUISITION_REQUIRED
```

## Next stage

`C03_CHROMIUM_SIMULTANEOUS_CP_RESISTIVITY_DIGITIZATION_AND_BRANCH_AUDIT`

C03 must first acquire or digitize the simultaneous heat-capacity and resistivity curves, preserve modulation or thermal-branch semantics, and freeze axis and pixel uncertainty. Thermal-expansion and magnetic-order channels remain separate until their specimen registration is explicit.
