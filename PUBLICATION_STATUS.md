# Publication Status

## Current decision

**Stage:** Paper analysis and manuscript preparation  
**Repository visibility:** Private  
**Scientific status:** Headline V4 result independently reproduced from the frozen processed dataset  
**Publication bundle status:** Frozen compact bundle generated and checksummed  
**Paper analysis status:** Reproducible subgroup, residual, coverage-error and conventional baseline tables generated  
**Legacy serialization status:** Full-report hash mismatch disclosed in Issue #2  
**Journal status:** Recognised external mass-model comparison and temporally separated validation remain recommended

## Gate A: Scientific framing

- [x] State the primary empirical result.
- [x] Separate demonstrated results from broader theoretical interpretation.
- [x] State that the result is internally calibrated and not yet an externally validated universal law.
- [x] Define the exact frozen dataset release and provenance.
- [x] Define the final inclusion and exclusion rules.
- [x] Freeze the V4 algorithm and configuration.

## Gate B: Reproducibility

- [x] Copy the standalone V4 implementation into `src/`.
- [x] Copy and consolidate the relevant tests into `tests/`.
- [x] Declare the supported Python environment.
- [x] Add a deterministic end-to-end reproduction command.
- [x] Run the complete package in GitHub Actions.
- [x] Verify the dataset checksum, row count, schema, prediction count, abstention count and headline metrics.
- [x] Add continuous integration and persisted reproduction certificates.
- [ ] Recover or formally retire the uncommitted legacy JSON artifact associated with the historical full-report hash.

## Gate C: Frozen release artefacts

The directory `releases/uam-v4/publication_bundle/` contains:

- [x] `configuration.json`
- [x] `dataset_manifest.json`
- [x] `predictions.csv`
- [x] `abstentions.csv`
- [x] `mass_region_metrics.csv`
- [x] `mass_region_metrics.json`
- [x] `environment.json`
- [x] `reproduction_command.txt`
- [x] `report_hash.txt`
- [x] `SHA256SUMS`
- [x] `bundle_certificate.json`

## Gate D: Analysis required for the paper

- [x] Report residuals in both keV/A and total keV or MeV.
- [x] Report performance by mass region.
- [x] Report performance near shell closures.
- [ ] Complete a defensible stable-versus-unstable classification; current processed half-life fields do not expose a distinct stable group reliably.
- [x] Generate and inspect the 50 largest retained residuals.
- [x] Include coverage-error and abstention-error curves.
- [x] Compare V4 against both individual axes.
- [x] Compare against a leakage-safe local-neighbour interpolation baseline.
- [x] Compare against an equal unweighted two-axis blend.
- [x] Compare against a deterministic five-fold out-of-fold semi-empirical mass-formula baseline.
- [ ] Add at least one recognised external mass-model comparison where reproducible.

## Current analysis findings

- Overall guarded MAE: **10.2147 keV/A**, corresponding to **0.4403 MeV mean absolute total binding-energy error**.
- Heavy nuclei, `100 <= A < 180`: **1.8193 keV/A MAE** at full coverage.
- Very-heavy nuclei, `A >= 180`: **0.8920 keV/A MAE** at **99.63%** coverage.
- Medium nuclei, `40 <= A < 100`: **10.5844 keV/A MAE**.
- Light nuclei, `A < 40`: **89.3060 keV/A MAE** at **88.12%** coverage; this region dominates the retained error tail.
- At conventional magic proton or neutron numbers: **31.9798 keV/A MAE**.
- Within two units of a magic number: **20.3986 keV/A MAE**.
- Away from magic numbers: **3.2502 keV/A MAE** at **99.82%** coverage.
- Neutron-axis MAE: **30.6717 keV/A**; proton-axis MAE: **33.6621 keV/A**; guarded blend MAE: **10.2147 keV/A**.
- Leakage-safe local-neighbour mean MAE: **38.1164 keV/A**.
- Equal unweighted two-axis blend MAE: **27.2556 keV/A**.
- Five-fold out-of-fold SEMF baseline MAE: **181.7699 keV/A**.
- UAM V4 reduces MAE by approximately **73.2%** relative to the local-neighbour baseline and **62.5%** relative to the equal-axis blend.
- The subgroup, coverage-error and fitted-baseline analyses are not external or temporal validation.
- The fitted SEMF baseline is deliberately conventional and simple; it must not be represented as a state-of-the-art global mass model.

## Gate E: Manuscript

- [ ] Title and abstract.
- [ ] Dataset and provenance section.
- [ ] Method section with leakage controls.
- [ ] Validation design.
- [ ] Results and uncertainty.
- [ ] Failure analysis.
- [x] Conventional baseline comparison tables.
- [ ] Recognised external mass-model comparison.
- [ ] Limitations and claim boundary.
- [ ] Reproducibility statement.
- [ ] Data and code availability statement.
- [ ] References.

## Gate F: Public release metadata

- [ ] Add `LICENSE` after the release licence is selected.
- [ ] Add `CITATION.cff` after author names, affiliations and preferred citation are confirmed.
- [ ] Add `CONTRIBUTING.md` if outside contributions will be accepted.
- [ ] Add a versioned release tag.
- [ ] Archive the release in a DOI-issuing repository.
- [ ] Change repository visibility only after Gates A–F are reviewed.

## Reproduced result

- Dataset rows: **3,558**
- Guarded predictions: **3,514**
- Abstentions: **44**
- Coverage: **98.76335019673974%**
- MAE: **10.214723170037805 keV/A**
- RMSE: **54.750312355960354 keV/A**
- Dataset SHA-256: `6277e46ea5f38795a3c2295dd655af754fedf6bc1ce02245564026058cd82d47`
- Reproducible standalone report hash: `0b6f67777a1ba176fbf8478db3c11c12a4a1024bdb001d6932840d114805bb4c`
- Historical unverified serialization hash: `34efc196e348d58fedf13d7491d20c069345606cd06393b5338a9dc12359edd7`

## Release rule

The repository should not be made public merely because the central metric is impressive. Public release occurs when another researcher can identify the exact inputs, run one documented command, reproduce the principal tables, verify the declared scientific fingerprint, and understand where the claim stops.
