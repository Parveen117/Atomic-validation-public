"""Temporal validation of the later predictors: RKF V5 (cross-fitted cut-graded decoder), Recognition
Repair V5.1 and Madhava-Smriti V6 -- all imported unchanged from src/.

Design as in temporal_validation.py.  For every target nucleus:
  * the decoders (levels 1, 2, 3) are fitted on the OLDER table only, with the target's element chain held out
    (the repository's own leave-one-element-out rule);
  * the target's observer record is built by the frozen build_observer_records from the older table's
    neighbours; the target enters with a placeholder value that no observer component reads (tested);
  * V5.1 and V6 decisions use the frozen V4 record computed on the older table.
Python 3.12, standard library only.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'src'))
import temporal_validation as tv
from src import rkf_nuclear_prediction as v5
from src import rkf_recognition_repair as repair
from src import rkf_madhava_smriti_nuclear as v6

PLACEHOLDER = 1.0


def rows_of(table, targets, keep_estimates):
    return [dict(Z=z, N=n, A=z + n, Symbol=r['sym'], binding_energy_per_A_keV=r['b'])
            for (z, n), r in table.items() if (z, n) not in targets and (keep_estimates or not r['est'])]


def target_observer(rows_by_key, key, placeholder=PLACEHOLDER, reach=(3, 6)):
    """the frozen observer record of one target, from its local neighbourhood in the older table."""
    z, n = key
    local = [row for (zz, nn), row in rows_by_key.items() if abs(zz - z) <= reach[0] and abs(nn - n) <= reach[1]]
    local.append(dict(Z=z, N=n, A=z + n, Symbol='', binding_energy_per_A_keV=placeholder))
    for rec in v5.build_observer_records(local):
        if (int(rec['z']), int(rec['n'])) == key:
            rec = dict(rec)
            rec['actual_binding_energy_per_A_keV'] = None
            rec.pop('observer_hash', None)
            return rec
    return None


def frozen_v4_records(table, targets, keep_estimates):
    rows = []
    for (z, n), rec in table.items():
        value = rec['b']
        if (z, n) in targets or (rec['est'] and not keep_estimates):
            value = ''
        rows.append(dict(Z=z, N=n, A=z + n, Symbol=rec['sym'], binding_energy_per_A_keV=value))
    for (z, n) in targets:
        if (z, n) not in table:
            rows.append(dict(Z=z, N=n, A=z + n, Symbol='', binding_energy_per_A_keV=''))
    rep = tv.v4.build_report(rows, 'temporal')
    return {(r['z'], r['n']): r for r in rep['records']}


def predict(table, truth, keep_estimates, min_a=16):
    targets = {k for k, t in truth.items() if not t['est'] and (k not in table or table[k]['est']) and sum(k) >= min_a}
    rows = rows_of(table, targets, keep_estimates)
    rows_by_key = {(r['Z'], r['N']): r for r in rows}
    training = v5.build_observer_records(rows)
    frozen = frozen_v4_records(table, targets, keep_estimates)
    models = {}
    out = {}
    for key in sorted(targets):
        z0 = key[0]
        obs = target_observer(rows_by_key, key)
        if obs is None:
            continue
        if z0 not in models:
            fit_on = [r for r in training if int(r['z']) != z0]
            models[z0] = {level: v5.fit_minimum_burden_decoder(fit_on, level=level, ridge=1.0) for level in (1, 2, 3)}
        level_records = {}
        for level in (1, 2, 3):
            applied = v5.apply_decoder(models[z0][level], obs)
            level_records[level] = dict(z=key[0], n=key[1], a=sum(key),
                                        rkf_prediction_keV_per_a=None if applied is None else applied['prediction_keV_per_a'],
                                        decoder_burden=None if applied is None else applied['decoder_burden'],
                                        burden_guard_pass=False if applied is None else applied['burden_guard_pass'])
        fz = frozen.get(key, {})
        item = dict(level_records[3])
        item['actual_binding_energy_per_A_keV'] = None
        item['frozen_uam_guarded_prediction_keV_per_a'] = fz.get('guarded_blended_prediction_keV_per_a')
        item.update(repair.recognition_repair_decision(item, fz))
        mad = v6.build_madhava_record(obs, level_records[1], level_records[2], item)
        p3 = level_records[3]['rkf_prediction_keV_per_a']
        out[key] = dict(
            axis_mean=obs.get('axis_mean_prediction_keV_per_a'),
            tensor_cubic=obs.get('tensor_cubic_prediction_keV_per_a'),
            rkf_v5_level3=p3,
            rkf_v5_burden_guarded=p3 if level_records[3]['burden_guard_pass'] else None,
            frozen_v4=fz.get('guarded_blended_prediction_keV_per_a'),
            recognition_repair_v5_1=item['recognition_repair_prediction_keV_per_a'],
            repair_source=item['recognition_repair_source'],
            v6_strict=mad['v6_strict_prediction_keV_per_a'],
            v6_fallback=mad['v6_fallback_prediction_keV_per_a'],
            v6_order_selected=mad['v6_order_selected_prediction_keV_per_a'],
            v6_class=mad['madhava_refinement_classification'])
    return targets, out


METHODS = ('frozen_v4', 'axis_mean', 'tensor_cubic', 'rkf_v5_level3', 'rkf_v5_burden_guarded',
           'recognition_repair_v5_1', 'v6_strict', 'v6_fallback', 'v6_order_selected')


def evaluate(table, truth, label):
    result = dict(label=label)
    measured_total = {k: r['b'] * sum(k) for k, r in table.items() if not r['est']}
    for policy, keep in (('measured_neighbours_only', False), ('with_older_estimates', True)):
        targets, pred = predict(table, truth, keep)
        block = dict(targets=len(targets))
        errors = {}
        for m in METHODS:
            errors[m] = {k: p[m] - truth[k]['b'] for k, p in pred.items() if p[m] is not None}
            block[m] = tv.stats(list(errors[m].values()), [sum(k) for k in errors[m]])
        gk = {}
        for k in sorted(targets):
            g, cnt = tv.garvey_kelson(measured_total, *k)
            if g is not None:
                gk[k] = g / sum(k) - truth[k]['b']
        old_est = {k: table[k]['b'] - truth[k]['b'] for k in targets if k in table and table[k]['est']}
        block['garvey_kelson'] = tv.stats(list(gk.values()), [sum(k) for k in gk])
        block['older_evaluation_estimate'] = tv.stats(list(old_est.values()), [sum(k) for k in old_est])
        common = set(gk) & set(old_est) & set(errors['recognition_repair_v5_1']) & set(errors['v6_order_selected']) & set(errors['rkf_v5_level3'])
        cs = sorted(common)
        block['common_set'] = dict(count=len(cs))
        for m in ('frozen_v4', 'rkf_v5_level3', 'recognition_repair_v5_1', 'v6_fallback', 'v6_order_selected'):
            if all(k in errors[m] for k in cs):
                block['common_set'][m] = tv.stats([errors[m][k] for k in cs], [sum(k) for k in cs])
        block['common_set']['garvey_kelson'] = tv.stats([gk[k] for k in cs], [sum(k) for k in cs])
        block['common_set']['older_evaluation_estimate'] = tv.stats([old_est[k] for k in cs], [sum(k) for k in cs])
        srcs = {}
        for p in pred.values():
            srcs[p['repair_source']] = srcs.get(p['repair_source'], 0) + 1
        block['repair_sources'] = srcs
        cls = {}
        for p in pred.values():
            cls[p['v6_class']] = cls.get(p['v6_class'], 0) + 1
        block['v6_classes'] = cls
        result[policy] = block
    return result


def run():
    truth = tv.load_2020()
    return dict(temporal_2016_to_2020=evaluate(tv.load_2016(), truth, 'AME2016 -> AME2020'),
                temporal_2012_to_2020=evaluate(tv.load_2012(), truth, 'AME2012 -> AME2020'))


if __name__ == '__main__':
    res = run()
    json.dump(res, open(HERE / 'TEMPORAL_VALIDATION_V5_V6_RESULT.json', 'w'), indent=1, sort_keys=True)
    for name, d in res.items():
        for policy in ('measured_neighbours_only', 'with_older_estimates'):
            b = d[policy]
            print('==', d['label'], policy, 'targets', b['targets'])
            for m in METHODS + ('garvey_kelson', 'older_evaluation_estimate'):
                s = b[m]
                if s.get('count'):
                    print('   %-28s n=%3d  median %7.1f keV  rms %8.1f keV' % (m, s['count'], s['median_keV'], s['rms_keV']))
            print('   common set', b['common_set']['count'])
            for m, s in b['common_set'].items():
                if isinstance(s, dict):
                    print('      %-28s median %7.1f keV  rms %8.1f keV' % (m, s['median_keV'], s['rms_keV']))
            print('   repair sources', b['repair_sources'])
            print('   v6 classes', b['v6_classes'])
