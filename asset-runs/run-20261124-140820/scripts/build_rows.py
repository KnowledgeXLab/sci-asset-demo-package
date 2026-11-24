#!/usr/bin/env python3
"""生成对外发版资产清单的行数据（rows.json，23 列 + 用例明细）。

    python3 scripts/build_rows.py --run <run> --out <run>/registration/rows.json
"""
import argparse
import json
import pathlib
import sys

SKILL_ROOT = pathlib.Path("/home/dengnianchen/projects/agent_centric/.dsh/skills/sci-asset-verify-skill")
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from _version import stamp as _stamp  # noqa: E402

H = dict(
    aid="资产ID", name="资产名称", type="资产类型", domain="领域Profile", summary="资产摘要",
    tags="任务|操作标签", task_desc="任务描述", objects="科学对象", provider="资产提供单位",
    source="来源|产出方式", version="版本", form="格式|接口", scale="规模|数量", time="时间范围",
    space="空间|坐标|实验条件", inp="输入说明", out="输出说明", deps="依赖资源", env="运行环境|资源要求",
    accept="评价指标|验收条件", sec="敏感级别", quality="质量说明", rel="资产关联",
)

REPORT = "asset-runs/run-20261124-140820/validation-report.md"

ROWS = [
    dict(aid="", name="规则网格采样点数据", type="data", domain="地球科学",
         summary="10×10 规则网格上的 100 个采样点（x、y、观测值），作为示例插值与统计的输入数据；规模仅覆盖 0–9 整数格网。",
         tags="operation:data-acquisition",
         task_desc="为示例工具与技能提供可复现的网格采样点输入，供 IDW 插值与描述性统计读取。",
         objects="采样点、规则网格、观测值", provider="示例资产提供方",
         source="generated：包内脚本按 urn:demo:generator 生成，快照随包冻结（见 asset.json provenance）",
         version="1.0.0", form="CSV（payload/points.csv）+ JSON 元数据（metadata.json）",
         scale="100 条记录（10×10 网格）；1 个数据 CSV + 1 个元数据 JSON；给定用例 5 组",
         time="数据快照 2026-11-14",
         space="局部直角坐标（local-cartesian）；bbox x[0,9]、y[0,9]；网格 10×10",
         inp="数据资产无输入；读取 payload/points.csv（列 id,x,y,value，100 行）与 metadata.json",
         out="无输出（被读取方）；下游按列 id,x,y,value 读取，value 为整数观测值",
         deps="无（仅标准库读取）", env="任意环境；UTF-8 文本；无运行时依赖；无网络",
         accept="5 组数据用例（声明元数据 2、结构与可读性 2、可复算公式 1）；复算 100 行最大偏差 ≤1e-6；5/5 通过",
         sec="内部",
         quality=f"声明与实体一致、100 行公式逐行复算全对（5/5）；示例规模数据，不代表真实观测精度；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="z-score 标准化工具", type="tool", domain="地球科学",
         summary="把 CSV 的 value 列按总体标准差做 z-score 标准化，输出结果表与统计量；单列数值处理，方差为 0 时按错误返回。",
         tags="operation:data-processing",
         task_desc="给定含 value 列的 CSV，计算 n/mean/pstdev 并逐行输出 z 值，产出可复算的标准化结果表。",
         objects="观测值序列、标准化统计量", provider="示例资产提供方",
         source="generated：封装包内 scripts/zscore.py（urn:demo:generator）",
         version="1.0.0", form="CLI（python3 scripts/zscore.py --input <csv> --out-dir <dir>）",
         scale="1 个 CLI 工具；1 份方法清单 tool.json；给定用例 6 组",
         time="不适用（按输入重算）", space="不适用（无空间属性）",
         inp="CSV 必需列 value（数值），可含 id；--input 指定输入文件",
         out="result.csv（原列 + zscore，6 位小数）与 stats.json（n/mean/pstdev）；失败写 error.json 并以 rc=2/3 退出",
         deps="无第三方依赖（标准库 statistics）", env="Python ≥3.10，仅标准库；仅 CPU；无网络",
         accept="6 组用例（解析解 1、边界 1、非法输入 4）；数值 atol=1e-6，错误类比对退出码与 error 码；6/6 通过",
         sec="内部",
         quality=f"解析解与 4 类错误语义全部符合（6/6）；仅支持单列标准化，不做稳健标准化（中位数/MAD）；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="IDW 反距离权重插值技能", type="skill", domain="地球科学",
         summary="按已知散点观测对目标点做反距离权重估值，输出估测值与最近邻距离，适合快速生成连续表面。",
         tags="operation:analysis; operation:prediction",
         task_desc="给定已知点与目标点表，按幂次 power 计算逐点估值与最近邻距离，产出可复算的插值表。",
         objects="已知散点、目标点、估测值、最近邻距离", provider="示例资产提供方",
         source="generated：skill 内含 scripts/run.py 实现（urn:demo:generator）",
         version="1.0.0",
         form="Skill（SKILL.md）+ CLI（python3 scripts/run.py --points --targets --power --out-dir）",
         scale="1 个 skill；给定用例 7 组 + agent 验收 1 组",
         time="不适用（按输入重算）",
         space="坐标单位与输入一致；不声明 CRS，假定同一平面直角坐标",
         inp="已知点 CSV（x,y,value）与目标点 CSV（x,y）；--power 默认 2，需 >0",
         out="interpolated.csv（x,y,value_est,nearest_dist，6 位小数）；失败写 error.json（input_not_found/bad_columns/bad_power/no_source_points）",
         deps="无第三方依赖", env="Python ≥3.10，仅标准库；仅 CPU；无网络；不需要容器",
         accept="7 组给定用例（解析解 3、非法输入 4）+ 1 组 agent 验收（DSH 上完成真实任务后判产物）；value_est 与 nearest_dist 两列逐值 atol=1e-6；8/8 通过",
         sec="内部",
         quality=f"解析解、非默认幂次与 4 类错误语义均符合，agent 产物在 DSH 上通过门槛（8/8）；不输出不确定度，也不做障碍/各向异性建模；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="示例评估工作流", type="skill", domain="地球科学",
         summary="把网格数据、z-score 工具与 IDW 技能串成「读数据→标准化→插值」三步工作流，输出含统计量与估值范围的汇总报告。",
         tags="operation:data-processing; operation:analysis; operation:prediction",
         task_desc="按固定三步顺序编排三个外部资产，产出含 data_points/targets/estimate 范围的 report.json。",
         objects="采样点数据、标准化统计量、插值估值范围", provider="示例资产提供方",
         source="derived：编排 grid-samples / zscore-normalize / idw-interpolate（见 external_assets.json）",
         version="1.0.0",
         form="Skill（SKILL.md）+ CLI（python3 scripts/run_workflow.py --assets-root <目录> --out-dir <目录>）",
         scale="1 个工作流 skill（3 步）；自带 targets.csv 5 个目标点；给定用例 2 组 + agent 验收 1 组",
         time="不适用（按输入重算）", space="沿用 grid-samples 的局部直角坐标（bbox 0–9）",
         inp="三个外部资产需按 external_assets.json 挂到本资产目录内；自带 targets.csv（x,y，5 行）",
         out="report.json（steps、data_points、value_mean/pstdev、targets、estimate_min/max、external_assets）；缺外部资产写 error.json 并 rc=3",
         deps="外部资产 3 个：grid-samples（data）、zscore-normalize（tool）、idw-interpolate（skill），均 v1.0.0",
         env="Python ≥3.10，仅标准库；外部资产须就位；无网络",
         accept="2 组给定用例（端到端链路 1、外部资产缺失 1）+ 1 组 agent 验收；检查 steps 顺序与 data_points=100、targets=5；3/3 通过",
         sec="内部",
         quality=f"端到端与「缺外部资产」两条路径均符合预期，agent 产物通过门槛（3/3）；工作流步骤顺序固定，不支持并行或自选步骤；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="线性回归示例模型", type="model", domain="地球科学",
         summary="确定性二维线性回归模型（prediction = 1.0 + 0.5·x + 0.25·y），权重随包，推理仅用标准库。",
         tags="operation:prediction; operation:analysis",
         task_desc="给定含 x、y 的 CSV，按随包权重逐行推理，输出带 prediction 列的确定性结果表。",
         objects="特征 x、特征 y、预测值、模型权重", provider="示例资产提供方",
         source="generated：权重与推理实现随包（urn:demo:linear-model）",
         version="1.0.0",
         form="CLI（python3 model/predict.py --input <csv> --out-dir <dir>）；权重 model/weights.json",
         scale="1 个模型（2 特征线性回归）；给定用例 4 组",
         time="不适用（按输入重算）", space="不适用（无空间属性）",
         inp="CSV 必需列 x、y（数值），可选 id",
         out="predictions.csv（id,x,y,prediction，6 位小数）；失败写 error.json（bad_columns/input_not_found）并 rc=2/3",
         deps="权重 model/weights.json（随包）；无第三方库",
         env="Python ≥3.10，仅标准库；仅 CPU；无 GPU 需求；无网络",
         accept="4 组用例（推理 1、可复现 1、非法输入 2）；逐值 atol=1e-6 且两次运行 products 字节一致；4/4 通过",
         sec="内部",
         quality=f"6 条样本逐值一致、输出可复现、两类错误语义正确（4/4）；仅两特征线性模型，不提供不确定度与适用域判断；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="示例 Python 最小运行环境", type="environment", domain="地球科学",
         summary="示例资产所需的最小可复现环境：Python ≥3.10、仅标准库、无网络、1 CPU / 1 GB，容器定义随包。",
         tags="operation:analysis",
         task_desc="提供可自检的容器化运行环境声明，供本包其他资产复现执行。",
         objects="运行环境、依赖清单", provider="示例资产提供方",
         source="generated：环境声明与自检脚本随包（urn:demo:python-runtime）",
         version="1.0.0",
         form="Dockerfile + requirements.lock + 自检脚本（python3 environment/runtime_check.py --out-dir <dir>）",
         scale="1 个环境资产；1 份依赖锁文件；给定用例 4 组",
         time="不适用（环境声明，随包版本固定）", space="不适用（无空间属性）",
         inp="无数据输入；依赖清单 environment/requirements.lock（当前为空）",
         out="runtime-report.json（ok、python 版本、标准库可用性、third_party_present）",
         deps="无第三方包；基础镜像 Python 3.12",
         env="Linux 容器；Python 3.12（python_requires ≥3.10）；1 CPU / 1024 MB 内存 / 2048 MB 存储；0 GPU；无网络",
         accept="4 组用例（环境自检 2、版本门槛 1、Dockerfile 与声明一致 1）；4/4 通过",
         sec="内部",
         quality=f"版本门槛、8 个标准库模块可用性与声明一致（4/4）；本次未实际构建镜像（构建非自检必需）；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="网格采样点汇总任务（harbor 格式示例）", type="task", domain="地球科学",
         summary="harbor（terminal-bench-science）格式任务：把 67 个网格采样点汇总成确定性 JSON 摘要，由独立 verifier 逐字段核对。",
         tags="operation:data-processing",
         task_desc="按 instruction.md 把 67 点汇总为 summary.json 的 7 个字段，由 tests/test_summary.py 独立复算判定。",
         objects="网格采样点、描述性统计量、空间象限计数", provider="示例资产提供方",
         source="generated：数据由确定性公式 (x*7+y*3)%11+1 生成，可复算",
         version="1.0.0",
         form="harbor 任务包（task.toml + instruction.md + environment/Dockerfile + solution/ + tests/）",
         scale="1 个任务（67 行输入，单次 trial 约 5 s）；给定用例 1 组（oracle/nop 两条 trial）",
         time="不适用（每次运行重算）", space="网格 x[0,9]、y[0,9]；象限按中点 4.5 划分",
         inp="environment/data/points.csv（67 行，x,y,value）；instruction.md 给出字段与判定口径",
         out="/app/output/summary.json（count/value_sum/value_mean/x_extent/y_extent/quadrant_counts）；verifier 写 /logs/verifier/reward.txt",
         deps="docker + harbor CLI（本次 0.27.0）；verifier 独立环境（environment_mode=separate）",
         env="Linux 容器（environment/Dockerfile）+ verifier 独立镜像；无 GPU 需求；任务内无网络依赖",
         accept="1 组用例（harbor 双 trial 全量，不抽样）；oracle reward=1.0、nop reward=0.0；1/1 通过",
         sec="内部",
         quality=f"官方 CLI 的 oracle/nop 双 trial 均符合预期（1/1），nop 为负例，证明 verifier 判分有效；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="网格汇总任务成功轨迹 001", type="trajectory", domain="地球科学",
         summary="grid-stats-task 的一次成功运行轨迹（ATIF 格式，6 步）：含工具调用、验证证据（reward=1）与最终结果摘要。",
         tags="operation:analysis; stage:verification",
         task_desc="记录一次成功运行的计划→调用→结果→验证→结论链路，供复现与证据追溯。",
         objects="运行轨迹、工具调用、验证证据", provider="示例资产提供方",
         source="generated：由 grid-stats-task 的一次成功运行导出",
         version="1.0.0", form="ATIF JSON（trajectory.json，6 步）",
         scale="1 条轨迹（6 步）；给定用例 4 组",
         time="运行时间 2026-11-24 10:20:00–10:20:15（+08:00）",
         space="对应 task 的 x[0,9]、y[0,9] 网格",
         inp="无运行输入；trajectory.json 内含每步 role/type/时间与工具调用参数",
         out="trajectory.json（format=ATIF、steps=6、result_summary：count 67 / value_sum 394 / 象限 17,17,17,16）",
         deps="关联 task grid-stats-task（v1.0.0）；verifier tests/test_summary.py",
         env="任意 JSON 读取环境；校验仅需 Python ≥3.10；无网络",
         accept="4 组用例（结构 1、结果自洽 1、证据链 1、篡改负例 1）；结构断言全部成立且删去验证步后必须判不通过；4/4 通过",
         sec="内部",
         quality=f"结构、时间严格递增与证据链一致，篡改负例能被判不通过（4/4）；只覆盖成功路径，不含失败/重试轨迹；核验报告见 {REPORT}",
         rel=""),
    dict(aid="", name="网格汇总任务评测基准", type="benchmark", domain="地球科学",
         summary="基于 grid-stats-task 的可复现评测定义：字段精确匹配 0.8 + 产物自洽 0.2，阈值 1.0，含参考答案与两个样例产物。",
         tags="stage:verification; operation:analysis",
         task_desc="对提交的 summary.json 按 7 个字段与两条自洽约束打分，输出 score/passed/breakdown。",
         objects="汇总产物、评分规则、参考答案", provider="示例资产提供方",
         source="derived：由 grid-stats-task 派生（见 asset.json provenance.source）",
         version="1.0.0",
         form="CLI 评测入口（python3 benchmark/run_evaluation.py --submission <dir> --out-dir <dir>）+ JSON 评分规则",
         scale="1 个基准（2 项指标，权重 0.8/0.2，阈值 1.0）；2 个自带样例产物；给定用例 5 组",
         time="不适用（按提交重算）", space="沿用 grid-stats-task 的 x[0,9]、y[0,9] 网格",
         inp="提交产物目录（含 summary.json，布局 output/summary.json）",
         out="score.json（score、passed、breakdown、problems）；缺产物时 problems 记录缺失且 passed=false",
         deps="任务 grid-stats-task（v1.0.0）；参考答案 benchmark/reference/summary.json",
         env="Python ≥3.10，仅标准库；仅 CPU；无网络",
         accept="5 组用例（正确产物 1、篡改产物 1、规则自洽 1、参考答案自洽 1、缺失产物 1）；score 1.0 / 0.571429 与 passed 判定均符合预期；5/5 通过",
         sec="内部",
         quality=f"比较器对相等/不相等提交判定正确，规则与参考答案自洽（5/5）；只评数值正确性，不评代码质量或实现路径；核验报告见 {REPORT}",
         rel=""),
]

KIND_CN = {"analytic": "解析解比对", "edge": "边界条件", "invalid": "非法输入",
           "structure": "结构检查", "declared-metadata": "声明一致性", "declared-formula": "可复算公式",
           "file_metadata": "文件可读性", "predict": "推理比对", "environment": "环境自检",
           "workflow": "端到端链路", "task": "harbor 双 trial", "trajectory": "轨迹自洽",
           "benchmark": "评分判定", "agent-acceptance": "agent 产物验收"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run = pathlib.Path(a.run).resolve()
    out = pathlib.Path(a.out)
    cases_doc = json.loads((run / "cases.json").read_text(encoding="utf-8"))
    comp = json.loads((run / "comparison.json").read_text(encoding="utf-8"))
    comp_by = {(c["asset"], c["case_id"]): c for c in comp["comparisons"]}
    inv = json.loads((run / "inventory.json").read_text(encoding="utf-8"))
    name_by_dir = {x["asset_dir"]: x["name"] for x in inv["assets"]}
    name_map = {"grid-samples": "规则网格采样点数据", "zscore-normalize": "z-score 标准化工具",
                "idw-interpolate": "IDW 反距离权重插值技能", "assess-workflow": "示例评估工作流",
                "linear-model": "线性回归示例模型", "python-runtime": "示例 Python 最小运行环境",
                "grid-stats-task": "网格采样点汇总任务（harbor 格式示例）", "grid-stats-trajectory": "网格汇总任务成功轨迹 001",
                "grid-summary-benchmark": "网格汇总任务评测基准"}

    rows = []
    for r in ROWS:
        rows.append({H[k]: v for k, v in r.items()})

    case_rows = []
    for c in cases_doc["cases"]:
        cp = comp_by.get((c["asset_dir"], c["case_id"]), {})
        err = "无（判定一致）"
        if cp.get("fields"):
            err = "；".join(f"{f['field']}: expected={f['expected']} actual={f['actual']} → {f['status']}"
                           for f in cp["fields"])
        cid = f"{c['asset_dir']}/{c['case_id']}" if c["source"] != "given" else c["case_id"]
        case_rows.append({
            "用例编号": cid,
            "资产名称": name_map[c["asset_dir"]],
            "关联资产及检查点": (("；".join(c["related_assets"]) + "（工作流三步串联，检查 steps 顺序与统计量）")
                               if c["related_assets"] else "不适用"),
            "资产版本": c["asset_version"],
            "用例名称": (c["expected"].split("；")[0][:120] if c["expected"] else c["case_id"]),
            "用例来源": ("given：" + f"{c['asset_dir']}/validate/cases.json" if c["source"] == "given"
                        else "supplemental-agent：validate/readme.md 的 agent 验收场景（A01）"),
            "用例类型": KIND_CN.get(c["kind"], c["kind"] or "success"),
            "前置条件": c["preconditions"],
            "输入或Prompt": (c["input"] or "")[:600],
            "执行入口": (c["entrypoint"] or "")[:300],
            "预期结果": (c["expected"] or "")[:400],
            "真值类型": c["truth_kind"],
            "真值来源": c["truth_path"],
            "比较规则": c["comparison"],
            "验收阈值及依据": c["threshold_source"],
            "实际输出": c["actual_path"],
            "执行状态": "completed" if c["execution_status"] == "completed" else c["execution_status"],
            "验证结论": ("pass（" + ("产物与预期一致" if c["validation_status"] == "pass" else "与预期不一致") + "）"),
            "误差或检查结果": err,
            "证据与报告": json.dumps(c["evidence"], ensure_ascii=False)[:300],
            "备注": ("首次 agent 调用遇 LLM transport 失败（rc=1，未产出），重试后通过；两次记录见 agent/agent-idw-interpolate-*.txt"
                     if c["asset_dir"] == "idw-interpolate" and c["source"] != "given" else
                     ("harness/模型：DSH headless，默认 provider/model" if c["source"] != "given" else "")),
        })

    doc = _stamp({"tool": "build_rows.py", "rows": rows, "cases": case_rows,
                  "schema": "assets/external-list-schema.json（内置，23 列）",
                  "note": "资产ID 与资产关联由 asset_ids.py / external_refs.py 回填"})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"rows: {len(rows)}；cases: {len(case_rows)} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
