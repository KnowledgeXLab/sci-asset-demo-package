#!/usr/bin/env python3
"""verifier：只校验 /workspace/output/summary.json 的内容，不看实现方式。

判定标准（与 instruction.md 一一对应）：
1. 文件存在、是合法 JSON 对象、键集合完全等于约定集合（不多不少）
2. 类型正确（整数 / 浮点 / 二元数组 / 四键对象）
3. 数值与从 /workspace/data/points.csv 独立复算的结果一致（mean 容差 1e-6）
4. quadrant_counts 四项之和等于 count
"""
import csv
import json
import os
from pathlib import Path

WS = Path(os.environ.get("TBS_WORKSPACE", "/workspace"))      # 被测方工作区（产物在 output/ 下）
# 真值随 verifier 一起打包（separate 模式下被测方的 data/ 不一定可见，不能依赖它）
DATA = Path(os.environ.get("TBS_DATA_CSV", str(Path(__file__).parent / "data" / "points.csv")))
OUT = WS / "output" / "summary.json"
KEYS = {"count", "value_mean", "value_min", "value_max", "x_extent", "y_extent",
        "quadrant_counts", "value_sum"}
QUADS = {"Q1", "Q2", "Q3", "Q4"}
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def median(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def expected() -> dict:
    with DATA.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    vs = [int(r["value"]) for r in rows]
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
    return {"count": len(rows), "value_mean": sum(vs) / len(vs), "value_min": min(vs),
            "value_max": max(vs), "x_extent": [min(xs), max(xs)], "y_extent": [min(ys), max(ys)],
            "quadrant_counts": q, "value_sum": sum(vs)}


def main() -> int:
    check(OUT.is_file(), f"缺少产物：{OUT}")
    if not OUT.is_file():
        print("FAIL: " + "; ".join(failures))
        return 1
    try:
        got = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: summary.json 不是合法 JSON：{exc}")
        return 1
    check(isinstance(got, dict), "summary.json 顶层必须是 JSON 对象")
    if not isinstance(got, dict):
        print("FAIL: " + "; ".join(failures))
        return 1
    check(set(got) == KEYS, f"键集合不符：多 {sorted(set(got) - KEYS)}，少 {sorted(KEYS - set(got))}")

    exp = expected()
    for key in ("count", "value_min", "value_max", "value_sum"):
        check(isinstance(got.get(key), int) and not isinstance(got.get(key), bool),
              f"{key} 必须是整数，实际 {type(got.get(key)).__name__}")
        check(got.get(key) == exp[key], f"{key} 不符：期望 {exp[key]}，实际 {got.get(key)}")
    mean = got.get("value_mean")
    check(isinstance(mean, (int, float)) and not isinstance(mean, bool), "value_mean 必须是数值")
    if isinstance(mean, (int, float)) and not isinstance(mean, bool):
        check(abs(float(mean) - exp["value_mean"]) <= 1e-6,
              f"value_mean 不符：期望 {exp['value_mean']:.6f}，实际 {mean}")
    for key in ("x_extent", "y_extent"):
        val = got.get(key)
        check(isinstance(val, list) and len(val) == 2, f"{key} 必须是二元数组")
        if isinstance(val, list) and len(val) == 2:
            check(val == exp[key], f"{key} 不符：期望 {exp[key]}，实际 {val}")
    q = got.get("quadrant_counts")
    check(isinstance(q, dict) and set(q) == QUADS, "quadrant_counts 必须恰好含 Q1~Q4")
    if isinstance(q, dict):
        check(all(isinstance(v, int) and not isinstance(v, bool) for v in q.values()),
              "quadrant_counts 的值必须是整数")
        check(sum(v for v in q.values() if isinstance(v, int)) == exp["count"],
              f"quadrant_counts 之和必须等于 count={exp['count']}")
        check(q == exp["quadrant_counts"],
              f"quadrant_counts 不符：期望 {exp['quadrant_counts']}，实际 {q}")

    if failures:
        print("FAIL:")
        for f_ in failures:
            print(f"  - {f_}")
        return 1
    print("PASS: summary.json 与数据独立复算结果完全一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
