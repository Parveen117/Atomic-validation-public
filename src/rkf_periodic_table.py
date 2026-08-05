from __future__ import annotations

"""Exact Recognition-shell periodic-table skeleton.

This module derives the 118-position periodic-table skeleton from:

1. the one-electron state labels (n, l, m, spin);
2. Pauli occupancy, giving 2(2l+1) states per subshell;
3. the declared Madelung ordering by (n+l, n);
4. electron-number closure for neutral atoms.

It does not claim to derive the many-electron energy ordering, correlated
ground-state exceptions, chemical properties, or the disputed group-3 boundary
from the nuclear model.
"""

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping

ELEMENT_SYMBOLS = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt",
    "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn",
    "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf",
    "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
    "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
)

ORBITAL_LABELS = {
    0: "s",
    1: "p",
    2: "d",
    3: "f",
    4: "g",
    5: "h",
    6: "i",
}

EXPECTED_PERIOD_LENGTHS = (2, 8, 8, 18, 18, 32, 32)
EXPECTED_PERIOD_CLOSURES = (2, 10, 18, 36, 54, 86, 118)
EXPECTED_BLOCK_COUNTS = {"s": 14, "p": 36, "d": 40, "f": 28}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def certificate_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def subshell_capacity(l: int) -> int:
    """Return the Pauli capacity 2(2l+1)."""
    if l < 0:
        raise ValueError("l must be nonnegative")
    return 2 * (2 * l + 1)


def shell_capacity(n: int) -> int:
    """Return the total hydrogenic shell capacity 2n^2."""
    if n < 1:
        raise ValueError("n must be positive")
    return sum(subshell_capacity(l) for l in range(n))


def electron_hole_cut(occupancy: int, capacity: int) -> int:
    """Subshell particle-hole involution q -> capacity-q."""
    if capacity < 0 or occupancy < 0 or occupancy > capacity:
        raise ValueError("occupancy must lie in [0, capacity]")
    return capacity - occupancy


def cut_coordinates(occupancy: int, capacity: int) -> dict[str, str]:
    """Return exact even/odd coordinates under the electron-hole cut."""
    hole = electron_hole_cut(occupancy, capacity)
    even = Fraction(occupancy + hole, 2)
    odd = Fraction(occupancy - hole, 2)
    return {
        "occupancy": str(occupancy),
        "hole_occupancy": str(hole),
        "cut_even": str(even),
        "cut_odd": str(odd),
    }


def subshell_name(n: int, l: int) -> str:
    try:
        label = ORBITAL_LABELS[l]
    except KeyError as exc:
        raise ValueError(f"unsupported orbital l={l}") from exc
    return f"{n}{label}"


def madelung_subshells(
    *,
    max_n: int = 7,
    max_l: int = 3,
) -> tuple[tuple[int, int], ...]:
    """Return subshells ordered by increasing (n+l, n)."""
    if max_n < 1 or max_l < 0:
        raise ValueError("invalid shell limits")
    shells = [
        (n, l)
        for n in range(1, max_n + 1)
        for l in range(min(n - 1, max_l) + 1)
    ]
    return tuple(sorted(shells, key=lambda item: (item[0] + item[1], item[0])))


def _group_for(
    configuration: Mapping[tuple[int, int], int],
    *,
    atomic_number: int,
    period: int,
    last_l: int,
    last_occupancy: int,
) -> int | None:
    if last_l == 0:
        return 18 if atomic_number == 2 else last_occupancy
    if last_l == 1:
        return 12 + last_occupancy
    if last_l == 2:
        return (
            int(configuration.get((period - 1, 2), 0))
            + int(configuration.get((period, 0), 0))
        )
    return None


def derive_periodic_table(max_atomic_number: int = 118) -> list[dict[str, Any]]:
    if max_atomic_number < 1 or max_atomic_number > len(ELEMENT_SYMBOLS):
        raise ValueError("max_atomic_number must lie in [1, 118]")

    order = madelung_subshells()
    configuration: dict[tuple[int, int], int] = {}
    elements: list[dict[str, Any]] = []
    atomic_number = 0
    period = 0

    for n, l in order:
        if l == 0:
            period = n
        capacity = subshell_capacity(l)
        for occupancy in range(1, capacity + 1):
            atomic_number += 1
            if atomic_number > max_atomic_number:
                return elements
            configuration[(n, l)] = occupancy
            block = ORBITAL_LABELS[l]
            group = _group_for(
                configuration,
                atomic_number=atomic_number,
                period=period,
                last_l=l,
                last_occupancy=occupancy,
            )
            series = None
            if block == "f":
                if period == 6:
                    series = "madelung_lanthanide_filling"
                elif period == 7:
                    series = "madelung_actinide_filling"
                else:
                    series = "inner_transition_filling"

            occupied = [
                f"{subshell_name(nn, ll)}{configuration[(nn, ll)]}"
                for nn, ll in order
                if configuration.get((nn, ll), 0) > 0
            ]
            cut = cut_coordinates(occupancy, capacity)
            element = {
                "atomic_number": atomic_number,
                "symbol": ELEMENT_SYMBOLS[atomic_number - 1],
                "period": period,
                "group": group,
                "madelung_block": block,
                "series": series,
                "last_subshell": subshell_name(n, l),
                "last_subshell_occupancy": occupancy,
                "last_subshell_capacity": capacity,
                "electron_hole_cut": cut,
                "electron_count": sum(configuration.values()),
                "neutrality_residue": sum(configuration.values()) - atomic_number,
                "madelung_configuration": " ".join(occupied),
                "ground_state_exception_ledger": "NOT_APPLIED",
            }
            elements.append(element)

    if len(elements) < max_atomic_number:
        raise RuntimeError("declared subshell order did not reach requested atomic number")
    return elements


def period_summary(elements: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(elements)
    lengths = Counter(int(row["period"]) for row in rows)
    block_counts = Counter(str(row["madelung_block"]) for row in rows)
    closures = [
        int(row["atomic_number"])
        for row in rows
        if row.get("group") == 18
    ]
    return {
        "period_lengths": [lengths[index] for index in range(1, 8)],
        "period_closure_atomic_numbers": closures,
        "block_counts": dict(sorted(block_counts.items())),
    }


def build_certificate() -> dict[str, Any]:
    elements = derive_periodic_table(118)
    summary = period_summary(elements)
    state_counting = {
        "subshell_capacities": {
            ORBITAL_LABELS[l]: subshell_capacity(l)
            for l in range(4)
        },
        "shell_capacities_n_1_to_7": {
            str(n): shell_capacity(n)
            for n in range(1, 8)
        },
        "shell_capacity_identity": "sum_{l=0}^{n-1} 2(2l+1) = 2n^2",
    }
    used_order: list[str] = []
    seen: set[str] = set()
    for row in elements:
        name = str(row["last_subshell"])
        if name not in seen:
            seen.add(name)
            used_order.append(name)

    checks = {
        "element_count_is_118": len(elements) == 118,
        "neutrality_closes_for_every_element": all(
            int(row["neutrality_residue"]) == 0 for row in elements
        ),
        "electron_count_matches_atomic_number": all(
            int(row["electron_count"]) == int(row["atomic_number"])
            for row in elements
        ),
        "electron_hole_cut_is_involutive": all(
            electron_hole_cut(
                electron_hole_cut(
                    int(row["last_subshell_occupancy"]),
                    int(row["last_subshell_capacity"]),
                ),
                int(row["last_subshell_capacity"]),
            )
            == int(row["last_subshell_occupancy"])
            for row in elements
        ),
        "period_lengths_match_2_8_8_18_18_32_32": (
            tuple(summary["period_lengths"]) == EXPECTED_PERIOD_LENGTHS
        ),
        "period_closures_match_noble_gas_boundaries": (
            tuple(summary["period_closure_atomic_numbers"])
            == EXPECTED_PERIOD_CLOSURES
        ),
        "block_counts_sum_to_118": summary["block_counts"] == EXPECTED_BLOCK_COUNTS,
        "hydrogen_to_oganesson_symbol_spine": (
            elements[0]["symbol"] == "H"
            and elements[-1]["symbol"] == "Og"
        ),
        "group_14_homologous_sequence": [
            row["symbol"] for row in elements if row["group"] == 14
        ] == ["C", "Si", "Ge", "Sn", "Pb", "Fl"],
    }

    certificate = {
        "schema": "rkf.periodic_table_skeleton.v1",
        "status": (
            "PASS_RKF_PERIODIC_TABLE_SKELETON_V1"
            if all(checks.values())
            else "INCONCLUSIVE_RKF_PERIODIC_TABLE_SKELETON_V1"
        ),
        "recognition_grammar": {
            "bindu": "NUCLEAR_ATOMIC_NUMBER_Z",
            "rekha": "SUCCESSIVE_NEUTRAL_ELECTRON_ADDITION",
            "chandas": "ORDERED_SUBSHELL_CAPACITY_RHYTHM",
            "seam": "SUBSHELL_OR_PERIOD_CLOSURE",
            "smriti": "GROUND_STATE_PROMOTION_RELATIVISTIC_CORRELATION_LEDGER",
            "rta": "TOTAL_OCCUPANCY_EQUALS_Z_AND_NO_SUBSHELL_EXCEEDS_CAPACITY",
            "cut": "SUBSHELL_ELECTRON_HOLE_INVOLUTION_Q_TO_CAPACITY_MINUS_Q",
        },
        "assumptions": {
            "one_electron_labels": "(n,l,m,spin)",
            "pauli_occupancy": "AT_MOST_ONE_ELECTRON_PER_COMPLETE_STATE_LABEL",
            "declared_energy_order": "INCREASING_(n+l,n)_MADELUNG_ORDER",
            "neutral_atom": "ELECTRON_COUNT_EQUALS_ATOMIC_NUMBER",
        },
        "state_counting": state_counting,
        "used_madelung_order": used_order,
        "derived_summary": summary,
        "checks": checks,
        "claim_boundary": {
            "subshell_capacities_derived": True,
            "shell_capacity_2n_squared_derived": True,
            "period_lengths_and_118_positions_derived_given_order": True,
            "block_and_group_skeleton_derived_given_order": True,
            "madelung_order_derived_from_many_electron_hamiltonian": False,
            "correlated_ground_state_exception_ledger_completed": False,
            "chemical_properties_derived": False,
            "group_3_boundary_resolved": False,
            "nuclear_model_alone_sufficient": False,
        },
        "elements": elements,
    }
    return certificate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("releases/rkf-periodic-table-v1/periodic_table_skeleton.json"),
    )
    args = parser.parse_args()
    certificate = build_certificate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(certificate))
    print(json.dumps({
        "status": certificate["status"],
        "sha256": certificate_sha256(certificate),
        "period_lengths": certificate["derived_summary"]["period_lengths"],
        "period_closures": certificate["derived_summary"]["period_closure_atomic_numbers"],
        "block_counts": certificate["derived_summary"]["block_counts"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
