#!/usr/bin/env python3
"""按 scoring-rubric.json 给 agent 产物打分。

  python benchmark/run_evaluation.py --submission <目录> --out-dir <目录>
产物：<out>/score.json —— {score, passed, metrics[], problems[]}
退出码：0 打分完成（无论分数高低）/ 2 参数或规则错误
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
RUBRIC = HERE / "benchmark" / "scoring-rubric.json"
REFERENCE = HERE / "benchmark" / "reference" / "summary.json"
TOL = 1e-6


def load(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= TOL
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    return a == b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True, help="含 summary.json 的产物目录")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    rubric, ref = load(RUBRIC), load(REFERENCE)
    sub_dir = pathlib.Path(a.submission)
    sub_file = sub_dir / "summary.json"
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    problems, metric_results = [], []
    got = load(sub_file) if sub_file.is_file() else None
    if got is None:
        problems.append(f"缺少产物：{sub_file}")

    for m in rubric["metrics"]:
        if m["type"] == "field_exact_match":
            ok_fields = [f for f in m["fields"]
                         if isinstance(got, dict) and f in got and same(got.get(f), ref.get(f))]
            ratio = len(ok_fields) / len(m["fields"])
            metric_results.append({"id": m["id"], "score": round(ratio, 6),
                                   "correct_fields": ok_fields,
                                   "wrong_fields": [f for f in m["fields"] if f not in ok_fields]})
        elif m["type"] == "invariant":
            checks = []
            if isinstance(got, dict):
                q = got.get("quadrant_counts") or {}
                checks.append(("quadrant_counts 之和 == count",
                               isinstance(q, dict) and sum(q.values()) == got.get("count")))
                try:
                    checks.append(("|value_mean - value_sum/count| <= 1e-6",
                                   abs(float(got["value_mean"]) - float(got["value_sum"]) / float(got["count"]))
                                   <= TOL))
                except Exception:  # noqa: BLE001
                    checks.append(("|value_mean - value_sum/count| <= 1e-6", False))
            else:
                checks = [(c, False) for c in m.get("invariants", [])]
            score = sum(1 for _, ok in checks if ok) / len(checks) if checks else 0.0
            metric_results.append({"id": m["id"], "score": round(score, 6),
                                   "checks": [{"name": n, "ok": ok} for n, ok in checks]})

    score = sum(mr["score"] * m["weight"] for mr, m in zip(metric_results, rubric["metrics"]))
    passed = score >= rubric["pass_threshold"]
    result = {"rubric": rubric["name"], "score": round(score, 6), "passed": passed,
              "pass_threshold": rubric["pass_threshold"], "metrics": metric_results,
              "problems": problems, "submission": str(sub_file)}
    (out / "score.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"score": result["score"], "passed": passed, "problems": problems}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
