---
name: idw-interpolate
description: 用反距离权重（IDW）把已知采样点的观测值插值到目标点。当需要在不做地统计建模的前提下快速给出连续表面估值时使用。
---

# IDW 插值

## 适用与不适用
- 适用：散点观测、目标点较少、只需确定性估值。
- 不适用：需要误差估计或空间相关性建模（应改用克里金）。

## 输入输出
- 输入：`--points <csv>`（x,y,value）、`--targets <csv>`（x,y[,value]）、可选 `--power`（**必须 > 0**，默认 2.0）。
- 输出：`<out-dir>/interpolated.csv`（x,y,value_est,nearest_dist）与 `run.json`。

## 执行
```
python scripts/run.py --points points.csv --targets targets.csv --out-dir out --power 2
```
命中已知点（距离 0）时直接取该点观测值。`--power ≤ 0` → 退出码 2 并写 `error.json(bad_power)`；输入缺列 → 退出码 2（`bad_columns`）；文件不存在 → 退出码 3（`input_not_found`）。
