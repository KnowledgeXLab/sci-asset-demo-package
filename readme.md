# demo-assets-1.2.1（示例资产包）

一个最小的示例资产包（v1.2.1）：**数据 1 个、工具 1 个、skill 2 个（其中 1 个工作流）、harbor task 1 个**，共 5 个资产。工作流通过 `external_assets.json` 引用另外三个资产。合规性与功能以核验报告为准，本 readme 只描述内容与用法。
所有资产都用 Python 标准库实现，无需联网、无需第三方依赖。

## 仓库内容

本仓库就是一个**可交付的示例资产包**，外加一次完整核验的产出：

```
.
├── grid-samples/  zscore-normalize/  idw-interpolate/  assess-workflow/  grid-stats-task/   # 5 个资产
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
| `idw-interpolate/` | skill | 反距离权重（IDW）插值技能 |
| `assess-workflow/` | skill（工作流） | 编排前三个资产：读数据 → 标准化 → 插值 → 汇总 `report.json` |
| `grid-stats-task/` | task | harbor（terminal-bench-science）格式任务：把 67 个网格点汇总成确定性 JSON 摘要；oracle 期望 reward=1、nop 期望 reward=0 |

> 规范里没有独立的 `workflow` 资产类型，工作流按 `skill` 登记，并在 `spec.metadata.asset_role: workflow` 与 `steps` 里标明角色。

## 资产编号

```
sciasset://2026ZD000042/demo/data/grid-samples
sciasset://2026ZD000042/demo/tool/zscore-normalize
sciasset://2026ZD000042/demo/skill/idw-interpolate
sciasset://2026ZD000042/demo/skill/assess-workflow
sciasset://2026ZD000042/demo/task/grid-stats-task
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

与通用结构的差别：task 资产的"实现"是 `environment/` + `solution/` + `tests/`（而不是 script/payload），
判定由 harbor 官方 CLI 的两条 trial 给出，不用 `validate/cases.json` 逐条跑。

## 怎么核验

本包用 **`sci-asset-verify-skill`** 核验。脚本级细节（每条检查项的口径、命令行参数、报告格式）见该仓库的 README：
<https://github.com/KnowledgeXLab/sci-asset-verify-skill>

在装好该 skill 的 agent（DSH / Claude Code / Codex 等）里，直接给它这段话即可：

```
用 sci-asset-verify-skill 自查 <本仓库路径> 这个资产包，按对外发版口径全量跑一遍：
含 harbor 任务的 oracle/nop 双 trial 和 Sage 附加测试，交付前我想知道还有哪些项没过。
```

它会依次做：盘点资产并读使用说明 → 固定清单判定（P0/P1 + 覆盖表）→ 跑各资产自带用例 →
harbor 任务跑官方 CLI 的 oracle（期望 reward=1）与 nop（期望 reward=0）→ 生成核验报告与 23 列对外发版清单。

本包用当前版本如实跑过一遍，预期结论：**24 条用例全部通过、固定清单 P0 0 / P1 0、harbor oracle=1 / nop=0**。
只想核验其中一部分时，把范围写进 prompt 即可（例如「只看 `grid-stats-task` 这个资产」）。

## 版本记录

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
- 附 2026-11-24 10:20:08 批次完整核验产出（24/24 用例通过，P0 0 / P1 0）
