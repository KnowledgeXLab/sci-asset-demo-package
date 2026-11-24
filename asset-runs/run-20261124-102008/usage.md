# demo-assets 使用说明（本批次实测口径）

本文件只写「怎么用」：每个资产的用途、边界、输入输出字段与单位、运行环境、实际入口与示例命令。
所有路径均取自本资产包实际内容；`<包根>` = `examples/demo-assets`，`<副本>` = 本批次工作副本
（`examples/.asset-work/run-20261124-102008`，由 `scripts/work_copy.py init` 生成，与包内容逐字节一致）。

包内共 5 个资产：data ×1、tool ×1、skill ×2（其中 1 个是工作流）、task ×1（harbor 格式）。
全部资产仅用 Python 标准库实现，不需要联网、不需要第三方依赖。

## 0. 资产一览

| 目录 | 类型 | 版本 | 一句话用途 | 实际入口 |
|---|---|---|---|---|
| `grid-samples/` | data | 1.0.0 | 10×10 规则网格 100 个采样点 | 直接读 `payload/points.csv` + `metadata.json` |
| `zscore-normalize/` | tool | 1.0.0 | CSV `value` 列 z-score 标准化 | `python scripts/zscore.py --input <csv> --out-dir <dir>` |
| `idw-interpolate/` | skill | 1.0.0 | 散点观测 → 目标点 IDW 插值 | `python scripts/run.py --points <csv> --targets <csv> --out-dir <dir> [--power 2]` |
| `assess-workflow/` | skill（工作流） | 1.0.0 | 读数据 → 标准化 → 插值 → 汇总报告 | `python scripts/run_workflow.py --assets-root <本资产目录> --out-dir <dir>` |
| `grid-stats-task/` | task | 1.0.0 | harbor 任务：67 点汇总成确定性 JSON | harbor CLI（`harbor run -p <任务目录> -a oracle\|nop`） |

## 1. grid-samples（data）

- 用途：给示例工具/技能/工作流当输入；演示「声明公式可逐行复算」。
- 适用边界：合成数据，非真实观测；坐标为本地直角坐标系，不含真实地理参照。
- 输入：无运行输入（数据资产）。
- 输出/实体：`payload/points.csv`（UTF-8 CSV，逗号分隔，含表头），列 `id`(字符串，如 `p001`)、`x`(整数 0–9)、
  `y`(整数 0–9)、`value`(浮点，无量纲，实测范围 10.06741–20.4125)；`metadata.json` 声明记录数 100、列名、
  bbox（x/y 均 [0,9]）、网格 10×10、值域与生成公式。
- 复算口径：`value = 10 + 3·sin(x/2) + 2·cos(y/3) + 0.1·i`，`i` 为行号（自 1 起、逐行递增），行内 x 递增、行间 y 递增，容差 `1e-06`。
- 运行环境：任意能读 UTF-8 CSV 的环境；无 CPU/GPU/网络要求。
- 示例：`python3 grid-samples/validate/validate.py --case C05-formula --out-dir out`

## 2. zscore-normalize（tool）

- 用途：把 CSV 的 `value` 列按**总体标准差**（pstdev）做 z-score 标准化，并给出 n/mean/pstdev。
- 适用边界：单列标量标准化；不提供样本标准差口径，不做缺失值插补。
- 输入：`--input`（必填）UTF-8 CSV，需含 `value` 列（数值）；`--out-dir`（必填）输出目录。
- 输出：`result.csv`（列 `id,zscore`）；`stats.json`（`n`、`mean`、`pstdev`）。
- 失败语义：退出码 2 + `error.json`（`missing_value_column` / `bad_value` / `empty_input` / `zero_variance`）；
  退出码 3 + `error.json(input_not_found)`。
- 运行环境：Python ≥3.10（仅标准库），仅需 CPU。
- 示例：`python3 zscore-normalize/scripts/zscore.py --input grid-samples/payload/points.csv --out-dir out`

## 3. idw-interpolate（skill）

- 用途：按已知散点观测对目标点做反距离权重估值，输出估值与最近邻距离。
- 适用边界：目标点少、只要确定性估值；**不提供误差估计**，需要空间相关性建模应改用克里金。
- 输入：`--points`（必填）CSV，列 `x,y,value`；`--targets`（必填）CSV，列 `x,y[,value]`；`--power`（可选，必须 >0，默认 2.0）。
- 输出：`<out-dir>/interpolated.csv`（列 `x,y,value_est,nearest_dist`，单位同输入）与 `run.json`。
  命中已知点（距离 0）时直接取该点观测值。
- 失败语义：退出码 2 + `error.json`（`bad_power` / `bad_columns` / `no_source_points`）；退出码 3（`input_not_found`）。
- 交由 agent 使用的方式：让 agent 读到本目录的 `SKILL.md`；验收文档见 `validate/readme.md`。
- 运行环境：Python ≥3.10（仅标准库），仅需 CPU，不需容器。
- 示例：`python3 idw-interpolate/scripts/run.py --points p.csv --targets t.csv --out-dir out --power 2`

## 4. assess-workflow（skill，工作流）

- 用途：把数据 → 标准化 → 插值串成固定三步，产出汇总报告；演示跨资产引用。
- 适用边界：三步顺序固定；被编排的三个资产必须挂载到位，否则以退出码 3 明确失败（不静默降级）。
- 输入：`--assets-root`（必填）本资产目录，其下须可访问 `grid-samples/`、`zscore-normalize/`、`idw-interpolate/`
  三个目录（由运行环境按 `external_assets.json` 放到本资产目录内）；`--out-dir`（必填）；目标点用自带 `targets.csv`（5 行 `x,y`）。
- 输出：`report.json`，字段 `steps`（`read_data,zscore_normalize,idw_interpolate`）、`data_points`、`value_mean`、
  `value_pstdev`、`targets`、`estimate_min`、`estimate_max`、`external_assets`（只记相对位置，不写绝对路径）。
  其中 `value_mean`/`value_pstdev` 是**原始观测值**的统计量，`estimate_min`/`estimate_max` 是对**原始观测值**做 IDW 的估值范围。
- 失败语义：退出码 3 + `error.json(external_asset_missing)`；4（`tool_failed`）；5（`skill_failed`）。
- 运行环境：Python ≥3.10（仅标准库）；运行前外部资产须挂载到位。
- 示例：`python3 assess-workflow/validate/validate.py --case C01-end-to-end --out-dir out --assets-root <副本根>`

## 5. grid-stats-task（task / harbor 1.4）

- 用途：harbor / terminal-bench-science 格式任务包；把 67 个网格采样点汇总成固定字段的确定性 JSON 摘要。
- 适用边界：容器内执行、无网络、只用标准库；verifier 与 agent 环境隔离（`[verifier].environment_mode = "separate"`）。
- 输入（给被测 agent）：容器内 `/workspace/data/points.csv`，三列 `x,y,value`（整数，67 行，不含表头）。
- 输出（被测 agent 写）：`/workspace/output/summary.json`，固定 9 字段：`count`、`value_mean`（6 位小数）、`value_min`、
  `value_max`、`x_extent`、`y_extent`、`quadrant_counts{Q1..Q4}`、`value_sum`；UTF-8，单一文件。
- 判分：`tests/test.sh` 写 `/logs/verifier/reward.txt`；`tests/test_summary.py` 从**自带真值** `tests/data/points.csv` 独立复算，
  不依赖被测方输入。
- 运行环境：容器 1 CPU / 1024 MB / 2 GB 磁盘 / 无 GPU / `no-network`；agent 超时 900 s、verifier 180 s、构建 600 s。
  宿主需 docker + harbor CLI（本批次用 harbor 0.27.0）。
- 示例（官方 CLI 双 trial）：`python3 <skill>/scripts/harbor_run.py --package <副本根> --run-dir <run>`
- 离线自检（无 docker）：`python3 grid-stats-task/validate/validate.py` 与 `... --no-solution`

## 6. 本地路径 / 服务端路径 / 下载地址

- 本批次只有一个来源：本机资产包 `<包根>`（即 `examples/demo-assets`），无远端下载地址、无服务端点。
- 运行态实体一律在副本 `<副本>` 内产生，原始包只新增 `asset-runs/run-20261124-102008/` 一个批次目录。
- 本包不注册 MCP、不部署模型：包内没有 MCP 端点，也没有可部署的模型权重或推理服务
  （`asset_type` 只覆盖 data / tool / skill / task）。

## 7. 复现提示

- 所有用例都在工作副本中执行，原始资产文件不改动。
- 跑 task 资产时若宿主 `~/.docker/buildx` 不可写，需要设置 `BUILDX_CONFIG=<可写目录>` 再调 harbor，
  否则 `docker compose build` 会以 `permission denied` 失败（本批次即因此先失败一次，见报告 P2 与本目录 `harbor-run-attempt-01-blocked-buildx.json`）。
