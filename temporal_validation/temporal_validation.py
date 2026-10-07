"""Temporally separated validation of the frozen UAM-V4 predictor.

Question: given only an OLDER mass evaluation, how well does the frozen V4 method predict the nuclei whose
masses were first MEASURED in a later evaluation?

Inputs  : AME2012 / AME2016 (older tables; measured and estimated entries are flagged by '#')
Truth   : AME2020 measured entries (the repository's frozen processed dataset)
Targets : nuclei estimated ('#') or absent in the older table and measured in AME2020
Methods : frozen UAM-V4 (src/uam_v4_reproducer.build_report, unchanged), run on the older table with every
          target blanked; two neighbour policies -- measured neighbours only, and measured + the older table's
          own estimates (the policy of the headline in-sample run)
Baselines: the older evaluation's own estimate (trends from the mass surface), where it gave one;
           Garvey-Kelson local mass relations from the older table's measured masses.
Also reported: the in-sample headline restricted to measured targets.
Python 3.12, standard library only.
"""
import csv
import json
import math
import pathlib
import statistics
import sys
import zipfile
import io

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'src'))
import uam_v4_reproducer as v4  # frozen method, imported unchanged

U_KEV = 931494.10242


def load_2020():
    z = zipfile.ZipFile(HERE.parent / 'uam_v4_processed_dataset.zip')
    rows = list(csv.DictReader(io.TextIOWrapper(z.open('ame_nubase_atomic_native.csv'), encoding='utf-8-sig')))
    out = {}
    for r in rows:
        key = (int(r['Z']), int(r['N']))
        out[key] = dict(b=float(r['binding_energy_per_A_keV']), est=r['binding_energy_per_A_estimated'] == 'True',
                        sym=r['Symbol'])
    return out


def load_2016():
    out = {}
    with open(HERE / 'data' / 'ame2016_mass16.csv', encoding='utf-8-sig') as fh:
        rd = csv.reader(fh)
        next(rd)
        for row in rd:
            n, z, a = int(row[2]), int(row[3]), int(row[4])
            raw = row[8]
            est = '#' in raw
            per_a = float(raw.replace('#', ''))   # this column is binding energy per nucleon (Fe-56: 8790.354)
            out[(z, n)] = dict(b=per_a, est=est, sym=row[5])
    return out


def load_2012():
    rows = []
    for line in open(HERE / 'data' / 'ame2012_mass.mas12', encoding='latin-1'):
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split()
        n, z, a = int(parts[1]), int(parts[2]), int(parts[3])
        raw = parts[5]
        rows.append((z, n, a, parts[4], float(raw.replace('#', '')) * 1e-6, '#' in raw))
    m_h = next(m for z, n, a, s, m, e in rows if (z, n) == (1, 0))
    m_n = next(m for z, n, a, s, m, e in rows if (z, n) == (0, 1))
    out = {}
    for z, n, a, s, m, e in rows:
        out[(z, n)] = dict(b=(z * m_h + n * m_n - m) * U_KEV / a, est=e, sym=s)
    return out


def run_v4(table, targets, keep_estimates):
    rows = []
    for (z, n), rec in table.items():
        a = z + n
        value = rec['b']
        if (z, n) in targets or (rec['est'] and not keep_estimates):
            value = ''
        rows.append(dict(Z=z, N=n, A=a, Symbol=rec['sym'], binding_energy_per_A_keV=value))
    for (z, n) in targets:
        if (z, n) not in table:
            rows.append(dict(Z=z, N=n, A=z + n, Symbol='', binding_energy_per_A_keV=''))
    rep = v4.build_report(rows, 'temporal')
    pred = {}
    for r in rep['records']:
        if (r['z'], r['n']) in targets:
            pred[(r['z'], r['n'])] = dict(guarded=r['guarded_blended_prediction_keV_per_a'],
                                          raw=r['raw_blended_prediction_keV_per_a'],
                                          n_pred=r['n_predictor'], z_pred=r['z_predictor'])
    return pred


GK = (  # each relation: list of ((dN, dZ), sign) summing to zero for total binding energies
    [((2, -2), 1), ((0, 0), -1), ((0, -1), 1), ((1, -2), -1), ((1, 0), 1), ((2, -1), -1)],
    [((2, 0), 1), ((0, -2), -1), ((1, -2), 1), ((2, -1), -1), ((0, -1), 1), ((1, 0), -1)],
)


def garvey_kelson(total, z, n):
    """average of all available Garvey-Kelson estimates of the total binding energy of (z, n)."""
    estimates = []
    for rel in GK:
        for (dn0, dz0), s0 in rel:           # put the target at this position of the relation
            acc, ok = 0.0, True
            for (dn, dz), s in rel:
                if (dn, dz) == (dn0, dz0):
                    continue
                key = (z + dz - dz0, n + dn - dn0)
                if key not in total:
                    ok = False
                    break
                acc += s * total[key]
            if ok:
                estimates.append(-acc / s0)
    return (sum(estimates) / len(estimates), len(estimates)) if estimates else (None, 0)


def stats(errors_per_a, masses):
    if not errors_per_a:
        return dict(count=0)
    ab = [abs(e) for e in errors_per_a]
    tot = [abs(e) * a for e, a in zip(errors_per_a, masses)]
    return dict(count=len(ab), median_keV_per_A=round(statistics.median(ab), 3), mean_keV_per_A=round(sum(ab) / len(ab), 3),
                rms_keV_per_A=round(math.sqrt(sum(x * x for x in ab) / len(ab)), 3),
                median_keV=round(statistics.median(tot), 1), rms_keV=round(math.sqrt(sum(x * x for x in tot) / len(tot)), 1))


def temporal(old, truth, label, min_a=16):
    targets = {k for k, t in truth.items() if not t['est'] and (k not in old or old[k]['est']) and sum(k) >= min_a}
    measured_total = {k: r['b'] * sum(k) for k, r in old.items() if not r['est']}
    result = dict(label=label, targets=len(targets))
    rows = {}
    for policy, keep in (('measured_neighbours_only', False), ('with_older_estimates', True)):
        pred = run_v4(old, targets, keep)
        for kind in ('guarded', 'raw'):
            errs, masses, keys = [], [], []
            for k in sorted(targets):
                p = pred.get(k, {}).get(kind)
                if p is not None:
                    errs.append(p - truth[k]['b'])
                    masses.append(sum(k))
                    keys.append(k)
            result[f'v4_{kind}_{policy}'] = stats(errs, masses)
            rows[f'v4_{kind}_{policy}'] = dict(zip(keys, errs))
    errs, masses, keys = [], [], []
    for k in sorted(targets):
        if k in old and old[k]['est']:
            errs.append(old[k]['b'] - truth[k]['b'])
            masses.append(sum(k))
            keys.append(k)
    result['older_evaluation_estimate'] = stats(errs, masses)
    rows['older_evaluation_estimate'] = dict(zip(keys, errs))
    errs, masses, keys = [], [], []
    for k in sorted(targets):
        g, cnt = garvey_kelson(measured_total, k[0], k[1])
        if g is not None:
            errs.append(g / sum(k) - truth[k]['b'])
            masses.append(sum(k))
            keys.append(k)
    result['garvey_kelson_measured_only'] = stats(errs, masses)
    rows['garvey_kelson_measured_only'] = dict(zip(keys, errs))
    # like-for-like: nuclei predicted by all of strict V4 (guarded), the older estimate and Garvey-Kelson
    common = set(rows['v4_guarded_measured_neighbours_only']) & set(rows['older_evaluation_estimate']) & set(rows['garvey_kelson_measured_only'])
    result['common_set'] = {name: stats([rows[name][k] for k in sorted(common)], [sum(k) for k in sorted(common)])
                            for name in ('v4_guarded_measured_neighbours_only', 'older_evaluation_estimate', 'garvey_kelson_measured_only')}
    return result


def in_sample(truth, min_a=16):
    """the headline run, re-scored on measured targets only, with two neighbour policies; and Garvey-Kelson."""
    out = {}
    for policy, keep in (('all_entries_as_neighbours', True), ('measured_neighbours_only', False)):
        rows = [dict(Z=z, N=n, A=z + n, Symbol=r['sym'], binding_energy_per_A_keV=(r['b'] if (keep or not r['est']) else ''))
                for (z, n), r in truth.items()]
        rep = v4.build_report(rows, 'in_sample')
        e_meas, a_meas, e_est, a_est = [], [], [], []
        for r in rep['records']:
            k = (r['z'], r['n'])
            p = r['guarded_blended_prediction_keV_per_a']
            if p is None or r['actual_binding_energy_per_A_keV'] is None:
                continue
            (e_est if truth[k]['est'] else e_meas).append(p - truth[k]['b'])
            (a_est if truth[k]['est'] else a_meas).append(sum(k))
        out[policy] = dict(measured_targets=stats(e_meas, a_meas), estimated_targets=stats(e_est, a_est))
    total = {k: r['b'] * sum(k) for k, r in truth.items() if not r['est']}
    errs, masses = [], []
    for k, r in truth.items():
        if r['est'] or sum(k) < min_a:
            continue
        rest = dict(total)
        del rest[k]
        g, cnt = garvey_kelson(rest, k[0], k[1])
        if g is not None:
            errs.append(g / sum(k) - r['b'])
            masses.append(sum(k))
    out['garvey_kelson_measured_leave_one_out_A_ge_16'] = stats(errs, masses)
    return out


def run():
    truth = load_2020()
    return dict(in_sample_2020=in_sample(truth),
                temporal_2016_to_2020=temporal(load_2016(), truth, 'AME2016 -> AME2020'),
                temporal_2012_to_2020=temporal(load_2012(), truth, 'AME2012 -> AME2020'))


if __name__ == '__main__':
    res = run()
    json.dump(res, open(HERE / 'TEMPORAL_VALIDATION_RESULT.json', 'w'), indent=1, sort_keys=True)
    print(json.dumps(res, indent=1))
