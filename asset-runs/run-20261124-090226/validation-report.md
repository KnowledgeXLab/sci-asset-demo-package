---
skill: sci-asset-verify-skill
skill_version: 1.2-beta.9
skill_commit: b21305b
skill_version_source: VERSION
generated_at: 2026-11-24T09:19:51+08:00
---

# demo-assets 资产包核验报告（run-20261124-090226）

## 1. 结论

本次对 `examples/demo-assets` 的 5 个资产（data 1 / tool 1 / skill 2 / task 1）做全量核验：给定用例 20 组 + agent 产物验收 2 组，共 22 组全部执行且全部与 expected output 一致（22/22，失败 0、阻塞 0、未判定 0）；harbor 任务包的 oracle/nop 双 trial 均符合预期（reward 1.0 / 0.0）。

结论：**功能与声明的可执行性全部通过，可交付**；但存在 1 项 P1（`grid-stats-task/instruction.md` 的示例 `quadrant_counts` 与实际期望值及文档自身规则矛盾，会误导被测 agent），建议修完再对外发版。机器判定的 P0 为 0、P1 为 0（`probe-report.json`），本报告的唯一 P1 来自人工判读的 `P1-DOC-FACT`。

## 2. 对比对象

| 项目 | 值 |
|---|---|
| 被测对象 | `examples/demo-assets`（5 个资产，各 1.0.0） |
| 本次 run 目录 | `asset-runs/run-20261124-090226/`（执行在工作副本 `examples/.asset-work/run-20261124-090226/`，原件未改动） |
| expected output 来源 | 各资产自带 `validate/cases.json` + `validate/validate.py`/`validate/readme.md` 的门槛；task 为 `tests/test_summary.py` 的自带真值 |
| 对比日期 | 2026-11-24 |
| probe 指纹 | `e68c608a04d80717…`（`probe-report.json`），判定 P0 0 / P1 0，覆盖 pass 14 / na 2 |

## 3. 结果对比表

### 3.1 汇总（分母＝全部计划用例，均已执行）

| 资产 | 类型 | 计划 | 执行 | 通过 | 失败 | 未判定 | 通过率 |
|---|---|---|---|---|---|---|---|
| 规则网格采样点数据 `grid-samples` | data | 5 | 5 | 5 | 0 | 0 | 5/5 |
| z-score 标准化工具 `zscore-normalize` | tool | 6 | 6 | 6 | 0 | 0 | 6/6 |
| IDW 反距离权重插值技能 `idw-interpolate` | skill | 7 | 7 | 7 | 0 | 0 | 7/7（含 agent 产物 1） |
| 示例评估工作流 `assess-workflow` | skill | 3 | 3 | 3 | 0 | 0 | 3/3（含 agent 产物 1） |
| 网格采样点汇总任务 `grid-stats-task` | task | 1 | 1 | 1 | 0 | 0 | 1/1（双 trial） |
| **合计** | — | **22** | **22** | **22** | **0** | **0** | **22/22** |

### 3.2 关键检查点（差异＝0 的项）

| case | 关键字段 | expected | actual | 判定 |
|---|---|---|---|---|
| `grid-samples` C01–C05 | 记录数/列集合/bbox/网格完整性/公式最大偏差 | 100、`id,x,y,value`、x[0,9]、y[0,9]、10×10 全覆盖、≤1e-06 | 100、同左、同左、同左、全覆盖、4.92e-07 | pass |
| `zscore-normalize` C01 | `result.csv.zscore`、`stats.json` | `-1.224745/0.000000/1.224745`、n=3 mean=2.0 pstdev=0.816497 | 完全一致 | pass |
| `zscore-normalize` C02–C06 | 退出码 / `error.json.error` | 2(zero_variance/missing_value_column/bad_value/empty_input)、3(input_not_found) | 完全一致 | pass |
| `idw-interpolate` C01/C02/C05 | `value_est`、`nearest_dist`（两列都判） | 10/20、15、12.5；0/0、5、2.5 | 完全一致 | pass |
| `idw-interpolate` C03/C04/C06 | 退出码 / `error.json.error` | 3(input_not_found)、2(bad_columns)、2(bad_power) | 完全一致 | pass |
| `assess-workflow` C01 | `data_points`/`targets`/`steps`/`estimate` 范围 | 100、5、`read_data,zscore_normalize,idw_interpolate`、min<max | 100、5、同左、12.323535 < 18.208559 | pass |
| `assess-workflow` C02 | 退出码 / `error.json.error` | 3 / `external_asset_missing` | 一致 | pass |
| `grid-stats-task` C01 | `oracle_reward` / `nop_reward` | 1.0 / 0.0 | 1.0 / 0.0 | pass |
| `idw-interpolate` A01（agent 产物） | agent_rc / gate_rc | 0 / 0 | 0 / 0 | pass |
| `assess-workflow` A01（agent 产物） | agent_rc / gate_rc | 0 / 0 | 0 / 0 | pass |

`grid-stats-task` 另有离线口径两组自检，均符合预期：参考解 + verifier 通过（rc 0/0），`--no-solution` 时 verifier 判不通过（verifier rc=1，证明门槛非恒绿）。

## 4. 问题清单

### P0 阻断

无

### P1 重要

| 编号 | 归属 | 问题与证据 | 影响 / 整改要求 |
|---|---|---|---|
| P1-1（`P1-DOC-FACT`） | `grid-stats-task` | `instruction.md` 的「字段固定如下」示例给出 `quadrant_counts` 全为 0（Q1–Q4 = 0/0/0/0），而 verifier 独立复算的期望值是 Q1=17、Q2=17、Q3=17、Q4=16（证据：`tests/test_summary.py` 的 `expected()`、参考解输出 `solution/solve.py` 实跑 summary.json、`cases/grid-stats-task/C01-offline/`）；示例同时违反文档自己写的「四个计数之和必须等于 count（67）」 | 被测 agent 若照抄示例即被判 0 分，等于任务指令与实际判分口径不一致。整改：把示例里的 `quadrant_counts` 改为 `{"Q1":17,"Q2":17,"Q3":17,"Q4":16}`（或把示例明确标注为「仅示意键名与类型，数值须自行计算」） |

### P2 建议

| 编号 | 归属 | 现象与证据 | 建议 |
|---|---|---|---|
| P2-1 | `grid-stats-task` | `asset.json` 的 `task_classes[].id` 为 `operation:task-execution`，不在对外发版清单的注册词表内（`assets/external-list-schema.json` 的 `任务\|操作标签` options） | 改用词表内取值（本次清单按语义填 `operation:analysis`）或由清单维护方注册该标签 |
| P2-2 | `idw-interpolate` | `scripts/run.py` 存在 `no_source_points` 错误分支（已知点表为空，退出码 2），`SKILL.md`/`validate/readme.md` 的失败语义未列出 | 文档补一行，或在实现里把空点表并入 `bad_columns` |
| P2-3 | `grid-samples` | `validate/validate.py` 用 `eval()` 执行 `metadata.formula.expr`，本次用例 C05 因此通过 | 示例可接受；作为模板推广到第三方 `metadata.json` 时建议改受限表达式解析 |
| P2-4 | `grid-samples` | `validate/validate.py` 的 `--case` 默认值是 `C01`，但 `validate/cases.json` 的 id 是 `C01-metadata`～`C05-formula`；默认值会落到「跑全部检查」分支且不报未知用例，与 `zscore-normalize`/`idw-interpolate` 的 `validate.py`（未知 case 退出 2）行为不一致 | 默认值改为某个真实 case id，或未知 id 一律退出 2 |

<!-- coverage:begin -->
### 用例覆盖度（按资产类型）

各类型用例数均达到下限。

| 类型 | 计划 | 执行 | 通过 | 跳过 | 下限 | 判定 |
|---|---|---|---|---|---|---|
| data 数据 | 5 | 5 | 5 | 0 | ≥3 | ✅ 达标 |
| tool 工具 | 6 | 6 | 6 | 0 | ≥3 | ✅ 达标 |
| skill 技能 | 10 | 10 | 10 | 0 | ≥2 | ✅ 达标 |
| task 任务 | 1 | 1 | 1 | 0 | ≥1 | ✅ 达标 |
<!-- coverage:end -->

<!-- evidence-prune:begin -->
### 证据保留口径

本次跑完用例后按 skill 约定清理了中间产出（逐 case 工作目录 `*/work/`、探针 `out/`、以及`registration/` 之外的大体积实体文件）：清理 55 项、25.63 KB，保留报告类证据 455.90 KB。

**逐 case 的检查数值与判定仍在** `cases.json`、`comparison.json` 与 `validation-report.md` 里；被清理的只是可用原命令重跑复现的原始输出文件，清单见 `evidence-prune.json`。台账里被清理的 `actual_output` 已标记 `actual_pruned: true`。

补充说明（本次执行细节）：`prune_evidence.py` 的 harbor 白名单按 job 目录相对路径匹配，未命中 `verifier/reward.txt`，首次清理把 oracle/nop 的逐 trial reward 证据一并删掉了；为保证证据链完整，随后重新执行了一次 `harbor_run.py`（job 级 `result.json` 与新的逐 trial `verifier/reward.txt|json`、`test-stdout.txt` 均保留在 `harbor/grid-stats-task/` 下，本次未再 prune）。该问题属核验工具的缺陷，与资产无关。
<!-- evidence-prune:end -->

### Sage A1.5 兼容性测试（附加项，不计入判定）

| 项目 | 值 |
|---|---|
| 后端 | `Sage-A1.5`（`https://discovery-api.intern-ai.org.cn/v1`，密钥经环境变量注入，未落盘；配置解析见 `sage-config.json`） |
| 状态 | completed |
| 结果 | 2/2 通过：`idw-interpolate` 与 `assess-workflow` 的 agent 验收任务在同一 DSH harness 上换 Sage 后端后，产物门槛均通过（`agent-sage/*-report.json`）；与通用后端结果并列，只作对比 |
| 用途 | 仅反映换后端后的兼容性，**不参与通过率与覆盖度，也不改变第 1 节的判定** |

## 5. 最终判定

| 维度 | 判定 |
|---|---|
| 资产包结构与包络 | pass（`P0-STRUCT`/`P0-ENVELOPE`/`P0-COMPLETE`/`P0-SECRET` 全 pass） |
| 自包含与外部引用 | pass（5 个资产自包含违规 0；`external_assets.json` 3 条引用合规，同包解析 3/3 建成软链） |
| 给定用例（自带用例/门槛） | pass 22/22（含 2 组 agent 产物验收） |
| skill 的 agent 验收（readme 三要素 + 产物门槛） | pass 2/2 |
| task 的 harbor 双 trial | pass 1/1（oracle 1.0 / nop 0.0） |
| 覆盖度 | 各类型均达 `case-minimums.json` 下限 |
| 问题清单 | P0 0 / P1 1 / P2 4 |

综合：**除 P1-1（`grid-stats-task/instruction.md` 示例 `quadrant_counts` 数值错误）外，其余检查全部通过**；修掉该条后可按对外发版口径交付。
