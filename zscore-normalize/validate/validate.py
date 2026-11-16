#!/usr/bin/env python3
"""自检 / 验收。

  --case <id> --out-dir <dir>   自检：本脚本造固定输入跑工具，核对 result.csv 与 stats.json
  --artifact <dir>              验收：**直接判 agent 产物**（result.csv + stats.json），不重跑本资产脚本
"""
import argparse, csv, json, subprocess, sys, pathlib
KNOWN_CASES = ('C01-basic', 'C02-single', 'C03-bad-column', 'C04-input-missing',
               'C05-bad-value', 'C06-empty-input')
ap = argparse.ArgumentParser()
ap.add_argument('--case', default='C01-basic')
ap.add_argument('--out-dir')
ap.add_argument('--artifact', help='验收模式：agent 产物目录（含 result.csv 与 stats.json）')
a = ap.parse_args()
if a.artifact:
    import pathlib as _pl, csv as _csv
    d = _pl.Path(a.artifact)
    f_csv, f_stats = d / 'result.csv', d / 'stats.json'
    if not f_csv.is_file() or not f_stats.is_file():
        print(json.dumps({'mode': 'artifact', 'ok': False,
                          'why': f'产物缺失：{[str(x) for x in (f_csv, f_stats) if not x.is_file()]}'},
                         ensure_ascii=False)); sys.exit(1)
    zs = [r['zscore'] for r in _csv.DictReader(f_csv.open(encoding='utf-8'))]
    st = json.loads(f_stats.read_text(encoding='utf-8'))
    ok = zs == ['-1.224745', '0.000000', '1.224745'] and st == {'n': 3, 'mean': 2.0, 'pstdev': 0.816497}
    print(json.dumps({'mode': 'artifact', 'ok': ok, 'zscore': zs, 'stats': st}, ensure_ascii=False))
    sys.exit(0 if ok else 1)
if a.case not in KNOWN_CASES:
    print(f'未知用例 id：{a.case}；可用：{", ".join(KNOWN_CASES)}', file=sys.stderr); sys.exit(2)
if not a.out_dir:
    print('需要 --out-dir（自检）或 --artifact（验收）', file=sys.stderr); sys.exit(2)
here = pathlib.Path(__file__).resolve().parents[1]
out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

def run(inp):
    return subprocess.run([sys.executable, str(here / 'scripts' / 'zscore.py'), '--input', str(inp),
                           '--out-dir', str(out)], capture_output=True, text=True)

if a.case == 'C01-basic':
    data = out / 'in.csv'
    data.write_text('id,value\na,1\nb,2\nc,3\n', encoding='utf-8')
    p = run(data)
    stats = json.loads((out / 'stats.json').read_text(encoding='utf-8'))
    zs = [r['zscore'] for r in csv.DictReader((out / 'result.csv').open(encoding='utf-8'))]
    exp_z = ['-1.224745', '0.000000', '1.224745']
    ok = p.returncode == 0 and stats == {'n': 3, 'mean': 2.0, 'pstdev': 0.816497} and zs == exp_z
    res = {'case': a.case, 'rc': p.returncode, 'zscore': zs, 'stats': stats, 'passed': ok}
elif a.case == 'C02-single':
    data = out / 'in2.csv'; data.write_text('id,value\na,5\n', encoding='utf-8')
    p = run(data)
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 2 and err.get('error') == 'zero_variance'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}
elif a.case == 'C04-input-missing':     # 预期错误：输入文件不存在 → 退出码 3
    p = run(out / 'nope.csv')
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 3 and err.get('error') == 'input_not_found'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}
elif a.case == 'C05-bad-value':         # 预期错误：value 含非数值 → 退出码 2 + bad_value
    data = out / 'in5.csv'; data.write_text('id,value\na,abc\n', encoding='utf-8')
    p = run(data)
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 2 and err.get('error') == 'bad_value'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}
elif a.case == 'C06-empty-input':       # 预期错误：只有表头 → 退出码 2 + empty_input
    data = out / 'in6.csv'; data.write_text('id,value\n', encoding='utf-8')
    p = run(data)
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 2 and err.get('error') == 'empty_input'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}
else:   # C03 预期错误：缺 value 列
    data = out / 'in3.csv'; data.write_text('id,val\na,1\n', encoding='utf-8')
    p = run(data)
    err = json.loads((out / 'error.json').read_text(encoding='utf-8')) if (out / 'error.json').exists() else {}
    ok = p.returncode == 2 and err.get('error') == 'missing_value_column'
    res = {'case': a.case, 'rc': p.returncode, 'error': err, 'passed': ok}

(out / 'tool-checks.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: res[k] for k in ('case', 'rc', 'passed')}))
sys.exit(0 if res['passed'] else 1)
