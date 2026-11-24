# 任务：把网格采样点汇总成确定性 JSON 摘要

`/workspace/data/points.csv` 是规则网格上的采样点，三列：`x,y,value`（整数）。

请在 `/workspace/output/summary.json` 写出**唯一**产物，字段固定如下（键名与类型不得改）：

```json
{
  "count": 67,
  "value_mean": 5.880597,
  "value_min": 1,
  "value_max": 11,
  "x_extent": [0, 9],
  "y_extent": [0, 9],
  "quadrant_counts": {"Q1": 17, "Q2": 17, "Q3": 17, "Q4": 16},
  "value_sum": 394
}
```

约定：
- `count`：数据行数（不含表头）。
- `value_sum`：`value` 列整数和；`value_min` / `value_max` 同为整数。
- `value_mean`：`value_sum / count`，保留 6 位小数。
- `x_extent` / `y_extent`：该列 `[最小值, 最大值]`，整数。
- `quadrant_counts`：以 `x`、`y` 各自中位数（偶数个取中间两值均值，用 `<=` 归入低半区）把点分四象限，
  Q1=`x低 y低`、Q2=`x高 y低`、Q3=`x低 y高`、Q4=`x高 y高`，四个计数之和必须等于 `count`。

要求：
- 只用标准库，**不得联网**，不得读取 `/workspace/data/` 以外的输入。
- 输出必须是单个 JSON 文件，UTF-8，键值如上；不要写多余文件。
- 同样的输入必须得到同样的输出（不要用随机数、时间戳或哈希顺序）。
