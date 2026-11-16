#!/usr/bin/env python3
"""按包内 validate/validate.py 跑全部给定用例（在副本中执行，产物写回 run 目录）。"""
import json, os, subprocess, sys, pathlib, datetime

COPY = pathlib.Path(os.environ['COPY_ROOT'])
RUN = pathlib.Path(os.environ['RUN_DIR'])
PY = sys.executable
CASES = {
    'grid-samples': ['C01-metadata', 'C02-structure', 'C03-read', 'C04-extent', 'C05-formula'],
    'zscore-normalize': ['C01-basic', 'C02-single', 'C03-bad-column', 'C04-input-missing', 'C05-bad-value', 'C06-empty-input'],
    'idw-interpolate': ['C01-hits', 'C02-equidistant', 'C03-missing-file', 'C04-bad-column', 'C05-power-one', 'C06-bad-power'],
    'assess-workflow': ['C01-end-to-end', 'C02-missing-external'],
}
results = []
for asset, cases in CASES.items():
    adir = COPY / asset
    for cid in cases:
        outdir = RUN / 'cases' / asset / cid
        outdir.mkdir(parents=True, exist_ok=True)
        cmd = [PY, str(adir / 'validate' / 'validate.py'), '--case', cid, '--out-dir', str(outdir / 'out')]
        if asset == 'assess-workflow':
            if cid == 'C01-end-to-end':
                root = adir
            else:  # 缺外部资产：给一个空目录
                root = outdir / 'empty-root'; root.mkdir(parents=True, exist_ok=True)
            cmd += ['--assets-root', str(root)]
        t0 = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(adir), env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        t1 = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        (outdir / 'stdout.txt').write_text(p.stdout, encoding='utf-8')
        (outdir / 'stderr.txt').write_text(p.stderr, encoding='utf-8')
        produced = sorted(str(x.relative_to(outdir)) for x in (outdir / 'out').rglob('*') if x.is_file()) if (outdir / 'out').is_dir() else []
        meta = {'asset': asset, 'case': cid, 'cmd': cmd, 'cwd': str(adir), 'rc': p.returncode,
                'started_at': t0, 'finished_at': t1, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip(),
                'produced': produced, 'passed': p.returncode == 0,
                'python': sys.version.split()[0]}
        (outdir / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        results.append(meta)
        print(json.dumps({k: meta[k] for k in ('asset', 'case', 'rc', 'passed', 'stdout')}, ensure_ascii=False))
(RUN / '_raw-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('TOTAL', len(results), 'PASS', sum(1 for r in results if r['passed']))
