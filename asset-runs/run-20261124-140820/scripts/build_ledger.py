#!/usr/bin/env python3
"""汇总本次核验的台账：inventory.json / cases.json / comparison.json / usage.md。

数据来源：工作副本里的资产实体与声明、本次 run 内各 case 的执行记录
（cases-selfcheck.json、harbor-run-report.json、agent/*-report.json），不读包内历史批次。

    python3 scripts/build_ledger.py --work-copy <WC> --run <run>
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL_ROOT = pathlib.Path("/home/dengnianchen/projects/agent_centric/.dsh/skills/sci-asset-verify-skill")
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from _version import stamp as _stamp  # noqa: E402

# 每个资产的用途/边界说明（来自包内 readme、SKILL.md、asset.json，人工汇总）
USAGE = {
    "grid-samples": {
        "purpose": "10×10 规则网格上的 100 个采样点（x、y、value），用于示例统计与插值的输入数据。",
        "boundary": "示例规模数据，仅覆盖 0–9 的整数格网；不用于真实观测精度评估。",
        "input": "无输入（数据资产）；读取方式为直接读取 `payload/points.csv` 与 `metadata.json`。",
        "output": "`payload/points.csv`（列 id,x,y,value，100 行）、`metadata.json`（record_count/columns/formula/grid/bbox）。",
        "env": "任意可读 CSV/JSON 的环境；数据本身为 UTF-8。",
        "entry": "`cat payload/points.csv`；自检 `python3 validate/validate.py --case C01-metadata --out-dir <dir>`",
    },
    "zscore-normalize": {
        "purpose": "把 CSV 中 `value` 列按总体标准差（pstdev）做 z-score 标准化，并输出统计量。",
        "boundary": "单列数值标准化；方差为 0（单条记录）按错误处理，不做平滑。",
        "input": "CSV，必需列 `value`（可另有 `id`）；`--input <csv>`。",
        "output": "`result.csv`（原列 + `zscore`，6 位小数）与 `stats.json`（n/mean/pstdev）；失败时写 `error.json` 并以 rc=2/3 退出。",
        "env": "Python ≥3.10，仅标准库；无网络。",
        "entry": "`python3 scripts/zscore.py --input <csv> --out-dir <out>`；自检 `python3 validate/validate.py --case C01-basic --out-dir <dir>`",
    },
    "idw-interpolate": {
        "purpose": "反距离权重（IDW）插值：按已知散点估测目标点取值，并给出最近邻距离。",
        "boundary": "幂次 power>0；不考虑障碍、各向异性与地统计变异函数；已知点为空或列缺失按错误返回。",
        "input": "已知点 CSV（x,y,value）与目标点 CSV（x,y）；`--points`、`--targets`、`--power`（默认 2）。",
        "output": "`interpolated.csv`（x,y,value_est,nearest_dist，6 位小数）；失败写 `error.json`（input_not_found/bad_columns/bad_power/no_source_points）。",
        "env": "Python ≥3.10，仅标准库；不需要容器。",
        "entry": "`python3 scripts/run.py --points <p.csv> --targets <t.csv> --power 2 --out-dir <out>`；agent 验收 `python3 validate/validate.py --case C01-hits --artifact <产物目录>`",
    },
    "assess-workflow": {
        "purpose": "把 grid-samples 数据、zscore-normalize 工具与 idw-interpolate 技能串成「读数据 → 标准化 → 插值」三步工作流，输出汇总报告。",
        "boundary": "固定三步顺序；三个外部资产必须按 `external_assets.json` 挂到本资产目录内，否则以 rc=3 报 external_asset_missing。",
        "input": "本资产目录（含三个外部资产软链/副本）+ `targets.csv`（5 个目标点）。",
        "output": "`report.json`（steps、data_points、value_mean/pstdev、targets、estimate_min/max、external_assets）；缺外部资产时 `error.json` + rc=3。",
        "env": "Python ≥3.10，仅标准库；需外部资产就位。",
        "entry": "`python3 scripts/run_workflow.py --assets-root <本资产目录> --out-dir <out>`；自检需 `--assets-root`：`python3 validate/validate.py --case C01-end-to-end --out-dir <dir> --assets-root <本资产目录>`",
    },
    "linear-model": {
        "purpose": "确定性二维线性回归模型（prediction = 1.0 + 0.5·x + 0.25·y），权重随包，纯标准库推理。",
        "boundary": "仅两特征线性外推，无不确定度估计；输入缺 `x`/`y` 列按错误返回。",
        "input": "CSV，必需列 `x`、`y`，可选 `id`；`--input <csv>`。",
        "output": "`predictions.csv`（id,x,y,prediction，6 位小数）；失败写 `error.json` 并以 rc=2/3 退出。",
        "env": "Python ≥3.10，仅标准库；无需 GPU。",
        "entry": "`python3 model/predict.py --input <csv> --out-dir <out>`；自检 `python3 validate/validate.py --case C01-predict --out-dir <dir>`",
    },
    "python-runtime": {
        "purpose": "示例资产所需的最小可复现运行环境声明：Python ≥3.10、仅标准库、无网络、1 CPU / 1 GB。",
        "boundary": "只声明并自检环境；不含科学计算能力，也不做第三方依赖安装。",
        "input": "无数据输入；`environment/requirements.lock` 声明依赖（当前为空）。",
        "output": "`runtime-report.json`（ok、python 版本、标准库可用性、third_party_present）。",
        "env": "linux 容器（Dockerfile 基镜像 Python 3.12，python_requires ≥3.10），1 CPU / 1024 MB / 无网络 / 0 GPU。",
        "entry": "`python3 environment/runtime_check.py --out-dir <out>`；自检 `python3 validate/validate.py --case C01-runtime-ok --out-dir <dir>`",
    },
    "grid-stats-task": {
        "purpose": "harbor（terminal-bench-science）格式任务：把 67 个网格采样点汇总成确定性 JSON 摘要，由独立 verifier 逐字段核对。",
        "boundary": "单一确定性任务；oracle trial 期望 reward=1、nop trial 期望 reward=0；需 docker + harbor CLI 执行。",
        "input": "`environment/data/points.csv`（67 行，x,y,value）；`instruction.md` 给出字段与判定口径。",
        "output": "`/app/output/summary.json`（count/value_sum/value_mean/x_extent/y_extent/quadrant_counts）；verifier 写 `/logs/verifier/reward.txt`。",
        "env": "docker（environment/Dockerfile）+ harbor CLI 0.27.0；verifier 独立环境（environment_mode=separate）。",
        "entry": "`harbor run -p grid-stats-task -a oracle|nop`；离线快检 `python3 validate/validate.py [--no-solution]`",
    },
    "grid-stats-trajectory": {
        "purpose": "grid-stats-task 的一次成功运行轨迹（ATIF 格式，6 步）：计划 → 工具调用 → 结果 → 验证（reward=1）→ 结论。",
        "boundary": "记录单次成功运行；不覆盖失败路径；结果只对该 task 与同一输入成立。",
        "input": "无运行输入；`trajectory.json` 内含每一步的 role/type/时间与工具调用。",
        "output": "`trajectory.json`（format=ATIF、steps=6、result_summary：count 67 / value_sum 394 / quadrant_counts）。",
        "env": "任意 JSON 读取环境；校验仅需 Python ≥3.10。",
        "entry": "`python3 validate/validate.py --case C01-structure`；第三方轨迹 `python3 validate/validate.py --artifact <含 trajectory.json 的目录>`",
    },
    "grid-summary-benchmark": {
        "purpose": "基于 grid-stats-task 的可复现评测定义：字段精确匹配 0.8 + 产物自洽 0.2，阈值 1.0，含参考答案与两个样例产物。",
        "boundary": "只评 summary.json 的 7 个字段与两条自洽约束；不做科学合理性判断。",
        "input": "提交产物目录（含 `summary.json`）；`benchmark/run_evaluation.py --submission <dir> --out-dir <dir>`。",
        "output": "`score.json`（score、passed、breakdown、problems）；缺产物时 problems 记录缺失且 passed=false。",
        "env": "Python ≥3.10，仅标准库。",
        "entry": "`python3 benchmark/run_evaluation.py --submission <dir> --out-dir <dir>`；自检 `python3 validate/validate.py --case C01-score-good --out-dir <dir>`",
    },
}


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-copy", required=True)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    wc = pathlib.Path(a.work_copy).resolve()
    run = pathlib.Path(a.run).resolve()

    selfcheck = json.loads((run / "cases-selfcheck.json").read_text(encoding="utf-8"))
    harbor = json.loads((run / "harbor-run-report.json").read_text(encoding="utf-8"))
    rec_by = {(r["asset"], r["case_id"]): r for r in selfcheck["results"]}

    assets = []
    for d in sorted(p for p in wc.iterdir() if p.is_dir() and (p / "asset.json").is_file()):
        env = json.loads((d / "asset.json").read_text(encoding="utf-8"))
        spec = env.get("spec") or {}
        key_files = []
        for art in spec.get("artifacts") or []:
            uri = art.get("uri") or ""
            p = d / uri
            if p.is_file():
                key_files.append({"path": f"{d.name}/{uri}", "role": art.get("role"),
                                  "media_type": art.get("media_type"),
                                  "size_bytes": p.stat().st_size, "sha256": sha256(p)})
        ext = []
        ej = d / "external_assets.json"
        if ej.is_file():
            ext = [{"asset_id": x.get("asset_id"), "asset_version": x.get("asset_version"),
                    "target_path": x.get("target_path"), "required": x.get("required", True),
                    "media_type": x.get("media_type")}
                   for x in json.loads(ej.read_text(encoding="utf-8")).get("assets", [])]
        cases = json.loads((d / "validate" / "cases.json").read_text(encoding="utf-8")).get("cases", [])
        execs = []
        for c in cases:
            r = rec_by.get((d.name, c["id"]))
            if r:
                execs.append({"case_id": c["id"], "status": r["status"],
                              "evidence": r.get("evidence")})
        assets.append({
            "asset_dir": d.name,
            "asset_id": env.get("asset_id"),
            "asset_type": env.get("asset_type"),
            "asset_version": env.get("asset_version"),
            "lifecycle": env.get("lifecycle"),
            "name": env.get("name"),
            "source_path": str(d.relative_to(wc)),
            "entrypoints": {"asset_protocol": spec.get("asset_protocol"),
                            "validate": "validate/cases.json + validate/validate.py"},
            "key_files": key_files,
            "related_assets": ext,
            "cases": execs,
            "gaps": [],
        })

    inv = _stamp({"tool": "build_ledger.py", "run": str(run), "work_copy": str(wc),
                  "package_root": str(wc), "origin_package": str(run.parents[2]),
                  "asset_count": len(assets), "assets": assets,
                  "note": "路径均相对工作副本；原始包只写 asset-runs/<run_id>/"})
    (run / "inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- cases.json（每 case 一条，含协议要求的最小字段集）----
    ledger, comps = [], []
    for asset in assets:
        d = wc / asset["asset_dir"]
        cases = json.loads((d / "validate" / "cases.json").read_text(encoding="utf-8")).get("cases", [])
        for c in cases:
            rec = rec_by.get((asset["asset_dir"], c["id"]), {})
            is_harbor = asset["asset_dir"] == "grid-stats-task"
            if is_harbor:
                task = harbor["tasks"][0]
                oracle, nop = task["oracle"], task["nop"]
                ok = task["verdict"] == "pass"
                ledger.append({
                    "case_id": c["id"], "asset_id": asset["asset_id"], "asset_dir": asset["asset_dir"],
                    "asset_type": asset["asset_type"], "asset_version": asset["asset_version"],
                    "related_assets": [], "source": "given", "kind": "task",
                    "expected_kind": "harbor", "preconditions": "docker 可用 + harbor CLI（0.27.0，自动安装 venv）",
                    "input": "grid-stats-task/environment/data/points.csv（67 行）",
                    "entrypoint": "harbor run -p grid-stats-task -a oracle / -a nop",
                    "expected": "oracle reward=1 且 nop reward=0",
                    "truth_kind": "rule-based", "truth_path": "grid-stats-task/tests/test_summary.py",
                    "comparison": "两条 trial 的 reward 值严格等于 1/0",
                    "threshold_source": "task.toml + tests/test.sh（reward=1 通过、reward=0 失败）",
                    "actual_path": "harbor-run-report.json",
                    "execution_status": "completed",
                    "validation_status": "pass" if ok else "fail",
                    "evidence": {"oracle_dir": oracle.get("source"), "nop_dir": nop.get("source"),
                                 "report": "harbor-run-report.json"},
                })
                comps.append({
                    "case_id": c["id"], "asset": asset["asset_dir"], "asset_version": asset["asset_version"],
                    "expected": {"oracle_reward": 1.0, "nop_reward": 0.0},
                    "actual": {"oracle_reward": oracle.get("reward"), "nop_reward": nop.get("reward")},
                    "fields": [
                        {"field": "oracle_reward", "expected": 1.0, "actual": oracle.get("reward"),
                         "abs_error": abs((oracle.get("reward") or 0) - 1.0), "tolerance": 0.0,
                         "status": "pass" if oracle.get("reward") == 1.0 else "fail"},
                        {"field": "nop_reward", "expected": 0.0, "actual": nop.get("reward"),
                         "abs_error": abs(nop.get("reward") or 0.0), "tolerance": 0.0,
                         "status": "pass" if nop.get("reward") == 0.0 else "fail"}],
                    "status": "pass" if ok else "fail",
                    "evidence": "harbor/grid-stats-task/{oracle,nop}/<trial>/result.json",
                })
                continue
            out = run / "validation-run" / asset["asset_dir"] / c["id"]
            try:
                actual = json.loads((out / "stdout.log").read_text(encoding="utf-8").strip() or "{}")
            except Exception:  # noqa: BLE001
                actual = {"raw": (out / "stdout.log").read_text(encoding="utf-8")[-500:]}
            status = "pass" if rec.get("status") == "pass" else "fail"
            ledger.append({
                "case_id": c["id"], "asset_id": asset["asset_id"], "asset_dir": asset["asset_dir"],
                "asset_type": asset["asset_type"], "asset_version": asset["asset_version"],
                "related_assets": [x["asset_id"] for x in asset["related_assets"]] if asset["asset_dir"] == "assess-workflow" else [],
                "source": "given", "kind": c.get("kind"), "expected_kind": c.get("expected_kind"),
                "preconditions": ("外部资产 grid-samples/zscore-normalize/idw-interpolate 需挂到本资产目录内"
                                  if asset["asset_dir"] == "assess-workflow" else "仅标准库 Python 环境"),
                "input": c.get("title", ""),
                "entrypoint": rec.get("command", "validate/validate.py"),
                "expected": c.get("title", ""),
                "truth_kind": "analytic" if c.get("kind") == "analytic" else "rule-based",
                "truth_path": f"{asset['asset_dir']}/validate/validate.py",
                "comparison": "资产自带 validate.py 按声明口径逐项检查，退出码 0 即通过",
                "threshold_source": "validate/validate.py 内置容差（数值类 1e-6；错误类比对退出码与 error 码）",
                "actual_path": f"validation-run/{asset['asset_dir']}/{c['id']}/stdout.log",
                "execution_status": "completed",
                "validation_status": status,
                "evidence": {"stdout": f"validation-run/{asset['asset_dir']}/{c['id']}/stdout.log",
                             "stderr": f"validation-run/{asset['asset_dir']}/{c['id']}/stderr.log"},
            })
            comps.append({
                "case_id": c["id"], "asset": asset["asset_dir"], "asset_version": asset["asset_version"],
                "expected": {"expected_kind": c.get("expected_kind"), "title": c.get("title")},
                "actual": actual, "status": status,
                "fields": [{"field": "gate", "expected": "validate.py rc=0", "actual": f"rc={rec.get('exit_code')}",
                            "status": status}],
                "evidence": f"validation-run/{asset['asset_dir']}/{c['id']}/stdout.log",
            })

    # ---- skill 的 agent 验收（A01）：同一 harness 起独立进程，门槛判 agent 产物 ----
    for name, rel in (("idw-interpolate", "agent/idw-interpolate-report.json"),
                      ("assess-workflow", "agent/assess-workflow-report.json")):
        rep = json.loads((run / rel).read_text(encoding="utf-8"))
        env = json.loads((wc / name / "asset.json").read_text(encoding="utf-8"))
        ok = rep["verdict"] == "pass"
        cid = "A01-agent-acceptance"
        ledger.append({
            "case_id": cid, "asset_id": env["asset_id"], "asset_dir": name,
            "asset_type": env["asset_type"], "asset_version": env["asset_version"],
            "related_assets": ([x["asset_id"] for x in assets if x["asset_dir"] == name][0] and
                               [x["asset_id"] for x in json.loads((wc / name / "external_assets.json").read_text(encoding="utf-8"))["assets"]]
                               if (wc / name / "external_assets.json").is_file() else []),
            "source": "supplemental-agent",
            "kind": "agent-acceptance", "expected_kind": "success",
            "preconditions": "DSH（headless profile，隔离 DSH_HOME）+ 默认 provider/model；skill 目录只读、产物写 out-dir",
            "input": rep["cmd_head"][-1],
            "entrypoint": "scripts/run_skill_agent.py --harness dsh + validate/validate.py --artifact",
            "expected": "agent 产物通过 validate/validate.py --artifact 门槛（rc=0）",
            "truth_kind": "rule-based",
            "truth_path": f"{name}/validate/validate.py --artifact",
            "comparison": "对 agent 产物（不是重跑脚本）执行验收门槛，退出码 0 即通过",
            "threshold_source": "validate/readme.md「通过门槛」",
            "actual_path": rel,
            "execution_status": "completed",
            "validation_status": "pass" if ok else "fail",
            "evidence": {"report": rel, "gate_stdout": (rep.get("gate_stdout") or "")[:400],
                         "artifacts": f"agent/{name}/"},
        })
        comps.append({"case_id": cid, "asset": name, "asset_version": env["asset_version"],
                      "expected": {"gate_rc": 0}, "actual": {"gate_rc": rep["gate_rc"], "agent_rc": rep["agent_rc"]},
                      "fields": [{"field": "gate", "expected": "rc=0", "actual": f"rc={rep['gate_rc']}",
                                  "status": "pass" if ok else "fail"}],
                      "status": "pass" if ok else "fail", "evidence": rel})

    cases_doc = _stamp({"tool": "build_ledger.py", "run": str(run), "cases": ledger,
                        "summary": {"planned": len(ledger),
                                    "pass": sum(1 for c in ledger if c["validation_status"] == "pass"),
                                    "fail": sum(1 for c in ledger if c["validation_status"] == "fail")}})
    (run / "cases.json").write_text(json.dumps(cases_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    comp_doc = _stamp({"tool": "build_ledger.py", "run": str(run), "comparisons": comps,
                       "tolerance_note": "数值类容差沿用资产自带 validate.py（1e-6）；错误类比对退出码与 error 码"})
    (run / "comparison.json").write_text(json.dumps(comp_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- usage.md ----
    lines = ["# 使用说明（本次核验整理）", "",
             "路径基准：`<副本>` = 本次工作副本，字段/命令均取自各资产 `asset.json` 与包内 readme、SKILL.md。", ""]
    for asset in assets:
        u = USAGE[asset["asset_dir"]]
        lines += [f"## {asset['asset_dir']}（{asset['asset_type']}，v{asset['asset_version']}）", "",
                  f"- 资产ID：`{asset['asset_id']}`",
                  f"- 用途：{u['purpose']}",
                  f"- 适用边界：{u['boundary']}",
                  f"- 输入：{u['input']}",
                  f"- 输出：{u['output']}",
                  f"- 运行环境：{u['env']}",
                  f"- 入口/示例命令：{u['entry']}",
                  f"- 本地路径：`<副本>/{asset['asset_dir']}`"]
        if asset["related_assets"]:
            rel = "; ".join(f"`{x['asset_id']}`（v{x['asset_version']}）→ `{x['target_path']}`" for x in asset["related_assets"])
            lines.append(f"- 外部资产依赖（`external_assets.json`）：{rel}")
        lines.append("")
        lines.append("| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |")
        lines.append("|---|---|---|---|")
        for kf in asset["key_files"]:
            lines.append(f"| `{kf['path']}` | {kf['role']} | `{kf['sha256'][:16]}…` | {kf['size_bytes']} |")
        lines.append("")
    (run / "usage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"inventory: {len(assets)} 资产；cases: {len(ledger)}（pass {cases_doc['summary']['pass']} / fail {cases_doc['summary']['fail']}）；comparison: {len(comps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
