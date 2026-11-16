#!/usr/bin/env python3
"""自检 / 验收。

  --case <id> --out-dir <dir> --assets-root <dir>   自检：跑完整工作流并核对 report.json
  --artifact <dir>                                  验收：**直接判 agent 产物** report.json，不重跑
"""
import argparse, json, subprocess, sys, pathlib
KNOWN_CASES = ('C01-end-to-end', 'C02-missing-external')
ap = argparse.ArgumentParser()
ap.add_argument('--case', default='C01-end-to-end')
ap.add_argument('--out-dir')
ap.add_argument('--assets-root')
ap.add_argument('--artifact', help='验收模式：agent 产物目录（含 report.json）')
a = ap.parse_args()
if a.artifact:
    f = pathlib.Path(a.artifact) / 'report.json'
    if not f.is_file():
        print(json.dumps({'mode': 'artifact', 'ok': False, 'why': f'产物不存在：{f}'}, ensure_ascii=False)); sys.exit(1)
    rep = json.loads(f.read_text(encoding='utf-8'))
    checks = {
        'data_points': rep.get('data_points') == 100,
        'targets': rep.get('targets') == 5,
        'steps': rep.get('steps') == ['read_data', 'zscore_normalize', 'idw_interpolate'],
        'estimate_range': isinstance(rep.get('estimate_min'), (int, float)) and isinstance(rep.get('estimate_max'), (int, float))
                          and rep['estimate_min'] < rep['estimate_max'],
    }
    ok = all(checks.values())
    print(json.dumps({'mode': 'artifact', 'ok': ok, 'checks': checks, 'report': rep}, ensure_ascii=False))
    sys.exit(0 if ok else 1)
if a.case not in KNOWN_CASES:
    print(f'未知用例 id：{a.case}；可用：{", ".join(KNOWN_CASES)}', file=sys.stderr); sys.exit(2)
if not (a.out_dir and a.assets_root):
    print('需要 --out-dir + --assets-root（自检）或 --artifact（验收）', file=sys.stderr); sys.exit(2)
here = pathlib.Path(__file__).resolve().parents[1]
out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
p = subprocess.run([sys.executable, str(here / 'scripts' / 'run_workflow.py'),
                    '--assets-root', a.assets_root, '--out-dir', str(out)], capture_output=True, text=True)
if a.case == 'C01-end-to-end':
    rep = json.loads((out / 'report.json').read_text(encoding='utf-8')) if (out / 'report.json').exists() else {}
    ok = (p.returncode == 0 and rep.get('data_points') == 100 and rep.get('targets') == 5
          and rep.get('steps') == ['read_data', 'zscore_normalize', 'idw_interpolate'])
    res = {'case': a.case, 'rc': p.returncode, 'report': rep, 'passed': ok}
else:   # C02 预期错误：缺外部资产
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 3 and err.get('error') == 'external_asset_missing'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}
(out / 'workflow-checks.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'case': a.case, 'rc': p.returncode, 'passed': res['passed']}))
sys.exit(0 if res['passed'] else 1)
