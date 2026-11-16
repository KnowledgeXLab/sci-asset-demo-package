# zscore-normalize 自检/验收说明

- 自检输入：脚本内造的固定输入（`1,2,3` 三点；单条记录；缺 `value` 列）
- 用例：
  - `C01-basic`：z 值 -1.224745/0.000000/1.224745，`mean=2.0`、`pstdev=0.816497`
  - `C02-single`：单条记录方差为 0 → 退出码 2 + `error.json(zero_variance)`
  - `C03-bad-column`：缺 `value` 列 → 退出码 2 + `error.json(missing_value_column)`
  - `C04-input-missing`：输入文件不存在 → 退出码 3 + `error.json(input_not_found)`
  - `C05-bad-value`：`value` 含非数值（如 `abc`）→ 退出码 2 + `error.json(bad_value)`
  - `C06-empty-input`：只有表头的空输入 → 退出码 2 + `error.json(empty_input)`
- 门槛：
  - 自检：`python validate/validate.py --case <id> --out-dir <dir>` 退出码 0
  - **验收（判 agent 产物）**：`python validate/validate.py --artifact <agent 产物目录>`，目录内需有 `result.csv` 与 `stats.json`；
    退出码 0 才算通过，**不会重跑本资产脚本**
- 判定口径：z 值逐值相等且 stats 完全一致才算通过
