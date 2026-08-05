from __future__ import annotations

import unittest

from src.rkf_periodic_table import (
    EXPECTED_BLOCK_COUNTS,
    EXPECTED_PERIOD_CLOSURES,
    EXPECTED_PERIOD_LENGTHS,
    build_certificate,
    cut_coordinates,
    derive_periodic_table,
    electron_hole_cut,
    madelung_subshells,
    period_summary,
    shell_capacity,
    subshell_capacity,
)


class RKFPeriodicTableTests(unittest.TestCase):
    def test_state_counting(self) -> None:
        self.assertEqual(
            [subshell_capacity(l) for l in range(4)],
            [2, 6, 10, 14],
        )
        self.assertEqual(
            [shell_capacity(n) for n in range(1, 8)],
            [2, 8, 18, 32, 50, 72, 98],
        )

    def test_electron_hole_cut_is_involutive(self) -> None:
        for capacity in (2, 6, 10, 14):
            for occupancy in range(capacity + 1):
                self.assertEqual(
                    electron_hole_cut(
                        electron_hole_cut(occupancy, capacity),
                        capacity,
                    ),
                    occupancy,
                )
        self.assertEqual(
            cut_coordinates(1, 2),
            {
                "occupancy": "1",
                "hole_occupancy": "1",
                "cut_even": "1",
                "cut_odd": "0",
            },
        )

    def test_madelung_order_used_by_current_table(self) -> None:
        names = [f"{n}{'spdf'[l]}" for n, l in madelung_subshells()]
        self.assertEqual(
            names[:19],
            [
                "1s", "2s", "2p", "3s", "3p", "4s", "3d", "4p", "5s",
                "4d", "5p", "6s", "4f", "5d", "6p", "7s", "5f", "6d",
                "7p",
            ],
        )

    def test_period_lengths_and_closures(self) -> None:
        elements = derive_periodic_table()
        summary = period_summary(elements)
        self.assertEqual(
            tuple(summary["period_lengths"]),
            EXPECTED_PERIOD_LENGTHS,
        )
        self.assertEqual(
            tuple(summary["period_closure_atomic_numbers"]),
            EXPECTED_PERIOD_CLOSURES,
        )
        self.assertEqual(summary["block_counts"], EXPECTED_BLOCK_COUNTS)

    def test_generated_spine_has_118_neutral_positions(self) -> None:
        elements = derive_periodic_table()
        self.assertEqual(len(elements), 118)
        self.assertEqual(elements[0]["symbol"], "H")
        self.assertEqual(elements[-1]["symbol"], "Og")
        self.assertTrue(
            all(row["electron_count"] == row["atomic_number"] for row in elements)
        )
        self.assertTrue(all(row["neutrality_residue"] == 0 for row in elements))

    def test_periodic_groups_and_blocks(self) -> None:
        elements = derive_periodic_table()
        by_symbol = {row["symbol"]: row for row in elements}
        self.assertEqual(by_symbol["He"]["group"], 18)
        self.assertEqual(by_symbol["Ne"]["group"], 18)
        self.assertEqual(by_symbol["Na"]["group"], 1)
        self.assertEqual(by_symbol["Cl"]["group"], 17)
        self.assertEqual(by_symbol["Fe"]["group"], 8)
        self.assertEqual(by_symbol["C"]["group"], 14)
        self.assertEqual(by_symbol["Fl"]["group"], 14)
        self.assertEqual(by_symbol["Og"]["group"], 18)
        self.assertEqual(by_symbol["Ce"]["madelung_block"], "f")
        self.assertEqual(by_symbol["Hf"]["madelung_block"], "d")

    def test_certificate_is_deterministic_and_passing(self) -> None:
        first = build_certificate()
        second = build_certificate()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS_RKF_PERIODIC_TABLE_SKELETON_V1")
        self.assertTrue(all(first["checks"].values()))


if __name__ == "__main__":
    unittest.main()
