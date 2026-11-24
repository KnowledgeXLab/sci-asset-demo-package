---
skill: sci-asset-verify-skill
skill_version: 1.2-beta.9
skill_commit: b21305b
skill_version_source: VERSION
generated_at: 2026-11-24T10:29:25+08:00
---

# demo-assets 资产包核验报告（对外交付口径）

## 1. 结论

本次按「对外发版」口径全量核验了 `examples/demo-assets` 资产包的 5 个资产（data 1 / tool 1 / skill 2 / task 1）：
**24 条用例全部执行、24 条与预期一致（通过率 24/24，无跳过、无未判定）**，固定清单判定 **P0 0 项 / P1 0 项**。
harbor 任务包的判分体系经 oracle/nop 双 trial 实测有效（reward 1.0 / 0.0），两个 skill 资产除自带用例外在
agent（DSH）上完成真实任务并通过产物门槛。

结论：**本包可交付**。23 列对外发版清单已生成并通过自检（0 error / 0 warning）。没有阻断项，也没有重要项；
只有 3 条改进建议（P2），且都不影响交付与复现。

需要说明的一处核验环境限制：harbor 首轮因宿主 `~/.docker/buildx` 不可写（沙箱限制，非资产问题）失败，
记 blocked 后在 `BUILDX_CONFIG` 指向可写目录的条件下重跑通过；两轮证据都留在本批次目录里。

## 2. 对比对象

- 被测对象：`examples/demo-assets`（`VERSION` 声明 1.1.0，未读作判据），5 个资产各 `asset_version` 均为 `1.0.0`
- 本次 run 目录：`asset-runs/run-20261124-102008/`
- expected output：各资产自带的 `validate/cases.json`（解析解/结构规则/错误语义约定）、`grid-samples/metadata.json`
  的声明与公式、`grid-stats-task/tests/data/points.csv`（verifier 自带真值）、`grid-samples`/`assess-workflow` 的 agent 产物门槛脚本
- 对比日期：2026-11-24（skill 版本与指纹见本文件 front matter 与 `probe-report.json` 的 `probe_fingerprint`）
- 执行位置：工作副本 `examples/.asset-work/run-20261124-102008/`（原始包只新增本批次目录，资产文件未改动）

## 3. 结果对比

| 资产（类型） | 计划 | 执行 | 通过 | 关键比对数值（expected → actual） | 判定 |
|---|---|---|---|---|---|
| `grid-samples`（data） | 5 | 5 | 5 | 记录数 100 → 100；columns 4 → 4；bbox x/y [0,9] → [0,9]；格子 100 → 100；公式复算 100 行最大偏差 0.0 ≤ 1e-06 | 通过 |
| `zscore-normalize`（tool） | 6 | 6 | 6 | z 值 -1.224745/0/1.224745 → 同值（6 位小数精确）；mean 2.0、pstdev 0.816497 → 同值；4 组错误用例退出码 2/2/3/2 与错误码全部一致 | 通过 |
| `idw-interpolate`（skill） | 7 + agent 1 | 8 | 8 | value_est 10/20、15、12.5 → 同值；nearest_dist 0/0、5、2.5 → 同值；4 组错误用例一致；agent 产物 `value_est_exact=0` | 通过 |
| `assess-workflow`（skill） | 2 + agent 1 | 3 | 3 | data_points 100 → 100；targets 5 → 5；steps 三步顺序一致；缺外部资产 rc=3 + `external_asset_missing`；agent 产物 4 项检查全 true | 通过 |
| `grid-stats-task`（task） | 1 + 离线 1 | 2 | 2 | oracle reward 1.0 → 1.0；nop reward 0.0 → 0.0；离线默认模式 rc=0、`--no-solution` verifier rc=1 | 通过 |
| **合计** | **24** | **24** | **24** | 通过率 24/24（分母 = 全部已执行用例，无跳过） | 通过 |

固定清单（`probe-report.json`，带 `--run-dir`）：P0-STRUCT / ENVELOPE / COMPLETE / VERIFY / SECRET / SAGE /
HARB-STRUCT / HARB-RUN 全部 pass；P1-DOC-REF / VERSION / DECL / VERIFY-DOC / HARB-ENVELOPE / HARB-LINT 全部 pass。
`P1-DOC-FACT` 机器标 na（需人工判读），本次人工抽查结果：`instruction.md` 的示例 JSON（count 67、value_mean 5.880597、
quadrant 17/17/17/16、value_sum 394）与 verifier 真值一致（由资产自带 `validate/validate.py` 机检覆盖），
各资产文档声明的记录数/列数/用例数与实体一致，未发现事实性偏差。
`P1-HARB-DATASET` 为 na（包内无 `dataset.toml` 显式数据集，任务目录是单任务包）。

## 4. 问题清单

### P0 阻断

无

### P1 重要

无

### P2 建议

| 编号 | 归属 | 问题与证据 | 影响 / 整改要求 |
|---|---|---|---|
| P2-1 | `grid-stats-task` | 官方 harbor CLI 在宿主 `~/.docker/buildx` 不可写时 `docker compose build` 直接失败（证据：`harbor-run-attempt-01-blocked-buildx.json`、`harbor/grid-stats-task-attempt-01-blocked-buildx/`）；设 `BUILDX_CONFIG` 后同一任务 oracle/nop 均通过（`harbor-run-report.json`） | 属核验环境限制而非资产缺陷；建议在 `validate/readme.md` 的 agent/harness 一节补一句「宿主 buildx 目录不可写时设 `BUILDX_CONFIG`」，减少他人复跑时的同一处卡点 |
| P2-2 | `assess-workflow` | `validate/readme.md` 用 `A01` 指代 agent 验收，而 `validate/cases.json` 只有 `C01`/`C02`（证据：两份文件对照） | 编号口径不统一，易被误读为「存在第三个给定用例」；建议在 readme 里注明 `A01` 是 agent 验收编号、不属 `cases.json` 给定用例 |
| P2-3 | `grid-stats-task` | `validate/validate.py` 自检默认把中间产物写到系统临时目录（`/tmp/grid-stats-validate-*/`），本批次为留证把它重定向到 run 目录（`validation-run/grid-stats-task/offline/`） | 不影响判定；建议给自检脚本加一个显式输出目录参数，便于把证据固定在同一批次目录内 |

<!-- coverage:begin -->
### 用例覆盖度（按资产类型）

各类型用例数均达到下限。

| 类型 | 计划 | 执行 | 通过 | 跳过 | 下限 | 判定 |
|---|---|---|---|---|---|---|
| data 数据 | 5 | 5 | 5 | 0 | ≥3 | ✅ 达标 |
| tool 工具 | 6 | 6 | 6 | 0 | ≥3 | ✅ 达标 |
| skill 技能 | 11 | 11 | 11 | 0 | ≥2 | ✅ 达标 |
| task 任务 | 2 | 2 | 2 | 0 | ≥1 | ✅ 达标 |
<!-- coverage:end -->

<!-- evidence-prune:begin -->
### 证据保留口径

本次跑完用例后按 skill 约定清理了中间产出（逐 case 工作目录 `*/work/`、探针 `out/`、以及`registration/` 之外的大体积实体文件）：清理 49 项、82.75 KB，保留报告类证据 504.08 KB。

**逐 case 的检查数值与判定仍在** `cases.json`、`comparison.json` 与 `validation-report.md` 里；被清理的只是可用原命令重跑复现的原始输出文件，清单见 `evidence-prune.json`。台账里被清理的 `actual_output` 已标记 `actual_pruned: true`。
<!-- evidence-prune:end -->

## 5. Sage A1.5 兼容性测试（附加，不计入通过率）

- 需求判定 `sage-need.json`：`needed=true`（包内含 skill 资产，验收须在 agent 上完成）
- 配置 `sage-config.json`：`status=configured`，地址与模型取自宿主 DSH profile，密钥从凭据文件内存解析（未落盘、未打印）；
  探测 `models` 接口返回 200 且 `Sage-A1.5` 在列（`probe_ok=true`）
- 执行：沿用同一 harness（`dsh` headless）只换后端模型为 `Sage-A1.5`
- 结果：`idw-interpolate` 与 `assess-workflow` 两个 skill 资产的 agent 产物门槛均 `gate_rc=0`、判定 pass（证据：`agent-sage/*-report.json`）
- 口径：Sage 结果**不进入通过率与覆盖度分母**，也不改变第 1 节的结论

## 6. 最终判定

| 维度 | 判定 |
|---|---|
| 包结构 / 包络 / 实体完整性 | 通过（5/5 资产包络合规，声明实体存在且摘要一致） |
| 资产自包含 | 通过（5/5 无越界；`assess-workflow` 的 3 条外部引用走 `external_assets.json` 合规通道） |
| 用例执行（给定用例） | 通过（21/21） |
| skill agent 验收 | 通过（2/2，harness=DSH，与 readme 建议一致、无需替换） |
| task 双 trial 判分 | 通过（oracle 1.0 / nop 0.0） |
| 对外发版清单（23 列） | 通过（5 行 × 23 列 + 用例明细 24 行，自检 0 error / 0 warning） |
| Sage A1.5 兼容性 | 通过（2/2，附加项，不计入判定） |
| 问题清单 | P0 无、P1 无、P2 3 条建议 |

综合结论：**本资产包按对外发版口径已完整核验，无阻断项与重要项，可交付**；剩余 3 条 P2 建议属改进项，
不影响可用性、可复现性与验收结论。
