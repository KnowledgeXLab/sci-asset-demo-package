#!/usr/bin/env python3
"""线性模型推理：读 CSV（需 x,y 列），按 model/weights.json 计算 prediction。

用法：
  python model/predict.py --input payload/samples.csv --out-dir <dir>
产物：
  <dir>/predictions.csv   # id,x,y,prediction
  <dir>/model-info.json   # 使用的权重摘要（系数、截距、容差、输入行数）
退出码：0 成功 / 2 输入不合法（bad_columns、bad_value）/ 3 输入文件不存在 / 4 权重不可用
"""
import argparse
import csv
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
WEIGHTS = HERE / "model" / "weights.json"


def load_weights():
    try:
        w = json.loads(WEIGHTS.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"错误：权重不可读（{exc}）", file=sys.stderr)
        return None
    if not w.get("features") or not w.get("coef") or len(w["features"]) != len(w["coef"]):
        print("错误：权重结构不合法（features/coef 缺失或长度不一致）", file=sys.stderr)
        return None
    return w


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    w = load_weights()
    if w is None:
        (out / "error.json").write_text(json.dumps({"error": "weights_invalid"}), encoding="utf-8")
        return 4

    try:
        with open(a.input, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        (out / "error.json").write_text(json.dumps({"error": "input_not_found", "path": a.input}),
                                        encoding="utf-8")
        print(f"错误：找不到输入（{a.input}）", file=sys.stderr)
        return 3

    missing = [c for c in ["x", "y"] if not rows or c not in rows[0]]
    if missing:
        (out / "error.json").write_text(json.dumps({"error": "bad_columns", "missing": missing}),
                                        encoding="utf-8")
        print(f"错误：输入缺列 {missing}", file=sys.stderr)
        return 2

    preds = []
    for r in rows:
        try:
            x, y = float(r["x"]), float(r["y"])
        except (TypeError, ValueError):
            (out / "error.json").write_text(json.dumps({"error": "bad_value", "row": r}, ensure_ascii=False),
                                            encoding="utf-8")
            print("错误：x/y 含非数值", file=sys.stderr)
            return 2
        z = float(w["intercept"]) + sum(float(c) * v for c, v in zip(w["coef"], (x, y)))
        preds.append({"id": r.get("id", ""), "x": r["x"], "y": r["y"], "prediction": f"{z:.6f}"})

    with (out / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=["id", "x", "y", "prediction"])
        wtr.writeheader()
        wtr.writerows(preds)

    info = {"model_type": w["model_type"], "features": w["features"], "coef": w["coef"],
            "intercept": w["intercept"], "tolerance": w["tolerance"],
            "rows": len(preds), "weights_sha256_prefix": _sha_prefix()}
    (out / "model-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    print(f"已写出 {len(preds)} 条预测 → {out/'predictions.csv'}")
    return 0


def _sha_prefix() -> str:
    import hashlib
    return hashlib.sha256(WEIGHTS.read_bytes()).hexdigest()[:12]


if __name__ == "__main__":
    raise SystemExit(main())
