"""Standard library only. Python 3.12."""
import unittest

import temporal_validation as t


class TemporalValidationTests(unittest.TestCase):
    def test_tables_agree_on_a_stable_nucleus(self):
        fe = (26, 30)
        b20, b16, b12 = t.load_2020()[fe]['b'], t.load_2016()[fe]['b'], t.load_2012()[fe]['b']
        self.assertAlmostEqual(b20, 8790.354, places=2)
        self.assertAlmostEqual(b16, b20, places=2)
        self.assertAlmostEqual(b12, b20, places=1)

    def test_garvey_kelson_is_exact_on_a_separable_surface(self):
        total = {(z, n): 3.0*z*z + 5.0*n*n*n - 2.0*(z+n)**2 + 7.0*(z+n) for z in range(20, 30) for n in range(20, 30)}
        target = (24, 25)
        rest = dict(total)
        del rest[target]
        value, count = t.garvey_kelson(rest, *target)
        self.assertEqual(count, 12)
        self.assertAlmostEqual(value, total[target], places=6)

    def test_target_sets(self):
        truth = t.load_2020()
        for old, expected in ((t.load_2016(), 73), (t.load_2012(), 126)):
            targets = {k for k, x in truth.items() if not x['est'] and (k not in old or old[k]['est']) and sum(k) >= 16}
            self.assertEqual(len(targets), expected)

    def test_targets_are_blanked_before_prediction(self):
        truth, old = t.load_2020(), t.load_2016()
        targets = {k for k, x in truth.items() if not x['est'] and (k not in old or old[k]['est']) and sum(k) >= 16}
        poisoned = {k: dict(v) for k, v in old.items()}
        for k in targets:
            if k in poisoned:
                poisoned[k]['b'] = 1.0e9
        self.assertEqual(t.run_v4(old, targets, False), t.run_v4(poisoned, targets, False))


if __name__ == '__main__':
    unittest.main()
