# Publication Status

## Current decision

**Stage:** Reproduced release packaging  
**Repository visibility:** Private  
**Scientific status:** Headline V4 result independently reproduced from the frozen processed dataset  
**Legacy serialization status:** Full-report hash mismatch disclosed in Issue #2  
**Journal status:** External baselines and temporally separated validation remain recommended

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

The directory `releases/uam-v4/` contains or must contain:

- [x] `source_provenance.json`
- [x] `metrics.json`
- [x] `dataset_certificate.json`
- [x] `universal_atomic_guarded_two_axis_v4.json`
- [x] `reproduction_certificate.json`
- [x] documented reproduction command
- [x] dataset and archive SHA-256 values
- [ ] compact `predictions.csv`
- [ ] compact `abstentions.csv`
- [ ] release-wide `SHA256SUMS`

## Gate D: Analysis required for the paper

- [ ] Report residuals in both keV/A and total keV or MeV.
- [ ] Report performance by mass region.
- [ ] Report performance near shell closures.
- [ ] Report performance for stable and unstable nuclei.
- [ ] Analyse the remaining extreme retained residuals.
- [ ] Include coverage-error and abstention-error curves.
- [ ] Compare V4 against both individual axes.
- [ ] Compare against simple interpolation baselines.
- [ ] Compare against the semi-empirical mass formula.
- [ ] Add at least one recognised external mass-model comparison where reproducible.

## Gate E: Manuscript

- [ ] Title and abstract.
- [ ] Dataset and provenance section.
- [ ] Method section with leakage controls.
- [ ] Validation design.
- [ ] Results and uncertainty.
- [ ] Failure analysis.
- [ ] Baseline comparison.
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
