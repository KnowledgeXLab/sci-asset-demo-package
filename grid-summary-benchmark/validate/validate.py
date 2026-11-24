#!/usr/bin/env python3
"""grid-summary-benchmark 自检：评分引擎、规则自洽、参考答案自洽、缺失产物。

  python validate/validate.py --case C01-score-good --out-dir <dir>
退出码：0 通过 / 1 不通过 / 2 用法错误
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]
ENGINE = HERE / "benchmark" / "run_evaluation.py"
RUBRIC = HERE / "benchmark" / "scoring-rubric.json"
REFERENCE = HERE / "benchmark" / "reference" / "summary.json"
SUPPORTED = {"field_exact_match", "invariant"}
TOL = 1e-6


def score(sub: pathlib.Path, out: pathlib.Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(ENGINE), "--submission", str(sub), "--out-dir", str(out)],
                          capture_output=True, text=True)
    sf = out / "score.json"
    return {"rc": proc.returncode, "score": json.loads(sf.read_text(encoding="utf-8")) if sf.is_file() else {},
            "stderr": proc.stderr[-300:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="C01-score-good")
    ap.add_argument("--out-dir", default=str(pathlib.Path(tempfile.gettempdir()) / "grid-summary-benchmark-check"))
    a = ap.parse_args()
    known = ["C01-score-good", "C02-score-bad", "C03-rubric-schema",
             "C04-reference-consistency", "C05-missing-submission"]
    if a.case not in known:
        print(f"未知用例 id：{a.case}；可用：{', '.join(known)}", file=sys.stderr)
        return 2
    out = pathlib.Path(a.out_dir)

    if a.case == "C01-score-good":
        r = score(HERE / "benchmark" / "cases" / "good", out / "c01")
        s = r["score"]
        ok = r["rc"] == 0 and s.get("passed") is True and abs(s.get("score", 0) - 1.0) <= TOL
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok, "score": s.get("score"),
                          "passed": s.get("passed")}, ensure_ascii=False))
        return 0 if ok else 1

    if a.case == "C02-score-bad":
        r = score(HERE / "benchmark" / "cases" / "bad", out / "c02")
        s = r["score"]
        wrong = next((m for m in s.get("metrics", []) if m["id"] == "field_exact"), {})
        ok = (r["rc"] == 0 and s.get("passed") is False and s.get("score", 1) < 1
              and "value_sum" in (wrong.get("wrong_fields") or []))
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok, "score": s.get("score"),
                          "wrong_fields": wrong.get("wrong_fields")}, ensure_ascii=False))
        return 0 if ok else 1

    if a.case == "C03-rubric-schema":
        rub = json.loads(RUBRIC.read_text(encoding="utf-8"))
        problems = []
        w = sum(float(m.get("weight", 0)) for m in rub.get("metrics", []))
        if abs(w - 1.0) > TOL:
            problems.append(f"权重之和应为 1，实际 {w}")
        th = rub.get("pass_threshold")
        if not isinstance(th, (int, float)) or not (0 <= th <= 1):
            problems.append(f"pass_threshold 应为 [0,1] 内数值，实际 {th}")
        for m in rub.get("metrics", []):
            if m.get("type") not in SUPPORTED:
                problems.append(f"指标 {m.get('id')} 类型不受支持：{m.get('type')}")
        layout = (rub.get("protocol") or {}).get("submission_layout")
        if layout != "output/summary.json":
            problems.append(f"submission_layout 应与 task 产物一致（output/summary.json），实际 {layout}")
        ok = not problems
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok, "problems": problems},
                         ensure_ascii=False))
        return 0 if ok else 1

    if a.case == "C04-reference-consistency":
        ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
        problems = []
        need = {"count", "value_mean", "value_min", "value_max", "x_extent", "y_extent",
                "quadrant_counts", "value_sum"}
        if set(ref) != need:
            problems.append(f"参考字段不符：多 {sorted(set(ref) - need)}，少 {sorted(need - set(ref))}")
        q = ref.get("quadrant_counts") or {}
        if sum(q.values()) != ref.get("count"):
            problems.append(f"象限之和 {sum(q.values())} ≠ count {ref.get('count')}")
        if abs(float(ref["value_mean"]) - float(ref["value_sum"]) / float(ref["count"])) > TOL:
            problems.append("value_mean 与 value_sum/count 不一致")
        ok = not problems
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok, "problems": problems},
                         ensure_ascii=False))
        return 0 if ok else 1

    empty = out / "c05-empty"
    empty.mkdir(parents=True, exist_ok=True)
    r = score(empty, out / "c05")
    s = r["score"]
    ok = (s.get("passed") is False and any("缺少产物" in p for p in (s.get("problems") or [])))
    print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok,
                      "problems": s.get("problems")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
