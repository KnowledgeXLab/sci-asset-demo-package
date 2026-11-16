---
skill: sci-asset-verify-skill
skill_version: 1.2-beta.4-dev
skill_commit: bdf50dd
skill_version_source: VERSION
generated_at: 2026-11-16T16:12:28+08:00
---

# demo-assets-1.0.0 交付核验报告

## 1. 结论

本次对示例资产包 `demo-assets-1.0.0` 的 4 个资产（1 个 data、1 个 tool、2 个 skill，其中 `assess-workflow` 以 skill 登记、角色为 workflow）做了全量执行：包内自带的 **19 组给定用例全部执行、全部通过**，两个 skill 资产按各自 `validate/readme.md` 声明的门槛在 DSH agent 上完成 **2 组 agent 产物验收，全部通过**；合计 **21/21 通过**（分母 21，无跳过、无阻塞、无未判定）。包络、自包含、skill 测试说明三项机检均为 0 问题。

关键数值均与**独立复算**一致：`grid-samples` 的 CSV 摘要 `e696fc3c…b81d` 与声明相同、公式逐行复算最大偏差 `4.92e-07`（容差 `1e-06`）；`zscore-normalize` 的 z 值 `-1.224745/0.000000/1.224745`、`pstdev 0.816497` 与解析解相同；`idw-interpolate` 的解析解 `10/20`、`15`、`12.5` 与 `nearest_dist 0/5/2.5` 逐值相同；`assess-workflow` 的 `value_mean 15.699537`、`value_pstdev 2.318747`、`estimate_min 12.323535`、`estimate_max 18.208559` 与独立复算逐值相同。

**未发现 P0 阻断与 P1 重要问题**；仅有 2 条 P2 建议。结论：本批资产可交付。

## 2. 对比对象

| 项目 | 值 |
|---|---|
| 被测对象 | `demo-assets-1.0.0`：`grid-samples` 1.0.0（data）、`zscore-normalize` 1.0.0（tool）、`idw-interpolate` 1.0.0（skill）、`assess-workflow` 1.0.0（skill，角色 workflow） |
| 本次 run 目录 | `examples/demo-assets-1.0.0/asset-runs/run-20261116-160701/` |
| 执行环境 | Python 3.14（仅标准库）；工作副本 `examples/.asset-work/run-20261116-160701/`（原始包未被写入） |
| expected output 来源 | 包内声明（`asset.json`、`grid-samples/metadata.json`、各资产 `validate/cases.json` 与 `validate/readme.md`）+ 独立复算（`independent-check.json`，不复用包内脚本的判定逻辑） |
| 对比日期 | 2026-11-16 |

## 3. 结果对比表

### 3.1 汇总

| 范围 | 计划 | 执行 | 通过 | 失败 | 阻塞 | 跳过 | 未判定 | 通过率（分母） |
|---|---|---|---|---|---|---|---|---|
| 包内给定用例 | 19 | 19 | 19 | 0 | 0 | 0 | 0 | 19/19（分母 19 组给定用例） |
| skill agent 产物验收 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 2/2（分母 2 个 skill 资产） |
| 合计 | 21 | 21 | 21 | 0 | 0 | 0 | 0 | 21/21（分母 21，无未执行项） |

### 3.2 按资产

| 资产 | 类型 | 用例数 | 通过 | 关键检查（expected = actual） |
|---|---|---|---|---|
| `grid-samples` | data | 5 | 5 | 记录数 100、列 `id,x,y,value`、首行 `p001`、`bbox x[0,9]/y[0,9]`、网格 100 格全满、值域 `10.06741–20.4125`、公式最大偏差 `4.92e-07 ≤ 1e-06`、CSV `sha256` 与 `size_bytes 1895` 与声明一致 |
| `zscore-normalize` | tool | 6 | 6 | `C01` z 值 `-1.224745/0.000000/1.224745`、`mean 2.0`、`pstdev 0.816497`；其余 5 组非法输入分别返回 `rc=2`（`zero_variance`/`missing_value_column`/`bad_value`/`empty_input`）与 `rc=3`（`input_not_found`） |
| `idw-interpolate` | skill | 6 | 6 | `C01` `value_est 10/20` + `nearest_dist 0/0`；`C02` 均值 `15` + 距离 `5`；`C05`（`--power 1`）`12.5` + 距离 `2.5`；错误分支 `rc=3 input_not_found`、`rc=2 bad_columns`、`rc=2 bad_power` |
| `assess-workflow` | skill | 2 | 2 | `C01` `data_points 100`、`targets 5`、`steps` 三步顺序正确、统计量与估值范围与独立复算逐值一致；`C02` 缺外部资产 → `rc=3 external_asset_missing` |
| `idw-interpolate`（agent） | skill | 1 | 1 | agent 自写 `interpolated.csv`：`value_est 10.000000/20.000000`、`nearest_dist 0.000000/0.000000`（两列都判） |
| `assess-workflow`（agent） | skill | 1 | 1 | agent 自写 `report.json`：`data_points/targets/steps/estimate_range` 四项检查全部成立 |

`assess-workflow` 的外部引用（`grid-samples`、`zscore-normalize`、`idw-interpolate`，均 `required=true`）在副本内按 `external_assets.json` 的 `target_path` 挂载到位，未写入原始包；挂载记录见 `external-mounts.json`。

填表口径说明（不是缺陷）：清单「敏感级别」词表只有 `内部/敏感/高度敏感`，四个资产 `governance.access` 均为 `public`，按最低档填「内部」，属清单词表缺口；「资产关联」列只填本资产 `external_assets.json` 声明的编号，其余三个资产无外部引用故留空。

## 4. 问题清单

### P0 阻断

无

### P1 重要

无

### P2 建议

| 编号 | 问题与证据 | 影响 / 整改要求 |
|---|---|---|
| P2-1 | 四个资产 `spec.artifacts` 的声明范围口径不一致：`zscore-normalize` 声明了 `tool.json` 与 `readme.md`，`grid-samples` 声明了 `metadata.json`/`readme.md`，`idw-interpolate` 只声明 `SKILL.md` 与 `scripts/run.py`，四个资产都没有声明各自的 `validate/` 实体（证据：各资产 `asset.json`，`envelope-report.json` 全部 PASS） | 不影响校验与使用，但对外清单「格式\|接口」「规模\|数量」两列的证据链不齐；建议统一声明「实现 / 说明 / 用例」三类实体 |
| P2-2 | `grid-samples/usage/readme.md` 只有一句「直接读取 `payload/points.csv`」，而 `asset_protocol.prepare` 与 `asset_protocol.use` 都指向它，列含义、坐标与 `i` 规则要翻同级 `readme.md`（证据：`grid-samples/usage/readme.md`、`grid-samples/asset.json#spec.asset_protocol`） | 使用方按协议只看 prepare/use 时信息不足；建议把最小使用要点（列名、坐标、公式 `i` 规则）补进 `usage/readme.md` |

<!-- coverage:begin -->
### 用例覆盖度（按资产类型）

各类型用例数均达到下限。

| 类型 | 计划 | 执行 | 通过 | 跳过 | 下限 | 判定 |
|---|---|---|---|---|---|---|
| data 数据 | 5 | 5 | 5 | 0 | ≥3 | ✅ 达标 |
| tool 工具 | 6 | 6 | 6 | 0 | ≥3 | ✅ 达标 |
| skill 技能 | 10 | 10 | 10 | 0 | ≥2 | ✅ 达标 |
<!-- coverage:end -->

<!-- evidence-prune:begin -->
### 证据保留口径

本次跑完用例后按 skill 约定清理了中间产出（逐 case 工作目录 `*/work/`、探针 `out/`、以及`registration/` 之外的大体积实体文件）：清理 19 项、5.56 KB，保留报告类证据 335.67 KB。

**逐 case 的检查数值与判定仍在** `cases.json`、`comparison.json` 与 `validation-report.md` 里；被清理的只是可用原命令重跑复现的原始输出文件，清单见 `evidence-prune.json`。本批台账的 `actual_output` 指向的目录均仍存在（被清理的是目录内的实体文件），两个 skill 的 agent 产物 CSV/JSON 内容另已转存为 `artifact-interpolated.json` 与 `artifact-report-snapshot.json`，判定不依赖被清理的实体。
<!-- evidence-prune:end -->

### Sage A1.5 兼容性测试（附加项，不计入判定）

沿用与通用后端同一个 harness（DSH headless），只把后端换成 Sage A1.5 重跑两个 skill 资产的 agent 验收。

| 项目 | 值 |
|---|---|
| 后端 | `Sage-A1.5`（`https://discovery-api.intern-ai.org.cn/v1`，密钥经环境变量注入，不落盘） |
| 状态 | completed（配置由宿主机 DSH profile/凭据解析，`/models` 探测 200 且模型在列） |
| 结果 | 2/2 用例通过：`idw-interpolate` agent 产物 `value_est 10.000000/20.000000`、`nearest_dist 0.000000/0.000000`；`assess-workflow` agent 产物 `report.json` 四项检查全部成立——与通用后端结果一致 |
| 证据 | `agent-sage/idw-interpolate-report.json`、`agent-sage/assess-workflow-report.json`、`sage-config.json`、`sage-need.json`、`sage-a1.5-report.json` |
| 用途 | 仅反映换后端后的兼容性，**不参与通过率与覆盖度，也不改变第 5 节判定** |

## 5. 最终判定

| 维度 | 判定 |
|---|---|
| 资产实体完整性（包络 + 自包含） | 通过（4/4 资产包络合规、越界 0） |
| 给定用例（科学结果） | 通过（19/19） |
| skill agent 验收（产物门槛） | 通过（2/2） |
| 对外发版清单（23 列） | 通过（自检 0 error / 0 warning，4 行 × 23 列，用例明细 21 行） |
| 覆盖度 | 见覆盖度小节 |

综合结论：本批 21/21 用例通过、无 P0/P1 问题，**可进入交付**；P2 两条为可改进项，不构成交付阻断。
