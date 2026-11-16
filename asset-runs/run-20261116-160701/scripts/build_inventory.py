import hashlib, json, os, pathlib
PKG = pathlib.Path('/home/dengnianchen/projects/agent_centric/examples/demo-assets-1.0.0')
RUN = PKG / 'asset-runs' / 'run-20261116-160701'
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''): h.update(b)
    return h.hexdigest()
recipes = {
 'grid-samples': {'type': 'data', 'key': ['asset.json', 'metadata.json', 'payload/points.csv', 'readme.md', 'usage/readme.md', 'validate/cases.json', 'validate/validate.py', 'validate/readme.md', 'LICENSE'], 'rel': [], 'cases': ['C01-metadata','C02-structure','C03-read','C04-extent','C05-formula']},
 'zscore-normalize': {'type': 'tool', 'key': ['asset.json', 'tool.json', 'scripts/zscore.py', 'readme.md', 'usage/readme.md', 'validate/cases.json', 'validate/validate.py', 'validate/readme.md', 'LICENSE'], 'rel': [], 'cases': ['C01-basic','C02-single','C03-bad-column','C04-input-missing','C05-bad-value','C06-empty-input']},
 'idw-interpolate': {'type': 'skill', 'key': ['asset.json', 'SKILL.md', 'scripts/run.py', 'usage/readme.md', 'validate/cases.json', 'validate/validate.py', 'validate/readme.md', 'LICENSE', 'validate/cases/C01/points.csv', 'validate/cases/C01/targets.csv', 'validate/cases/C02/points.csv', 'validate/cases/C02/targets.csv', 'validate/cases/C05/points.csv', 'validate/cases/C05/targets.csv'], 'rel': [], 'cases': ['C01-hits','C02-equidistant','C03-missing-file','C04-bad-column','C05-power-one','C06-bad-power']},
 'assess-workflow': {'type': 'skill', 'key': ['asset.json', 'external_assets.json', 'SKILL.md', 'scripts/run_workflow.py', 'targets.csv', 'usage/readme.md', 'validate/cases.json', 'validate/validate.py', 'validate/readme.md', 'LICENSE'], 'rel': ['sciasset://2026ZD000042/demo/data/grid-samples','sciasset://2026ZD000042/demo/tool/zscore-normalize','sciasset://2026ZD000042/demo/skill/idw-interpolate'], 'cases': ['C01-end-to-end','C02-missing-external']},
}
assets = []
for name, r in recipes.items():
    d = PKG / name
    aj = json.loads((d / 'asset.json').read_text(encoding='utf-8'))
    files = []
    for k in r['key']:
        p = d / k
        files.append({'path': f'{name}/{k}', 'exists': p.is_file(),
                      'sha256': sha(p) if p.is_file() else None,
                      'size_bytes': p.stat().st_size if p.is_file() else None})
    rel = []
    if (d / 'external_assets.json').is_file():
        for a in json.loads((d/'external_assets.json').read_text(encoding='utf-8'))['assets']:
            rel.append({'asset_id': a['asset_id'], 'asset_version': a['asset_version'],
                        'target_path': a['target_path'], 'required': a.get('required', True)})
    assets.append({
        'asset_id': aj['asset_id'], 'asset_type': aj['asset_type'], 'asset_version': aj['asset_version'],
        'name': aj['name'], 'lifecycle': aj['lifecycle'],
        'source_path': f'demo-assets-1.0.0/{name}',
        'entrypoint': ({'data': 'payload/points.csv（直接读取）'}.get(r['type']) or
                       ('scripts/zscore.py --input <csv> --out-dir <dir>' if name=='zscore-normalize' else 'scripts/run.py --points <csv> --targets <csv> --out-dir <dir> [--power 2]')
                       if name!='assess-workflow' else 'scripts/run_workflow.py --assets-root <本资产目录> --out-dir <dir>'),
        'interface': aj['spec']['metadata'].get('interface_type') or ('skill（SKILL.md 指令 + Python runner）'),
        'runtime': aj['spec']['metadata'].get('runtime') or 'N/A（纯数据）',
        'key_files': files,
        'declared_relations': rel,
        'given_cases': r['cases'],
        'evidence': {'envelope': 'envelope-report.json', 'selfcontained': 'selfcontained-report.json',
                     'cases': f'cases/{name}/', 'agent': (f'agent/{name}-report.json' if r['type']=='skill' else None)},
        'pending_info': [] if name != 'assess-workflow' else ['挂载外部资产的运行说明依赖使用方实现（external_assets.json 已声明 target_path）'],
    })
inv = {
 'package': {'root': str(PKG), 'name': 'demo-assets-1.0.0', 'run_id': 'run-20261116-160701',
             'package_readme': 'readme.md', 'asset_count': len(assets),
             'types': sorted({a['asset_type'] for a in assets}),
             'note': '示例资产包：project-id 2026ZD000042、提供方「示例资产提供方」、来源 urn:demo:generator 均为示例占位（包 readme 已明示），按占位处理，不计问题。'},
 'assets': assets, 'skill': {'name': 'sci-asset-verify-skill', 'version': '1.2-beta.4-dev', 'commit': 'bdf50dd'},
}
(RUN / 'inventory.json').write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding='utf-8')
print('assets', len(assets), 'files', sum(len(a['key_files']) for a in assets))
print('missing', [(a['source_path'], f['path']) for a in assets for f in a['key_files'] if not f['exists']])
