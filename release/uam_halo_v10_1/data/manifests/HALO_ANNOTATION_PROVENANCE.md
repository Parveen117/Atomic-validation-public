# Halo Annotation Provenance

External halo labels are benchmark metadata only. They do not enter prediction values or matched-control distance scoring.

## Publication rule

No candidate list may be treated as frozen public input until every entry has:

- canonical isotope identifier;
- source citation;
- source publication year;
- observable basis for the halo classification;
- annotation confidence or status;
- licence or quotation boundary where applicable.

## Required observables

The provenance table should distinguish classifications based on matter radius, interaction or reaction cross section, breakup or momentum distribution, spectroscopy, separation energy, or review-level consensus.

## Current status

The private default candidate set has not yet been copied into the public repository. This is intentional. Publication requires citation-level provenance rather than an unexplained list inherited from private code.

The public analysis engine therefore accepts an explicit JSON annotation file in either form:

```json
["He-6", "Li-11"]
```

or:

```json
{"halo_candidates": ["He-6", "Li-11"]}
```

A final frozen annotation file will be added only after the provenance table and rights review are complete.
