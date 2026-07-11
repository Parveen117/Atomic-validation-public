# External nuclear-mass model tables

This directory is reserved for verified external-model predictions.

Do not place AME target values here as model predictions.

Every imported table must record:

- model name and version;
- authoritative source;
- download date;
- original checksum;
- licence or redistribution terms;
- original units;
- conversion method;
- matching keys;
- whether the model was fitted using the evaluated AME release.

External tables should use these normalised columns:

`model_name,Z,N,A,predicted_binding_energy_per_A_keV`

Raw source files should not be committed unless redistribution is permitted.
