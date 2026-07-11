# Publication Status

## Current decision

**Stage:** Publication package assembly  
**Repository visibility:** Private  
**Scientific status:** Preprint candidate after reproducibility and manuscript gates pass  
**Journal status:** Additional external baselines and temporally separated validation recommended

## Gate A: Scientific framing

- [x] State the primary empirical result.
- [x] Separate demonstrated results from broader theoretical interpretation.
- [x] State that the result is internally calibrated and not yet an externally validated universal law.
- [ ] Define the exact frozen dataset release and provenance.
- [ ] Define the final inclusion and exclusion rules.
- [ ] Freeze the V4 algorithm and configuration.

## Gate B: Reproducibility

- [ ] Copy the minimal V4 implementation into `src/`.
- [ ] Copy and consolidate the relevant tests into `tests/`.
- [ ] Add a dependency lock or pinned environment file.
- [ ] Add a deterministic end-to-end reproduction command.
- [ ] Run the complete test suite from a clean environment.
- [ ] Verify all publication output hashes.
- [ ] Add continuous integration for tests and hash verification.

## Gate C: Frozen release artefacts

The directory `release/uam_v4_publication/` must contain:

- [ ] `configuration.json`
- [ ] `dataset_manifest.json`
- [ ] `metrics.json`
- [ ] `predictions.csv`
- [ ] `abstentions.csv`
- [ ] `report_hash.txt`
- [ ] `environment.txt`
- [ ] `reproduction_command.txt`
- [ ] `SHA256SUMS`

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

## Release rule

The repository should not be made public merely because the central metric is impressive. Public release occurs when another researcher can identify the exact inputs, run one documented command, reproduce the principal tables, verify the hashes, and understand where the claim stops.
