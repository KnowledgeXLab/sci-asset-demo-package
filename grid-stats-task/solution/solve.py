#!/usr/bin/env python3
"""参考解：读 /workspace/data/points.csv，写 /workspace/output/summary.json（只用标准库）。"""
import csv
import json
import os
from pathlib import Path

WS = Path(os.environ.get("TBS_WORKSPACE", "/workspace"))   # harbor 内固定为 /workspace
DATA = WS / "data" / "points.csv"
OUT = WS / "output" / "summary.json"


def median(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main() -> int:
    with DATA.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit("points.csv 为空")
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
    summary = {
        "count": len(rows),
        "value_mean": round(sum(vs) / len(vs), 6),
        "value_min": min(vs),
        "value_max": max(vs),
        "x_extent": [min(xs), max(xs)],
        "y_extent": [min(ys), max(ys)],
        "quadrant_counts": q,
        "value_sum": sum(vs),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写出 {OUT}：count={summary['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
