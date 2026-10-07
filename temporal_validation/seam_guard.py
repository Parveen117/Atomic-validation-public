"""The repository's prospective disagreement guard, applied to mixed-difference (Garvey-Kelson) estimates.

Each target has up to twelve estimates.  Their spread is known before the target value is used.
Question: does the spread predict the error, so that abstaining on high spread helps?
Python 3.12, standard library only.
"""
import json
import math
import pathlib
import statistics

import temporal_validation as t

HERE = pathlib.Path(__file__).resolve().parent


def estimates(total, z, n):
    out = []
    for rel in t.GK:
        for (dn0, dz0), s0 in rel:
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
                out.append(-acc / s0)
    return out


def rms(values):
    return math.sqrt(sum(x * x for x in values) / len(values))


def in_sample(truth, min_a=16, min_estimates=3):
    total = {k: r['b'] * sum(k) for k, r in truth.items() if not r['est']}
    rows = []
    for k, r in truth.items():
        if r['est'] or sum(k) < min_a:
            continue
        rest = dict(total)
        del rest[k]
        e = estimates(rest, *k)
        if len(e) >= min_estimates:
            rows.append((statistics.pstdev(e), abs(statistics.mean(e) - total[k])))
    rows.sort()
    n = len(rows)
    table = []
    for q in (0.25, 0.5, 0.75, 0.9, 1.0):
        sub = rows[:int(n * q)]
        table.append(dict(coverage=q, count=len(sub), spread_at_most_keV=round(sub[-1][0], 1),
                          median_keV=round(statistics.median(x[1] for x in sub), 1), rms_keV=round(rms([x[1] for x in sub]), 1)))
    worst = rows[int(n * 0.9):]
    return dict(count=n, by_coverage=table,
                highest_spread_tenth=dict(median_keV=round(statistics.median(x[1] for x in worst), 1), rms_keV=round(rms([x[1] for x in worst]), 1)))


def temporal(old, truth, min_a=16):
    total_old = {k: r['b'] * sum(k) for k, r in old.items() if not r['est']}
    rows = []
    for k, x in truth.items():
        if x['est'] or sum(k) < min_a or not (k not in old or old[k]['est']):
            continue
        e = estimates(total_old, *k)
        if len(e) >= 2:
            rows.append((statistics.pstdev(e), abs(statistics.mean(e) - x['b'] * sum(k))))
    rows.sort()
    h = len(rows) // 2
    return dict(count=len(rows),
                lower_spread_half=dict(median_keV=round(statistics.median(x[1] for x in rows[:h]), 1), rms_keV=round(rms([x[1] for x in rows[:h]]), 1)),
                higher_spread_half=dict(median_keV=round(statistics.median(x[1] for x in rows[h:]), 1), rms_keV=round(rms([x[1] for x in rows[h:]]), 1)))


def run():
    truth = t.load_2020()
    return dict(in_sample_2020=in_sample(truth), temporal_2016=temporal(t.load_2016(), truth), temporal_2012=temporal(t.load_2012(), truth))


if __name__ == '__main__':
    res = run()
    json.dump(res, open(HERE / 'SEAM_GUARD_RESULT.json', 'w'), indent=1, sort_keys=True)
    print(json.dumps(res, indent=1))
