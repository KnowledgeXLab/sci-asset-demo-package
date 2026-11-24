#!/usr/bin/env python3
"""部署/直连探针：为每个可执行资产留一次最小业务调用 + 一次预期失败调用。

无 MCP 端点（包内没有声明），按 skill 第 3 步记「CLI/库直连验证」，
请求、响应、退出码与运行时版本写进 <run>/deployment/probes/<资产>/probe.json。

    python3 scripts/deploy_probe.py --work-copy <WC> --run <run>
"""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile

SKILL_ROOT = pathlib.Path("/home/dengnianchen/projects/agent_centric/.dsh/skills/sci-asset-verify-skill")
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from _version import stamp as _stamp  # noqa: E402


def call(cmd, cwd, env):
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)
    return {"argv": [str(c) for c in cmd], "exit_code": p.returncode,
            "stdout": p.stdout.strip()[-1500:], "stderr": p.stderr.strip()[-600:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-copy", required=True)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    wc = pathlib.Path(a.work_copy).resolve()
    run = pathlib.Path(a.run).resolve()
    out_root = run / "deployment" / "probes"
    out_root.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="deploy-probe-"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", LC_ALL="C")

    probes = []

    # zscore-normalize：CLI 直连
    z = wc / "zscore-normalize"
    inp = tmp / "z-in.csv"
    inp.write_text("id,value\n1,1\n2,2\n3,3\n", encoding="utf-8")
    probes.append({"asset": "zscore-normalize", "interface": "CLI",
                   "entry": "scripts/zscore.py",
                   "ok": call([sys.executable, "scripts/zscore.py", "--input", str(inp),
                              "--out-dir", str(tmp / "z-ok")], z, env),
                   "expected_failure": call([sys.executable, "scripts/zscore.py", "--input",
                                            str(tmp / "no-such.csv"), "--out-dir", str(tmp / "z-bad")], z, env),
                   "failure_expect": "rc=3 + error.json(input_not_found)"})

    # linear-model：权重随包，CLI 推理（模型部署的 CLI 形态）
    m = wc / "linear-model"
    win = m / "model" / "weights.json"
    probes.append({"asset": "linear-model", "interface": "CLI（库内推理）",
                   "entry": "model/predict.py",
                   "weights": {"path": "model/weights.json",
                               "sha256": hashlib.sha256(win.read_bytes()).hexdigest(),
                               "size_bytes": win.stat().st_size},
                   "ok": call([sys.executable, "model/predict.py", "--input", "payload/samples.csv",
                              "--out-dir", str(tmp / "m-ok")], m, env),
                   "expected_failure": call([sys.executable, "model/predict.py", "--input",
                                            str(tmp / "no-such.csv"), "--out-dir", str(tmp / "m-bad")], m, env),
                   "failure_expect": "rc=3 + error.json(input_not_found)"})

    # idw-interpolate：skill 内含 CLI
    i = wc / "idw-interpolate"
    probes.append({"asset": "idw-interpolate", "interface": "CLI",
                   "entry": "scripts/run.py",
                   "ok": call([sys.executable, "scripts/run.py",
                              "--points", "validate/cases/C01/points.csv",
                              "--targets", "validate/cases/C01/targets.csv", "--power", "2",
                              "--out-dir", str(tmp / "i-ok")], i, env),
                   "expected_failure": call([sys.executable, "scripts/run.py",
                                            "--points", "validate/cases/C01/points.csv",
                                            "--targets", "validate/cases/C01/targets.csv", "--power", "0",
                                            "--out-dir", str(tmp / "i-bad")], i, env),
                   "failure_expect": "rc=2 + error.json(bad_power)"})

    # grid-summary-benchmark：评测入口
    b = wc / "grid-summary-benchmark"
    probes.append({"asset": "grid-summary-benchmark", "interface": "CLI",
                   "entry": "benchmark/run_evaluation.py",
                   "ok": call([sys.executable, "benchmark/run_evaluation.py",
                              "--submission", "benchmark/cases/good", "--out-dir", str(tmp / "b-ok")], b, env),
                   "expected_failure": call([sys.executable, "benchmark/run_evaluation.py",
                                            "--submission", str(tmp / "no-sub"), "--out-dir", str(tmp / "b-bad")], b, env),
                   "failure_expect": "score.json 记缺失、passed=false"})

    # assess-workflow：工作流（需外部资产就位，副本内已挂载）
    w = wc / "assess-workflow"
    probes.append({"asset": "assess-workflow", "interface": "CLI（工作流编排）",
                   "entry": "scripts/run_workflow.py",
                   "ok": call([sys.executable, "scripts/run_workflow.py", "--assets-root", str(w),
                              "--out-dir", str(tmp / "w-ok")], w, env),
                   "expected_failure": call([sys.executable, "scripts/run_workflow.py",
                                            "--assets-root", str(tmp), "--out-dir", str(tmp / "w-bad")], w, env),
                   "failure_expect": "rc=3 + error.json(external_asset_missing)"})

    meta = {"python": platform.python_version(), "platform": platform.platform(),
            "python_executable": sys.executable}
    for p in probes:
        d = out_root / p["asset"]
        d.mkdir(parents=True, exist_ok=True)
        p["runtime"] = meta
        (d / "probe.json").write_text(json.dumps(_stamp(p), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{p['asset']:26} ok_rc={p['ok']['exit_code']} fail_rc={p['expected_failure']['exit_code']}")

    mcp = _stamp({"tool": "deploy_probe.py", "mcp_endpoints": [],
                  "status": "not_applicable_no_such_asset",
                  "why": "包内 9 个资产的 asset.json 均未声明 MCP 端点（无 stdio/Streamable HTTP 服务）；"
                         "zscore-normalize 的 interface_type=cli，其余为 CLI/Skill/任务包，"
                         "故按 skill 第 3 步记「无 MCP 端点，采用 CLI/库直连验证」",
                  "cli_probes": [p["asset"] for p in probes],
                  "model_deployment": {"asset": "linear-model",
                                       "form": "CLI 推理（权重随包，无常驻服务）",
                                       "probe": "deployment/probes/linear-model/probe.json"}})
    (run / "deployment" / "mcp.json").write_text(json.dumps(mcp, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"deployment/ 写入 {len(probes)} 个探针 + mcp.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
