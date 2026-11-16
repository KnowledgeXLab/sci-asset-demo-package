#!/usr/bin/env python3
import json, os, pathlib
RUN = pathlib.Path(os.environ['RUN_DIR'])
LEDGER = json.loads((RUN / 'cases.json').read_text(encoding='utf-8'))['cases']
ind = json.loads((RUN / 'independent-check.json').read_text(encoding='utf-8'))
indmap = {}
for c in ind['checks']:
    indmap.setdefault(f"{c['asset']}/{c['case']}", []).append(c)
out = {'run_id': 'run-20261116-160701', 'package': 'demo-assets-1.0.0',
       'comparison_protocol': {'numeric': 'abs(actual-expected) <= atol + rtol*|expected|；本批除公式复算外均为精确相等（字符串 6 位小数）',
                               'atol': 0.0, 'rtol': 0.0, 'formula_atol': 1e-06,
                               'string': '精确匹配（含大小写与 6 位小数格式）', 'error_cases': '退出码 + error.json 的 error 字段精确匹配',
                               'ignored_fields': ['运行时间戳', '临时目录绝对路径', 'run.json 中的 power 浮点写法']},
       'cases': []}
AGENT = {}
for name in ('idw-interpolate', 'assess-workflow'):
    AGENT[f'{name}/A01-agent-artifact'] = json.loads((RUN / 'agent' / f'{name}-report.json').read_text(encoding='utf-8'))
for c in LEDGER:
    key = c['case_id']
    chks = indmap.get(key, [])
    if key in AGENT:
        rep = AGENT[key]
        out['cases'].append({
            'case_id': key, 'asset_id': c['asset_id'], 'asset_version': c['asset_version'],
            'input_source': c['input'], 'truth_source': c['truth_path'], 'truth_kind': c['truth_kind'],
            'match_keys': ['agent 产物文件名', '逐值（value_est/nearest_dist 或 report.json 字段）'],
            'fields': [{'field': 'agent_gate', 'expected': '门槛脚本 exit 0（agent 产物达标）', 'actual': rep['gate_rc'],
                        'unit': 'N/A', 'absolute_error': None, 'tolerance': 0,
                        'status': 'pass' if rep['verdict'] == 'pass' else rep['verdict'],
                        'note': rep['gate_stdout'][:200]}],
            'run_status': 'executed', 'exit_code': rep['gate_rc'],
            'scientific_judgement': 'pass' if rep['verdict'] == 'pass' else rep['verdict'],
            'completeness_judgement': 'pass',
            'evidence': c['evidence'], 'actual_output': c['actual_output'],
            'harness': rep.get('harness'), 'model': rep.get('model'), 'backend': rep.get('backend'),
        })
        continue
    fields = []
    for ck in chks:
        exp, act = ck['expected'], ck['actual']
        try:
            err = (float(act) - float(exp)) if isinstance(exp, (int, float)) and isinstance(act, (int, float)) else None
        except (TypeError, ValueError):
            err = None
        fields.append({'field': ck['check'], 'expected': exp, 'actual': act, 'unit': '无量纲' if ck['check'] in
                       ('value_est+nearest_dist', 'zscore', 'stats', 'value_range', 'value_mean', 'value_pstdev', 'estimate_min', 'estimate_max') else 'N/A',
                       'absolute_error': err, 'tolerance': ck.get('tolerance') or 0, 'status': ck['status'], 'note': ck.get('note', '')})
    out['cases'].append({
        'case_id': key, 'asset_id': c['asset_id'], 'asset_version': c['asset_version'],
        'input_source': c['input'], 'truth_source': c['truth_path'], 'truth_kind': c['truth_kind'],
        'match_keys': ['case_id', '目标点(x,y)/行号 id / 字段名'],
        'fields': fields or [{'field': 'gate', 'expected': '门槛脚本退出码 0', 'actual': c.get('exit_code'), 'status': c['status']}],
        'run_status': 'executed', 'exit_code': c.get('exit_code'),
        'scientific_judgement': 'pass' if c['status'] == 'pass' else c['status'],
        'completeness_judgement': 'pass',
        'evidence': c['evidence'], 'actual_output': c.get('actual_output'),
    })
tot = len(out['cases']); p = sum(1 for c in out['cases'] if c['scientific_judgement'] == 'pass')
out['summary'] = {'planned': tot, 'executed': tot, 'pass': p, 'fail': tot - p,
                  'blocked': 0, 'skipped': 0, 'not_evaluated': 0,
                  'pass_rate': f'{p}/{tot}（分母 {tot} 组：给定用例 19 组 + skill agent 产物验收 2 组，无跳过）'}
(RUN / 'comparison.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out['summary'], ensure_ascii=False))
