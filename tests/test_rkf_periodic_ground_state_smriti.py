from __future__ import annotations

import copy
import unittest

from src.rkf_periodic_ground_state_smriti import (
    EXPECTED_EXCEPTION_SYMBOLS,
    build_ground_state_ledger,
    load_nist_source,
    certificate_sha256,
    donor_acceptor_cut,
    occupancy_delta,
    parse_expanded_configuration,
    promotion_count,
)
from src.rkf_periodic_table import derive_periodic_table


class PeriodicGroundStateSmritiTests(unittest.TestCase):
    def test_exception_ledger_counts_and_families(self) -> None:
        certificate = build_ground_state_ledger()
        self.assertEqual(
            certificate["status"],
            "PASS_RKF_PERIODIC_GROUND_STATE_SMRITI_LEDGER_V2A",
        )
        summary = certificate["summary"]
        self.assertEqual(summary["nist_audited_positions"], 92)
        self.assertEqual(summary["superheavy_abstentions"], 26)
        self.assertEqual(summary["nonzero_smriti_count"], 17)
        self.assertEqual(summary["promotion_family_counts"], {"F_TO_D": 7, "S_TO_D": 10})
        self.assertEqual(summary["promotion_count_histogram"], {"1": 15, "2": 2})
        self.assertEqual(summary["total_promoted_electrons"], 19)

    def test_exception_symbol_sequence_is_exact(self) -> None:
        certificate = build_ground_state_ledger()
        self.assertEqual(
            tuple(row["symbol"] for row in certificate["exception_rows"]),
            EXPECTED_EXCEPTION_SYMBOLS,
        )

    def test_chromium_and_copper_close_inner_d_seams(self) -> None:
        rows = {row["symbol"]: row for row in build_ground_state_ledger()["exception_rows"]}
        chromium = rows["Cr"]
        copper = rows["Cu"]
        self.assertEqual(chromium["smriti_delta"], {"3d": 1, "4s": -1})
        self.assertEqual(chromium["active_inner_special_closure"], "HALF_FILLED_SUBSHELL")
        self.assertEqual(copper["smriti_delta"], {"3d": 1, "4s": -1})
        self.assertEqual(copper["active_inner_special_closure"], "FULL_SUBSHELL")

    def test_palladium_and_thorium_are_double_promotions(self) -> None:
        rows = {row["symbol"]: row for row in build_ground_state_ledger()["exception_rows"]}
        self.assertEqual(rows["Pd"]["promotion_count"], 2)
        self.assertEqual(rows["Pd"]["smriti_delta"], {"4d": 2, "5s": -2})
        self.assertEqual(rows["Th"]["promotion_count"], 2)
        self.assertEqual(rows["Th"]["smriti_delta"], {"5f": -2, "6d": 2})

    def test_gadolinium_closes_half_filled_f_seam(self) -> None:
        rows = {row["symbol"]: row for row in build_ground_state_ledger()["exception_rows"]}
        gadolinium = rows["Gd"]
        self.assertEqual(gadolinium["smriti_delta"], {"4f": -1, "5d": 1})
        self.assertEqual(gadolinium["special_closure_subshell"], "4f")
        self.assertEqual(gadolinium["active_inner_special_closure"], "HALF_FILLED_SUBSHELL")

    def test_promotion_cut_is_odd_and_conserves_charge(self) -> None:
        for row in build_ground_state_ledger()["exception_rows"]:
            delta = row["smriti_delta"]
            self.assertEqual(sum(delta.values()), 0)
            self.assertEqual(
                donor_acceptor_cut(delta),
                {key: -value for key, value in delta.items()},
            )
            self.assertEqual(promotion_count(delta), row["promotion_count"])

    def test_unmodified_element_has_zero_smriti(self) -> None:
        rows = {
            row["symbol"]: row
            for row in build_ground_state_ledger()["rows"]
            if row["atomic_number"] <= 92
        }
        iron = rows["Fe"]
        self.assertEqual(iron["audit_state"], "NIST_MATCHES_V1")
        self.assertEqual(iron["smriti_delta"], {})
        self.assertEqual(iron["madelung_configuration"], iron["nist_configuration"])

    def test_superheavy_positions_fail_closed(self) -> None:
        rows = {
            row["symbol"]: row
            for row in build_ground_state_ledger()["rows"]
        }
        self.assertEqual(
            rows["Np"]["audit_state"],
            "ABSTAIN_SUPERHEAVY_OUTSIDE_NIST_H_U_SOURCE",
        )
        self.assertIsNone(rows["Np"]["nist_configuration"])
        self.assertEqual(
            rows["Og"]["audit_state"],
            "ABSTAIN_SUPERHEAVY_OUTSIDE_NIST_H_U_SOURCE",
        )

    def test_frozen_source_snapshot_drives_chromium_delta(self) -> None:
        baseline = parse_expanded_configuration(
            derive_periodic_table(24)[-1]["madelung_configuration"]
        )
        source = load_nist_source()
        self.assertEqual(len(source), 92)
        self.assertEqual(source[24]["neutral_configuration"], "[Ar] 3d5 4s1")
        self.assertEqual(
            occupancy_delta(source[24]["occupancy"], baseline),
            {"3d": 1, "4s": -1},
        )

    def test_certificate_hash_is_deterministic(self) -> None:
        first = build_ground_state_ledger()
        second = copy.deepcopy(first)
        self.assertEqual(certificate_sha256(first), certificate_sha256(second))


if __name__ == "__main__":
    unittest.main()
