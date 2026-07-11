# Reproducibility

## Supported environment

- Python 3.11 or newer
- Standard library only
- No network access is required after cloning the repository

## One-command verification

From the repository root, run:

```bash
python scripts/reproduce_release.py
```

The command performs the complete frozen UAM-V4 verification sequence:

1. extracts `uam_v4_processed_dataset.zip`;
2. verifies the CSV schema and 3,558-row count;
3. calculates the dataset SHA-256 checksum;
4. regenerates the guarded two-axis V4 report;
5. compares the observed report hash with the frozen expected hash;
6. writes `releases/uam-v4/reproduction_certificate.json`.

## Expected frozen result

- Valid rows: 3,558
- Guarded predictions: 3,514
- Abstentions: 44
- Expected report hash: `34efc196e348d58fedf13d7491d20c069345606cd06393b5338a9dc12359edd7`

A successful run must end with a certificate status of `REPRODUCED`. Any row-count, schema, execution, or hash mismatch must terminate with a non-zero exit status.

## Generated files

The following files are generated and should be retained with a frozen release:

- `releases/uam-v4/dataset_certificate.json`
- `build/universal_atomic_guarded_two_axis_v4.json`
- `releases/uam-v4/reproduction_certificate.json`

The generated report may be large. It should not be manually edited. Its report hash, source label, dataset checksum, and execution environment form the reproducibility record.
