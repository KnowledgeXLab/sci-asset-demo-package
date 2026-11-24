#!/usr/bin/env python3
"""grid-stats-trajectory 校验：结构、时间序、结果自洽、证据链。

  python validate/validate.py --case C01-structure
  python validate/validate.py --artifact <含 trajectory.json 的目录>    # 验收第三方轨迹
退出码：0 通过 / 1 不通过 / 2 用法错误
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROLES = {"user", "agent", "environment"}
TYPES = {"message", "plan", "tool_call", "tool_result", "verification", "final"}
QUADS = {"Q1", "Q2", "Q3", "Q4"}
EXPECT = {"count": 67, "value_sum": 394, "value_mean": 5.880597,
          "x_extent": [0, 9], "y_extent": [0, 9],
          "quadrant_counts": {"Q1": 17, "Q2": 17, "Q3": 17, "Q4": 16}}


def check_structure(t: dict) -> list[str]:
    problems = []
    if t.get("format") != "ATIF":
        problems.append(f"format 应为 ATIF，实际 {t.get('format')}")
    steps = t.get("steps") or []
    if len(steps) < 3:
        problems.append(f"步数过少：{len(steps)}")
    prev = ""
    for i, s in enumerate(steps, 1):
        if s.get("role") not in ROLES:
            problems.append(f"第 {i} 步 role 非法：{s.get('role')}")
        if s.get("type") not in TYPES:
            problems.append(f"第 {i} 步 type 非法：{s.get('type')}")
        ts = str(s.get("timestamp") or "")
        if not ts:
            problems.append(f"第 {i} 步缺 timestamp")
        elif prev and ts <= prev:
            problems.append(f"第 {i} 步时间未严格递增（{prev} → {ts}）")
        prev = ts or prev
    if (t.get("run") or {}).get("status") != "success":
        problems.append(f"run.status 应为 success，实际 {(t.get('run') or {}).get('status')}")
    return problems


def check_outcome(t: dict) -> list[str]:
    problems = []
    final = next((s for s in reversed(t.get("steps") or []) if s.get("type") == "final"), None)
    if final is None:
        return ["缺少 final 步"]
    rs = final.get("result_summary") or {}
    for k, want in EXPECT.items():
        got = rs.get(k)
        if k == "value_mean":
            if not isinstance(got, (int, float)) or abs(float(got) - want) > 1e-6:
                problems.append(f"value_mean 不符：期望 {want}，实际 {got}")
        elif got != want:
            problems.append(f"{k} 不符：期望 {want}，实际 {got}")
    q = rs.get("quadrant_counts")
    if not isinstance(q, dict) or set(q) != QUADS:
        problems.append("quadrant_counts 必须恰好含 Q1~Q4")
    elif sum(q.values()) != rs.get("count"):
        problems.append(f"quadrant_counts 之和 {sum(q.values())} ≠ count {rs.get('count')}")
    return problems


def check_evidence(t: dict) -> list[str]:
    problems = []
    ver = [s for s in (t.get("steps") or []) if s.get("type") == "verification"]
    if not ver:
        return ["缺少 verification 步（轨迹必须带验证证据）"]
    v = ver[-1]
    if not v.get("verifier"):
        problems.append("verification 步缺 verifier 名称")
    if str(v.get("result")) != "pass":
        problems.append(f"verification 结果应为 pass，实际 {v.get('result')}")
    rw = v.get("reward")
    if not isinstance(rw, (int, float)) or abs(float(rw) - 1.0) > 1e-9:
        problems.append(f"verification reward 应为 1，实际 {rw}")
    if not v.get("evidence"):
        problems.append("verification 步缺证据位置（evidence）")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="C01-structure")
    ap.add_argument("--artifact", help="含 trajectory.json 的目录")
    ap.add_argument("--out-dir", help="兼容其它资产校验脚本的通用参数（本校验不写中间产物）")
    a = ap.parse_args()
    known = ["C01-structure", "C02-outcome-consistency", "C03-evidence-linked", "C04-broken-step"]
    if a.case not in known:
        print(f"未知用例 id：{a.case}；可用：{', '.join(known)}", file=sys.stderr)
        return 2

    path = (pathlib.Path(a.artifact) / "trajectory.json") if a.artifact else (HERE / "trajectory.json")
    if not path.is_file():
        print(json.dumps({"ok": False, "why": f"找不到 {path}"}, ensure_ascii=False))
        return 1
    t = json.loads(path.read_text(encoding="utf-8"))

    if a.case == "C01-structure":
        problems = check_structure(t)
    elif a.case == "C02-outcome-consistency":
        problems = check_outcome(t)
    elif a.case == "C03-evidence-linked":
        problems = check_evidence(t)
    else:  # C04：删掉 verification 步后必须判不通过（证明门槛不是恒绿）
        broken = json.loads(json.dumps(t))
        broken["steps"] = [s for s in broken["steps"] if s.get("type") != "verification"]
        problems = check_evidence(broken)
        ok = bool(problems)
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok,
                          "problems": problems}, ensure_ascii=False))
        return 0 if ok else 1

    ok = not problems
    print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok,
                      "steps": len(t.get("steps") or []), "problems": problems}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
