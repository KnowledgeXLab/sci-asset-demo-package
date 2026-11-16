---
name: assess-workflow
description: 一条最小工作流：读示例数据 → 用 z-score 工具标准化 → 用 IDW 技能插值到指定目标点 → 汇总报告。演示工作流如何引用其他资产。
---

# 示例工作流（assess-workflow）

## 它做什么
1. 读数据资产 `grid-samples` 的 `payload/points.csv`；
2. 调工具资产 `zscore-normalize` 做标准化，取 `stats.json`；
3. 调技能资产 `idw-interpolate`，用本目录 `targets.csv` 插值；
4. 汇总成 `report.json`：`value_mean`/`value_pstdev` 是**原始观测值**的统计量（来自第 2 步的 z-score 工具输出），
   `estimate_min`/`estimate_max` 是对**原始观测值**做 IDW 的估值范围——标准化只用于产出统计量，不改变插值输入。
`external_assets` 字段只记声明的相对位置（如 `grid-samples`），**不写挂载的绝对路径**，保证产物换机器后仍可逐值比对。

## 依赖（见 external_assets.json）
本目录只放工作流自己的脚本与目标点。数据、工具、技能三项外部资产按资产编号声明在 `external_assets.json` 里，
**由使用方（校验环境或平台的自动挂载机制）负责把它们放到本资产目录内**：运行时要求本目录下能按相对路径访问到
`grid-samples/`、`zscore-normalize/`、`idw-interpolate/` 三个目录。

## 执行
```
python scripts/run_workflow.py --assets-root <本资产目录> --out-dir out
```

## 失败语义
- 运行环境没把外部资产放到位（上面三个目录不可达） → `error.json` 记 `external_asset_missing`，退出码 3；
- 工具/技能自身失败 → `tool_failed`/`skill_failed`，退出码 4/5。
