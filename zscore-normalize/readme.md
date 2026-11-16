# zscore-normalize（示例工具资产）

把 CSV 的 `value` 列做 z-score 标准化。

```
python scripts/zscore.py --input payload.csv --out-dir out
```

输出：`out/result.csv`（id,zscore）、`out/stats.json`（n/mean/pstdev）。
预期错误：缺 `value` 列或方差为 0 → 退出码 2 并写 `out/error.json`；输入不存在 → 退出码 3。
