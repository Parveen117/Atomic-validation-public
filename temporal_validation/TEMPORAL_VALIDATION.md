# Temporally separated validation of the frozen UAM-V4 predictor

Monty Dabas. 7 October 2026. Python 3.12, standard library only.
Discharges the item of `PUBLICATION_STATUS.md`: "recognised external
mass-model comparison and temporally separated validation remain
recommended".

## What the repository already establishes (unchanged by this record)

```text
headline V4, 3,558 entries           median 0.99 keV per nucleon, coverage 98.76 %          releases/uam-v4/metrics.json
V4 against FRDM2012, 3,448 common    median 0.95 against 2.60 keV per nucleon;
                                     V4 closer on 2,418 nuclei, FRDM2012 on 1,028          releases/uam-v4/external_comparison
V4 against SEMF (out of fold)        median 0.99 against 149.9 keV per nucleon              releases/uam-v4/baseline_comparison
Recognition Repair V5.1              rms 29.3 against 54.8 keV per nucleon at equal coverage releases/rkf-nuclear-v5
```

These are reconstruction results: a nucleus is rebuilt from measured
neighbours on both sides. The present record asks a different question —
prediction of nuclei beyond the edge of the older chart — and adds the
one comparator the repository did not yet have, a local mass relation.

## Design (fixed before the numbers were looked at)

```text
input      an older mass evaluation: AME2012, AME2016
truth      AME2020 measured entries (the repository's frozen processed dataset)
targets    nuclei, A ≥ 16, estimated ('#') or absent in the older table and measured in AME2020
method     src/uam_v4_reproducer.build_report, imported unchanged; every target blanked in the input
policies   neighbours = measured entries only ; neighbours = measured + the older table's own estimates
baselines  the older evaluation's own estimate ; Garvey–Kelson local relations from measured masses
```

A test confirms that changing the blanked target values does not change
any prediction.

## Results

Absolute error of the total binding energy, keV (median / root mean square).

```text
                                              AME2016 → 2020 (73 targets)      AME2012 → 2020 (126 targets)
                                              n     median    rms              n     median    rms
Garvey–Kelson, measured masses only           38    143       392              70    126       394
older evaluation's own estimate               71    134       276              116   178       465
UAM-V4, measured neighbours only              53    806       2142             93    718       2166
UAM-V4, with the older table's estimates      67    500       885              112   431       1449

same nuclei for all three                     32                               59
  Garvey–Kelson                                     116       409                    126       404
  older evaluation's own estimate                   111       230                    168       376
  UAM-V4, measured neighbours only                  918       2561                   802       2157
```

Against the global model already in the repository, on the temporal targets both predict:

```text
                     AME2016 → 2020 (51 nuclei)       AME2012 → 2020 (89 nuclei)
UAM-V4 (strict)      median 830 keV   rms 2180        median 718 keV   rms 1939
FRDM2012             median 447 keV   rms 848         median 392 keV   rms 998
V4 closer on         14 of 51                         32 of 89
```

In-sample on AME2020, measured targets, A ≥ 16, the same 2,417 nuclei for both methods:

```text
UAM-V4 (all entries as neighbours)     median 89 keV     rms 568 keV
Garvey–Kelson, leave one out           median 52 keV     rms 170 keV
V4 closer than Garvey–Kelson on 833 of 2,417 nuclei
```

Two facts about the dataset that bear on the headline numbers:

- 1,008 of the 3,558 entries are evaluation estimates, not measurements
  (`binding_energy_per_A_estimated = True`). They are smooth by
  construction, and they enter the headline run both as targets (996 of
  the retained predictions) and as neighbours.
- With measured neighbours only, the in-sample median on measured
  targets is 176 keV (1.38 keV per nucleon) instead of 93 keV.

## Reading

- On newly measured nuclei the frozen V4 method is about six to eight
  times less accurate than either baseline. Of its 53 strict
  predictions for 2016 → 2020, 51 are one-sided: the new nuclei lie at
  the edge of the known chart, where a two-sided interpolation of
  binding energy per nucleon has support on one side only.
- The disagreement guard abstained on none of the temporal targets.
- The Garvey–Kelson relations are mixed differences in (N, Z). They are
  the cancellation that the V5 document calls the mixed seam; the
  single-axis jets of V4 do not contain it.
- Garvey–Kelson from measured masses alone is level with the
  evaluators' own estimates on these targets, and ahead of them in the
  median for 2012 → 2020.

## The later predictors in the same design

`temporal_validation_v5_v6.py` runs V5, Recognition Repair V5.1 and
Madhava–Smriti V6 unchanged from `src/`. Decoders are fitted on the older
table with the target's element chain held out; the target's observer
record is built from the older table's neighbours (tests confirm the
placeholder value is never read, and that the local build equals the
full one).

Measured neighbours only; total binding energy, keV (median / rms), same nuclei in each column:

```text
                                   AME2016 → 2020 (32)        AME2012 → 2020 (59)
frozen V4                          918  /  2561               802  /  2157
Recognition Repair V5.1            850  /  1554               710  /  1295
V6, order selected                 850  /  1554               710  /  1319
raw V5 decoder, level 3            2248 /  3903               2871 /  3567
Garvey–Kelson                      116  /  409                126  /  404
older evaluation's own estimate    111  /  230                168  /  376
```

- **The repair transfers.** V5.1 lowers the root-mean-square error of V4
  by about 40 % on nuclei it has never seen, in both periods, at equal
  coverage. The in-sample claim of `releases/rkf-nuclear-v5` holds out
  of sample in this respect.
- The medians barely move, and all V-series predictors remain about six
  times behind the local mass relation on these targets.
- The tensor-cubic seam needs sixteen surrounding nuclei; it was
  available for one or two targets only. At the edge of the chart the
  mixed-seam layer of V5 is therefore not exercised.

## The disagreement guard on mixed-difference estimates

`seam_guard.py` applies the repository's own prospective idea — abstain
where independent reconstructions disagree — to the up-to-twelve
Garvey–Kelson estimates of each nucleus. The spread is known before the
target value is used.

```text
in-sample, AME2020 measured, A ≥ 16, at least three estimates (2,273 nuclei)
coverage      spread at most     median error     rms error
100 %         —                  50.5 keV         160.6 keV
90 %          458 keV            44.8 keV          94.6 keV
75 %          222 keV            40.2 keV          77.3 keV
50 %          140 keV            33.6 keV          66.3 keV
highest-spread tenth                224.6 keV         420.5 keV

temporal                    lower-spread half        higher-spread half
AME2016 → 2020 (21)         114 / 201 keV            204 / 438 keV
AME2012 → 2020 (45)         119 / 327 keV            205 / 392 keV
```

Abstaining on the highest-spread tenth removes 41 % of the
root-mean-square error; the ordering holds on newly measured nuclei.
The guard is the part of the V-series design that carries over to the
stronger local relation.

## Not tested here

Global models other than FRDM2012 were not compared. A predictor that
combines the mixed-difference relation with the guard and the repair has
not been built. Target nuclei
are few (73 and 126), so the medians carry sizeable sampling spread.

## Data provenance

```text
data/ame2016_mass16.csv    sha256 17eb49f5…3406d9   community mirror (astroDimitrios/astroedu) of the AMDC table
data/ame2012_mass.mas12    sha256 f296b8e0…cf16c8d3  community mirror (csullivan/origami) of the AMDC table
```

Authenticity rests on the mirrors; iron-56 agrees across the three
tables to 0.01 keV per nucleon (tested).

## Reproduce

```text
python temporal_validation.py
python temporal_validation_v5_v6.py
python seam_guard.py
python -m unittest test_temporal_validation
```
