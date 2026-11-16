# demo-assets-1.0.0 使用说明（本次核验批次 run-20261116-160701）

资产包根：`examples/demo-assets-1.0.0/`；本地运行环境：Python ≥3.10（全部资产仅用标准库，无需联网）。
包内**没有**模型权重、MCP/HTTP 服务端点、容器镜像；也没有任何需要下载的远程 URL 或服务端路径——
所有资产都以「本地目录 + 命令行/直接读文件」的方式使用。因此下文只给本地路径与本地命令。
工作副本：`examples/.asset-work/run-20261116-160701/`（与原始包同构，核验期间的执行都在副本内完成）。

---

## 1. grid-samples（data · 规则网格采样点数据 1.0.0）

- 用途：给工具/技能/工作流当输入示例，10×10 网格 100 个采样点。
- 适用边界：本地平面直角坐标（`crs: local-cartesian`），无时间维、无真实地理投影；只作示例，不可直接当作实测数据。
- 输入：无（数据资产，直接读实体）。
- 输出/实体：
  - `payload/points.csv`：UTF-8 CSV，表头 `id,x,y,value`；`x`/`y` 为**整数格点坐标**（0–9，无量纲单位）；`value` 为**无量纲观测值**（范围 10.06741–20.4125）。
  - `metadata.json`：`records=100`、`columns`、`bbox{x:[0,9],y:[0,9]}`、`grid{nx:10,ny:10}`、`value_range`、`sha256`、`formula{expr,i_base:1,tolerance:1e-06}`（机器可读的取值公式声明：`value = 10 + 3·sin(x/2) + 2·cos(y/3) + 0.1·i`，`i` 为行号、自 1 起）。
- 运行环境：无需运行环境（纯数据）；读取端任意支持 UTF-8 CSV 的工具。
- 入口与示例：
  ```
  head -3 payload/points.csv          # id,x,y,value
  python validate/validate.py --case C05-formula --out-dir out
  ```
- 注意：`usage/readme.md` 只写「直接读取 payload/points.csv」，不含额外参数约定。

## 2. zscore-normalize（tool · z-score 标准化工具 1.0.0）

- 用途：把 CSV 的 `value` 列按**总体标准差**（pstdev，非样本标准差）做 z-score 标准化，输出结果表与统计量。
- 适用边界：单列数值标准化；不做分组、不做缺失值填充；方差为 0 时拒绝执行（符合定义）。
- 输入：`--input <csv>`（必填，UTF-8 CSV，**必须含 `value` 列**；`id` 列可选，用于回填结果行；数值为无量纲浮点）。
- 输出：`--out-dir <dir>`（必填）
  - `result.csv`：表头 `id,zscore`，z 值保留 6 位小数（无量纲）。
  - `stats.json`：`{"n":总数,"mean":均值(6 位),"pstdev":总体标准差(6 位)}`。
  - 失败时写 `error.json`：`missing_value_column` / `bad_value` / `empty_input` / `zero_variance` → 退出码 **2**；`input_not_found` → 退出码 **3**。
- 运行环境：Python ≥3.10，仅标准库（`csv`/`json`/`statistics`）；无 GPU、无网络。
- 入口与示例：
  ```
  python scripts/zscore.py --input payload.csv --out-dir out
  python validate/validate.py --case C01-basic --out-dir out          # 自检
  python validate/validate.py --artifact <agent 产物目录>              # 验收（只判产物，不重跑）
  ```
- 机器可读接口描述：`tool.json`（entrypoint/parameters/outputs/errors 四段齐全，与脚本实际行为一致）。

## 3. idw-interpolate（skill · IDW 反距离权重插值技能 1.0.0）

- 用途：用反距离权重把已知散点观测插值到目标点，输出估测值与最近邻距离。
- 适用边界：确定性插值，**不提供误差估计**、不做空间自相关建模（需要误差/变差函数时应改用克里金）；命中已知点直接取观测值。
- 输入：
  - `--points <csv>`（必填）：`x,y,value`，坐标为本地平面直角坐标，`value` 无量纲。
  - `--targets <csv>`（必填）：`x,y[,value]`（`value` 可缺省，缺省按 0，不参与计算）。
  - `--power <float>`（可选，默认 `2.0`，**必须 > 0**）。
  - `--out-dir <dir>`（必填）。
- 输出：
  - `interpolated.csv`：表头 `x,y,value_est,nearest_dist`；`value_est` 与 `nearest_dist` 均保留 6 位小数，行序与目标点一致。
  - `run.json`：`{"mode":"idw","power":…,"source_points":…,"targets":…}`。
  - 失败：`bad_power` → 退出码 2；`bad_columns`（缺 x/y 列或非数值）→ 退出码 2；`input_not_found` → 退出码 3；均写 `error.json`。
- 运行环境：Python ≥3.10，仅标准库；无 GPU、无网络。
- 入口与示例：
  ```
  python scripts/run.py --points points.csv --targets targets.csv --out-dir out --power 2
  python validate/validate.py --case C01-hits --out-dir out                        # 自检（6 组给定用例）
  python validate/validate.py --case C01-hits --artifact <agent 产物目录>           # 验收：判 interpolated.csv 的 value_est 与 nearest_dist 两列
  ```
- 作为 skill 使用：把资产目录交给 agent（或给出 `SKILL.md` 路径），指令与边界写在 `SKILL.md`；验收方式见 `validate/readme.md`。

## 4. assess-workflow（skill · 示例评估工作流 1.0.0）

- 用途：把 grid-samples → zscore-normalize → idw-interpolate 串成三步最小工作流，产出汇总 `report.json`。
- 适用边界：示例编排；**只做串行三步**，不含并行、缓存或失败重试；被编排的三个资产须按 `external_assets.json` 放到本资产目录内。
- 输入：
  - `--assets-root <dir>`（必填）：本资产目录，其下需能按相对路径访问 `grid-samples/`、`zscore-normalize/`、`idw-interpolate/`。
  - `--out-dir <dir>`（必填）。
  - 目标点：本资产自带 `targets.csv`（`x,y`，5 个目标点）。
- 输出：`report.json`，字段 `workflow`/`version`/`steps[3]`/`data_points`/`value_mean`/`value_pstdev`/`targets`/`estimate_min`/`estimate_max`/`external_assets`。
  - `value_mean`/`value_pstdev` 是**原始观测值**的统计量（取自 z-score 工具输出）；`estimate_min`/`estimate_max` 是对**原始观测值**做 IDW（power=2）的估值范围；标准化只产统计量，不改变插值输入。
  - `external_assets` 只记声明的相对目录名，不写挂载绝对路径。
  - 中间产物：`out/tool/{result.csv,stats.json}`、`out/skill/{interpolated.csv,run.json}`。
  - 失败语义：外部资产缺失 → `error.json(external_asset_missing)` 退出码 **3**；工具失败 → `tool_failed` 退出码 **4**；技能失败 → `skill_failed` 退出码 **5**。
- 运行环境：Python ≥3.10，仅标准库；以子进程调用被编排资产，需要三个外部资产目录可读。
- 入口与示例：
  ```
  python scripts/run_workflow.py --assets-root . --out-dir out
  python validate/validate.py --case C01-end-to-end --out-dir out --assets-root .        # 自检
  python validate/validate.py --case C02-missing-external --out-dir out --assets-root <空目录>   # 预期错误
  python validate/validate.py --case C01-end-to-end --artifact <agent 产物目录>           # 验收：只判 report.json
  ```
- 外部资产挂载：按 `external_assets.json` 的 `target_path` 在本资产目录内提供同名目录（本次核验由 `mount_external.py` 在工作副本内建软链；原始包未被写入）。

---

## 资产间关系

`assess-workflow` 通过 `external_assets.json` 声明引用另外三个资产（均 `required: true`）：
`sciasset://2026ZD000042/demo/data/grid-samples`、`.../tool/zscore-normalize`、`.../skill/idw-interpolate`。
其余三个资产之间无引用关系。

## 使用前必读的边界

- 三个被编排资产没有版本锁文件（纯标准库），换 Python 主版本时数值格式化仍按 6 位小数，但 `statistics.pstdev` 精度随实现可能变化。
- 坐标全部为**无量纲本地平面坐标**，不涉及投影与单位换算；把示例换成本项目真实数据时需另行声明坐标系。
