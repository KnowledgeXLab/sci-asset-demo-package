#!/usr/bin/env python3
"""自检：读本资产 payload 与 metadata，核对记录数、列名、值与元数据一致。"""
import argparse, csv, json, sys, pathlib
ap = argparse.ArgumentParser(); ap.add_argument('--case', default='C01'); ap.add_argument('--out-dir', default='out')
a = ap.parse_args()
here = pathlib.Path(__file__).resolve().parents[1]
meta = json.loads((here / 'metadata.json').read_text(encoding='utf-8'))
with open(here / 'payload' / 'points.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
vals = [float(r['value']) for r in rows]
import math

def formula_max_dev(rows, meta):
    """按 metadata.formula 复算每行 value，返回最大绝对偏差（无声明则 None）。"""
    f = meta.get('formula') or {}
    if not f.get('expr'):
        return None
    base = int(f.get('i_base', 1))
    ns = {'sin': math.sin, 'cos': math.cos, 'sqrt': math.sqrt, 'pi': math.pi, 'exp': math.exp}
    worst = 0.0
    for k, r in enumerate(rows, start=base):
        ns.update({'x': int(r['x']), 'y': int(r['y']), 'i': k})
        worst = max(worst, abs(eval(f['expr'], {'__builtins__': {}}, ns) - float(r['value'])))  # noqa: S307
    return worst

xs = sorted({int(r['x']) for r in rows}); ys = sorted({int(r['y']) for r in rows})
cells = {(int(r['x']), int(r['y'])) for r in rows}
g = meta.get('grid') or {}
expected_cells = {(x, y) for x in range(g.get('nx', 0)) for y in range(g.get('ny', 0))} if g.get('nx') else set()
ALL = [
    {'name': 'record_count', 'expected': meta['records'], 'actual': len(rows)},
    {'name': 'columns', 'expected': meta['columns'], 'actual': list(rows[0].keys())},
    {'name': 'value_min', 'expected': meta['value_range'][0], 'actual': min(vals)},
    {'name': 'value_max', 'expected': meta['value_range'][1], 'actual': max(vals)},
    {'name': 'row_order_stable', 'expected': 'p001', 'actual': rows[0]['id']},
    # 声明与实体一致：bbox 与网格完整性（这两项曾漏检，导致"10×10 网格"实际 y 到 10）
    {'name': 'bbox_x', 'expected': meta['bbox']['x'], 'actual': [xs[0], xs[-1]]},
    {'name': 'bbox_y', 'expected': meta['bbox']['y'], 'actual': [ys[0], ys[-1]]},
    {'name': 'grid_complete', 'expected': True,
     'actual': (cells == expected_cells) if expected_cells else True},
    # 声明公式可复算：按 metadata.formula 逐行重算，最大偏差需在容差内
    {'name': 'formula_recompute', 'expected': True,
     'actual': (lambda dev: False if dev is None else
                dev <= float((meta.get('formula') or {}).get('tolerance', 1e-6)))(formula_max_dev(rows, meta))},
]
BY_CASE = {
    'C01-metadata': ['record_count', 'value_min', 'value_max'],
    'C02-structure': ['columns', 'row_order_stable'],
    'C03-read': ['record_count', 'columns'],
    'C04-extent': ['bbox_x', 'bbox_y', 'grid_complete'],   # 声明空间范围/网格完整性
    'C05-formula': ['formula_recompute'],                  # 声明公式逐行复算
}
want = BY_CASE.get(a.case, [c['name'] for c in ALL])
checks = [c for c in ALL if c['name'] in want]
ok = all(c['expected'] == c['actual'] for c in checks)
out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
(out / 'data-checks.json').write_text(json.dumps(
    {'case': a.case, 'checks': checks, 'passed': ok,
     'formula_max_dev': formula_max_dev(rows, meta)}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'case': a.case, 'checks': len(checks), 'passed': ok}))
sys.exit(0 if ok else 1)
