#!/usr/bin/env python3
"""自检/验收：IDW 在已知点处还原观测值、等距点取均值。

两种模式：
  --case C01-hits --out-dir <dir>        自检：用随包交付的 validate/cases/<case>/ 输入跑一遍
  --case C03-missing-file|C04-bad-column 预期错误分支：核对退出码与 error.json 的 error 字段
  --artifact <agent 输出目录>            验收：**直接判 agent 产物** interpolated.csv，不重跑本资产脚本
"""
import argparse, csv, json, subprocess, sys, pathlib

EXPECT = {
    'C01-hits': {'rows': 2, 'value_est': ['10.000000', '20.000000'], 'nearest_dist': ['0.000000', '0.000000']},
    'C02-equidistant': {'rows': 1, 'value_est': ['15.000000'], 'nearest_dist': ['5.000000']},
    'C05-power-one': {'rows': 1, 'value_est': ['12.500000'], 'nearest_dist': ['2.500000']},
}
CASE_DIR = {'C01-hits': 'C01', 'C02-equidistant': 'C02', 'C05-power-one': 'C05'}   # case 名 → 随包交付的输入目录
POWER = {'C05-power-one': '1'}                     # 非默认幂次的用例
ERROR_CASES = {                                    # 文档承诺的错误分支（退出码 + error.json 的 error 字段）
    'C03-missing-file': {'rc': 3, 'error': 'input_not_found'},
    'C04-bad-column': {'rc': 2, 'error': 'bad_columns'},
    'C06-bad-power': {'rc': 2, 'error': 'bad_power'},
}

def judge(csv_path: pathlib.Path, case: str) -> dict:
    exp = EXPECT[case]
    if not csv_path.is_file():
        return {'ok': False, 'why': f'产物不存在：{csv_path}'}
    rows = list(csv.DictReader(csv_path.open(encoding='utf-8')))
    if 'value_est' not in (rows[0].keys() if rows else []):
        return {'ok': False, 'why': f'产物缺 value_est 列：{list(rows[0].keys()) if rows else "空文件"}'}
    vals = [r['value_est'] for r in rows]
    dists = [r.get('nearest_dist') for r in rows]
    ok_v = vals == exp['value_est']
    ok_d = dists == exp['nearest_dist']          # 输出合同里的 nearest_dist 也要判，否则写成常数也能过
    ok = len(rows) == exp['rows'] and ok_v and ok_d
    why = ''
    if not ok_v:
        why = f'value_est 与期望不符：期望 {exp["value_est"]}，实际 {vals}'
    elif not ok_d:
        why = f'nearest_dist 与期望不符：期望 {exp["nearest_dist"]}，实际 {dists}'
    elif len(rows) != exp['rows']:
        why = f'行数不符：期望 {exp["rows"]}，实际 {len(rows)}'
    return {'ok': ok, 'rows': len(rows), 'value_est': vals, 'nearest_dist': dists,
            'expected': exp, 'why': why}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', default='C01-hits')
    ap.add_argument('--out-dir', help='自检模式：输出目录')
    ap.add_argument('--artifact', help='验收模式：agent 产物目录（内含 interpolated.csv）')
    a = ap.parse_args()
    here = pathlib.Path(__file__).resolve().parents[1]
    known = list(EXPECT) + list(ERROR_CASES)
    if a.case not in known:
        print(f'未知用例 id：{a.case}；可用：{", ".join(known)}', file=sys.stderr)
        return 2
    case = a.case

    if case in ERROR_CASES:                         # 预期错误分支
        exp = ERROR_CASES[case]
        out = pathlib.Path(a.out_dir or '/tmp/idw-err'); out.mkdir(parents=True, exist_ok=True)
        if case == 'C06-bad-power':
            args = ['--points', str(here / 'validate' / 'cases' / 'C01' / 'points.csv'),
                    '--targets', str(here / 'validate' / 'cases' / 'C01' / 'targets.csv'), '--power', '0']
        elif case == 'C03-missing-file':
            args = ['--points', str(out / 'nope.csv'), '--targets', str(here / 'validate' / 'cases' / 'C01' / 'targets.csv')]
        else:                                       # 目标点缺 x 列
            bad = out / 'bad-targets.csv'; bad.write_text('y\n1\n', encoding='utf-8')
            args = ['--points', str(here / 'validate' / 'cases' / 'C01' / 'points.csv'), '--targets', str(bad)]
        proc = subprocess.run([sys.executable, str(here / 'scripts' / 'run.py'), *args,
                               '--out-dir', str(out / case)], capture_output=True, text=True)
        ep = out / case / 'error.json'
        err = json.loads(ep.read_text(encoding='utf-8')).get('error') if ep.is_file() else None
        ok = proc.returncode == exp['rc'] and err == exp['error']
        print(json.dumps({'mode': 'self-check', 'case': case, 'rc': proc.returncode,
                          'error': err, 'expected': exp, 'ok': ok}, ensure_ascii=False))
        return 0 if ok else 1

    if a.artifact:                                  # 验收：只判产物
        res = {'mode': 'artifact', 'case': case, **judge(pathlib.Path(a.artifact) / 'interpolated.csv', case)}
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res['ok'] else 1

    if not a.out_dir:
        print('需要 --out-dir（自检）或 --artifact（验收）', file=sys.stderr); return 2
    src = here / 'validate' / 'cases' / CASE_DIR[case]
    out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(here / 'scripts' / 'run.py'),
                           '--points', str(src / 'points.csv'), '--targets', str(src / 'targets.csv'),
                           '--out-dir', str(out), '--power', POWER.get(case, '2')], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({'mode': 'self-check', 'case': case, 'rc': proc.returncode,
                          'stderr': proc.stderr[-300:], 'passed': False}, ensure_ascii=False))
        return 1
    res = {'mode': 'self-check', 'case': case, **judge(out / 'interpolated.csv', case)}
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
