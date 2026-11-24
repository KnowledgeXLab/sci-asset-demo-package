# 使用说明

## 准备

无第三方依赖，Python ≥ 3.10。评测需要两样东西：

1. 被测 agent 的产物目录（内含 `summary.json`，即 task 的 `output/summary.json`）
2. 本资产的 `benchmark/reference/summary.json`（**只给评测方用**）

## 调用

```bash
python benchmark/run_evaluation.py --submission <产物目录> --out-dir <输出目录>
```

产物 `score.json`：

| 字段 | 含义 |
|---|---|
| `score` | 加权总分（0~1） |
| `passed` | 是否达到 `pass_threshold` |
| `metrics[]` | 每个指标的得分、`correct_fields` / `wrong_fields` 或 `checks` |
| `problems` | 结构性问题的说明（如缺产物） |

## 评分口径

- `field_exact`（0.8）：`count`、`value_min`、`value_max`、`value_sum`、`x_extent`、`y_extent`、`quadrant_counts`
  与参考答案逐字段相等（数值容差 `1e-6`），按"对几个/共几个"给分
- `internal_consistency`（0.2）：`quadrant_counts` 之和等于 `count`；`value_mean` 等于 `value_sum/count`（容差 `1e-6`）
- 总分 = 0.8×字段得分 + 0.2×自洽得分；`passed = score ≥ 1.0`

## 安全要求

参考答案与评分规则**不得**出现在被测 agent 可见的环境里（容器、提示词、任务包），
否则评测失去意义——这也是本资产 `governance.usage_constraints` 的第一条。
