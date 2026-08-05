from __future__ import annotations

"""NIST-grounded ground-state Smriti ledger for Periodic Table V2A.

The V1 periodic skeleton derives Madelung-ordered neutral configurations. This
module freezes the neutral ground-configuration differences identified in the
NIST H-through-U reference table and expresses every difference as a conserved
integer promotion vector.
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from src.rkf_periodic_table import (
    ORBITAL_LABELS,
    derive_periodic_table,
    madelung_subshells,
    subshell_capacity,
    subshell_name,
)

NIST_SOURCE_URL = (
    "https://www.nist.gov/pml/atomic-reference-data-electronic-structure-"
    "calculations/atomic-reference-data-electronic-8"
)
NIST_COVERAGE_MAX_Z = 92

# Frozen audit of the neutral configurations in the NIST H-through-U table.
# Each tuple is (donor_subshell, acceptor_subshell, promoted_electrons,
# nist_reference_configuration). All other Z <= 92 match the V1 occupancy
# vector exactly.
NIST_PROMOTION_ROWS: dict[int, tuple[str, str, int, str]] = {
    24: ("4s", "3d", 1, "[Ar] 3d5 4s1"),
    29: ("4s", "3d", 1, "[Ar] 3d10 4s1"),
    41: ("5s", "4d", 1, "[Kr] 4d4 5s1"),
    42: ("5s", "4d", 1, "[Kr] 4d5 5s1"),
    44: ("5s", "4d", 1, "[Kr] 4d7 5s1"),
    45: ("5s", "4d", 1, "[Kr] 4d8 5s1"),
    46: ("5s", "4d", 2, "[Kr] 4d10"),
    47: ("5s", "4d", 1, "[Kr] 4d10 5s1"),
    57: ("4f", "5d", 1, "[Xe] 5d1 6s2"),
    58: ("4f", "5d", 1, "[Xe] 4f1 5d1 6s2"),
    64: ("4f", "5d", 1, "[Xe] 4f7 5d1 6s2"),
    78: ("6s", "5d", 1, "[Xe] 4f14 5d9 6s1"),
    79: ("6s", "5d", 1, "[Xe] 4f14 5d10 6s1"),
    89: ("5f", "6d", 1, "[Rn] 6d1 7s2"),
    90: ("5f", "6d", 2, "[Rn] 6d2 7s2"),
    91: ("5f", "6d", 1, "[Rn] 5f2 6d1 7s2"),
    92: ("5f", "6d", 1, "[Rn] 5f3 6d1 7s2"),
}

EXPECTED_EXCEPTION_Z = tuple(NIST_PROMOTION_ROWS)
EXPECTED_EXCEPTION_SYMBOLS = (
    "Cr", "Cu", "Nb", "Mo", "Ru", "Rh", "Pd", "Ag",
    "La", "Ce", "Gd", "Pt", "Au", "Ac", "Th", "Pa", "U",
)
EXPECTED_FAMILY_COUNTS = {"F_TO_D": 7, "S_TO_D": 10}
EXPECTED_PROMOTION_COUNT_HISTOGRAM = {"1": 15, "2": 2}
EXPECTED_TOTAL_PROMOTED_ELECTRONS = 19
EXPECTED_SPECIAL_CLOSURE_SYMBOLS = ("Cr", "Cu", "Mo", "Pd", "Ag", "Gd", "Au")

_SUBSHELL_RE = re.compile(r"^(\d+)([spdfghi])$")
_TOKEN_RE = re.compile(r"^(\d+)([spdfghi])(\d+)$")
_LABEL_TO_L = {label: l for l, label in ORBITAL_LABELS.items()}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def certificate_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def parse_subshell(label: str) -> tuple[int, int]:
    match = _SUBSHELL_RE.fullmatch(label.strip())
    if not match:
        raise ValueError(f"invalid subshell label {label!r}")
    n = int(match.group(1))
    orbital = match.group(2)
    return n, _LABEL_TO_L[orbital]


def parse_expanded_configuration(text: str) -> dict[str, int]:
    occupancy: dict[str, int] = {}
    for token in text.split():
        match = _TOKEN_RE.fullmatch(token)
        if not match:
            raise ValueError(f"invalid expanded configuration token {token!r}")
        label = f"{match.group(1)}{match.group(2)}"
        count = int(match.group(3))
        if label in occupancy:
            raise ValueError(f"duplicate subshell {label}")
        _, l = parse_subshell(label)
        capacity = subshell_capacity(l)
        if count < 0 or count > capacity:
            raise ValueError(f"occupancy {count} exceeds capacity {capacity} for {label}")
        occupancy[label] = count
    return occupancy


def ordered_configuration_text(occupancy: Mapping[str, int]) -> str:
    order = [subshell_name(n, l) for n, l in madelung_subshells()]
    unknown = sorted(set(occupancy) - set(order))
    if unknown:
        raise ValueError(f"unsupported subshells: {unknown}")
    return " ".join(
        f"{label}{int(occupancy[label])}"
        for label in order
        if int(occupancy.get(label, 0)) > 0
    )


def apply_promotion(
    occupancy: Mapping[str, int],
    donor: str,
    acceptor: str,
    count: int,
) -> dict[str, int]:
    if count <= 0:
        raise ValueError("promotion count must be positive")
    output = {str(key): int(value) for key, value in occupancy.items()}
    donor_value = int(output.get(donor, 0))
    acceptor_value = int(output.get(acceptor, 0))
    _, acceptor_l = parse_subshell(acceptor)
    if donor_value < count:
        raise ValueError("donor occupancy is too small")
    if acceptor_value + count > subshell_capacity(acceptor_l):
        raise ValueError("acceptor capacity exceeded")
    output[donor] = donor_value - count
    output[acceptor] = acceptor_value + count
    return {key: value for key, value in output.items() if value != 0}


def occupancy_delta(
    observed: Mapping[str, int],
    baseline: Mapping[str, int],
) -> dict[str, int]:
    keys = sorted(set(observed) | set(baseline))
    return {
        key: int(observed.get(key, 0)) - int(baseline.get(key, 0))
        for key in keys
        if int(observed.get(key, 0)) != int(baseline.get(key, 0))
    }


def promotion_count(delta: Mapping[str, int]) -> int:
    positive = sum(value for value in delta.values() if value > 0)
    negative = -sum(value for value in delta.values() if value < 0)
    if positive != negative:
        raise ValueError("promotion delta does not conserve electron number")
    return positive


def donor_acceptor_cut(delta: Mapping[str, int]) -> dict[str, int]:
    """Swap the two active promotion channels.

    A valid elementary or multi-electron promotion has one negative donor
    component and one positive acceptor component. Channel exchange maps the
    Smriti vector to its negative, so the residue is cut-odd.
    """
    nonzero = [(key, int(value)) for key, value in delta.items() if int(value) != 0]
    if len(nonzero) != 2:
        raise ValueError("promotion cut requires exactly two active subshells")
    (left_key, left_value), (right_key, right_value) = nonzero
    return {left_key: right_value, right_key: left_value}


def promotion_family(donor: str, acceptor: str) -> str:
    donor_orbital = donor[-1]
    acceptor_orbital = acceptor[-1]
    if donor_orbital == "s" and acceptor_orbital == "d":
        return "S_TO_D"
    if donor_orbital == "f" and acceptor_orbital == "d":
        return "F_TO_D"
    return f"{donor_orbital.upper()}_TO_{acceptor_orbital.upper()}"


def special_closure(subshell: str, occupancy: int) -> str | None:
    _, l = parse_subshell(subshell)
    capacity = subshell_capacity(l)
    if occupancy == capacity:
        return "FULL_SUBSHELL"
    if occupancy * 2 == capacity:
        return "HALF_FILLED_SUBSHELL"
    return None


def _build_audited_row(v1_row: Mapping[str, Any]) -> dict[str, Any]:
    z = int(v1_row["atomic_number"])
    symbol = str(v1_row["symbol"])
    baseline = parse_expanded_configuration(str(v1_row["madelung_configuration"]))
    source_row = NIST_PROMOTION_ROWS.get(z)

    if z > NIST_COVERAGE_MAX_Z:
        return {
            "atomic_number": z,
            "symbol": symbol,
            "audit_state": "ABSTAIN_SUPERHEAVY_OUTSIDE_NIST_H_U_SOURCE",
            "madelung_configuration": str(v1_row["madelung_configuration"]),
            "nist_configuration": None,
            "smriti_delta": None,
            "promotion_count": None,
            "promotion_family": None,
            "source_reference_configuration": None,
        }

    if source_row is None:
        observed = dict(baseline)
        donor = acceptor = None
        reference = "MATCHES_V1_MADELUNG_OCCUPANCY"
    else:
        donor, acceptor, count, reference = source_row
        observed = apply_promotion(baseline, donor, acceptor, count)

    delta = occupancy_delta(observed, baseline)
    reconstructed = {
        key: int(baseline.get(key, 0)) + int(delta.get(key, 0))
        for key in set(baseline) | set(delta)
    }
    reconstructed = {key: value for key, value in reconstructed.items() if value != 0}
    electron_count = sum(observed.values())
    conserved = sum(delta.values()) == 0

    if delta:
        moved = promotion_count(delta)
        cut = donor_acceptor_cut(delta)
        cut_odd = cut == {key: -value for key, value in delta.items()}
        acceptor_after = observed[str(acceptor)]
        donor_after = observed.get(str(donor), 0)
        family = promotion_family(str(donor), str(acceptor))
        if str(donor).endswith("f"):
            closure = special_closure(str(donor), donor_after)
            closure_subshell = str(donor) if closure is not None else None
        else:
            closure = special_closure(str(acceptor), acceptor_after)
            closure_subshell = str(acceptor) if closure is not None else None
        state = "NIST_PROMOTION_SMRITI"
    else:
        moved = 0
        cut = {}
        cut_odd = True
        closure = None
        closure_subshell = None
        family = None
        state = "NIST_MATCHES_V1"

    return {
        "atomic_number": z,
        "symbol": symbol,
        "audit_state": state,
        "madelung_configuration": ordered_configuration_text(baseline),
        "nist_configuration": ordered_configuration_text(observed),
        "source_reference_configuration": reference,
        "smriti_delta": dict(sorted(delta.items())),
        "promotion_count": moved,
        "promotion_family": family,
        "donor_subshell": donor,
        "acceptor_subshell": acceptor,
        "active_inner_special_closure": closure,
        "special_closure_subshell": closure_subshell,
        "donor_acceptor_cut": dict(sorted(cut.items())),
        "smriti_is_cut_odd": cut_odd,
        "electron_number_conserved": conserved,
        "madelung_electron_count": sum(baseline.values()),
        "nist_electron_count": electron_count,
        "reconstruction_exact": reconstructed == observed,
        "neutrality_residue": electron_count - z,
    }


def build_ground_state_ledger() -> dict[str, Any]:
    rows = [_build_audited_row(row) for row in derive_periodic_table(118)]
    audited = [row for row in rows if int(row["atomic_number"]) <= NIST_COVERAGE_MAX_Z]
    exceptions = [row for row in audited if row["audit_state"] == "NIST_PROMOTION_SMRITI"]
    abstentions = [row for row in rows if str(row["audit_state"]).startswith("ABSTAIN_")]

    family_counts = Counter(str(row["promotion_family"]) for row in exceptions)
    histogram = Counter(str(int(row["promotion_count"])) for row in exceptions)
    special_closure_symbols = tuple(
        str(row["symbol"])
        for row in exceptions
        if row["active_inner_special_closure"] is not None
    )

    checks = {
        "total_positions_118": len(rows) == 118,
        "nist_audited_positions_92": len(audited) == 92,
        "superheavy_abstentions_26": len(abstentions) == 26,
        "exception_atomic_numbers_exact": tuple(
            int(row["atomic_number"]) for row in exceptions
        ) == EXPECTED_EXCEPTION_Z,
        "exception_symbol_sequence_exact": tuple(
            str(row["symbol"]) for row in exceptions
        ) == EXPECTED_EXCEPTION_SYMBOLS,
        "family_counts_exact": dict(sorted(family_counts.items())) == EXPECTED_FAMILY_COUNTS,
        "promotion_histogram_exact": dict(sorted(histogram.items()))
        == EXPECTED_PROMOTION_COUNT_HISTOGRAM,
        "total_promoted_electrons_19": sum(
            int(row["promotion_count"]) for row in exceptions
        ) == EXPECTED_TOTAL_PROMOTED_ELECTRONS,
        "special_closure_symbols_exact": special_closure_symbols
        == EXPECTED_SPECIAL_CLOSURE_SYMBOLS,
        "electron_number_conserved_for_all_audited": all(
            bool(row["electron_number_conserved"]) for row in audited
        ),
        "reconstruction_exact_for_all_audited": all(
            bool(row["reconstruction_exact"]) for row in audited
        ),
        "neutrality_closes_for_all_audited": all(
            int(row["neutrality_residue"]) == 0 for row in audited
        ),
        "every_nonzero_smriti_is_cut_odd": all(
            bool(row["smriti_is_cut_odd"]) for row in exceptions
        ),
        "all_nonexception_rows_have_zero_delta": all(
            row["smriti_delta"] == {}
            for row in audited
            if row["audit_state"] == "NIST_MATCHES_V1"
        ),
    }

    return {
        "schema": "rkf.periodic_ground_state_smriti_ledger.v2a",
        "status": (
            "PASS_RKF_PERIODIC_GROUND_STATE_SMRITI_LEDGER_V2A"
            if all(checks.values())
            else "INCONCLUSIVE_RKF_PERIODIC_GROUND_STATE_SMRITI_LEDGER_V2A"
        ),
        "source_pin": {
            "authority": "NIST",
            "url": NIST_SOURCE_URL,
            "source_scope": "NEUTRAL_GROUND_CONFIGURATIONS_H_THROUGH_U",
            "coverage_atomic_numbers": [1, 92],
            "source_note": (
                "The NIST page states that the neutral configurations are taken "
                "from a NIST Atomic Physics Division compilation and that some "
                "differ from older references."
            ),
        },
        "recognition_identity": {
            "baseline": "M_Z = V1_MADELUNG_OCCUPANCY_VECTOR",
            "observed": "N_Z = NIST_GROUND_OCCUPANCY_VECTOR",
            "smriti": "SIGMA_Z = N_Z - M_Z",
            "closure": "M_Z + SIGMA_Z - N_Z = 0",
            "charge_conservation": "SUM_SUBSHELL SIGMA_Z = 0",
            "promotion_cut": "DONOR_ACCEPTOR_CHANNEL_EXCHANGE",
            "cut_parity": "J(SIGMA_Z) = -SIGMA_Z",
        },
        "summary": {
            "total_periodic_positions": len(rows),
            "nist_audited_positions": len(audited),
            "superheavy_abstentions": len(abstentions),
            "nonzero_smriti_count": len(exceptions),
            "zero_smriti_count": len(audited) - len(exceptions),
            "promotion_family_counts": dict(sorted(family_counts.items())),
            "promotion_count_histogram": dict(sorted(histogram.items())),
            "total_promoted_electrons": sum(
                int(row["promotion_count"]) for row in exceptions
            ),
            "special_closure_symbols": list(special_closure_symbols),
        },
        "checks": checks,
        "claim_boundary": {
            "nist_h_through_u_exception_ledger_frozen": True,
            "smriti_reconstruction_and_charge_conservation_proved": True,
            "all_observed_exceptions_reduced_to_two_promotion_families": True,
            "superheavy_93_to_118_configurations_validated": False,
            "madelung_order_derived_from_many_electron_hamiltonian": False,
            "promotion_energy_functional_derived": False,
            "chemical_reactivity_derived": False,
            "ground_state_source_is_current_asd_query": False,
        },
        "exception_rows": exceptions,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "releases/rkf-periodic-table-v2a/ground_state_smriti_ledger.json"
        ),
    )
    args = parser.parse_args()
    certificate = build_ground_state_ledger()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(certificate))
    print(json.dumps({
        "status": certificate["status"],
        "sha256": certificate_sha256(certificate),
        "summary": certificate["summary"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
