# grid-stats-trajectory（轨迹资产示例）

一个最小的 **trajectory** 资产：`grid-stats-task` 任务的一次成功运行记录，按 harbor/ATIF 轨迹格式组织，
含用户指令、agent 计划、工具调用、工具结果、验证证据与最终结果六个有序步骤。

## 目录

```
grid-stats-trajectory/
├── asset.json        # 公共包络（asset_type=trajectory）
├── readme.md         # 本文件
├── trajectory.json   # 轨迹主体：6 步 + run 元信息 + 最终结果摘要
├── usage/readme.md   # 怎么读/怎么校验
└── validate/         # cases.json + validate.py + readme.md
```

## 轨迹内容

| 步 | role | type | 关键内容 |
|---|---|---|---|
| 1 | user | message | 给出任务：把 67 行采样点汇总成 `summary.json` |
| 2 | agent | plan | 说明算法（统计量 + 中位数象限划分） |
| 3 | agent | tool_call | `python3 grid-stats-task/solution/solve.py`，输入/输出路径 |
| 4 | environment | tool_result | 退出码 0，写出 `summary.json` |
| 5 | agent | verification | `grid-stats-task/tests/test_summary.py` → `pass`，`reward=1`，证据位置 |
| 6 | agent | final | 结论 + `result_summary`（count 67 / sum 394 / mean 5.880597 / 17·17·17·16） |

关联：`task` = `sciasset://2026ZD000042/demo/task/grid-stats-task`；
`environment_id` = `sciasset://2026ZD000042/demo/environment/python-runtime`；
`conforms_to` 指向 harbor 的轨迹格式 RFC。

## 判定口径

`validate/cases.json` 四条：结构合法（C01）、结果与关联任务一致（C02）、证据链完整（C03）、
删掉验证步必须判不通过（C04）。详细门槛见 `validate/readme.md`。
