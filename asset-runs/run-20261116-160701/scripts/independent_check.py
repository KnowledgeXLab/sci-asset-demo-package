#!/usr/bin/env python3
"""独立复算：不依赖包内脚本，用包内实体与声明重新算真值并比对本次实际输出。"""
import csv, hashlib, json, math, os, pathlib, statistics, sys

COPY = pathlib.Path(os.environ['COPY_ROOT'])
RUN = pathlib.Path(os.environ['RUN_DIR'])
out = {'checks': [], 'skill': None}

def add(asset, case, name, expected, actual, status, note='', tol=None):
    out['checks'].append({'asset': asset, 'case': case, 'check': name,
                          'expected': expected, 'actual': actual,
                          'tolerance': tol, 'status': status, 'note': note})

# ---------- A. grid-samples：声明 vs 实体 ----------
g = COPY / 'grid-samples'
aj = json.loads((g / 'asset.json').read_text(encoding='utf-8'))
meta = json.loads((g / 'metadata.json').read_text(encoding='utf-8'))
raw = (g / 'payload' / 'points.csv').read_bytes()
sha = hashlib.sha256(raw).hexdigest()
art = {a['id']: a for a in aj['spec']['artifacts']}
add('grid-samples', 'C03-read', 'sha256(payload/points.csv)', art['points']['sha256'], sha,
    'pass' if sha == art['points']['sha256'] == meta['sha256'] else 'fail')
add('grid-samples', 'C03-read', 'size_bytes', art['points']['size_bytes'], len(raw),
    'pass' if art['points']['size_bytes'] == len(raw) else 'fail')
rows = list(csv.DictReader((g / 'payload' / 'points.csv').open(encoding='utf-8')))
add('grid-samples', 'C01-metadata', 'records', meta['records'], len(rows),
    'pass' if len(rows) == meta['records'] == aj['spec']['metadata']['record_count'] else 'fail')
add('grid-samples', 'C02-structure', 'columns', meta['columns'], list(rows[0].keys()),
    'pass' if list(rows[0].keys()) == meta['columns'] else 'fail')
add('grid-samples', 'C02-structure', 'first_row_id', 'p001', rows[0]['id'],
    'pass' if rows[0]['id'] == 'p001' else 'fail')
xs = sorted({int(r['x']) for r in rows}); ys = sorted({int(r['y']) for r in rows})
add('grid-samples', 'C04-extent', 'bbox.x', meta['bbox']['x'], [xs[0], xs[-1]],
    'pass' if [xs[0], xs[-1]] == meta['bbox']['x'] == aj['spec']['domain_attributes']['spatial']['bbox']['x'] else 'fail')
add('grid-samples', 'C04-extent', 'bbox.y', meta['bbox']['y'], [ys[0], ys[-1]],
    'pass' if [ys[0], ys[-1]] == meta['bbox']['y'] == aj['spec']['domain_attributes']['spatial']['bbox']['y'] else 'fail')
cells = {(int(r['x']), int(r['y'])) for r in rows}
exp_cells = {(x, y) for x in range(meta['grid']['nx']) for y in range(meta['grid']['ny'])}
add('grid-samples', 'C04-extent', 'grid_cells_complete', len(exp_cells), len(cells),
    'pass' if cells == exp_cells else 'fail', note='集合完全一致且无重复' if cells == exp_cells else '存在缺失或多余格子')
vals = [float(r['value']) for r in rows]
add('grid-samples', 'C01-metadata', 'value_range', meta['value_range'], [min(vals), max(vals)],
    'pass' if [min(vals), max(vals)] == meta['value_range'] else 'fail')
f = meta['formula']; ns0 = {'sin': math.sin, 'cos': math.cos, 'sqrt': math.sqrt, 'pi': math.pi, 'exp': math.exp}
worst = 0.0
for k, r in enumerate(rows, start=int(f.get('i_base', 1))):
    ns = dict(ns0, x=int(r['x']), y=int(r['y']), i=k)
    worst = max(worst, abs(eval(f['expr'], {'__builtins__': {}}, ns) - float(r['value'])))
add('grid-samples', 'C05-formula', 'formula_max_abs_dev', f"<= {f['tolerance']}", f'{worst:.3e}',
    'pass' if worst <= float(f['tolerance']) else 'fail', tol=f['tolerance'])

# ---------- B. zscore-normalize：解析解独立复算 ----------
def z_expect(vs):
    m = statistics.fmean(vs); sd = statistics.pstdev(vs)
    return m, sd, [f'{(v - m) / sd:.6f}' for v in vs]
m, sd, zexp = z_expect([1.0, 2.0, 3.0])
zdir = RUN / 'cases' / 'zscore-normalize' / 'C01-basic' / 'out'
zact = [r['zscore'] for r in csv.DictReader((zdir / 'result.csv').open(encoding='utf-8'))]
st = json.loads((zdir / 'stats.json').read_text(encoding='utf-8'))
add('zscore-normalize', 'C01-basic', 'zscore', zexp, zact, 'pass' if zact == zexp else 'fail')
exp_stats = {'n': 3, 'mean': round(m, 6), 'pstdev': round(sd, 6)}
add('zscore-normalize', 'C01-basic', 'stats', exp_stats, st, 'pass' if st == exp_stats else 'fail')
for cid, code, rc in [('C02-single', 'zero_variance', 2), ('C03-bad-column', 'missing_value_column', 2),
                      ('C04-input-missing', 'input_not_found', 3), ('C05-bad-value', 'bad_value', 2),
                      ('C06-empty-input', 'empty_input', 2)]:
    d = RUN / 'cases' / 'zscore-normalize' / cid / 'out'
    e = json.loads((d / 'error.json').read_text(encoding='utf-8')) if (d / 'error.json').is_file() else {}
    sub = json.loads((d / 'tool-checks.json').read_text(encoding='utf-8'))
    add('zscore-normalize', cid, 'error_semantics', {'rc': rc, 'error': code},
        {'rc': sub['rc'], 'error': e.get('error')},
        'pass' if sub['rc'] == rc and e.get('error') == code else 'fail')

# ---------- C. idw-interpolate：解析解 ----------
def idw(points, targets, power=2.0):
    res = []
    for tx, ty in targets:
        num = den = 0.0; dn = float('inf')
        hit = None
        for px, py, pv in points:
            d = math.hypot(tx - px, ty - py); dn = min(dn, d)
            if d == 0:
                hit = pv; break
            w = 1.0 / d ** power; num += w * pv; den += w
        v = hit if hit is not None else num / den
        res.append((f'{tx:g}', f'{ty:g}', f'{v:.6f}', f'{dn:.6f}'))
    return res
P = [(0.0, 0.0, 10.0), (10.0, 0.0, 20.0)]
for cid, targets, power in [('C01-hits', [(0, 0), (10, 0)], 2.0),
                            ('C02-equidistant', [(5, 0)], 2.0),
                            ('C05-power-one', [(2.5, 0)], 1.0)]:
    d = RUN / 'cases' / 'idw-interpolate' / cid / 'out' / 'interpolated.csv'
    act = [tuple(r[c] for c in ('x', 'y', 'value_est', 'nearest_dist')) for r in csv.DictReader(d.open(encoding='utf-8'))]
    exp = idw(P, targets, power)
    add('idw-interpolate', cid, 'value_est+nearest_dist', exp, act, 'pass' if act == exp else 'fail',
        note=f'independent IDW power={power}')
for cid, code, rc in [('C03-missing-file', 'input_not_found', 3), ('C04-bad-column', 'bad_columns', 2),
                      ('C06-bad-power', 'bad_power', 2)]:
    d = RUN / 'cases' / 'idw-interpolate' / cid / 'out' / cid
    e = json.loads((d / 'error.json').read_text(encoding='utf-8')) if (d / 'error.json').is_file() else {}
    add('idw-interpolate', cid, 'error_semantics', {'rc': rc, 'error': code}, {'error': e.get('error')},
        'pass' if e.get('error') == code else 'fail')

# ---------- D. assess-workflow：独立复算三步结果 ----------
wd = RUN / 'cases' / 'assess-workflow' / 'C01-end-to-end' / 'out'
rep = json.loads((wd / 'report.json').read_text(encoding='utf-8'))
tg = [(float(r['x']), float(r['y'])) for r in csv.DictReader((COPY / 'assess-workflow' / 'targets.csv').open(encoding='utf-8'))]
pts = [(float(r['x']), float(r['y']), float(r['value'])) for r in rows]
est = [float(v) for _, _, v, _ in idw(pts, tg, 2.0)]
add('assess-workflow', 'C01-end-to-end', 'data_points', 100, rep.get('data_points'), 'pass' if rep.get('data_points') == 100 else 'fail')
add('assess-workflow', 'C01-end-to-end', 'targets', 5, rep.get('targets'), 'pass' if rep.get('targets') == 5 else 'fail')
add('assess-workflow', 'C01-end-to-end', 'steps', ['read_data', 'zscore_normalize', 'idw_interpolate'], rep.get('steps'),
    'pass' if rep.get('steps') == ['read_data', 'zscore_normalize', 'idw_interpolate'] else 'fail')
add('assess-workflow', 'C01-end-to-end', 'value_mean', round(statistics.fmean(vals), 6), rep.get('value_mean'),
    'pass' if rep.get('value_mean') == round(statistics.fmean(vals), 6) else 'fail')
add('assess-workflow', 'C01-end-to-end', 'value_pstdev', round(statistics.pstdev(vals), 6), rep.get('value_pstdev'),
    'pass' if rep.get('value_pstdev') == round(statistics.pstdev(vals), 6) else 'fail')
add('assess-workflow', 'C01-end-to-end', 'estimate_min', round(min(est), 6), rep.get('estimate_min'),
    'pass' if rep.get('estimate_min') == round(min(est), 6) else 'fail')
add('assess-workflow', 'C01-end-to-end', 'estimate_max', round(max(est), 6), rep.get('estimate_max'),
    'pass' if rep.get('estimate_max') == round(max(est), 6) else 'fail')
add('assess-workflow', 'C01-end-to-end', 'external_assets_relative',
    {'data': 'grid-samples', 'tool': 'zscore-normalize', 'skill': 'idw-interpolate'}, rep.get('external_assets'),
    'pass' if rep.get('external_assets') == {'data': 'grid-samples', 'tool': 'zscore-normalize', 'skill': 'idw-interpolate'} else 'fail',
    note='产物只记声明相对位置，不含挂载绝对路径')

bad = [c for c in out['checks'] if c['status'] != 'pass']
out['summary'] = {'checks': len(out['checks']), 'pass': len(out['checks']) - len(bad), 'fail': len(bad)}
(RUN / 'independent-check.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out['summary'], ensure_ascii=False))
for c in bad: print('FAIL', c)
