# grid-summary-benchmark（基准资产示例）

一个最小的 **benchmark** 资产：把 `grid-stats-task` 当作评测任务，用自带参考答案与评分规则
（字段精确匹配 80% + 产物自洽 20%）给被测 agent 的 `output/summary.json` 打分，`pass_threshold = 1.0`。

## 目录

```
grid-summary-benchmark/
├── asset.json                 # 公共包络（asset_type=benchmark）
├── readme.md                  # 本文件
├── benchmark/
│   ├── scoring-rubric.json    # 指标、权重、聚合方式、通过阈值、评测协议
│   ├── run_evaluation.py      # 打分引擎：--submission <目录> --out-dir <目录>
│   ├── reference/summary.json # 参考答案（评测时不得暴露给被测 agent）
│   └── cases/good|bad/        # 两个自带样例产物：全对 / 篡改
├── usage/readme.md            # 怎么跑评测
└── validate/                  # cases.json + validate.py + readme.md
```

## 评测协议

| 项 | 值 |
|---|---|
| 关联任务 | `sciasset://2026ZD000042/demo/task/grid-stats-task` |
| 被测产物 | `output/summary.json`（task 的 `artifacts` 声明） |
| 指标 | `field_exact`（权重 0.8，7 个字段逐一比对，容差 1e-6）、`internal_consistency`（权重 0.2，两条不变量） |
| 聚合 | 加权求和 → `score ∈ [0,1]` |
| 通过阈值 | `score ≥ 1.0` |
| trial 数 | 1（确定性任务，无需多次采样） |
| 治理约束 | 参考答案与评分规则**不得暴露给被测 agent**（`governance.usage_constraints`） |

## 用法

```bash
python benchmark/run_evaluation.py --submission benchmark/cases/good --out-dir /tmp/good   # → 1.0 / passed
python benchmark/run_evaluation.py --submission benchmark/cases/bad  --out-dir /tmp/bad    # → 0.571429 / failed
```

## 判定口径

`validate/cases.json` 五条：正例满分（C01）、篡改产物不通过（C02）、评分规则自洽（C03）、
参考答案自洽（C04）、缺产物记问题（C05）。详见 `validate/readme.md`。
