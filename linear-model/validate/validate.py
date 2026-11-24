#!/usr/bin/env python3
"""linear-model 自检 / 验收。

  python validate/validate.py --case C01-predict --out-dir <dir>     自检：跑本资产推理并核对数值
  python validate/validate.py --artifact <agent 产物目录>             验收：只判 predictions.csv，不重跑推理
退出码：0 通过 / 1 不通过 / 2 用法错误
"""
import argparse
import csv
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
TOL = 1e-6
EXPECT = ["2.000000", "3.000000", "2.750000", "3.750000", "3.500000", "4.500000"]
ERROR_CASES = {
    "C03-bad-column": {"rc": 2, "error": "bad_columns"},
    "C04-input-missing": {"rc": 3, "error": "input_not_found"},
}


def run_predict(inp: pathlib.Path, out: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "model" / "predict.py"),
                           "--input", str(inp), "--out-dir", str(out)],
                          capture_output=True, text=True)


def judge(pred_csv: pathlib.Path) -> dict:
    if not pred_csv.is_file():
        return {"ok": False, "why": f"缺少产物 {pred_csv.name}"}
    with pred_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    got = [r.get("prediction", "") for r in rows]
    if len(got) != len(EXPECT):
        return {"ok": False, "why": f"行数不符：期望 {len(EXPECT)}，实际 {len(got)}"}
    bad = [(i, g, e) for i, (g, e) in enumerate(zip(got, EXPECT), 1)
           if abs(float(g) - float(e)) > TOL]
    return {"ok": not bad, "why": "" if not bad else f"第 {bad[0][0]} 行不符：期望 {bad[0][2]}，实际 {bad[0][1]}",
            "rows": len(got), "values": got}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="C01-predict")
    ap.add_argument("--out-dir")
    ap.add_argument("--artifact")
    a = ap.parse_args()
    known = ["C01-predict", "C02-reproducible"] + list(ERROR_CASES)
    if a.case not in known:
        print(f"未知用例 id：{a.case}；可用：{', '.join(known)}", file=sys.stderr)
        return 2

    if a.artifact:
        res = {"mode": "artifact", "case": a.case, **judge(pathlib.Path(a.artifact) / "predictions.csv")}
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["ok"] else 1

    if not a.out_dir:
        print("需要 --out-dir（自检）或 --artifact（验收）", file=sys.stderr)
        return 2
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if a.case in ERROR_CASES:
        exp = ERROR_CASES[a.case]
        if a.case == "C04-input-missing":
            inp = out / "nope.csv"
        else:
            inp = out / "bad.csv"
            inp.write_text("id,x\np001,1\n", encoding="utf-8")
        proc = run_predict(inp, out / a.case)
        ep = out / a.case / "error.json"
        err = json.loads(ep.read_text(encoding="utf-8")).get("error") if ep.is_file() else None
        ok = proc.returncode == exp["rc"] and err == exp["error"]
        print(json.dumps({"mode": "self-check", "case": a.case, "rc": proc.returncode,
                          "error": err, "expected": exp, "ok": ok}, ensure_ascii=False))
        return 0 if ok else 1

    src = HERE / "payload" / "samples.csv"
    proc = run_predict(src, out / "c01")
    if proc.returncode != 0:
        print(json.dumps({"mode": "self-check", "case": a.case, "rc": proc.returncode,
                          "stderr": proc.stderr[-300:], "ok": False}, ensure_ascii=False))
        return 1
    pred1 = out / "c01" / "predictions.csv"
    res = {"mode": "self-check", "case": a.case, **judge(pred1)}

    if a.case == "C02-reproducible":
        proc2 = run_predict(src, out / "c02")
        pred2 = out / "c02" / "predictions.csv"
        same = pred2.is_file() and hashlib.sha256(pred1.read_bytes()).hexdigest() == \
            hashlib.sha256(pred2.read_bytes()).hexdigest()
        res["reproducible"] = same
        if not same:
            res["ok"] = False
            res["why"] = res.get("why") or "两次推理产物不一致（非确定性）"

    print(json.dumps(res, ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
