# Reproducibility

## Supported environment

- Python 3.11 or newer
- Standard library only
- No network access is required after cloning the repository

## One-command scientific verification

From the repository root, run:

```bash
python scripts/reproduce_release.py
python scripts/build_scientific_fingerprint.py
```

The commands perform the frozen UAM-V4 verification sequence:

1. extract `uam_v4_processed_dataset.zip`;
2. verify the CSV schema and 3,558-row count;
3. calculate the dataset SHA-256 checksum;
4. regenerate the guarded two-axis V4 report;
5. compare every declared frozen count and headline metric;
6. write `releases/uam-v4/reproduction_certificate.json`;
7. build the versioned scientific fingerprint certificate.

## Expected frozen result

- Valid rows: 3,558
- Guarded predictions: 3,514
- Abstentions: 44
- Scientific fingerprint schema: `UAM_V4_SCIENTIFIC_FINGERPRINT_V1`
- Scientific fingerprint SHA-256: `fcf83345a4f18ca82fd5282c1dae6d183f1015e68dceb4719cd6fbbecdcfc25b`

A successful run must reproduce all declared scientific values. Missing fields, non-finite values, count mismatches or metric mismatches terminate verification with a non-zero exit status.

## Artifact identity versus scientific identity

The historical complete-report hash

```text
34efc196e348d58fedf13d7491d20c069345606cd06393b5338a9dc12359edd7
```

is retained as historical metadata. The original JSON artifact producing that hash was not committed, so exact field-level recovery is impossible. The current reproducer preserves the regenerated report hash and file SHA-256 as byte-level artifact identifiers.

The scientific fingerprint is separate. It is computed only from the versioned frozen counts and headline metrics, so changes to timestamps, source labels, record ordering or unrelated metadata do not falsely appear as scientific disagreement. See [`docs/REPORT_HASH_PROVENANCE.md`](docs/REPORT_HASH_PROVENANCE.md).

## Generated files

The following files should be retained with the frozen release:

- `releases/uam-v4/dataset_certificate.json`
- `releases/uam-v4/universal_atomic_guarded_two_axis_v4.json`
- `releases/uam-v4/reproduction_certificate.json`
- `releases/uam-v4/scientific_fingerprint.json`

The generated report may be large and must not be manually edited. Dataset hashes, artifact hashes, the embedded report hash and the scientific fingerprint serve distinct provenance roles.
