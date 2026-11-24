# grid-stats-task（harbor 任务包示例）

一个最小的 **task** 类示例资产，遵循 harbor / terminal-bench-science 格式：给定 67 个网格采样点，
产出确定性 JSON 摘要，由独立 verifier 逐字段核对。

## 目录

```
grid-stats-task/
├── asset.json                 # 公共包络（asset_type=task；四段 asset_id）
├── readme.md                  # 本文件
├── instruction.md             # 给被测 agent 的任务指令（字段与判定口径）
├── task.toml                  # harbor 1.4 任务声明（环境/超时/产物）
├── environment/
│   ├── Dockerfile             # python:3.12-slim，拷入 data/
│   └── data/points.csv        # 67 行采样点（x,y,value）
├── solution/
│   ├── solve.sh               # harbor oracle 的入口
│   └── solve.py               # 参考解（只用标准库）
├── tests/
│   ├── Dockerfile             # verifier 独立环境（environment_mode=separate，tests/ 整目录拷进 /tests）
│   ├── data/points.csv        # verifier 自带的真值（不依赖被测方的 data/）
│   ├── test.sh                # 写出 /logs/verifier/reward.txt（1/0）
│   └── test_summary.py        # 从自带真值独立复算，逐字段比对产物
└── validate/
    ├── cases.json             # 用例声明（harbor 双 trial 即一条用例）
    ├── readme.md              # 验证说明（Agent / 测试任务 / 通过门槛）
    └── validate.py            # 无 docker 时的离线自检
```

## 用法

```bash
# 离线自检（不需要 docker）
python3 validate/validate.py

# 官方 CLI 双 trial（核验脚本会自动调用）
python3 <skill>/scripts/harbor_run.py --package <包根> --run-dir <run>
```

## 判定口径

- **oracle**：注入 `solution/` → `reward=1`
- **nop**：不注入 solution → `reward=0`（负例，证明 verifier 不是恒绿）
- 两条都符合才算通过；任一不符即 P0，不允许抽样或只跑一条
- verifier 与 agent 沙箱隔离（`[verifier].environment_mode = "separate"`），避免被测方篡改判分环境；`harbor lint` 无发现

## 说明

- 数据仅 67 行、纯标准库、无网络，构建与执行都在秒级，适合作为 harbor 格式的最小样例
- `TBS_WORKSPACE` 覆盖工作区（默认 `/workspace`）、`TBS_DATA_CSV` 覆盖 verifier 真值路径，
  便于在 harbor 之外复跑
- `validate/validate.py` 还会核对 `instruction.md` 的示例 JSON 与 verifier 期望值一致（防「示例写错、被测方照抄」），这属于校验的一部分
- verifier 自带真值是有意的：`environment_mode = "separate"` 下被测方的 `data/` 未必可见，
  判分不能依赖它（否则 nop trial 会因为"读不到输入"而误判 0，oracle 也会假失败）
