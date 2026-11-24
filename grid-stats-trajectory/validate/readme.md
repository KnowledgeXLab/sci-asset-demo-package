# grid-stats-trajectory 校验说明

- 自检输入：随包交付的 `trajectory.json`（6 步成功轨迹）；C04 用内存副本删掉验证步
- 用例：
  - `C01-structure`：`format=ATIF`、步数 ≥ 3、每步 `role`/`type` 在词表内、`timestamp` 严格递增、`run.status=success`
  - `C02-outcome-consistency`：`final.result_summary` 与关联任务期望一致（count 67 / sum 394 / mean 5.880597 /
    x、y 范围 [0,9] / 四象限 17·17·17·16），且四象限之和等于 count
  - `C03-evidence-linked`：存在 `verification` 步，且带 verifier 名称、`result=pass`、`reward=1`、证据位置
  - `C04-broken-step`：删掉验证步后必须判不通过（证明门槛不是恒绿）
- 门槛：`python validate/validate.py --case <id>` 退出码 0；第三方轨迹用 `--artifact <目录>`
- 判定口径：四类问题（结构/时序/结果/证据）任一存在即不通过；轨迹不要求"跑得漂亮"，但必须能证明结果可信
