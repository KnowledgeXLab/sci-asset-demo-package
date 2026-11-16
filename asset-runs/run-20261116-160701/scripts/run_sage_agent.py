#!/usr/bin/env python3
"""用宿主 DSH 凭据里的 Sage 后端（不打印密钥）跑 skill agent 的 Sage 附加测试。"""
import os, pathlib, re, subprocess, sys, json
cfg = json.loads(pathlib.Path(os.environ['RUN_DIR'], 'sage-config.json').read_text(encoding='utf-8'))
cred = (pathlib.Path.home() / '.dsh' / '.credentials.yaml').read_text(encoding='utf-8')
m = re.search(r'INKSTONE_API_KEY\s*:\s*["\']?([^"\'\n]+)', cred)
key = (m.group(1).strip() if m else '')
env = dict(os.environ)
env['SAGE_BASE_URL'] = cfg['base_url']
env['SAGE_MODEL'] = cfg['model']
if key:
    env['SAGE_API_KEY'] = key
env['PYTHONDONTWRITEBYTECODE'] = '1'
skill_dir, out_dir, rep = sys.argv[1], sys.argv[2], sys.argv[3]
cmd = [sys.executable, os.environ['SKILL_SCRIPT'], '--skill', skill_dir, '--out-dir', out_dir,
       '--harness', 'dsh', '--backend', 'sage', '--json-out', rep]
p = subprocess.run(cmd, env=env, capture_output=True, text=True)
print(p.stdout[-3000:]); print(p.stderr[-3000:], file=sys.stderr)
sys.exit(p.returncode)
