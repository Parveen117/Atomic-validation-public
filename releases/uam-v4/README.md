# UAM V4 Publication Candidate

This directory defines the frozen publication candidate for the guarded two-axis Universal Atomic Model validation result.

## Frozen result

- Evaluated nuclei: 3,558
- Guarded predictions: 3,514
- Abstentions: 44
- Coverage: 98.7634%
- Mean absolute residual: 10.2147 keV/A
- Median absolute residual: 0.9894 keV/A
- 95th-percentile absolute residual: 36.9846 keV/A
- Root-mean-square residual: 54.7503 keV/A
- Report hash: `34efc196e348d58fedf13d7491d20c069345606cd06393b5338a9dc12359edd7`

## Provenance

The result is anchored to source repository `Parveen117/Atomic-model` at commit:

`5133413a5a88b0a571d7254d547aca9965620c8e`

The V4 implementation source blob is:

`c9ac194d7736c16636e69b089940a0a7de4deb4b`

See `source_provenance.json` for machine-readable identifiers.

## Current status

The values in `metrics.json` are frozen from the source trials ledger. They are not yet marked independently reproduced inside this publication repository.

The release becomes reproducible only after all of the following are present and verified:

1. Exact implementation and dependency files.
2. Exact V4 test suite.
3. Input-data provenance and transformation scripts.
4. Full generated report or a deterministic regeneration path.
5. Environment specification.
6. A clean CI run reproducing the declared report hash.

## Claim boundary

This release supports an internally calibrated guarded two-axis reconstruction result on the stated AME/NUBASE-derived working dataset. It does not, by itself, establish an externally validated universal nuclear law.
