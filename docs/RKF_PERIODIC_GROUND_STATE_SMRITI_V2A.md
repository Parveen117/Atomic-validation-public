# Recognition Periodic Table V2A: NIST Ground-State Smriti Ledger

## Status

V1 derived the 118-position shell/block/group skeleton from one-electron state
counting, Pauli occupancy, neutral closure, and a declared Madelung ordering.

V2A freezes the next physical layer against the NIST neutral ground-configuration
table for hydrogen through uranium. It does not overwrite V1. It records the
difference between the Madelung occupancy vector and the NIST reference occupancy
vector as a typed, charge-conserving Smriti promotion.

The repository freezes all 92 normalized neutral source rows, preserves their
noble-gas-core notation, expands every core recursively, validates the symbol
sequence and electron count, and derives the Smriti vectors from those rows. The
75 zero residues are therefore checked source matches rather than an untested
complement of the 17 familiar exceptions.

The NIST source states that its neutral ground configurations are taken from a
NIST Atomic Physics Division compilation, that some differ from older
references, and that the displayed table covers H through U.

## Occupancy carriers

For atomic number \(Z\), let

\[
M_Z(a)
\]

be the V1 Madelung occupancy of subshell \(a\), and let

\[
N_Z(a)
\]

be the NIST neutral ground-state occupancy.

Define the ground-state Smriti vector

\[
\boxed{\Sigma_Z(a)=N_Z(a)-M_Z(a).}
\]

Then the exact closure identity is

\[
\boxed{M_Z+\Sigma_Z-N_Z=0.}
\]

Because both configurations represent the same neutral atom,

\[
\boxed{\sum_a \Sigma_Z(a)=0.}
\]

Thus Smriti moves electrons between channels but never creates or destroys
electron number.

## Promotion count

The number of promoted electrons is

\[
\boxed{
p_Z
=
\sum_{\Sigma_Z(a)>0}\Sigma_Z(a)
=
-\sum_{\Sigma_Z(a)<0}\Sigma_Z(a)
=
\frac12\|\Sigma_Z\|_1.
}
\]

For every nonzero NIST residue through uranium, the support contains exactly one
donor and one acceptor subshell.

## Donor-acceptor Recognition cut

Let \(J_{a,b}\) exchange the active donor and acceptor channels. For a promotion

\[
\Sigma_Z=k(e_b-e_a),
\]

channel exchange gives

\[
\boxed{J_{a,b}\Sigma_Z=-\Sigma_Z.}
\]

Therefore every nonzero ground-state Smriti residue in V2A is cut-odd.

## Exact H-through-U ledger

Among the 92 NIST-audited neutral atoms:

```text
75 configurations match the V1 Madelung occupancy exactly
17 configurations carry nonzero Smriti
15 are one-electron promotions
 2 are two-electron promotions
19 electrons are promoted in total
```

The exception sequence is

```text
Cr Cu Nb Mo Ru Rh Pd Ag La Ce Gd Pt Au Ac Th Pa U
```

The two promotion families are

\[
\boxed{ns\longrightarrow(n-1)d}
\]

for 10 atoms, and

\[
\boxed{f\longrightarrow d}
\]

for 7 atoms.

The two double promotions are

\[
\mathrm{Pd}:\quad 5s^2\,4d^8\longrightarrow5s^0\,4d^{10},
\]

and

\[
\mathrm{Th}:\quad 5f^2\,6d^0\longrightarrow5f^0\,6d^2.
\]

## Special inner-subshell closures

Seven promotions land on, or restore, an exact half-filled or full inner
subshell:

```text
Cr  3d5   half-filled
Cu  3d10  full
Mo  4d5   half-filled
Pd  4d10  full
Ag  4d10  full
Gd  4f7   half-filled
Au  5d10  full
```

This is a real structural subset, but it is not a complete explanation of all
17 exceptions. Ten NIST promotions do not terminate at an exact half/full inner
closure. Therefore the usual classroom slogan is not promoted to a universal
energy theorem.

## Fail-closed superheavy boundary

The cited static NIST reference table covers H through U. V2A keeps the complete
118-position V1 skeleton, but assigns

```text
ABSTAIN_SUPERHEAVY_OUTSIDE_NIST_H_U_SOURCE
```

to \(Z=93,\ldots118\).

This is a source boundary, not a claim that those configurations are unknowable.
A separate superheavy source pin is required because evaluated, semi-empirical,
and theoretical assignments must not be merged into one confidence class.

## Exact certificate

The generated certificate verifies:

```text
118 periodic positions retained
92 frozen NIST source rows parsed and expanded
92 source symbols and electron counts validated
26 explicit superheavy abstentions
17 exact nonzero Smriti residues
75 exact source-verified zero-Smriti matches
promotion families F_TO_D=7 and S_TO_D=10
promotion histogram one-electron=15 and two-electron=2
19 total promoted electrons
exact reconstruction M_Z + Sigma_Z = N_Z
electron-number conservation
zero neutrality residue
cut-odd donor-acceptor Smriti
special-closure sequence Cr,Cu,Mo,Pd,Ag,Gd,Au
```

Expected status:

```text
PASS_RKF_PERIODIC_GROUND_STATE_SMRITI_LEDGER_V2A
```

Expected serialized SHA-256:

```text
dcf52808325a520c0d9bea0ddae13fe0682f57df8e2e15d405ab06a8e029a04b
```

## Claim boundary

```text
NIST H-THROUGH-U CONFIGURATION SNAPSHOT               FROZEN
NIST H-THROUGH-U CONFIGURATION DIFFERENCE LEDGER      DERIVED
GROUND-STATE SMRITI RECONSTRUCTION                    PROVED
ELECTRON-NUMBER CONSERVATION                          PROVED
DONOR-ACCEPTOR CUT ODDNESS                            PROVED
TWO PROMOTION-SEAM FAMILIES                           PROVED FOR V2A DATA
HALF/FULL INNER-CLOSURE SUBSET                        IDENTIFIED

SUPERHEAVY Z=93..118 CONFIGURATIONS                    ABSTAIN
CURRENT LIVE ASD QUERY SNAPSHOT                       NOT YET PINNED
MADELUNG ORDER FROM MANY-ELECTRON HAMILTONIAN         NOT YET DERIVED
PROMOTION ENERGY FUNCTIONAL                           NOT YET DERIVED
CHEMICAL REACTIVITY AND BONDING                       NOT YET DERIVED
```

## Next development

V2B should freeze a confidence-typed superheavy configuration source.

V3 should construct a leave-one-period or leave-one-block-out energy functional
for the promotion decision. Candidate coordinates include donor/acceptor
occupancy, half/full closure distance, exchange multiplicity, screening,
spin-orbit scale, relativistic \(Z\)-coordinates, and configuration uncertainty.
The model must predict whether \(\Sigma_Z=0\) or \(\Sigma_Z\ne0\) without reading
the held-out configuration label.
