# linear-model 自检/验收说明

- 自检输入：随包交付的 `payload/samples.csv`（6 条样本），以及用例内造的非法输入
- 用例：
  - `C01-predict`：6 条样本的 `prediction` 与解析解一致 —— `2.000000 / 3.000000 / 2.750000 / 3.750000 / 3.500000 / 4.500000`
  - `C02-reproducible`：同一输入连跑两次，`predictions.csv` 逐字节一致（模型推理必须确定性）
  - `C03-bad-column`：输入缺 `y` 列 → 退出码 2 + `error.json(bad_columns)`
  - `C04-input-missing`：输入文件不存在 → 退出码 3 + `error.json(input_not_found)`
- 门槛：
  - 自检：`python validate/validate.py --case <id> --out-dir <dir>` 退出码 0
  - **验收（判 agent 产物）**：`python validate/validate.py --artifact <agent 产物目录>`，目录内需有 `predictions.csv`；
    只比对数值，**不会重跑本资产脚本**
- 判定口径：6 行数值逐值比对，容差 `1e-6`；行数不符或任一值超差即不通过
