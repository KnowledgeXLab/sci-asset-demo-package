# idw-interpolate 测试说明

## Agent

- 建议 agent harness：DSH（DeepSeek Harness）Web 会话 —— 把本资产目录放进 agent 可读的 skills 位置，或在 prompt 里给出 `SKILL.md` 路径
- 装载方式：agent 需能读到 `SKILL.md` 与本目录；不需要额外注册 MCP
- 建议 agent model：DS-4.1（DeepSeek-V4.1-Flash-1017）
- 是否必须特定模型：否 —— 计算是确定性的，模型只负责理解任务与组织参数；换模型结果应一致，若误读参数（如幂次）则按门槛判失败
- 备选 harness：任何能加载 skill 目录并执行脚本的 agent 环境（Claude Code、平台 Agent 均可）
- 备注：纯标准库实现，Python ≥3.10；不需要容器

## 测试任务（怎么测）

- 任务：让 agent 使用 `idw-interpolate` 技能，把已知点表插值到目标点表，并写出结果文件
- 输入：随包交付的 `validate/cases/C01/points.csv`（x,y,value）与 `validate/cases/C01/targets.csv`（x,y），输出目录任意（由 agent 决定并告知）
- 期望输出：`interpolated.csv`，列为 `x,y,value_est,nearest_dist`，行数与目标点一致
- 提示词模板：

```
用 idw-interpolate 这个 skill 做插值：已知点用 validate/cases/C01/points.csv，
目标点用 validate/cases/C01/targets.csv，幂次取 2，结果写到当前工作目录下的 interpolated.csv。
完成后告诉我输出路径和每行的 value_est。
```

## 通过门槛

- 门槛类型：脚本 + 指标
- 指标：`value_est_exact = 0`（命中已知点的两行估值分别等于 10.000000 / 20.000000）、`nearest_dist` 逐值相等（0.000000 / 0.000000）——**两列都判**，防止产物把某列写成常数
- 给定用例共 7 组：`C01-hits`（命中已知点 → 10/20）、`C02-equidistant`（等距 → 均值 15）、
  `C05-power-one`（`--power 1` → (2.5,0) 处解析解 12.5，覆盖非默认幂次分支），
  以及 **4 组预期错误用例**：`C03-missing-file` → 退出码 3 + `input_not_found`、`C04-bad-column` → 退出码 2 + `bad_columns`、`C06-bad-power`（`--power ≤ 0`）→ 退出码 2 + `bad_power`、`C07-no-source-points`（已知点表只有表头）→ 退出码 2 + `no_source_points`；均由 `--case` 自检覆盖
- 验证脚本：`python validate/validate.py --case C01-hits --artifact <agent 产物目录>`
  （`--artifact` 只读 agent 输出的 `interpolated.csv`，逐值比对 `value_est` 与 `nearest_dist` 两列，**不会重跑本资产脚本**）
- 判定口径：脚本退出码 0 且上述指标成立才算通过；agent 没产出文件或路径缺失记 `blocked`，不得记通过
