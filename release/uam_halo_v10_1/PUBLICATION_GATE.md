# UAM Halo V10.1 Publication Gate

The halo study may move from migration branch to public release only after every required gate below is satisfied.

## 1. Scope and provenance

- [x] Preserve UAM V4 as an unchanged frozen release.
- [x] State that V10.1 is a separate experimental evidence layer.
- [ ] Record the exact private source commits used for migration.
- [ ] Document the origin, version, licence, and transformation of every nuclear-data input.
- [ ] Publish a machine-readable input manifest with hashes.
- [ ] Publish the external halo-annotation list with citations and provenance.

## 2. Leakage and methodology

- [ ] Verify that target binding energy is never used to construct its own prediction.
- [ ] Verify that halo labels never affect prediction values.
- [ ] Verify that halo labels never improve control-distance scoring.
- [ ] Report results separately by predictor class.
- [ ] Report support counts and missing-support cases explicitly.
- [ ] Freeze the drip-line threshold sweep in configuration.
- [ ] Freeze the matched-control selection rule in configuration.

## 3. Executable migration

- [ ] Replace or publicly migrate all private-only imports.
- [ ] Remove private paths, credentials, unpublished notes, and internal-only metadata.
- [ ] Add a standalone public command-line entry point.
- [ ] Add deterministic hashing for the final report and principal outputs.
- [ ] Add dependency and environment files.

## 4. Validation

- [ ] Test symmetric cubic prediction.
- [ ] Test symmetric linear fallback.
- [ ] Test one-sided left and right fallbacks.
- [ ] Test insufficient-support abstention.
- [ ] Test halo-label leakage invariance.
- [ ] Test threshold-sensitive classification.
- [ ] Test matched-control exclusion of labelled halo nuclei.
- [ ] Test deterministic report generation.
- [ ] Run the complete public test suite in clean CI.

## 5. Results and interpretation

- [ ] Generate the frozen V10.1 report from public inputs.
- [ ] Publish aggregate metrics by predictor class.
- [ ] Publish per-halo matched-control records.
- [ ] Publish threshold-sensitivity tables.
- [ ] Publish figures generated only from frozen outputs.
- [ ] State sample sizes beside every aggregate claim.
- [ ] Distinguish mass-surface anomaly evidence from direct spatial halo evidence.
- [ ] Include null, mixed, or negative findings without selective omission.

## 6. Release integrity

- [ ] Produce a reproduction certificate.
- [ ] Hash all principal artefacts.
- [ ] Confirm that one documented command regenerates outputs.
- [ ] Confirm the archive from a clean checkout.
- [ ] Complete third-party data and licence review.
- [ ] Complete patent/public-disclosure review before tagging the release.

## Release decision

Until all required gates are complete, the directory must remain labelled as a migration or experimental pre-release package, not a final halo-detection claim.
