# demo-assets-1.3.0（示例资产包）

一个示例资产包（v1.3.0）：**八类资产各至少 1 个**——数据、工具、模型、环境、skill（2 个，其中 1 个工作流）、task（harbor 格式）、trajectory、benchmark，共 9 个资产。工作流通过 `external_assets.json` 引用另外三个资产；task / trajectory / benchmark 三者按 asset id 相互关联。合规性与功能以核验报告为准，本 readme 只描述内容与用法。
所有资产都用 Python 标准库实现，无需联网、无需第三方依赖。

## 仓库内容

本仓库就是一个**可交付的示例资产包**，外加一次完整核验的产出：

```
.
├── grid-samples/  zscore-normalize/  linear-model/  python-runtime/        # data / tool / model / environment
├── idw-interpolate/  assess-workflow/                                      # skill ×2（其一为工作流）
├── grid-stats-task/  grid-stats-trajectory/  grid-summary-benchmark/      # task / trajectory / benchmark
├── readme.md                                                                              # 本说明
├── VERSION                                                                                # 包版本
└── asset-runs/run-<批次>/                                                                 # 一次核验的完整证据
    ├── validation-report.md        # 结果对比与判定（问题清单含归属列）
    ├── registration/               # 23 列对外发版清单（xlsx + 行数据）
    ├── cases.json / comparison.json / coverage.json
    ├── probe-report.json           # 固定清单判定的确定性事实 + 覆盖表
    ├── agent/  agent-sage/         # skill 的 agent 验收产物（默认后端 / Sage 后端）
    ├── harbor/                     # harbor 任务的 oracle/nop 双 trial 证据（仅保留 reward 相关文件）
    └── *.json                      # 包络、自包含、外部挂载、Sage、harbor 执行等机检结果
```

核验产出由 `sci-asset-verify-skill` 生成；`asset-runs/` 只作参考，**再次核验时不会被读取或对比**（skill 规定不参考包内已有结果）。

## 目录

| 目录 | 资产类型 | 说明 |
|---|---|---|
| `grid-samples/` | data | 10×10 网格 100 个采样点（`payload/points.csv` + `metadata.json`，含可复算公式声明） |
| `zscore-normalize/` | tool | 把 CSV 的 `value` 列做 z-score 标准化 |
| `linear-model/` | model | 确定性线性回归（`prediction = 1.0 + 0.5x + 0.25y`），权重随包，推理仅标准库 |
| `python-runtime/` | environment | 最小运行环境声明：Python ≥ 3.10、仅标准库、无网络，含 Dockerfile 与环境自检 |
| `idw-interpolate/` | skill | 反距离权重（IDW）插值技能 |
| `assess-workflow/` | skill（工作流） | 编排前三个资产：读数据 → 标准化 → 插值 → 汇总 `report.json` |
| `grid-stats-task/` | task | harbor（terminal-bench-science）格式任务：把 67 个网格点汇总成确定性 JSON 摘要；oracle 期望 reward=1、nop 期望 reward=0 |
| `grid-stats-trajectory/` | trajectory | 上述 task 的一次成功运行轨迹（ATIF，6 步：计划→调用→结果→验证→结论） |
| `grid-summary-benchmark/` | benchmark | 基于该 task 的评测定义：字段精确匹配 0.8 + 产物自洽 0.2，阈值 1.0，含参考答案与样例 |

> 规范里没有独立的 `workflow` 资产类型，工作流按 `skill` 登记，并在 `spec.metadata.asset_role: workflow` 与 `steps` 里标明角色。

## 资产编号

```
sciasset://2026ZD000042/demo/data/grid-samples
sciasset://2026ZD000042/demo/tool/zscore-normalize
sciasset://2026ZD000042/demo/model/linear-model
sciasset://2026ZD000042/demo/environment/python-runtime
sciasset://2026ZD000042/demo/skill/idw-interpolate
sciasset://2026ZD000042/demo/skill/assess-workflow
sciasset://2026ZD000042/demo/task/grid-stats-task
sciasset://2026ZD000042/demo/trajectory/grid-stats-trajectory
sciasset://2026ZD000042/demo/benchmark/grid-summary-benchmark
```

`project-id` 用示例编号 `2026ZD000042`（虚构，仅用于演示格式）；真实项目按其任务书首页的编号填写。

## 每个资产里有什么

通用结构（`grid-samples/`、`zscore-normalize/`、`idw-interpolate/`、`assess-workflow/`）：

```
<资产>/
├── asset.json                 # 公共包络（schema_version 1.0.0；四段 asset_id、task_classes、governance 等）
├── readme.md | SKILL.md       # 说明与使用方式
├── usage/readme.md            # 准备/调用说明
├── script / payload / …       # 实现、数据或指令
├── validate/                  # 用例定义 validate/cases.json + 自检脚本 validate.py
└── external_assets.json       # 可选：声明本资产引用的**其他资产**（示例中只有工作流有）
```

### harbor task 的目录约定（`grid-stats-task/`）

```
grid-stats-task/
├── asset.json                 # asset_type=task
├── readme.md                  # 说明
├── instruction.md             # 给被测 agent 的任务指令（字段与判定口径）
├── task.toml                  # harbor 1.4 任务声明（环境/超时/产物）
├── environment/
│   ├── Dockerfile             # 被测环境镜像
│   └── data/points.csv        # 输入数据
├── solution/
│   ├── solve.sh               # oracle trial 的入口
│   └── solve.py               # 参考解
├── tests/
│   ├── Dockerfile             # verifier 独立环境（environment_mode=separate）
│   ├── data/points.csv        # verifier 自带真值
│   ├── test.sh                # 写 /logs/verifier/reward.txt（1/0）
│   └── test_summary.py        # 独立复算 + 逐字段比对产物
└── validate/                  # cases.json（oracle+nop 即一条用例）+ readme.md + 离线自检 validate.py
```

与通用结构的差别：

| 类型 | 实现位置 | 判定方式 |
|---|---|---|
| `task` | `environment/` + `solution/` + `tests/` | harbor 官方 CLI 的 oracle/nop 两条 trial |
| `model` | `model/weights.json` + `model/predict.py` | `validate/cases.json` 四条（数值、可复现、两类错误） |
| `environment` | `environment/Dockerfile` + `requirements.lock` + `runtime_check.py` | 环境自检四条（版本门槛、标准库、无第三方、声明一致） |
| `trajectory` | `trajectory.json`（ATIF，6 步） | 结构/结果自洽/证据链/门槛有效四条 |
| `benchmark` | `benchmark/scoring-rubric.json` + `run_evaluation.py` + `reference/` | 评分引擎与规则自洽五条 |

## 怎么核验

本包用 **`sci-asset-verify-skill`** 核验。脚本级细节（每条检查项的口径、命令行参数、报告格式）见该仓库的 README：
<https://github.com/KnowledgeXLab/sci-asset-verify-skill>

在装好该 skill 的 agent（DSH / Claude Code / Codex 等）里，直接给它这段话即可：

```
用 sci-asset-verify-skill 自查 <本仓库路径> 这个包，
全量跑一遍，清单按对外发版口径填，交付前我想知道还有哪些项没过。
```

它会依次做：盘点资产并读使用说明 → 固定清单判定（P0/P1 + 覆盖表）→ 跑各资产自带用例 →
harbor 任务跑官方 CLI 的 oracle（期望 reward=1）与 nop（期望 reward=0）→ 生成核验报告与 23 列对外发版清单。

预期结论：**固定清单 P0 0 / P1 0**、**40 例用例全部通过**（覆盖度 sufficient）、
`grid-stats-task` 的 harbor oracle=1 / nop=0。随包 `asset-runs/run-20261124-140820` 就是这一批完整产出，
可直接对照。
只想核验其中一部分时，把范围写进 prompt 即可（例如「只看 `grid-stats-task` 这个资产」）；harbor 任务的 oracle/nop 双 trial 与 Sage 附加测试由 skill 按包内情况自动触发，不必在 prompt 里点名。

## 版本记录

### 1.3.0 — 2026-11-24

**补齐八类资产**（新增 model / environment / trajectory / benchmark 四个示例资产）

- `linear-model`（model）：确定性线性回归，权重随包、推理仅标准库；4 条用例（数值、可复现、缺列、缺文件）
- `python-runtime`（environment）：Python ≥ 3.10 + 仅标准库 + 无网络的容器声明，含 Dockerfile、空依赖锁与环境自检；
  4 条用例（自检通过、无第三方、版本门槛生效、Dockerfile 与声明一致）
- `grid-stats-trajectory`（trajectory）：`grid-stats-task` 的一次成功运行轨迹（ATIF，6 步，含验证证据 reward=1）；
  4 条用例（结构、结果自洽、证据链、删验证步必须不通过）
- `grid-summary-benchmark`（benchmark）：基于该 task 的评测定义（字段精确匹配 0.8 + 自洽 0.2，阈值 1.0，含参考答案与正/负样例）；
  5 条用例（满分、篡改不通过、规则自洽、参考答案自洽、缺产物）
- 三者按 asset id 关联：trajectory 声明 `task_ids`/`environment_id`，benchmark 声明 `task_ids` 与 `tasks[].id`

校验结论：9 个资产包络 jsonschema 全部通过；固定清单 P0 0 / P1 0。

### 1.2.1 — 2026-11-24

**本 readme 的排版与内容同步修正**（资产与核验结论均未变）

- 修掉「每个资产里有什么」后面坏掉的空代码块：改为「通用结构」+「harbor task 的目录约定」两小节，各自独立成块
- 资产构成写准：数据 1 / 工具 1 / skill 2（其中 1 个工作流）/ harbor task 1 = **5 个资产**
  （原文仍写"4 个资产"、且漏掉 `grid-stats-task/`）
- 「仓库内容」补 `VERSION`、`grid-stats-task/`、`probe-report.json`、`harbor/`（oracle/nop 证据）
- 新增「怎么核验」小节：给出用 `sci-asset-verify-skill` 核验本包时的 prompt，脚本细节指向该 skill 仓库 README
- 章节顺序调整：「仓库内容」提到最前（在「目录」之前），先讲仓库里有什么再看资产明细

### 1.2.0 — 2026-11-24

- 新增 harbor（terminal-bench-science）格式的 task 示例资产 `grid-stats-task/`：oracle 期望 reward=1、nop 期望 reward=0；
  verifier 与 agent 沙箱隔离（`environment_mode=separate`）、自带真值、`harbor lint` 无发现
- `grid-stats-task`：修正 instruction 示例值（`quadrant_counts` 应为 17/17/17/16）、`task_classes` 改用词表内取值；
  `validate/validate.py` 增加"示例值 vs 判分口径"自检
- `idw-interpolate`：补 `no_source_points` 失败语义与用例 `C07-no-source-points`（用例 6 → 7 组）
- `grid-samples`：`validate.py` 用白名单 AST 求值替代 `eval()`；`--case` 默认值对齐 `cases.json`，未知 id 直接 exit 2
- `assess-workflow`：readme 注明 `A01` 是 agent 验收编号、不属于 `cases.json` 给定用例
- 附完整核验产出：`asset-runs/run-20261124-140820`（9 个资产、40 例用例全部通过、覆盖度 sufficient、
  P0 0 / P1 0、harbor oracle=1 / nop=0）
