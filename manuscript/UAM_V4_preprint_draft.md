# Guarded Two-Axis Interpolation for Nuclear Binding Energy per Nucleon

## A reproducible empirical study on a frozen AME/NUBASE-derived dataset

**Author:** Monty Dabas  
**Affiliation:** Independent researcher  
**Draft status:** Internal preprint manuscript  
**Repository status:** Private during analysis and review

## Abstract

We evaluate a guarded two-axis interpolation method for estimating nuclear binding energy per nucleon from neighbouring nuclei in proton and neutron directions. The method combines leakage-safe same-element and cross-element local predictors, calibrates direction-specific uncertainty from residual distributions, and abstains when support is insufficient, nuclei are ultralight, or directional disagreement is excessive. Evaluation uses a frozen processed AME/NUBASE-derived dataset containing 3,558 nuclei. The method returns 3,514 predictions and 44 abstentions, corresponding to 98.7634% coverage. On retained predictions, the mean absolute residual is 10.2147 keV/A, the median absolute residual is 0.9894 keV/A, the root mean square residual is 54.7503 keV/A, and the mean absolute total binding-energy residual is 0.4403 MeV. Performance is strongly mass dependent: mean absolute residuals are 0.8920 keV/A for A >= 180, 1.8193 keV/A for 100 <= A < 180, 10.5844 keV/A for 40 <= A < 100, and 89.3060 keV/A for A < 40. Errors also increase near conventional shell closures. The guarded model outperforms an equal two-axis blend, a local-neighbour mean, and a deterministic five-fold out-of-fold semi-empirical mass-formula baseline on this dataset. These results establish a reproducible, internally calibrated empirical interpolation result. They do not constitute temporal validation, external validation, or evidence for a universal nuclear law.

## 1. Introduction

Accurate nuclear mass and binding-energy prediction remains a central problem in nuclear physics. Established approaches range from semi-empirical liquid-drop expressions to microscopic and hybrid mass models. The present work addresses a narrower question: how accurately can binding energy per nucleon be reconstructed from local regularity along neutron and proton directions when prediction support, disagreement, and abstention are made explicit?

The method studied here, referred to as UAM V4, uses two local interpolation axes. The first predicts within a fixed proton number using same-parity neutron neighbours. The second predicts across proton number at fixed neutron number. These directions are calibrated separately and then combined using inverse-variance weighting when both calibrated estimates are available. A guard layer abstains from prediction in declared high-risk cases.

The contribution of this study is empirical and reproducible. We provide a frozen dataset archive, standalone implementation, deterministic reproduction command, automated checks, compact prediction and abstention tables, subgroup analyses, baseline comparisons, and cryptographic checksums. The principal claim is limited to the reproduced performance on the declared dataset and evaluation protocol.

## 2. Dataset and provenance

### 2.1 Frozen dataset

The evaluation dataset is `ame_nubase_atomic_native.csv`, distributed in the repository archive `uam_v4_processed_dataset.zip`. It contains 3,558 rows and no rejected records under the declared schema checks. The processed source is derived from AME2020 and NUBASE2020 materials [1–3].

The verified dataset SHA-256 is:

`6277e46ea5f38795a3c2295dd655af754fedf6bc1ce02245564026058cd82d47`

The archive SHA-256 is:

`2e5746009909fb071a5e45be1bcfea0aa8cbc2fa8617a6e77c34d017edc4d675`

Each row includes proton number Z, neutron number N, mass number A, element symbol, binding energy per nucleon, uncertainty and estimated-value flags, mass quantities, separation energies, decay information, half-life fields, spin-parity fields, and source metadata.

### 2.2 Inclusion and target

All rows satisfying the declared integer composition fields and readable target field are retained. The target is `binding_energy_per_A_keV`. Prediction routines do not use the target value of the nucleus being predicted. Neighbouring nuclei may supply their observed binding-energy values.

### 2.3 Reproducibility status

The dataset row count, schema, prediction count, abstention count, coverage, and all declared headline metrics reproduce exactly in GitHub Actions. The resulting scientific reproduction certificate reports `SCIENTIFICALLY_REPRODUCED`.

The reproducible standalone complete-report hash is:

`0b6f67777a1ba176fbf8478db3c11c12a4a1024bdb001d6932840d114805bb4c`

A previously recorded historical serialization hash does not match because the original JSON artifact associated with that hash was not committed. This provenance discrepancy is disclosed separately and does not affect the reproduced counts or scientific metrics.

## 3. Method

### 3.1 Same-element neutron-direction predictor

For a target nucleus at fixed Z and neutron number N, the method first seeks same-parity neighbours at N ± 2 and N ± 4.

When all four neighbours are available, the predictor is

\[
\hat{y}_N = \frac{2}{3}\left(y_{N-2}+y_{N+2}\right)-\frac{1}{6}\left(y_{N-4}+y_{N+4}\right).
\]

When only N ± 2 are available, linear interpolation is used:

\[
\hat{y}_N = \frac{y_{N-2}+y_{N+2}}{2}.
\]

At chain boundaries, declared one-sided extrapolations are used when two same-side support points exist. Otherwise the direction reports insufficient support.

### 3.2 Cross-element proton-direction predictor

At fixed N, the proton-direction predictor uses Z ± 1 and Z ± 2 neighbours. With four neighbours,

\[
\hat{y}_Z = \frac{2}{3}\left(y_{Z-1}+y_{Z+1}\right)-\frac{1}{6}\left(y_{Z-2}+y_{Z+2}\right).
\]

With only Z ± 1 support,

\[
\hat{y}_Z = \frac{y_{Z-1}+y_{Z+1}}{2}.
\]

One-sided alternatives are available at boundaries. One-sided proton-direction predictions are not treated as eligible standalone substitutes in the guarded blend.

### 3.3 Residual calibration

Each directional predictor is grouped by predictor type and mass region. For each group, the median signed residual is recorded and a robust scale is estimated as

\[
\sigma_{\mathrm{robust}} = 1.4826\,\mathrm{median}\left(|r-\mathrm{median}(r)|\right).
\]

A calibration group must contain at least eight samples before its scale is used for inverse-variance blending.

### 3.4 Two-axis blend

When both directional estimates and both calibrated robust scales are available, inverse-variance weights are used:

\[
w_N = \frac{\sigma_N^{-2}}{\sigma_N^{-2}+\sigma_Z^{-2}}, \qquad
w_Z = \frac{\sigma_Z^{-2}}{\sigma_N^{-2}+\sigma_Z^{-2}},
\]

\[
\hat{y}_{\mathrm{blend}} = w_N\hat{y}_N+w_Z\hat{y}_Z.
\]

When only an eligible neutron-direction estimate is available, it is used directly. When only an eligible proton-direction estimate is available, it may be used directly. The raw blend precedes guard decisions.

### 3.5 Guard and abstention rules

The model abstains when any declared guard condition is met:

1. `ULTRALIGHT_A_LT_8`: mass number A is below 8.
2. `NO_ELIGIBLE_DIRECTION`: neither direction provides an eligible estimate.
3. `EXCESSIVE_DIRECTIONAL_DISAGREEMENT`: the absolute disagreement between directional predictions exceeds

\[
\max\left(50,\;3\sqrt{\sigma_N^2+\sigma_Z^2}\right)\;\mathrm{keV/A}.
\]

The frozen evaluation produces 44 abstentions and 3,514 retained predictions.

## 4. Evaluation design

### 4.1 Primary metrics

The principal residual is

\[
r_i = \hat{y}_i-y_i,
\]

measured in keV/A. We report coverage, mean absolute residual, median absolute residual, p95 and p99 absolute residual, maximum absolute residual, root mean square residual, and mean signed residual.

Total binding-energy residuals are computed as A times the per-nucleon residual and are reported in keV and MeV.

### 4.2 Subgroup analyses

Performance is analysed by four mass regions:

- A < 40
- 40 <= A < 100
- 100 <= A < 180
- A >= 180

Shell-closure analysis uses conventional magic numbers 2, 8, 20, 28, 50, 82, and 126. Nuclei are classified as exactly at a magic Z or N, within two units of a magic Z or N, or away from magic numbers.

The stability analysis derived from processed half-life fields is retained as exploratory only because the current processed fields do not expose a reliable distinct stable group.

### 4.3 Baselines

Three internal baselines are evaluated:

1. Equal-axis blend: unweighted mean of available neutron- and proton-direction predictions before calibration and guarding.
2. Local-neighbour mean: mean of available leakage-safe neighbours at N ± 2 within an element and Z ± 1 at fixed N.
3. Semi-empirical mass formula: a five-parameter liquid-drop-style linear model based on the conventional Weizsäcker form [4], fitted and evaluated using deterministic five-fold out-of-fold prediction. The fold rule is `(31*Z + 17*N + A) mod 5`.

The SEMF baseline is a simple conventional reference and is not presented as a modern state-of-the-art nuclear mass model.

## 5. Results

### 5.1 Overall performance

The guarded model produces 3,514 predictions from 3,558 nuclei, yielding 98.7634% coverage. The retained prediction metrics are:

| Metric | Value |
|---|---:|
| Mean absolute residual | 10.2147 keV/A |
| Median absolute residual | 0.9894 keV/A |
| p95 absolute residual | 36.9846 keV/A |
| p99 absolute residual | 165.2220 keV/A |
| Maximum absolute residual | 1282.4164 keV/A |
| Root mean square residual | 54.7503 keV/A |
| Mean signed residual | +2.0482 keV/A |
| Mean absolute total-energy residual | 0.4403 MeV |
| Median absolute total-energy residual | 0.1380 MeV |
| p95 absolute total-energy residual | 1.7613 MeV |

The low median relative to the mean and RMSE indicates a concentrated low-error bulk with a smaller heavy residual tail.

### 5.2 Performance by mass region

| Mass region | Coverage | MAE (keV/A) | RMSE (keV/A) |
|---|---:|---:|---:|
| A < 40 | 88.12% | 89.3060 | 195.3110 |
| 40 <= A < 100 | 99.51% | 10.5844 | 20.0796 |
| 100 <= A < 180 | 100.00% | 1.8193 | 3.5334 |
| A >= 180 | 99.63% | 0.8920 | 1.5763 |

The model is most accurate for heavy and very-heavy nuclei. Light nuclei dominate both abstentions and extreme retained residuals. This mass dependence is a central limitation and should be considered part of the result rather than treated as a peripheral anomaly.

### 5.3 Shell-closure behaviour

| Shell class | Coverage | MAE (keV/A) | RMSE (keV/A) |
|---|---:|---:|---:|
| At magic Z or N | 95.97% | 31.9798 | 115.7494 |
| Within two units of magic Z or N | 97.13% | 20.3986 | 82.2956 |
| Away from magic numbers | 99.82% | 3.2502 | 11.1087 |

Errors rise markedly at and near conventional shell closures. This behaviour is consistent with the difficulty of representing abrupt structural effects using smooth local interpolation alone.

### 5.4 Axis comparison

| Method | Coverage | MAE (keV/A) | RMSE (keV/A) |
|---|---:|---:|---:|
| Neutron direction | 99.72% | 30.6717 | 249.4646 |
| Proton direction | 99.94% | 33.6621 | 170.7858 |
| Raw calibrated blend | 99.86% | 26.1732 | 239.6016 |
| Guarded blend | 98.76% | 10.2147 | 54.7503 |

The guarded blend substantially reduces the residual tail compared with either direction and with the unguarded calibrated blend. The improvement is therefore attributable not merely to averaging but to calibration, directional eligibility rules, and abstention.

### 5.5 Conventional baseline comparison

| Method | Coverage | MAE (keV/A) | RMSE (keV/A) |
|---|---:|---:|---:|
| UAM V4 guarded | 98.76% | 10.2147 | 54.7503 |
| Equal-axis blend | 100.00% | 27.2556 | 188.5780 |
| Local-neighbour mean | 100.00% | 38.1164 | 204.0074 |
| SEMF, five-fold out of fold | 100.00% | 181.7699 | 341.4553 |

Relative to these baselines, UAM V4 reduces MAE by approximately 62.5% versus the equal-axis blend, 73.2% versus the local-neighbour mean, and 94.4% versus the fitted five-fold SEMF reference.

These comparisons demonstrate that the observed performance is not reproduced by simple averaging, naive neighbourhood smoothing, or a low-capacity liquid-drop expression. They do not establish superiority over modern recognised nuclear mass models.


### 5.6 Recognised external-model comparison

UAM V4 was compared with the recognised FRDM(2012) nuclear-mass model on the exact intersection of nuclei for which both methods produced predictions. This common set contains **3,448 nuclei**.

| Method | MAE (keV/A) | Median absolute error (keV/A) | p95 (keV/A) | p99 (keV/A) | RMSE (keV/A) | Maximum error (keV/A) |
|---|---:|---:|---:|---:|---:|---:|
| UAM V4 guarded | 6.1442 | 0.9525 | 26.5449 | 94.1586 | 21.4926 | 365.7575 |
| FRDM(2012) | 6.6248 | 2.6019 | 29.1815 | 59.1936 | 13.4898 | 131.4058 |

UAM V4 has a lower MAE by **0.4806 keV/A** on the common set. It also has lower median and p95 absolute error. On a nucleus-by-nucleus basis, UAM V4 has the lower absolute error for **2,418 nuclei**, while FRDM(2012) has the lower error for **1,028 nuclei**, with **2 ties**.

FRDM(2012), however, has lower RMSE, p99 error and maximum error. The comparison therefore indicates that UAM V4 has lower absolute error for most nuclei in this common-set benchmark and performs better on central error statistics, while FRDM(2012) controls the extreme residual tail more effectively.

This comparison is not a temporally independent validation. FRDM(2012) was fitted using historical measured nuclear masses, and UAM V4 calibration and evaluation use the frozen processed AME/NUBASE-derived dataset.


### 5.7 Coverage-error behaviour

A risk-ranking diagnostic orders raw predictions by directional disagreement and combined robust scale, then progressively abstains from the highest-risk tail. The resulting coverage-error curve confirms that lower retained coverage reduces error. Because the same dataset supplies calibration and evaluation residuals, this curve is an in-sample selective-prediction diagnostic rather than an externally validated uncertainty curve [5].

## 6. Failure analysis

The 50 largest retained residuals are exported in `extreme_retained_residuals_top50.csv`. The dominant failure patterns are concentrated among light nuclei, nuclei at or near conventional shell closures, and cases with large directional disagreement that remain below the declared abstention threshold.

The largest retained absolute residual is 1282.4164 keV/A. Such outliers account for the substantial separation between median absolute residual, MAE, and RMSE. The model should therefore not be characterised using MAE alone. Median, tail percentiles, maximum residual, mass-region results, and coverage must accompany any summary.

The present guard threshold is fixed at three combined robust standard deviations with a 50 keV/A floor. Future work should evaluate this threshold under nested or temporally separated validation rather than tune it retrospectively on the frozen evaluation set.

## 7. Discussion

The results show that local nuclear regularity contains substantial predictive information when neutron- and proton-direction estimates are treated as distinct evidence channels. The low median error and strong heavy-nucleus performance indicate that the local response is highly regular across much of the chart. The deterioration for light nuclei and shell closures shows where smooth local transport assumptions break down.

The selective guard is essential. An unguarded blend retains nearly complete coverage but has substantially higher MAE and RMSE. This establishes a coverage-accuracy trade-off and motivates reporting abstention as part of the model rather than as missing output.

The baseline results strengthen the internal empirical case. However, all principal calibration and subgroup findings are derived from the same processed dataset. The study therefore supports a reproducible interpolation result, not a universal physical claim. Independent assessment requires at least one temporally separated mass release, comparison against additional recognised external mass-model tables, and preferably evaluation by investigators who did not construct the method.

## 8. Limitations

1. The evaluation is internally calibrated and in sample with respect to residual-scale estimation.
2. No temporally later AME/NUBASE release has yet been used as a frozen external test set.
3. A recognised FRDM(2012) comparison has been completed on the common prediction subset. Temporally independent validation remains incomplete.
4. Stable-versus-radioactive classification remains incomplete because the processed half-life representation does not reliably expose a distinct stable group.
5. Performance varies strongly by mass region and shell proximity.
6. The full historical report serialization hash cannot be reconstructed because the original hashed JSON artifact was not committed.
7. The current uncertainty proxy is empirical and should not be interpreted as a calibrated physical probability without external validation.

## 9. Reproducibility statement

The complete reproduction path is implemented using Python 3.11 and standard-library code. From the repository root, run:

```bash
python scripts/reproduce_release.py
python scripts/build_publication_bundle.py
python scripts/build_paper_analysis.py
python scripts/build_baseline_comparison.py
```

GitHub Actions executes the same pipeline, verifies the frozen dataset and scientific fingerprint, and commits generated certificates and tables. Release-wide checksums are provided in `releases/uam-v4/publication_bundle/SHA256SUMS`.

## 10. Data and code availability

The repository currently remains private during manuscript and release review. It contains the frozen processed-data archive, standalone implementation, tests, reproduction scripts, certificates, compact prediction and abstention tables, analysis outputs, baseline comparisons, and checksum manifests.

The intended public release is a technical inspection and citation release associated with inventor-controlled intellectual-property materials. Publication does not grant a patent licence or unrestricted reuse rights unless an explicit licence says otherwise. Repository visibility should change only after final review of data redistribution rights, external-model comparison, citation metadata, and the claim boundary.

## 11. Conclusion

A guarded two-axis interpolation method reproduces nuclear binding energy per nucleon for 3,514 of 3,558 nuclei at a mean absolute residual of 10.2147 keV/A and 98.7634% coverage on a frozen AME/NUBASE-derived dataset. Accuracy is especially strong for heavy and very-heavy nuclei and degrades for light nuclei and near shell closures. Calibration, directional blending, and abstention materially improve performance over either axis alone and over three conventional internal baselines.

The result is fully reproducible at the level of the frozen dataset, implementation, prediction counts, abstentions, and declared scientific metrics. It remains an internally calibrated empirical result. External validation and recognised-model comparison are required before stronger physical or generalisation claims are justified.

## References

1. Huang, W. J., Wang, M., Kondev, F. G., Audi, G., and Naimi, S. “The AME 2020 atomic mass evaluation (I). Evaluation of input data, and adjustment procedures.” *Chinese Physics C* **45**, 030002 (2021). DOI: 10.1088/1674-1137/abddb0.
2. Wang, M., Huang, W. J., Kondev, F. G., Audi, G., and Naimi, S. “The AME 2020 atomic mass evaluation (II). Tables, graphs and references.” *Chinese Physics C* **45**, 030003 (2021). DOI: 10.1088/1674-1137/abddaf.
3. Kondev, F. G., Wang, M., Huang, W. J., Naimi, S., and Audi, G. “The NUBASE2020 evaluation of nuclear physics properties.” *Chinese Physics C* **45**, 030001 (2021). DOI: 10.1088/1674-1137/abddae.
4. von Weizsäcker, C. F. “Zur Theorie der Kernmassen.” *Zeitschrift für Physik* **96**, 431–458 (1935). DOI: 10.1007/BF01337700.
5. Geifman, Y., and El-Yaniv, R. “Selective classification for deep neural networks.” In *Advances in Neural Information Processing Systems 30* (2017). Used here only for the general selective-prediction framing; the present method is not a neural classifier.
