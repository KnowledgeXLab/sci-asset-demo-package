# demo-assets-1.0.0（示例资产包）

一个最小的示例资产包：数据、工具、skill、工作流各 1 个，工作流通过 `external_assets.json` 引用另外三个资产。合规性与功能以核验报告为准，本 readme 只描述内容与用法。
所有资产都用 Python 标准库实现，无需联网、无需第三方依赖。

## 目录

| 目录 | 资产类型 | 说明 |
|---|---|---|
| `grid-samples/` | data | 10×10 网格 100 个采样点（`payload/points.csv` + `metadata.json`，含可复算公式声明） |
| `zscore-normalize/` | tool | 把 CSV 的 `value` 列做 z-score 标准化 |
| `idw-interpolate/` | skill | 反距离权重（IDW）插值技能 |
| `assess-workflow/` | skill（工作流） | 编排前三个资产：读数据 → 标准化 → 插值 → 汇总 `report.json` |

> 规范里没有独立的 `workflow` 资产类型，工作流按 `skill` 登记，并在 `spec.metadata.asset_role: workflow` 与 `steps` 里标明角色。

## 资产编号

```
sciasset://2026ZD000042/demo/data/grid-samples
sciasset://2026ZD000042/demo/tool/zscore-normalize
sciasset://2026ZD000042/demo/skill/idw-interpolate
sciasset://2026ZD000042/demo/skill/assess-workflow
```

`project-id` 用示例编号 `2026ZD000042`（虚构，仅用于演示格式）；真实项目按其任务书首页的编号填写。

## 每个资产里有什么

```
<资产>/
├── asset.json                 # 公共包络（schema_version 1.0.0；四段 asset_id、task_classes、governance 等）
├── readme.md | SKILL.md       # 说明与使用方式
├── usage/readme.md            # 准备/调用说明
├── script / payload / …       # 实现、数据或指令
├── validate/                  # 用例定义 validate/cases.json + 自检脚本 validate.py
└── external_assets.json       # 可选：声明本资产引用的**其他资产**（示例中只有工作流有）
```

## 仓库内容

本仓库就是一个**可交付的示例资产包**，外加一次完整核验的产出：

```
.
├── grid-samples/  zscore-normalize/  idw-interpolate/  assess-workflow/   # 4 个资产
├── readme.md                                                             # 本说明
└── asset-runs/run-<批次>/                                                # 一次核验的完整证据
    ├── validation-report.md        # 结果对比与判定
    ├── registration/               # 23 列清单 xlsx + 行数据
    ├── cases.json / comparison.json / coverage.json
    ├── agent/  agent-sage/         # skill 的 agent 验收产物（默认后端 / Sage 后端）
    └── *.json                      # 包络、自包含、外部挂载、Sage 等机检结果
```

核验产出由 `sci-asset-verify-skill` 生成；`asset-runs/` 只作参考，**再次核验时不会被读取或对比**（skill 规定不参考包内已有结果）。

