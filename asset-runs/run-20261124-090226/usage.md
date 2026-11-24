# demo-assets 使用说明（本次核验整理）

包根：`examples/demo-assets`（示例资产包，全部资产为 Python 标准库实现，不联网、无第三方依赖）
本批次：`asset-runs/run-20261124-090226`

> 包根一级文件（`readme.md` / `VERSION` / `.gitignore`）只记存在性，本说明的内容全部从各资产目录内的
> `asset.json`、`SKILL.md`、`readme.md`、`usage/readme.md`、`validate/` 与脚本实体读出。

## 资产一览

| 目录 | 类型 | 版本 | 用途 | 运行环境 |
|---|---|---|---|---|
| `grid-samples/` | data | 1.0.0 | 10×10 网格 100 个采样点，示例插值/统计的输入数据 | 无需运行，直接读 CSV |
| `zscore-normalize/` | tool | 1.0.0 | 把 CSV 的 `value` 列做总体标准差 z-score 标准化 | CLI，`python>=3.10`（仅标准库） |
| `idw-interpolate/` | skill | 1.0.0 | 反距离权重（IDW）把已知散点观测插值到目标点 | CLI/技能，`python>=3.10`（仅标准库） |
| `assess-workflow/` | skill（`spec.metadata.asset_role=workflow`） | 1.0.0 | 编排前三个资产：读数据 → 标准化 → 插值 → 汇总 `report.json` | CLI，`python>=3.10`（仅标准库） |
| `grid-stats-task/` | task（harbor 1.4 格式） | 1.0.0 | 把 67 个网格点汇总成确定性 JSON 摘要，供 verifier 逐字段核对 | 容器 `python:3.12-slim`，1 CPU / 1 GB / 无网络 |

## 1. grid-samples（data）

- **用途**：规则 10×10 网格上的 100 个采样点，列 `id,x,y,value`；给示例工具/技能/工作流当输入。
- **适用边界**：演示与自检用途；数值由确定性公式生成，不代表真实观测。
- **入口**：直接读 `payload/points.csv`（UTF-8 CSV，含表头）；元数据 `metadata.json`。
- **输入字段**：无输入（静态数据）。
- **输出字段/单位**：`id`（字符串 `pNNN`）、`x`/`y`（整数格点，0–9，无单位）、`value`（浮点观测值，无单位，范围 10.0674–20.4125）。
- **声明事实**：`records=100`、`columns=[id,x,y,value]`、`bbox.x=[0,9]`、`bbox.y=[0,9]`、`grid={nx:10,ny:10}`、
  `formula.expr = 10 + 3*sin(x/2) + 2*cos(y/3) + 0.1*i`（`i` 行号自 1 起，容差 `1e-06`）。
- **验证入口**：`python validate/validate.py --case <id> --out-dir <dir>`（用例 C01–C05）。

## 2. zscore-normalize（tool）

- **用途**：把 CSV 的 `value` 列按**总体标准差**（pstdev，非样本）做 z-score 标准化，输出结果表与统计量。
- **适用边界**：单列数值、小型表；方差为 0（单条记录或常量列）按错误返回，不做兜底。
- **入口**：`python scripts/zscore.py --input <csv> --out-dir <dir>`
- **输入字段**：CSV 需含 `value` 列（数值，无单位）；`--out-dir` 为输出目录（必填）。
- **输出字段/单位**：
  - `result.csv`：`id`（来自输入 `id` 列）、`zscore`（无量纲，固定 6 位小数）
  - `stats.json`：`n`（记录数）、`mean`（均值）、`pstdev`（总体标准差，无量纲）
  - 失败时 `error.json`：`{"error": "..."}`，错误码：退出码 2 = `missing_value_column` / `bad_value` / `empty_input` / `zero_variance`，退出码 3 = `input_not_found`
- **验证入口**：自检 `python validate/validate.py --case <id> --out-dir <dir>`（C01–C06）；验收 agent 产物 `python validate/validate.py --artifact <dir>`（需 `result.csv` + `stats.json`）。

## 3. idw-interpolate（skill）

- **用途**：用反距离权重把已知散点观测插值到目标点，快速给出确定性连续表面估值。
- **适用边界**：适用于散点观测、目标点较少、只需确定性估值；**不适用**于需要误差估计或空间相关性建模（应改用克里金）。
- **入口**：`python scripts/run.py --points <csv> --targets <csv> --out-dir <dir> [--power <p>]`（`--power` 必须 > 0，默认 2.0）
- **输入字段**：`--points` 需 `x,y,value` 三列（`x`/`y` 为平面坐标，无单位；`value` 为观测值，无单位）；`--targets` 需 `x,y[,value]` 列。
- **输出字段/单位**：`interpolated.csv`（`x`,`y`,`value_est`,`nearest_dist`；`value_est` 与 `value` 同单位、6 位小数，`nearest_dist` 与 `x/y` 同单位、6 位小数）、`run.json`（运行元信息）。
- **失败语义**：`--power <= 0` → 退出码 2 + `error.json(bad_power)`；输入缺列 → 退出码 2（`bad_columns`）；文件不存在 → 退出码 3（`input_not_found`）。
- **验证入口**：自检 `python validate/validate.py --case <id> --out-dir <dir>`（C01/C02/C05 数值 + C03/C04/C06 错误分支）；验收 agent 产物 `python validate/validate.py --case C01-hits --artifact <dir>`（只读 `interpolated.csv`，`value_est` 与 `nearest_dist` 两列都判）。

## 4. assess-workflow（skill，工作流）

- **用途**：最小工作流示例——读 `grid-samples` 数据 → 用 `zscore-normalize` 出统计量 → 用 `idw-interpolate` 对目标点插值 → 汇总 `report.json`；演示工作流如何按资产编号引用其他资产。
- **适用边界**：依赖三个外部资产目录可达；`value_mean`/`value_pstdev` 是**原始观测值**统计量，`estimate_min`/`estimate_max` 是对**原始观测值**做 IDW 的估值范围（标准化只用于出统计量，不改插值输入）。
- **入口**：`python scripts/run_workflow.py --assets-root <本资产目录> --out-dir <dir>`
- **输入**：本资产目录下的 `targets.csv`（`x,y`，自带 5 个目标点）；外部资产按 `external_assets.json` 挂到本目录下 `grid-samples/`、`zscore-normalize/`、`idw-interpolate/`。
- **输出字段/单位**：`report.json` —— `steps`（固定 `read_data, zscore_normalize, idw_interpolate`）、`data_points`（点位个数）、`targets`（目标点个数）、`value_mean`/`value_pstdev`（观测值统计量）、`estimate_min`/`estimate_max`（估测值范围，与 `value` 同单位）、`external_assets`（只记声明的相对位置，不写挂载绝对路径）。
- **失败语义**：外部资产未挂载到位 → `error.json(external_asset_missing)`、退出码 3；工具/技能失败 → `tool_failed`/`skill_failed`、退出码 4/5。
- **验证入口**：自检 `python validate/validate.py --case C01-end-to-end --out-dir <dir> --assets-root <dir>`（C02 为预期错误分支）；验收 agent 产物 `python validate/validate.py --artifact <dir>`（只读 `report.json`）。

## 5. grid-stats-task（task，harbor 1.4）

- **用途**：harbor / terminal-bench-science 格式的最小 task 示例：67 个网格采样点 → 确定性 JSON 摘要，由独立 verifier 逐字段核对。
- **适用边界**：`[verifier].environment_mode = "separate"`，verifier 用自带真值 `tests/data/points.csv` 独立复算，不读被测方数据；无网络、无 GPU。
- **入口**：
  - 官方口径：`harbor run -p <任务目录> -a oracle`（期望 `reward=1`）与 `-a nop`（期望 `reward=0`）
  - 离线口径：`python validate/validate.py`（参考解 + verifier 应双双通过）、`python validate/validate.py --no-solution`（verifier 应判不通过）
- **输入字段**：容器内 `/workspace/data/points.csv`，列 `x,y,value`（整数格点 / 整数值）。verifier 真值同名文件在 `tests/data/points.csv`。
- **输出字段/单位**：`/workspace/output/summary.json` —— `count`、`value_mean`（6 位小数）、`value_min`、`value_max`、`x_extent`、`y_extent`、`quadrant_counts{Q1..Q4}`、`value_sum`。
- **失败语义**：verifier 任一字段不符 → `tests/test.sh` 写 `/logs/verifier/reward.txt` = `0`；全部符合 → `1`。
- **验证入口**：`validate/cases.json` 只声明一条用例 `C01-oracle-nop`（harbor 双 trial，nop 即负例）。

## 本批次执行位置

- 执行在**工作副本**：`examples/.asset-work/run-20261124-090226/`（原件不动；副本用于挂载外部资产、跑用例、跑 agent、跑容器）
- 产物汇总：`examples/demo-assets/asset-runs/run-20261124-090226/`
