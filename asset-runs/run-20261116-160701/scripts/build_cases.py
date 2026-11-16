#!/usr/bin/env python3
import json, os, pathlib
RUN = pathlib.Path(os.environ['RUN_DIR'])
PKG = RUN.parents[1]
raw = {f"{r['asset']}/{r['case']}": r for r in json.loads((RUN / '_raw-results.json').read_text(encoding='utf-8'))}
ind = json.loads((RUN / 'independent-check.json').read_text(encoding='utf-8'))
indmap = {}
for c in ind['checks']:
    indmap.setdefault(f"{c['asset']}/{c['case']}", []).append(c)
asset_info = {
 'grid-samples': ('sciasset://2026ZD000042/demo/data/grid-samples', 'data', 'grid-samples/validate/validate.py'),
 'zscore-normalize': ('sciasset://2026ZD000042/demo/tool/zscore-normalize', 'tool', 'zscore-normalize/validate/validate.py'),
 'idw-interpolate': ('sciasset://2026ZD000042/demo/skill/idw-interpolate', 'skill', 'idw-interpolate/validate/validate.py'),
 'assess-workflow': ('sciasset://2026ZD000042/demo/skill/assess-workflow', 'skill', 'assess-workflow/validate/validate.py'),
}
titles = {}
for a in asset_info:
    doc = json.loads((PKG / a / 'validate' / 'cases.json').read_text(encoding='utf-8'))
    for c in doc['cases']:
        titles[f'{a}/{c["id"]}'] = c
INPUT = {
 'grid-samples/C01-metadata': '随包 payload/points.csv + metadata.json',
 'grid-samples/C02-structure': '随包 payload/points.csv + metadata.json',
 'grid-samples/C03-read': '随包 payload/points.csv',
 'grid-samples/C04-extent': '随包 payload/points.csv + metadata.json（bbox/grid）',
 'grid-samples/C05-formula': '随包 payload/points.csv + metadata.json（formula，i 自 1 起）',
 'zscore-normalize/C01-basic': '脚本内置固定输入 id,value=a/1,b/2,c/3',
 'zscore-normalize/C02-single': '脚本内置固定输入 单条记录 id=a,value=5',
 'zscore-normalize/C03-bad-column': '脚本内置固定输入 缺 value 列 id,val=a/1',
 'zscore-normalize/C04-input-missing': '不存在的输入路径 out/nope.csv',
 'zscore-normalize/C05-bad-value': '脚本内置固定输入 value 非数值 id=a,value=abc',
 'zscore-normalize/C06-empty-input': '脚本内置固定输入 仅表头 id,value',
 'idw-interpolate/C01-hits': '随包 validate/cases/C01/{points,targets}.csv（power=2）',
 'idw-interpolate/C02-equidistant': '随包 validate/cases/C02/{points,targets}.csv（power=2）',
 'idw-interpolate/C03-missing-file': '不存在的已知点文件 + 随包 C01 targets',
 'idw-interpolate/C04-bad-column': '随包 C01 points + 临时构造的缺 x 列 targets',
 'idw-interpolate/C05-power-one': '随包 validate/cases/C05/{points,targets}.csv（--power 1）',
 'idw-interpolate/C06-bad-power': '随包 C01 输入 + --power 0',
 'assess-workflow/C01-end-to-end': '副本内已挂载 grid-samples/zscore-normalize/idw-interpolate + 本资产 targets.csv',
 'assess-workflow/C02-missing-external': '空 assets-root（不含三个外部资产目录）',
}
ledger, reg = [], []
for key, r in raw.items():
    asset, cid = key.split('/', 1)
    aid, atype, entry = asset_info[asset]
    meta = titles[key]
    chks = indmap.get(key, [])
    exp_kind = meta.get('expected_kind', 'success')
    ev = f'cases/{asset}/{cid}/'
    ledger.append({
        'case_id': f'{asset}/{cid}', 'asset_id': aid, 'asset_version': '1.0.0', 'asset_type': atype,
        'entrypoint': entry, 'input': INPUT[key],
        'expected_kind': exp_kind, 'truth_kind': ('declared' if asset == 'grid-samples' else
                                                  ('analytic' if exp_kind == 'success' else 'protocol-error')),
        'truth_path': (f'{asset}/metadata.json' if asset == 'grid-samples' else
                       (f'{asset}/validate/cases.json' if exp_kind == 'success' else f'{asset}/validate/readme.md')),
        'comparison': '逐字段精确相等；数值按字符串 6 位小数比对；公式复算按绝对容差 1e-6',
        'threshold_source': (f'{asset}/validate/readme.md 判定口径' if asset != 'assess-workflow' else 'assess-workflow/validate/readme.md + validate.py 检查项'),
        'status': 'pass' if r['passed'] else 'fail',
        'exit_code': r['rc'], 'command': ' '.join(r['cmd']), 'started_at': r['started_at'],
        'actual_output': ev + 'out/', 'evidence': [ev + 'meta.json', ev + 'stdout.txt', ev + 'stderr.txt'],
        'independent_checks': [{'check': c['check'], 'expected': c['expected'], 'actual': c['actual'], 'status': c['status']} for c in chks],
        'note': '' if r['passed'] else 'rc 非 0',
    })
    passed_n = sum(1 for c in chks if c['status'] == 'pass')
    reg.append({
        '用例编号': f'{asset}/{cid}', '资产名称': {'grid-samples': '规则网格采样点数据', 'zscore-normalize': 'z-score 标准化工具',
                                              'idw-interpolate': 'IDW 反距离权重插值技能', 'assess-workflow': '示例评估工作流'}[asset],
        '关联资产及检查点': f'{asset}；检查点：' + '、'.join(c['check'] for c in chks),
        '资产版本': '1.0.0', '用例名称': meta['title'], '用例来源': '资产自带给定用例（validate/cases.json）',
        '用例类型': f'{atype}/{meta.get("kind", "")}', '前置条件': 'Python ≥3.10（仅标准库）；在原始包的工作副本内执行',
        '输入或Prompt': INPUT[key], '执行入口': ' '.join(r['cmd']),
        '预期结果': json.dumps({c['check']: c['expected'] for c in chks}, ensure_ascii=False) if chks else meta['title'],
        '真值类型': '声明值（asset.json/metadata.json）' if asset == 'grid-samples' else ('解析解/独立复算' if exp_kind == 'success' else '协议约定错误码'),
        '真值来源': (f'{asset}/metadata.json' if asset == 'grid-samples' else 'index: independent-check.json（独立复算）' if exp_kind == 'success' else f'{asset}/validate/readme.md 错误语义'),
        '比较规则': '精确相等；数值 6 位小数比对；公式复算绝对容差 1e-6',
        '验收阈值及依据': (f'公式最大偏差 ≤ 1e-06（metadata.formula.tolerance）' if asset == 'grid-samples' else
                     '解析解逐值相等（validate/readme.md 门槛）' if exp_kind == 'success' else '退出码与 error.json 字段精确匹配（validate/readme.md 门槛）'),
        '实际输出': f'{ev}out/（stdout: {r["stdout"][:120]}）',
        '执行状态': 'executed', '验证结论': 'pass' if r['passed'] else 'fail',
        '误差或检查结果': f'{passed_n}/{len(chks)} 项独立检查通过；进程退出码 {r["rc"]}',
        '证据与报告': ev, '备注': '',
    })

# agent 验收用例（skill 产物）
for name, label in [('idw-interpolate', 'IDW 反距离权重插值技能'), ('assess-workflow', '示例评估工作流')]:
    rep = json.loads((RUN / 'agent' / f'{name}-report.json').read_text(encoding='utf-8'))
    art = {'idw-interpolate': 'interpolated.csv（x,y,value_est,nearest_dist）', 'assess-workflow': 'report.json'}[name]
    ledger.append({
        'case_id': f'{name}/A01-agent-artifact', 'asset_id': asset_info[name][0], 'asset_version': '1.0.0',
        'asset_type': 'skill', 'entrypoint': f'{name}/validate/validate.py --artifact <agent 产物目录>',
        'input': 'validate/readme.md 的提示词模板（agent 自选参数与输出路径）',
        'expected_kind': 'success', 'truth_kind': 'artifact-gate', 'truth_path': f'{name}/validate/readme.md',
        'comparison': '门槛脚本直接判 agent 产物（不重跑资产脚本）', 'threshold_source': f'{name}/validate/readme.md 通过门槛',
        'status': 'pass' if rep['verdict'] == 'pass' else rep['verdict'],
        'exit_code': rep['gate_rc'], 'command': rep['gate_cmd'],
        'actual_output': f'agent/{name}/', 'evidence': [f'agent/{name}-report.json', f'agent/{name}/']})
    reg.append({
        '用例编号': f'{name}/A01-agent-artifact', '资产名称': label, '关联资产及检查点': f'{name}；检查点：agent 产物达标（{art}）',
        '资产版本': '1.0.0', '用例名称': f'agent 产物验收：{art}', '用例来源': 'skill 验收要求（validate/readme.md 通过门槛）',
        '用例类型': 'skill/agent-artifact', '前置条件': f'harness=DSH headless（readme 建议），隔离 DSH_HOME；skill 目录={name}',
        '输入或Prompt': '按 validate/readme.md 的提示词模板执行，产物写入 agent 工作目录',
        '执行入口': rep['gate_cmd'], '预期结果': {'idw-interpolate': 'value_est=[10.000000,20.000000]、nearest_dist=[0.000000,0.000000]',
                                              'assess-workflow': 'data_points=100、targets=5、steps 三步、estimate_min<estimate_max'}[name],
        '真值类型': '解析解/产物门槛', '真值来源': f'{name}/validate/readme.md', '比较规则': '门槛脚本对 agent 产物逐项判定，退出码 0 为通过',
        '验收阈值及依据': 'value_est_exact=0 且 nearest_dist 逐值相等' if name == 'idw-interpolate' else 'report.json 四项检查全部成立',
        '实际输出': rep['gate_stdout'][:300], '执行状态': 'executed', '验证结论': 'pass' if rep['verdict'] == 'pass' else rep['verdict'],
        '误差或检查结果': f'agent 进程 rc={rep["agent_rc"]}，门槛 rc={rep["gate_rc"]}',
        '证据与报告': f'agent/{name}-report.json', '备注': 'nested DSH 首次因沙箱拒绝写 profile，自动改用隔离 DSH_HOME 后重试成功',
    })

(RUN / 'cases.json').write_text(json.dumps({'run_id': 'run-20261116-160701', 'cases': ledger}, ensure_ascii=False, indent=2), encoding='utf-8')
(RUN / 'registration' / 'cases.json').write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding='utf-8')
print('ledger', len(ledger), 'reg', len(reg))
