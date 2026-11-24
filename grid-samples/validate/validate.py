#!/usr/bin/env python3
"""自检：读本资产 payload 与 metadata，核对记录数、列名、值与元数据一致。"""
import argparse, ast, csv, json, sys, pathlib
ap = argparse.ArgumentParser(); ap.add_argument('--case', default='C01-metadata'); ap.add_argument('--out-dir', default='out')
a = ap.parse_args()
here = pathlib.Path(__file__).resolve().parents[1]
meta = json.loads((here / 'metadata.json').read_text(encoding='utf-8'))
with open(here / 'payload' / 'points.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
vals = [float(r['value']) for r in rows]
import math

# ---- 受限表达式求值：只允许算术、常量、白名单函数与变量 x/y/i ----
# 替代 eval()：metadata.json 来自第三方时，eval 可以执行任意代码（`__import__('os').system(...)`）
ALLOWED_FUNCS = {'sin': math.sin, 'cos': math.cos, 'sqrt': math.sqrt, 'exp': math.exp}
ALLOWED_CONSTS = {'pi': math.pi, 'e': math.e}
ALLOWED_VARS = {'x', 'y', 'i'}
ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
                 ast.Call, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                 ast.USub, ast.UAdd, ast.FloorDiv)


def safe_eval(expr: str, variables: dict) -> float:
    """按白名单求值；出现任何白名单外语法/名称就抛 ValueError（不静默放过）。"""
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as exc:
        raise ValueError(f'表达式语法错误：{exc}') from exc
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise ValueError(f'表达式含不允许的语法：{type(node).__name__}')
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise ValueError(f'表达式含不允许的函数调用：{ast.unparse(node.func)}')
            if node.keywords:
                raise ValueError('表达式不支持关键字参数')
        if isinstance(node, ast.Name) and node.id not in ALLOWED_VARS \
                and node.id not in ALLOWED_FUNCS and node.id not in ALLOWED_CONSTS:
            raise ValueError(f'表达式含未定义名称：{node.id}')
    env = dict(ALLOWED_CONSTS, **ALLOWED_FUNCS)
    for k in ALLOWED_VARS:
        if k in variables:
            env[k] = variables[k]
    return float(eval(compile(tree, '<expr>', 'eval'), {'__builtins__': {}}, env))  # noqa: S307


def formula_max_dev(rows, meta):
    """按 metadata.formula 复算每行 value，返回最大绝对偏差（无声明则 None）。"""
    f = meta.get('formula') or {}
    if not f.get('expr'):
        return None
    base = int(f.get('i_base', 1))
    worst = 0.0
    for k, r in enumerate(rows, start=base):
        val = safe_eval(f['expr'], {'x': int(r['x']), 'y': int(r['y']), 'i': k})
        worst = max(worst, abs(val - float(r['value'])))
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
if a.case not in BY_CASE:
    print(f'未知用例 id：{a.case}；可用：{", ".join(BY_CASE)}', file=sys.stderr)
    sys.exit(2)
want = BY_CASE[a.case]
checks = [c for c in ALL if c['name'] in want]
ok = all(c['expected'] == c['actual'] for c in checks)
out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
(out / 'data-checks.json').write_text(json.dumps(
    {'case': a.case, 'checks': checks, 'passed': ok,
     'formula_max_dev': formula_max_dev(rows, meta)}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'case': a.case, 'checks': len(checks), 'passed': ok}))
sys.exit(0 if ok else 1)
