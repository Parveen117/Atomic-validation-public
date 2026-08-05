# Recognition Shell–Seam Periodic Table V1

## Status

This module derives the **118-position periodic-table skeleton** from an explicit
electronic state-counting grammar. It does not claim that the nuclear mass model
alone determines electronic structure.

The derivation is:

```text
atomic number Z
+ one-electron labels (n,l,m,spin)
+ Pauli occupancy
+ declared Madelung order (n+l,n)
+ neutral-electron closure
=
subshell capacities, blocks, periods, groups and 118 positions.
```

The current IUPAC table contains 118 named elements, while the NIST Atomic
Spectra Database provides critically evaluated ground-state configurations and
warns that complex heavy-atom configurations can involve approximation and
coupling ambiguity. V1 therefore separates the exact counting theorem from the
still-open many-electron energy-order problem.

## Recognition grammar

For a neutral atom of atomic number \(Z\):

```text
Bindu      nuclear atomic number Z
Rekha      successive electron-addition path
Chandas    ordered subshell-capacity rhythm
Seam       subshell closure or period closure
Smriti     promotion/correlation/relativistic exception ledger
Rta        total occupancy = Z and every occupancy <= its capacity
Cut        electron-hole involution q -> c-q inside one subshell
```

For subshell occupancy \(q\) and capacity \(c\),

\[
J_c(q)=c-q,
\qquad
J_c^2(q)=q.
\]

The cut-even and cut-odd coordinates are

\[
q_+=\frac{q+J_c(q)}2=\frac c2,
\qquad
q_-=\frac{q-J_c(q)}2=q-\frac c2.
\]

Thus a closed subshell has zero hole occupancy, while a half-filled subshell is
fixed by the electron-hole cut.

## Theorem 1: subshell capacity

For fixed \(n\) and orbital quantum number \(\ell\), the magnetic quantum number
has

\[
2\ell+1
\]

values, and each spatial state has two spin states. Pauli occupancy therefore
gives

\[
\boxed{c_\ell=2(2\ell+1).}
\]

Hence

\[
s:2,\qquad p:6,\qquad d:10,\qquad f:14.
\]

## Theorem 2: shell capacity

For principal shell \(n\), the admitted orbital values are
\(\ell=0,\ldots,n-1\). Therefore

\[
\begin{aligned}
C_n
&=\sum_{\ell=0}^{n-1}2(2\ell+1)\\
&=2n^2.
\end{aligned}
\]

The first seven shell capacities are

\[
2,\ 8,\ 18,\ 32,\ 50,\ 72,\ 98.
\]

These are shell capacities, not period lengths. Confusing the two is how a
perfectly respectable atom gets forced into an ugly spreadsheet.

## Theorem 3: conditional period theorem

Declare the subshell energy-order adapter

\[
(n,\ell)\prec(n',\ell')
\]

when

\[
(n+\ell,n)<_{\mathrm{lex}}(n'+\ell',n').
\]

This is the Madelung ordering. Up to the current 118-element table, it gives

\[
\begin{aligned}
&1s;\\
&2s,2p;\\
&3s,3p;\\
&4s,3d,4p;\\
&5s,4d,5p;\\
&6s,4f,5d,6p;\\
&7s,5f,6d,7p.
\end{aligned}
\]

Summing the capacities inside each period yields

\[
\boxed{2,\ 8,\ 8,\ 18,\ 18,\ 32,\ 32.}
\]

The cumulative closures are

\[
\boxed{2,\ 10,\ 18,\ 36,\ 54,\ 86,\ 118.}
\]

These are exactly the noble-gas period boundaries in the generated skeleton.

## Theorem 4: block and group skeleton

The last filled subshell determines the Madelung block:

\[
\ell=0,1,2,3
\quad\longleftrightarrow\quad
s,p,d,f.
\]

The 118 positions split as

\[
\boxed{
14\ s\text{-positions}
+36\ p\text{-positions}
+40\ d\text{-positions}
+28\ f\text{-positions}
=118.
}
\]

For the generated group skeleton:

- \(ns^1,ns^2\) give groups 1 and 2, with helium assigned to group 18;
- \(np^q\), \(1\le q\le6\), gives group \(12+q\);
- transition positions use \(q_d+q_s\), giving groups 3 through 12;
- \(f\)-filling positions are reported as inner-transition series rather than
  forcing a disputed group-3 convention.

The generated group-14 homologous sequence is

\[
\mathrm{C,Si,Ge,Sn,Pb,Fl}.
\]

## Exact certificate

The deterministic certificate checks:

```text
118 generated positions;
electron count equals Z for every position;
zero neutrality residue;
electron-hole cut involution;
period lengths 2,8,8,18,18,32,32;
closures 2,10,18,36,54,86,118;
block counts s14,p36,d40,f28;
hydrogen-to-oganesson symbol spine;
group-14 homologous sequence.
```

Expected status:

```text
PASS_RKF_PERIODIC_TABLE_SKELETON_V1
```

Expected SHA-256:

```text
346dca4c97ecfab8f2b6008ec1b00bd09f0459cae8082402add3d7d275ba476e
```

## Claim boundary

```text
SUBSHELL CAPACITY 2(2l+1)                    DERIVED
SHELL CAPACITY 2n^2                          DERIVED
PERIOD LENGTHS GIVEN MADELUNG ORDER           DERIVED
118 POSITION / BLOCK / GROUP SKELETON         DERIVED
ELECTRON-HOLE RECOGNITION CUT                 DERIVED

MADELUNG ORDER FROM MANY-ELECTRON HAMILTONIAN NOT YET DERIVED
GROUND-STATE PROMOTION EXCEPTION LEDGER       NOT YET FROZEN
RELATIVISTIC / CORRELATION CORRECTIONS        NOT YET DERIVED
GROUP-3 BOUNDARY                              NOT CLAIMED RESOLVED
CHEMICAL REACTIVITY AND BONDING TRENDS        NOT YET DERIVED
NUCLEAR MODEL ALONE                           INSUFFICIENT
```

## Next development

V2 must consume NIST ground-state configurations and build the lawful Smriti
promotion ledger relative to the V1 Madelung skeleton. It must then test whether
the promotion residue is explained by a cross-fitted energy functional using
subshell occupancy, exchange, screening, spin-orbit and relativistic coordinates.
