#!/usr/bin/env python3
"""把 CSV 的 value 列做 z-score 标准化，输出 result.csv + stats.json。"""
import argparse, csv, json, statistics, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    out = __import__('pathlib').Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    try:
        with open(a.input, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        (out / 'error.json').write_text(json.dumps({'error': 'input_not_found', 'path': a.input}), encoding='utf-8')
        print(f'错误：找不到输入 {a.input}', file=sys.stderr); return 3
    if not rows:
        (out / 'error.json').write_text(json.dumps({'error': 'empty_input'}), encoding='utf-8')
        print('错误：输入没有数据行', file=sys.stderr); return 2
    if 'value' not in rows[0]:
        (out / 'error.json').write_text(json.dumps({'error': 'missing_value_column'}), encoding='utf-8')
        print('错误：输入缺少 value 列', file=sys.stderr); return 2
    try:
        vals = [float(r['value']) for r in rows]
    except (TypeError, ValueError) as exc:
        (out / 'error.json').write_text(json.dumps({'error': 'bad_value', 'detail': str(exc)}), encoding='utf-8')
        print(f'错误：value 列存在非数值：{exc}', file=sys.stderr); return 2
    mean = statistics.fmean(vals)
    sd = statistics.pstdev(vals)
    if sd == 0:
        (out / 'error.json').write_text(json.dumps({'error': 'zero_variance'}), encoding='utf-8')
        print('错误：value 方差为 0，无法标准化', file=sys.stderr); return 2
    with open(out / 'result.csv', 'w', newline='', encoding='utf-8') as f:
        wtr = csv.writer(f); wtr.writerow(['id', 'zscore'])
        for r, v in zip(rows, vals):
            wtr.writerow([r.get('id', ''), f'{(v - mean) / sd:.6f}'])
    (out / 'stats.json').write_text(json.dumps({'n': len(vals), 'mean': round(mean, 6),
                                                'pstdev': round(sd, 6)}, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'n': len(vals), 'mean': round(mean, 6), 'pstdev': round(sd, 6)}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
