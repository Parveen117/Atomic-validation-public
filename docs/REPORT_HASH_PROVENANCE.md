# Report Hash Provenance

## Resolution of issue #2

The frozen UAM-V4 headline result reproduces exactly, but the regenerated complete-report hash does not equal the historical hash recorded before the original JSON artifact was preserved.

These are different questions:

- an **artifact hash** identifies one exact serialized file byte for byte;
- the **scientific fingerprint** identifies the declared frozen counts and headline guarded metrics under a versioned canonical schema.

The unavailable historical JSON cannot be reconstructed or compared field by field. The legacy value therefore remains historical metadata rather than an enforceable byte-identity target.

## Versioned scientific fingerprint

Schema:

```text
UAM_V4_SCIENTIFIC_FINGERPRINT_V1
```

Frozen fingerprint:

```text
fcf83345a4f18ca82fd5282c1dae6d183f1015e68dceb4719cd6fbbecdcfc25b
```

The fingerprint contains only:

- valid and rejected row counts;
- guarded prediction and abstention counts;
- coverage;
- mean, median, p95, p99 and maximum absolute residual;
- mean signed residual;
- root mean square residual.

It deliberately excludes timestamps, source-path labels, record ordering, execution metadata and the full report hash. Those remain part of artifact provenance.

## Reproduction policy

A frozen release is scientifically reproduced when all declared metric checks pass and the versioned scientific fingerprint matches. Exact artifact identity is established separately by the generated report file SHA-256 and embedded report hash.

This separation prevents non-scientific serialization changes from being mistaken for changes in the reported result while preserving byte-level provenance for every newly generated artifact.
