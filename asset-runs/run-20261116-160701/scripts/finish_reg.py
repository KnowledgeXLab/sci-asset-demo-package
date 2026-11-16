#!/usr/bin/env python3
import json, os, pathlib
RUN = pathlib.Path(os.environ['RUN_DIR'])
REG = RUN / 'registration'
rows = json.loads((REG / 'rows.json').read_text(encoding='utf-8'))
for r in rows['rows']:
    if r['资产名称'] == '规则网格采样点数据':
        r['时间范围'] = '静态示例快照：生成于 2026-11-14（provenance.created_time），无采集时间序列'
(REG / 'rows.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

cmp = json.loads((RUN / 'comparison.json').read_text(encoding='utf-8'))
field_ev = {
 'run_id': 'run-20261116-160701', 'package': 'demo-assets-1.0.0',
 'note': '对外发版清单不设「资产协议」「验证报告路径」列：前者只写在 asset.json 的 spec.asset_protocol，后者记录在本文件；清单「质量说明」末句已指向 validation-report.md。',
 'report': 'validation-report.md', 'comparison': 'comparison.json', 'coverage': 'coverage.json',
 'assets': {},
}
rowmap = {'run_id': 'run-20261116-160701', 'row_key': ['资产ID', '版本'], 'rows': []}
for r in rows['rows']:
    name = r['资产名称']
    field_ev['assets'][name] = {
        'asset_id': r['资产ID'], '版本': r['版本'], 'validation_report': 'validation-report.md',
        'cases_evidence': f'cases/{rows["rows"].index(r) and ""}' if False else None,
        'sources': {
            '资产摘要': 'asset.json#description', '任务|操作标签': 'asset.json#task_classes[].id',
            '科学对象': 'asset.json#spec.domain_attributes.scientific_objects',
            '资产提供单位': 'asset.json#provenance.provider[].name', '来源|产出方式': 'asset.json#provenance.source',
            '格式|接口': 'asset.json#spec.metadata + spec.artifacts[].media_type',
            '规模|数量': 'asset.json#spec.metadata + validate/cases.json',
            '空间|坐标|实验条件': 'asset.json#spec.domain_attributes.spatial',
            '输入说明/输出说明': '资产 readme/SKILL.md + scripts/*.py + validate/readme.md',
            '运行环境|资源要求': 'asset.json#spec.metadata.runtime + 脚本 import 清单',
            '评价指标|验收条件': '本次 cases.json / comparison.json（run-20261116-160701）',
            '质量说明': 'validation-report.md + comparison.json',
            '资产关联': 'external_assets.json（仅 assess-workflow 有）',
        },
    }
    rowmap['rows'].append({'资产ID': r['资产ID'], '版本': r['版本'], '资产目录': {'规则网格采样点数据': 'grid-samples', 'z-score 标准化工具': 'zscore-normalize',
                        'IDW 反距离权重插值技能': 'idw-interpolate', '示例评估工作流': 'assess-workflow'}[name],
                        'internal_number': None, 'asset_name': name})
# 补每条资产的用例证据路径
by_asset = {}
for c in cmp['cases']:
    a = c['asset_id'].split('/')[-1]
    by_asset.setdefault(a, []).append(c['case_id'])
for entry in rowmap['rows']:
    ev = field_ev['assets'][entry['asset_name']]
    ev['cases_evidence'] = [f'cases/{entry["资产目录"]}/', 'cases.json', 'comparison.json', 'independent-check.json']
    ev['case_ids'] = by_asset.get(entry['资产目录'], [])
(REG / 'field-evidence.json').write_text(json.dumps(field_ev, ensure_ascii=False, indent=2), encoding='utf-8')
(REG / 'asset-row-map.json').write_text(json.dumps(rowmap, ensure_ascii=False, indent=2), encoding='utf-8')
print('ok', len(rowmap['rows']))
