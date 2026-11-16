#!/usr/bin/env python3
"""反距离权重（IDW）插值：按已知点对目标点估值。"""
import argparse, csv, json, math, sys
from pathlib import Path

def read_points(path):
    """读点表；目标点只需要 x,y（没有 value 列时按 0 处理）。"""
    with open(path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return [(float(r['x']), float(r['y']), float(r.get('value') or 0)) for r in rows]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--points', required=True)
    ap.add_argument('--targets', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--power', type=float, default=2.0)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    if not a.power > 0:                                  # 幂次必须为正，否则估值无意义
        (out / 'error.json').write_text(json.dumps({'error': 'bad_power', 'power': a.power}), encoding='utf-8')
        print(f'错误：--power 必须为正数（当前 {a.power}）', file=sys.stderr); return 2
    try:
        pts = read_points(a.points); tgts = read_points(a.targets)
    except FileNotFoundError as e:
        (out / 'error.json').write_text(json.dumps({'error': 'input_not_found', 'detail': str(e)}), encoding='utf-8')
        print(f'错误：找不到输入（{e}）', file=sys.stderr); return 3
    except (KeyError, ValueError) as e:
        (out / 'error.json').write_text(json.dumps({'error': 'bad_columns', 'detail': str(e)}), encoding='utf-8')
        print(f'错误：输入列不合法（{e}）', file=sys.stderr); return 2
    if not pts:
        (out / 'error.json').write_text(json.dumps({'error': 'no_source_points'}), encoding='utf-8')
        print('错误：没有已知点', file=sys.stderr); return 2
    with open(out / 'interpolated.csv', 'w', newline='', encoding='utf-8') as f:
        wtr = csv.writer(f); wtr.writerow(['x', 'y', 'value_est', 'nearest_dist'])
        for tx, ty, _ in tgts:
            num = den = 0.0; dn = float('inf')
            for px, py, pv in pts:
                d = math.hypot(tx - px, ty - py); dn = min(dn, d)
                if d == 0:
                    num, den = pv, 1.0; break
                wgt = 1.0 / d ** a.power
                num += wgt * pv; den += wgt
            wtr.writerow([f'{tx:g}', f'{ty:g}', f'{num / den:.6f}', f'{dn:.6f}'])
    (out / 'run.json').write_text(json.dumps({'mode': 'idw', 'power': a.power,
                                              'source_points': len(pts), 'targets': len(tgts)}, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'source_points': len(pts), 'targets': len(tgts)}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
