---
skill: sci-asset-verify-skill
skill_version: 1.3-beta.1
skill_commit: feebb76
skill_version_source: VERSION
generated_at: 2026-11-24T14:15:29+08:00
---

## 1. 结论

本次对示例资产包 `demo-assets`（v1.3.0，9 个资产覆盖 8 类资产类型）做了全量核验：包络校验、自包含校验、固定清单判定、38 组给定用例、2 组 skill 的 agent 验收、以及 harbor 任务的 oracle/nop 双 trial 全部执行完毕，**计划 40 例全部执行且全部通过（40/40，100%，分母为本次计划并执行的全部用例，无 skipped / blocked / not_evaluated）**。固定清单判定 **P0 0 条 / P1 0 条**，另有 3 条 P2 建议。Sage A1.5 兼容性附加测试同样通过（2/2，不计入判定）。

交付前需要知道的结论是：**没有阻断项，也没有 P1 项；本包按对外发版口径可以交付**，剩下的是 3 条可改进建议（见第 4 节 P2）。需要如实说明的两点执行口径：① 包内已有一个历史批次 `asset-runs/run-20261124-102008`，按 skill 规定**未读取、未对比**，本次结论只来自资产实体、资产自身声明与独立复算；② 外部资产挂载只在工作副本内进行（`mount_external.py` 软链到副本内其他资产），核验对象始终是原始包，因此固定清单以原始包为准——在工作副本上跑 `probe_package.py` 会把这三条合规挂载软链误判为越界（`P0-COMPLETE`），而 `check_selfcontained.py` 对同一批软链判为合规 note，两者口径差异已在 `selfcontained-workcopy.json` 留痕。

## 2. 对比对象

| 项目 | 值 |
|---|---|
| 被测对象 | `demo-assets` v1.3.0（`VERSION`），9 个资产：data / tool / model / environment / skill×2 / task / trajectory / benchmark |
| 核验工具 | `sci-asset-verify-skill` 1.3-beta.1（commit `feebb76`，`skill-update.json` 记录已是最新） |
| 本次批次 | `asset-runs/run-20261124-140820/`（唯一批次，历史批次未读取） |
| 执行位置 | 工作副本 `examples/.asset-work/run-20261124-140820`（774 文件 / 747525 字节，与源一致） |
| expected output 来源 | 各资产自带 `validate/validate.py` 内置真值、`benchmark/reference/summary.json`、`tests/test_summary.py`、task 的 oracle/nop 期望 reward |
| 对比日期 | 2026-11-24（+08:00） |
| probe 指纹 | `df96ebe112592edc`（原始包）；固定清单 P0 0 / P1 0 |

## 3. 结果对比

按资产汇总（逐 case 明细见 `cases.json`、`comparison.json`，逐 case 证据在 `validation-run/<资产>/<用例>/`）：

| 资产（类型） | 用例 | 通过 | 关键判据与本次实际结果 |
|---|---|---|---|
| `grid-samples`（data） | 5 | 5 | 元数据声明、列结构与行序、CSV 可读、bbox/网格完整性、`metadata.formula` 逐行复算 100 行；最大偏差 ≤1e-6 |
| `zscore-normalize`（tool） | 6 | 6 | 解析解 `-1.224745 / 0 / 1.224745`、mean 2.0、pstdev 0.816497；4 类非法/边界输入均返回约定 rc 与 `error.json` 码 |
| `idw-interpolate`（skill） | 8 | 8 | 7 组给定（解析解 3、非法 4）+ 1 组 agent 验收；命中点 `value_est`=10/20、`nearest_dist`=0/0，`--power 1` 得 12.5；agent 产物经 `--artifact` 门槛判通过 |
| `assess-workflow`（skill） | 3 | 3 | 2 组给定 + 1 组 agent 验收；`steps` 顺序为 read_data→zscore_normalize→idw_interpolate，data_points=100、targets=5、estimate 12.3235–18.2086；缺外部资产按 rc=3 报 `external_asset_missing` |
| `linear-model`（model） | 4 | 4 | 6 条样本预测 2.0/3.0/2.75/3.75/3.5/4.5（atol=1e-6）；同输入两次运行 `predictions.csv` 字节一致；缺列/缺文件错误码一致 |
| `python-runtime`（environment） | 4 | 4 | 宿主 Python 3.14.7 满足 ≥3.10、8 个标准库模块可用、`third_party_present` 为空；模拟 3.9 时版本门槛判不通过；Dockerfile 基镜像 3.12 与声明一致 |
| `grid-stats-task`（task） | 1 | 1 | harbor 0.27.0 官方 CLI 双 trial 全量：oracle `reward=1.0`、nop `reward=0.0`（nop 即负例，证明判分有效） |
| `grid-stats-trajectory`（trajectory） | 4 | 4 | ATIF 结构 6 步、时间严格递增；count 67 / value_sum 394 / 象限 17,17,17,16；删去 verification 步的篡改用例被判不通过 |
| `grid-summary-benchmark`（benchmark） | 5 | 5 | 正确产物 `score=1.0, passed=true`；篡改产物 `score=0.571429, passed=false`（错 `value_sum`、`quadrant_counts`）；规则权重和=1、参考答案自洽；缺产物记 problems 且 passed=false |
| **合计** | **40** | **40** | **100%（分母 40：38 组给定用例 + 2 组 skill 的 agent 验收）** |

固定清单覆盖表（`probe-report.json` 的 `coverage`，16 条）：

| check_id | 级别 | 结果 | 说明（na 必带理由） |
|---|---|---|---|
| P0-STRUCT | P0 | pass | 包根仅 9 个资产目录 + `asset-runs/`，包根无 `asset.json` |
| P0-ENVELOPE | P0 | pass | 9 个 `asset.json` 全部通过（jsonschema 4.26.0 交叉校验） |
| P0-COMPLETE | P0 | pass | 38 个声明实体存在且大小/SHA256 一致，无自指、无包外引用（原始包） |
| P0-VERIFY | P0 | pass | 9 个资产均有可执行验证入口，执行结论全部通过 |
| P0-SECRET | P0 | pass | 包内无凭据文件与明文密钥；核验产物未落任何密钥 |
| P0-SAGE | P0 | pass | 需测且已跑通：Sage-A1.5 上 2/2 通过（见 Sage 小节） |
| P0-HARB-STRUCT | P0 | pass | task.toml 可解析、instruction.md 非空、environment/、solution/solve.sh、tests/test.sh 齐备 |
| P0-HARB-RUN | P0 | pass | oracle reward=1.0 / nop reward=0.0（1/1 任务，未抽样） |
| P1-DOC-REF | P1 | pass | 文档/脚本引用的包内路径均存在（仅示例占位产物名不在包内，属正常） |
| P1-VERSION | P1 | pass | `asset_version` 1.0.0 与 `validate/cases.json` 等声明一致 |
| P1-DECL | P1 | pass | 声明为入口/实现/数据的对象与实体一致（含 record_count=100、grid 10×10） |
| P1-DOC-FACT | P1 | na | 机器不自动判；**本次人工判读结论：一致**（见下方说明） |
| P1-VERIFY-DOC | P1 | pass | 验证说明声明的用例数与 `validate/cases.json` 一致（idw 7 组、assess 2 组等） |
| P1-HARB-DATASET | P1 | na | 包内没有显式 `dataset.toml` 数据集（单任务包） |
| P1-HARB-ENVELOPE | P1 | pass | asset_type=task，无未登记任务 |
| P1-HARB-LINT | P1 | pass | `harbor lint` 已采集，正确性发现 0 条 |

P1-DOC-FACT 的人工判读记录（机器标 na，故在此说明）：包 readme 的「8 类资产 / 共 9 个资产」与包内实体一致；`grid-samples` 声明的 100 个点与实体行数一致；`grid-stats-task` 声明的 67 个点与 `environment/data/points.csv`（67 行）及 trajectory 的 `count=67` 一致；idw 的「给定用例共 7 组」与 `cases.json` 一致；benchmark 的权重 0.8/0.2 与阈值 1.0 与 `scoring-rubric.json` 一致；assess 的「给定用例只有 C01/C02」与 `cases.json` 一致。

agent 验收与 harbor 执行的操作性事实（供复核）：
- skill 的 agent 验收用 `run_skill_agent.py` 起独立进程（DSH headless，隔离 `DSH_HOME`，默认 provider/model），门槛脚本判的是 **agent 产物**而不是重跑资产脚本；`idw-interpolate` 首次调用遇 LLM transport 失败（rc=1、无产物），按协议重试一次后通过，两次记录都在 `agent/agent-idw-interpolate-*.txt`。
- harbor 首轮因 `~/.docker/buildx` 在沙箱内不可写而 blocked（`harbor-run-attempt-01-blocked-buildx/`），改用可写 `DOCKER_CONFIG` 重跑后通过；blocked 属于核验环境问题，不计为资产缺陷。

## 4. 问题清单

### P0 阻断

无。

### P1 重要

无。

### P2 建议

| 编号 | 归属 | 问题与证据 | 影响 / 整改要求 |
|---|---|---|---|
| P2-1 | `assess-workflow` | `validate/cases.json` 未记录自检入口所需的 `--assets-root`：缺该参数时两例都以 rc=2 报「需要 --out-dir + --assets-root」（证据：`validation-run/assess-workflow/C01-end-to-end/stderr.log`）；C02 还需另给一个不含外部资产的挂载根 | 复现方必须自行推断挂载根（本次用副本内本资产目录作 C01 根、空目录作 C02 根），建议在 `cases.json` 的 `entrypoint` 写明参数与挂载根约定 |
| P2-2 | `idw-interpolate` | `validate/readme.md` 的「通过门槛」只写 `--case C01-hits --artifact <产物目录>`，未像 `assess-workflow/validate/readme.md` 那样区分 A01（agent 验收场景）与给定用例编号（证据：两文件对照） | 建议两个 skill 统一 agent 验收的编号与判据表述，便于自动化核对与对外解释 |
| P2-3 | `python-runtime` | `C03-python-version-gate` 用注入假 `sys.version_info` 模拟 3.9，未在真实低版本解释器或容器内验证（证据：`validation-run/python-runtime/C03-python-version-gate/`；`environment/runtime_check.py` 的 shim 机制） | 门槛逻辑本身正确，但「低版本必失败」的结论依赖模拟；如需更强证据，建议在镜像内用 3.9 实跑一次 |

<!-- coverage:begin -->
### 用例覆盖度（按资产类型）

各类型用例数均达到下限。

| 类型 | 计划 | 执行 | 通过 | 跳过 | 下限 | 判定 |
|---|---|---|---|---|---|---|
| data 数据 | 5 | 5 | 5 | 0 | ≥3 | ✅ 达标 |
| tool 工具 | 6 | 6 | 6 | 0 | ≥3 | ✅ 达标 |
| model 模型 | 4 | 4 | 4 | 0 | ≥2 | ✅ 达标 |
| environment 环境 | 4 | 4 | 4 | 0 | ≥1 | ✅ 达标 |
| skill 技能 | 11 | 11 | 11 | 0 | ≥2 | ✅ 达标 |
| task 任务 | 1 | 1 | 1 | 0 | ≥1 | ✅ 达标 |
| trajectory 轨迹 | 4 | 4 | 4 | 0 | ≥1 | ✅ 达标 |
| benchmark 评测 | 5 | 5 | 5 | 0 | ≥2 | ✅ 达标 |
<!-- coverage:end -->

<!-- evidence-prune:begin -->
### 证据保留口径

本次跑完用例后按 skill 约定清理了中间产出（逐 case 工作目录 `*/work/`、探针 `out/`、以及`registration/` 之外的大体积实体文件）：清理 61 项、37.51 KB，保留报告类证据 861.08 KB。

**逐 case 的检查数值与判定仍在** `cases.json`、`comparison.json` 与 `validation-report.md` 里；被清理的只是可用原命令重跑复现的原始输出文件，清单见 `evidence-prune.json`。台账里被清理的 `actual_output` 已标记 `actual_pruned: true`。
<!-- evidence-prune:end -->

### Sage A1.5 兼容性测试（附加项，不计入判定）

| 项目 | 值 |
|---|---|
| 后端 | `Sage-A1.5`（`https://discovery-api.intern-ai.org.cn/v1`，密钥经环境变量注入，未落盘） |
| 状态 | completed |
| 结果 | 通用后端 2/2 通过；Sage 后端 2/2 通过（`idw-interpolate`、`assess-workflow` 各 1 例，同一 DSH harness 只换后端） |
| 证据 | `agent-sage/idw-interpolate-report.json`、`agent-sage/assess-workflow-report.json`、`sage-config.json`、`sage-a1.5-report.json` |
| 用途 | 仅反映换后端后的兼容性，**不参与通过率与覆盖度，也不改变第 1 节判定** |

## 5. 最终判定

| 维度 | 判定 |
|---|---|
| 包结构 / 包络 / 完整性 / 密钥 | 通过（P0 0） |
| 各资产自带用例 | 通过（38/38 给定用例） |
| skill 的 agent 验收 | 通过（2/2，判 agent 产物） |
| harbor 任务（oracle/nop 双 trial） | 通过（1/1，reward 1.0 / 0.0） |
| 文档、版本、声明一致性 | 通过（P1 0） |
| 覆盖度下限（按类型） | 达标（8 类均不低于下限） |
| Sage A1.5 兼容性（附加） | 通过（2/2，不计入判定） |

综合结论：**本包本次核验无 P0/P1 问题，40 例用例全部通过，覆盖度达标，可对外发版交付**；建议在下一版吸收 P2-1～P2-3 三条改进（均不影响本次交付）。
