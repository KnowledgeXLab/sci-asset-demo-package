# grid-stats-task 验证说明

## Agent

- harness：`DSH`（DeepSeek Harness），预设见 skill 的 `assets/harness-registry.json`
- model：harness 默认模型（本任务不依赖大模型能力，任何人/agent 实现都应通过；oracle 试跑用确定性参考解 `solution/solve.py`）
- 设备：无需 GPU；容器 1 CPU / 1 GB / 无网络

## 测试任务（怎么测）

**主口径（harbor，官方 CLI）**：

```bash
python3 <skill>/scripts/harbor_run.py --package <包根> --run-dir <run>
# 内部等价于：harbor run -p grid-stats-task -a oracle（期望 reward=1）
#             harbor run -p grid-stats-task -a nop   （期望 reward=0）
```

**无 docker 时的离线口径**：

```bash
python3 validate/validate.py                 # 参考解 + verifier，应双双通过
python3 validate/validate.py --no-solution   # 缺产物时 verifier 必须判不通过
```

**判分逻辑**：`tests/test_summary.py` 从**自带真值** `tests/data/points.csv` 独立复算期望值（不依赖被测方输入），再逐字段比对
`output/summary.json`；`tests/test.sh` 把结果写成 `/logs/verifier/reward.txt`（1/0）。

## 通过门槛

1. **oracle trial**：`reward = 1` —— 注入 `solution/` 后 verifier 判通过
2. **nop trial**：`reward = 0` —— 不注入 solution 时 verifier 必须判不通过（证明判分真的在判产物，不是恒绿）
3. 离线口径下 `validate/validate.py` 与 `--no-solution` 两种模式都必须符合预期
4. 任一不满足即判 P0（skill 的 `P0-HARB-RUN`），不得以「跑不了」结案
