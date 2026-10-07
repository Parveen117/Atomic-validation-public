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


class LaterPredictorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import temporal_validation_v5_v6 as w
        cls.w = w
        cls.truth = t.load_2020()
        cls.old = t.load_2016()
        cls.targets = {k for k, x in cls.truth.items() if not x['est'] and (k not in cls.old or cls.old[k]['est']) and sum(k) >= 16}
        cls.rows = w.rows_of(cls.old, cls.targets, False)
        cls.by_key = {(r['Z'], r['N']): r for r in cls.rows}

    def test_placeholder_is_not_read_by_the_observer(self):
        for key in sorted(self.targets)[:12]:
            a = self.w.target_observer(self.by_key, key, placeholder=1.0)
            b = self.w.target_observer(self.by_key, key, placeholder=9.0e6)
            self.assertEqual(a, b)

    def test_local_neighbourhood_reproduces_the_full_observer(self):
        key = sorted(self.targets)[20]
        full_rows = self.rows + [dict(Z=key[0], N=key[1], A=sum(key), Symbol='', binding_energy_per_A_keV=1.0)]
        full = [r for r in self.w.v5.build_observer_records(full_rows) if (int(r['z']), int(r['n'])) == key][0]
        local = self.w.target_observer(self.by_key, key)
        for field in ('neutron_jet', 'proton_jet', 'axis_mean_prediction_keV_per_a', 'tensor_cubic_prediction_keV_per_a', 'cut_even_jet', 'cut_odd_jet'):
            self.assertEqual(full[field], local[field])

    def test_seam_guard_orders_the_error(self):
        import seam_guard
        res = seam_guard.in_sample(self.truth)
        table = res['by_coverage']
        self.assertLess(table[3]['rms_keV'], 0.7*table[4]['rms_keV'])
        self.assertGreater(res['highest_spread_tenth']['rms_keV'], 3*table[1]['rms_keV'])


if __name__ == '__main__':
    unittest.main()
