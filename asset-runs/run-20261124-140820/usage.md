# 使用说明（本次核验整理）

路径基准：`<副本>` = 本次工作副本，字段/命令均取自各资产 `asset.json` 与包内 readme、SKILL.md。

## assess-workflow（skill，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/skill/assess-workflow`
- 用途：把 grid-samples 数据、zscore-normalize 工具与 idw-interpolate 技能串成「读数据 → 标准化 → 插值」三步工作流，输出汇总报告。
- 适用边界：固定三步顺序；三个外部资产必须按 `external_assets.json` 挂到本资产目录内，否则以 rc=3 报 external_asset_missing。
- 输入：本资产目录（含三个外部资产软链/副本）+ `targets.csv`（5 个目标点）。
- 输出：`report.json`（steps、data_points、value_mean/pstdev、targets、estimate_min/max、external_assets）；缺外部资产时 `error.json` + rc=3。
- 运行环境：Python ≥3.10，仅标准库；需外部资产就位。
- 入口/示例命令：`python3 scripts/run_workflow.py --assets-root <本资产目录> --out-dir <out>`；自检需 `--assets-root`：`python3 validate/validate.py --case C01-end-to-end --out-dir <dir> --assets-root <本资产目录>`
- 本地路径：`<副本>/assess-workflow`
- 外部资产依赖（`external_assets.json`）：`sciasset://2026ZD000042/demo/data/grid-samples`（v1.0.0）→ `grid-samples`; `sciasset://2026ZD000042/demo/tool/zscore-normalize`（v1.0.0）→ `zscore-normalize`; `sciasset://2026ZD000042/demo/skill/idw-interpolate`（v1.0.0）→ `idw-interpolate`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `assess-workflow/SKILL.md` | skill-instructions | `6000d575d465ec96…` | 1693 |
| `assess-workflow/scripts/run_workflow.py` | runner | `6d16f96ceb345967…` | 3445 |
| `assess-workflow/targets.csv` | input-template | `3546cdf785a1b642…` | 47 |
| `assess-workflow/external_assets.json` | external-references | `d55e406780cd511b…` | 785 |

## grid-samples（data，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/data/grid-samples`
- 用途：10×10 规则网格上的 100 个采样点（x、y、value），用于示例统计与插值的输入数据。
- 适用边界：示例规模数据，仅覆盖 0–9 的整数格网；不用于真实观测精度评估。
- 输入：无输入（数据资产）；读取方式为直接读取 `payload/points.csv` 与 `metadata.json`。
- 输出：`payload/points.csv`（列 id,x,y,value，100 行）、`metadata.json`（record_count/columns/formula/grid/bbox）。
- 运行环境：任意可读 CSV/JSON 的环境；数据本身为 UTF-8。
- 入口/示例命令：`cat payload/points.csv`；自检 `python3 validate/validate.py --case C01-metadata --out-dir <dir>`
- 本地路径：`<副本>/grid-samples`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `grid-samples/payload/points.csv` | primary-data | `e696fc3c86f9b972…` | 1895 |
| `grid-samples/metadata.json` | metadata | `ff6b585c548debbd…` | 711 |
| `grid-samples/readme.md` | readme | `e2e7a88bbc7823a7…` | 500 |

## grid-stats-task（task，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/task/grid-stats-task`
- 用途：harbor（terminal-bench-science）格式任务：把 67 个网格采样点汇总成确定性 JSON 摘要，由独立 verifier 逐字段核对。
- 适用边界：单一确定性任务；oracle trial 期望 reward=1、nop trial 期望 reward=0；需 docker + harbor CLI 执行。
- 输入：`environment/data/points.csv`（67 行，x,y,value）；`instruction.md` 给出字段与判定口径。
- 输出：`/app/output/summary.json`（count/value_sum/value_mean/x_extent/y_extent/quadrant_counts）；verifier 写 `/logs/verifier/reward.txt`。
- 运行环境：docker（environment/Dockerfile）+ harbor CLI 0.27.0；verifier 独立环境（environment_mode=separate）。
- 入口/示例命令：`harbor run -p grid-stats-task -a oracle|nop`；离线快检 `python3 validate/validate.py [--no-solution]`
- 本地路径：`<副本>/grid-stats-task`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `grid-stats-task/task.toml` | task-definition | `01633a51f282772d…` | 1098 |
| `grid-stats-task/instruction.md` | task-instruction | `7f1621a7a1304086…` | 1303 |
| `grid-stats-task/environment/data/points.csv` | primary-data | `96eaf6fc793ae6e5…` | 424 |
| `grid-stats-task/environment/Dockerfile` | environment | `e934fe9ab1b45d0f…` | 281 |
| `grid-stats-task/solution/solve.py` | reference-solution | `b0f829d85259e9fd…` | 1659 |
| `grid-stats-task/tests/test_summary.py` | verifier | `a43476e85fe39f3e…` | 4537 |
| `grid-stats-task/tests/test.sh` | verifier-entrypoint | `274fd5043ba80996…` | 570 |
| `grid-stats-task/tests/Dockerfile` | verifier-environment | `a91c09b1d5beadbb…` | 423 |
| `grid-stats-task/tests/data/points.csv` | verifier-ground-truth | `96eaf6fc793ae6e5…` | 424 |
| `grid-stats-task/readme.md` | documentation | `1aaa9e5792dd4cd1…` | 2886 |

## grid-stats-trajectory（trajectory，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/trajectory/grid-stats-trajectory`
- 用途：grid-stats-task 的一次成功运行轨迹（ATIF 格式，6 步）：计划 → 工具调用 → 结果 → 验证（reward=1）→ 结论。
- 适用边界：记录单次成功运行；不覆盖失败路径；结果只对该 task 与同一输入成立。
- 输入：无运行输入；`trajectory.json` 内含每一步的 role/type/时间与工具调用。
- 输出：`trajectory.json`（format=ATIF、steps=6、result_summary：count 67 / value_sum 394 / quadrant_counts）。
- 运行环境：任意 JSON 读取环境；校验仅需 Python ≥3.10。
- 入口/示例命令：`python3 validate/validate.py --case C01-structure`；第三方轨迹 `python3 validate/validate.py --artifact <含 trajectory.json 的目录>`
- 本地路径：`<副本>/grid-stats-trajectory`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `grid-stats-trajectory/trajectory.json` | trajectory-entrypoint | `a7d1591c1bc72eef…` | 2727 |
| `grid-stats-trajectory/readme.md` | readme | `1e3adfc41daae7bb…` | 1699 |

## grid-summary-benchmark（benchmark，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/benchmark/grid-summary-benchmark`
- 用途：基于 grid-stats-task 的可复现评测定义：字段精确匹配 0.8 + 产物自洽 0.2，阈值 1.0，含参考答案与两个样例产物。
- 适用边界：只评 summary.json 的 7 个字段与两条自洽约束；不做科学合理性判断。
- 输入：提交产物目录（含 `summary.json`）；`benchmark/run_evaluation.py --submission <dir> --out-dir <dir>`。
- 输出：`score.json`（score、passed、breakdown、problems）；缺产物时 problems 记录缺失且 passed=false。
- 运行环境：Python ≥3.10，仅标准库。
- 入口/示例命令：`python3 benchmark/run_evaluation.py --submission <dir> --out-dir <dir>`；自检 `python3 validate/validate.py --case C01-score-good --out-dir <dir>`
- 本地路径：`<副本>/grid-summary-benchmark`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `grid-summary-benchmark/benchmark/scoring-rubric.json` | scoring-rubric | `035e6afdb068ae00…` | 1017 |
| `grid-summary-benchmark/benchmark/run_evaluation.py` | evaluation-entrypoint | `1fad284f274ed1c3…` | 3927 |
| `grid-summary-benchmark/benchmark/reference/summary.json` | reference-answer | `46df25dc96939f5b…` | 252 |
| `grid-summary-benchmark/benchmark/cases/good/summary.json` | sample-submission-correct | `46df25dc96939f5b…` | 252 |
| `grid-summary-benchmark/benchmark/cases/bad/summary.json` | sample-submission-wrong | `ab6fc3c17644f028…` | 252 |
| `grid-summary-benchmark/readme.md` | readme | `1cce7f6987f3c78a…` | 2058 |

## idw-interpolate（skill，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/skill/idw-interpolate`
- 用途：反距离权重（IDW）插值：按已知散点估测目标点取值，并给出最近邻距离。
- 适用边界：幂次 power>0；不考虑障碍、各向异性与地统计变异函数；已知点为空或列缺失按错误返回。
- 输入：已知点 CSV（x,y,value）与目标点 CSV（x,y）；`--points`、`--targets`、`--power`（默认 2）。
- 输出：`interpolated.csv`（x,y,value_est,nearest_dist，6 位小数）；失败写 `error.json`（input_not_found/bad_columns/bad_power/no_source_points）。
- 运行环境：Python ≥3.10，仅标准库；不需要容器。
- 入口/示例命令：`python3 scripts/run.py --points <p.csv> --targets <t.csv> --power 2 --out-dir <out>`；agent 验收 `python3 validate/validate.py --case C01-hits --artifact <产物目录>`
- 本地路径：`<副本>/idw-interpolate`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `idw-interpolate/SKILL.md` | skill-instructions | `1ff58e97b3d19bd0…` | 1057 |
| `idw-interpolate/scripts/run.py` | runner | `09449d6477079801…` | 2758 |

## linear-model（model，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/model/linear-model`
- 用途：确定性二维线性回归模型（prediction = 1.0 + 0.5·x + 0.25·y），权重随包，纯标准库推理。
- 适用边界：仅两特征线性外推，无不确定度估计；输入缺 `x`/`y` 列按错误返回。
- 输入：CSV，必需列 `x`、`y`，可选 `id`；`--input <csv>`。
- 输出：`predictions.csv`（id,x,y,prediction，6 位小数）；失败写 `error.json` 并以 rc=2/3 退出。
- 运行环境：Python ≥3.10，仅标准库；无需 GPU。
- 入口/示例命令：`python3 model/predict.py --input <csv> --out-dir <out>`；自检 `python3 validate/validate.py --case C01-predict --out-dir <dir>`
- 本地路径：`<副本>/linear-model`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `linear-model/model/weights.json` | model-weights | `aca2cbed55d9cabf…` | 315 |
| `linear-model/model/predict.py` | inference-implementation | `dc552914a47a7f36…` | 3658 |
| `linear-model/payload/samples.csv` | sample-input | `9562e15076abdac1…` | 61 |
| `linear-model/readme.md` | readme | `3051066953b16384…` | 1453 |

## python-runtime（environment，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/environment/python-runtime`
- 用途：示例资产所需的最小可复现运行环境声明：Python ≥3.10、仅标准库、无网络、1 CPU / 1 GB。
- 适用边界：只声明并自检环境；不含科学计算能力，也不做第三方依赖安装。
- 输入：无数据输入；`environment/requirements.lock` 声明依赖（当前为空）。
- 输出：`runtime-report.json`（ok、python 版本、标准库可用性、third_party_present）。
- 运行环境：linux 容器（Dockerfile 基镜像 Python 3.12，python_requires ≥3.10），1 CPU / 1024 MB / 无网络 / 0 GPU。
- 入口/示例命令：`python3 environment/runtime_check.py --out-dir <out>`；自检 `python3 validate/validate.py --case C01-runtime-ok --out-dir <dir>`
- 本地路径：`<副本>/python-runtime`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `python-runtime/environment/Dockerfile` | environment-definition | `7958cbc25cfe5c21…` | 475 |
| `python-runtime/environment/requirements.lock` | dependency-lock | `aa1fbeb167ea6625…` | 206 |
| `python-runtime/environment/runtime_check.py` | environment-self-check | `c8ab459b9b45629d…` | 2240 |
| `python-runtime/readme.md` | readme | `8dade78063e3f9ff…` | 1708 |

## zscore-normalize（tool，v1.0.0）

- 资产ID：`sciasset://2026ZD000042/demo/tool/zscore-normalize`
- 用途：把 CSV 中 `value` 列按总体标准差（pstdev）做 z-score 标准化，并输出统计量。
- 适用边界：单列数值标准化；方差为 0（单条记录）按错误处理，不做平滑。
- 输入：CSV，必需列 `value`（可另有 `id`）；`--input <csv>`。
- 输出：`result.csv`（原列 + `zscore`，6 位小数）与 `stats.json`（n/mean/pstdev）；失败时写 `error.json` 并以 rc=2/3 退出。
- 运行环境：Python ≥3.10，仅标准库；无网络。
- 入口/示例命令：`python3 scripts/zscore.py --input <csv> --out-dir <out>`；自检 `python3 validate/validate.py --case C01-basic --out-dir <dir>`
- 本地路径：`<副本>/zscore-normalize`

| 声明实体 | 角色 | SHA256（前 16 位） | 字节 |
|---|---|---|---|
| `zscore-normalize/scripts/zscore.py` | implementation | `78a0549c2fb8422c…` | 2308 |
| `zscore-normalize/tool.json` | method-manifest | `eb79978e223f8b51…` | 963 |
| `zscore-normalize/readme.md` | readme | `dad4ddf60fb999e6…` | 365 |

