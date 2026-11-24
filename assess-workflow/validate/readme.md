# assess-workflow 测试说明

## Agent

- 建议 agent harness：DSH（DeepSeek Harness）Web 会话 —— 工作流需要先把外部资产挂载到位，再由 agent 执行
- 装载方式：agent 读到本目录 `SKILL.md` 即可；外部资产由运行环境按 `external_assets.json` 放到本资产目录内（见 SKILL.md「依赖」）
- 建议 agent model：DS-4.1（DeepSeek-V4.1-Flash-1017）
- 是否必须特定模型：否 —— 三个被编排资产都是确定性计算；换模型不影响数值，但可能漏掉串行顺序，需按门槛判失败
- 备选 harness：任何能加载 skill 目录、能执行 Python 的 agent 环境
- 备注：运行时本资产目录下需能访问 `grid-samples` / `zscore-normalize` / `idw-interpolate` 三个目录，否则工作流以退出码 3 报外部资产缺失

## 测试任务（怎么测）

- 任务：让 agent 使用 `assess-workflow` 工作流，把示例数据跑完「读数据 → 标准化 → 插值」三步并产出汇总报告
- 输入：本资产目录（其中 `grid-samples/`、`zscore-normalize/`、`idw-interpolate/` 由运行环境提供）、`targets.csv`（自带 5 个目标点）
- 期望输出：`report.json`，含 `steps`（三步）、`data_points=100`、`targets=5`、`estimate_min`/`estimate_max`
- 提示词模板：

```
用 assess-workflow 这个工作流跑一遍：数据用 grid-samples，工具用 zscore-normalize，
技能用 idw-interpolate，目标点用该资产自带的 targets.csv，报告写到当前工作目录下的 report.json。
完成后把 report.json 里的 data_points、targets、estimate 范围告诉我。
```

## 通过门槛

- 门槛类型：脚本 + 指标
- 指标：`data_points = 100`、`targets = 5`、`steps` 恰好为 `read_data, zscore_normalize, idw_interpolate` 三步
- 验证脚本：`python validate/validate.py --case C01-end-to-end --artifact <agent 产物目录>`
  （`--artifact` 只读 agent 输出的 `report.json` 并核对字段，**不会重跑工作流**）
- 判定口径：脚本退出码 0 且上述指标全部成立。注意两处 rc=3 含义不同：
  · **给定用例 `C02-missing-external`** 期望工作流以 rc=3 报"外部资产缺失"→ 这是**通过**；
  · **agent 验收 `A01`**（编号仅用于 agent 验收场景，**不属于** `validate/cases.json` 的给定用例；给定用例只有 `C01-end-to-end` / `C02-missing-external`）若因外部资产没挂上而 rc=3 → 记 `blocked`（不是通过，也不是失败）
