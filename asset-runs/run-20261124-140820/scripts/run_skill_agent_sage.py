#!/usr/bin/env python3
"""用 Sage A1.5 后端跑 skill 的 agent 验收（同一 harness，只换后端）。

Sage 配置按 skill 规定顺序解析（CLI > 环境变量 SAGE_* > 宿主机 DSH 配置），
解析结果只以环境变量注入子进程，不打印、不落盘。

    python3 scripts/run_skill_agent_sage.py --skill <副本内的 skill 资产> --out-dir <run>/agent-sage/<资产>
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path("/home/dengnianchen/projects/agent_centric/.dsh/skills/sci-asset-verify-skill")


def load_sage_probe():
    spec = importlib.util.spec_from_file_location("sage_probe", SKILL_ROOT / "scripts" / "sage_probe.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--harness", default="dsh")
    ap.add_argument("--timeout", default="1500")
    a = ap.parse_args()

    sp = load_sage_probe()
    cfg, missing = sp.resolve_config(argparse.Namespace(base_url=None, model=None, api_key_env=None))
    if not cfg.get("base_url") or not cfg.get("model") or not cfg.get("api_key"):
        print(json.dumps({"status": "blocked_missing_config", "missing": missing,
                          "sources": cfg.get("sources", {})}, ensure_ascii=False))
        return 3

    env = dict(os.environ)
    env["SAGE_BASE_URL"] = cfg["base_url"]
    env["SAGE_MODEL"] = cfg["model"]
    env["SAGE_API_KEY"] = cfg["api_key"]
    cmd = [sys.executable, str(SKILL_ROOT / "scripts" / "run_skill_agent.py"),
           "--skill", a.skill, "--out-dir", a.out_dir, "--harness", a.harness,
           "--backend", "sage", "--dsh-home", "auto", "--timeout", a.timeout,
           "--json-out", a.json_out]
    print(f"[sage] 后端 {cfg['model']} @ {cfg['base_url']}（密钥经环境变量注入）", flush=True)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
