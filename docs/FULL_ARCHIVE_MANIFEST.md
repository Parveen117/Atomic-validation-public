# Full Validation Archive Manifest

This manifest defines the intended publication repository structure.

```text
Atomic-validation-public/
├── README.md
├── PUBLICATION_STATUS.md
├── CITATION.cff
├── LICENSE
├── environment/
│   ├── requirements.txt
│   ├── python-version.txt
│   └── environment-lock.txt
├── data/
│   ├── README.md
│   ├── provenance/
│   ├── raw-manifests/
│   └── processed/
├── src/
│   └── universal_atomic/
├── tests/
│   ├── v1/
│   ├── v2/
│   ├── v3/
│   ├── v3_1/
│   ├── v3_2/
│   ├── v3_3/
│   └── v4/
├── validation/
│   ├── configs/
│   ├── scripts/
│   ├── baselines/
│   └── leakage_audits/
├── results/
│   ├── v1/
│   ├── v2/
│   ├── v3/
│   ├── v3_1/
│   ├── v3_2/
│   ├── v3_3/
│   └── v4/
├── releases/
│   └── uam_v4_publication/
├── docs/
│   ├── CLAIM_SCOPE.md
│   ├── VALIDATION_PLAN.md
│   ├── TRANSPARENCY_POLICY.md
│   ├── FULL_ARCHIVE_MANIFEST.md
│   ├── TRIALS_AND_RUNS_LEDGER.md
│   ├── LIMITATIONS.md
│   └── DATA_DICTIONARY.md
└── .github/workflows/
    └── validation.yml
```

## Required provenance records

Every reported stage must identify:

- source repository;
- source commit SHA;
- input dataset manifest and hash;
- processing script and configuration;
- execution command;
- output report hash;
- tests associated with the stage;
- known limitations or leakage risks.

## Frozen V4 release

The `releases/uam_v4_publication/` directory will contain the immutable principal publication artefacts. The surrounding repository will retain the complete V1–V4 validation history so the final result can be audited rather than admired from a safe distance.
