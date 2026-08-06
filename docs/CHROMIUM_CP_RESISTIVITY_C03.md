# C03 Chromium simultaneous heat-capacity and resistivity acquisition audit

## Primary source

C03 targets the 1969 Solid State Communications paper

**Simultaneous measurement of the anomalous heat capacity and resistivity of chromium near TN**

by M. B. Salamon, D. S. Simons and P. R. Garnier, volume 7, issue 15, pages 1035–1038, DOI `10.1016/0038-1098(69)90464-5`.

The verified publisher metadata and abstract support the following experiment description:

- elemental chromium near the Neel transition;
- heat capacity and the temperature coefficient of resistivity measured simultaneously;
- one specimen and one temperature calibration;
- an AC modulation technique;
- a reported relation in which the heat-capacity critical exponent is twice the exponent for `drho/dT`.

The verified abstract does not expose numerical exponent values or pointwise response arrays.

## Branch semantics

The experiment uses an AC modulation protocol. C03 therefore labels the protocol

```text
AC_MODULATION_NEAR_EQUILIBRIUM
MODULATION_BRANCH_NOT_HEATING_COOLING_BRANCH
```

It is not lawful to relabel this as a heating or cooling branch. A modulation response may encode amplitude and phase relative to the applied oscillation, whereas heating and cooling branches encode directional thermal history. Those are different experimental coordinates.

## Acquisition result

Four acquisition routes were audited:

1. the official publisher landing page;
2. exact-title and DOI public search;
3. connected conversation and Library files;
4. secondary chromium theses and reviews.

The official route verified metadata and abstract only. No publisher or author PDF, lossless primary figure, exact figure page or panel identity, or machine-readable `Cp` and `drho/dT` arrays were acquired. Secondary theses may establish citation context but are not admitted as substitutes for the primary figure.

## Digitization gates

Before digitization, C03 requires:

- immutable primary figure bytes and SHA-256 hash;
- exact page, figure and panel identity;
- two calibration points on the temperature axis;
- two calibration points on each response axis;
- linear or logarithmic scale declaration;
- panel pixel bounds and curve or marker identity;
- pixel-pick and tick-reading uncertainty;
- temperature calibration uncertainty;
- AC modulation frequency, amplitude and phase convention;
- at least twenty accepted points per channel;
- shared calibration covariance between the two simultaneous channels.

An abstract sentence cannot be converted into a numerical curve. Numeric critical exponents cannot be imported from later papers and assigned to the 1969 data. A secondary reproduction cannot silently replace the original graph.

## Result

```text
source metadata verified       true
same specimen                  true
simultaneous channels          Cp and drho/dT
primary figure acquired        false
machine-readable arrays        false
accepted points per channel    0
axis calibration               false
uncertainty and covariance     false
digitization ready             false
curvature allowed              false
anomaly significance allowed   false
```

Status:

```text
PASS_CHROMIUM_C03_ACQUISITION_AUDIT_DIGITIZATION_BLOCKED
```

`PASS` means that the source identity and fail-closed acquisition contract reproduce. It does not mean that a curve has been digitized.

## Next stage

`C04_CHROMIUM_PRIMARY_SCAN_OR_AUTHOR_DATA_ACQUISITION`

C04 must pin a publisher or author scan, or author-supplied numerical arrays. Only after the figure hash, axes, protocol metadata and uncertainty model are frozen can the simultaneous channel curves be digitized and differentiated.
