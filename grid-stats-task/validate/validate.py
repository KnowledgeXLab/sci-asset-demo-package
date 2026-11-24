#!/usr/bin/env python3
"""无 docker 的离线自检：在本目录内临时 workspace 跑一次"参考解 + verifier"。

用途：给出 harbor 之外的快速反馈（有 docker 时仍以 tests/test.sh + oracle/nop 为准）。
  python3 validate/validate.py            # 默认拿 solution/solve.py 当被测实现
  python3 validate/validate.py --no-solution   # 只跑 verifier（预期失败，用于确认门槛有效）
"""
import argparse
import ast as pyast
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]


def expected_summary() -> dict:
    """与 tests/test_summary.py 同口径的期望值（本地复算，避免复制粘贴漂移）。"""
    with (TASK / "tests" / "data" / "points.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    vs = [int(r["value"]) for r in rows]

    def median(v):
        sv = sorted(v)
        n = len(sv)
        return sv[n // 2] if n % 2 else (sv[n // 2 - 1] + sv[n // 2]) / 2

    mx, my = median(xs), median(ys)
    q = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for x, y in zip(xs, ys):
        if x <= mx and y <= my:
            q["Q1"] += 1
        elif x > mx and y <= my:
            q["Q2"] += 1
        elif x <= mx and y > my:
            q["Q3"] += 1
        else:
            q["Q4"] += 1
    return {"count": len(rows), "value_mean": round(sum(vs) / len(vs), 6), "value_min": min(vs),
            "value_max": max(vs), "x_extent": [min(xs), max(xs)], "y_extent": [min(ys), max(ys)],
            "quadrant_counts": q, "value_sum": sum(vs)}


def check_instruction_example(problems: list[str]) -> None:
    """instruction.md 里给出的示例 JSON 必须与实际期望值一致（防"示例写错、被测方照抄"）。"""
    text = (TASK / "instruction.md").read_text(encoding="utf-8")
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not m:
        problems.append("instruction.md 里没有找到示例 JSON")
        return
    try:
        example = json.loads(m.group(1))
    except Exception as exc:  # noqa: BLE001
        problems.append(f"instruction.md 示例 JSON 不可解析：{exc}")
        return
    exp = expected_summary()
    if set(example) != set(exp):
        problems.append(f"instruction 示例键集合与产物不一致：多 {sorted(set(example) - set(exp))}，"
                        f"少 {sorted(set(exp) - set(example))}")
    for key, want in exp.items():
        got = example.get(key)
        if key == "value_mean":
            if not isinstance(got, (int, float)) or abs(float(got) - want) > 1e-6:
                problems.append(f"instruction 示例 {key}={got} 与期望 {want} 不符")
        elif got != want:
            problems.append(f"instruction 示例 {key}={got} 与期望 {want} 不符")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-solution", action="store_true", help="不跑参考解，直接验证门槛会失败")
    args = ap.parse_args(argv)

    problems: list[str] = []
    check_instruction_example(problems)
    if problems:
        print("instruction.md 与判分口径不一致：")
        for x in problems:
            print(f"  - {x}")
        return 1
    print("OK：instruction.md 示例与 verifier 期望值一致")

    with tempfile.TemporaryDirectory(prefix="grid-stats-validate-") as tmp:
        ws = Path(tmp)
        (ws / "data").mkdir()
        (ws / "output").mkdir()
        shutil.copy2(TASK / "environment" / "data" / "points.csv", ws / "data" / "points.csv")
        env = dict(os.environ, TBS_WORKSPACE=str(ws), PYTHONDONTWRITEBYTECODE="1")
        rc_sol = 0
        if not args.no_solution:
            rc_sol = subprocess.run([sys.executable, str(TASK / "solution" / "solve.py")], env=env).returncode
        rc_t = subprocess.run([sys.executable, str(TASK / "tests" / "test_summary.py")], env=env).returncode
        print(f"\n参考解 rc={rc_sol}；verifier rc={rc_t}")
        if args.no_solution:
            ok = rc_t != 0
            print("OK：缺产物时 verifier 判不通过（门槛有效）" if ok else "ERROR：缺产物却判通过，门槛失效")
            return 0 if ok else 1
        ok = rc_sol == 0 and rc_t == 0
        print("OK：参考解通过自带 verifier" if ok else "ERROR：参考解未通过 verifier")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
