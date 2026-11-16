#!/usr/bin/env python3
"""工作流：读数据资产 → 调标准化工具 → 调插值技能 → 汇总报告。

外部资产由挂载提供：--assets-root 下应有各资产目录（<root>/<slug>/…），
对应关系见同目录 external_assets.json；缺哪个就在报告里说明并退出码 3。
"""
import argparse, csv, json, subprocess, sys
from pathlib import Path

def run(cmd, cwd=None):
    p = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets-root', required=True, help='挂载根目录（含各外部资产目录）')
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    root = Path(a.assets_root).resolve(); out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parents[1]

    # 固定目录名与同行 external_assets.json 的 target_path 一致；交付方自定的路径写死即可，不是缺陷
    need = {'data': root / 'grid-samples', 'tool': root / 'zscore-normalize', 'skill': root / 'idw-interpolate'}

    missing = {k: str(v) for k, v in need.items() if not v.is_dir()}
    if missing:
        (out / 'error.json').write_text(json.dumps({'error': 'external_asset_missing', 'missing': missing},
                                                   ensure_ascii=False), encoding='utf-8')
        print(f'错误：外部资产缺失 {missing}', file=sys.stderr)
        return 3

    points = need['data'] / 'payload' / 'points.csv'
    rc1, o1, e1 = run([str(need['tool'] / 'scripts' / 'zscore.py'), '--input', str(points),
                       '--out-dir', str(out / 'tool')])
    if rc1 != 0:
        (out / 'error.json').write_text(json.dumps({'error': 'tool_failed', 'rc': rc1, 'stderr': e1}), encoding='utf-8')
        print(f'错误：工具失败 rc={rc1} {e1}', file=sys.stderr); return 4

    rc2, o2, e2 = run([str(need['skill'] / 'scripts' / 'run.py'), '--points', str(points),
                       '--targets', str(here / 'targets.csv'), '--out-dir', str(out / 'skill'), '--power', '2'])
    if rc2 != 0:
        (out / 'error.json').write_text(json.dumps({'error': 'skill_failed', 'rc': rc2, 'stderr': e2}), encoding='utf-8')
        print(f'错误：技能失败 rc={rc2} {e2}', file=sys.stderr); return 5

    stats = json.loads((out / 'tool' / 'stats.json').read_text(encoding='utf-8'))
    with open(out / 'skill' / 'interpolated.csv', encoding='utf-8') as f:
        interp = list(csv.DictReader(f))
    est = [float(r['value_est']) for r in interp]
    report = {'workflow': 'assess-workflow', 'version': '1.0.0',
              'steps': ['read_data', 'zscore_normalize', 'idw_interpolate'],
              'data_points': stats['n'], 'value_mean': stats['mean'], 'value_pstdev': stats['pstdev'],
              'targets': len(interp), 'estimate_min': round(min(est), 6), 'estimate_max': round(max(est), 6),
              # 只记声明的相对位置，不写挂载的绝对路径——否则产物换机器后不可复现比对
              'external_assets': {k: v.name for k, v in need.items()}}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'steps': len(report['steps']), 'targets': len(interp)}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
