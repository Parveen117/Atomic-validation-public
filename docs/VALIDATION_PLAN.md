# Validation Plan

## Objective

Convert the current V4 internal result into a publication-grade, auditable validation package without importing unrelated exploratory material from the development repository.

## Stage 1: Freeze the computational object

1. Identify the exact source commit in the development repository that produced the reported V4 metrics.
2. Copy only the required source modules, tests and configuration.
3. Record the source commit SHA in the release manifest.
4. Prohibit silent algorithm changes after the freeze. Any later change requires a new version and a fresh result package.

## Stage 2: Freeze and document the data

The dataset manifest must record:

- original data sources and release identifiers;
- acquisition date;
- source file hashes;
- parsing and transformation steps;
- units;
- required columns;
- row counts before and after processing;
- rejection rules;
- duplicate handling;
- missing-value handling;
- licensing and redistribution constraints.

Where source-data licensing prevents redistribution, the repository must provide a deterministic acquisition and preprocessing route rather than silently committing restricted data.

## Stage 3: Leakage and calibration audit

The audit must verify that:

- a target value is never used to construct its own prediction;
- held-out element chains are excluded from chain-specific risk calibration where claimed;
- calibration statistics do not include the target record;
- thresholds described as prospective are not selected using the final test residuals without disclosure;
- all retrospective diagnostic policies are clearly labelled as retrospective;
- model selection and final evaluation are not reported as if they were independent when they are not.

## Stage 4: Baselines

The final paper should compare V4 against:

1. neutron-direction reconstruction alone;
2. proton-direction reconstruction alone;
3. unweighted two-axis averaging;
4. nearest-neighbour interpolation;
5. a simple polynomial or spline surface;
6. the semi-empirical mass formula;
7. at least one recognised nuclear mass model where inputs and outputs can be compared fairly.

Every baseline must use the same evaluation rows, units and missing-value rules.

## Stage 5: Error stratification

Report coverage and error by:

- mass-number region;
- proton-number region;
- neutron-number region;
- even-even, even-odd, odd-even and odd-odd nuclei;
- stable versus radioactive nuclei;
- distance from selected shell closures;
- predictor type;
- one-axis versus two-axis availability;
- directional-disagreement quantile;
- abstention reason.

Both keV/A and total binding-energy residuals must be reported.

## Stage 6: External validation

Preferred design:

1. freeze the complete method using an older AME/NUBASE release;
2. identify nuclei added or materially revised in a later release;
3. predict them without recalibration;
4. report coverage, residuals and abstentions exactly as produced by the frozen method.

If this is not yet possible, the paper must call the current work internal or cross-validated evaluation rather than external validation.

## Stage 7: Reproducibility test

A clean environment must be able to execute one documented command that:

1. verifies input hashes;
2. generates predictions and abstentions;
3. computes all principal metrics;
4. regenerates paper tables and figures;
5. verifies expected output hashes;
6. runs the complete test suite.

## Stage 8: Publication decision

### Preprint-ready

The package is preprint-ready when Stages 1–5 and 7 pass, limitations are explicit, and all principal artefacts are frozen.

### Journal-ready

The package becomes a strong journal candidate when the baseline comparison is complete and Stage 6 provides a genuinely independent temporal or external test.
