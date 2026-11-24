# grid-summary-benchmark 校验说明

- 自检输入：`benchmark/cases/good`（全对样例）、`benchmark/cases/bad`（篡改样例）、空目录（缺产物）
- 用例：
  - `C01-score-good`：正确产物 → `score=1.0`、`passed=true`
  - `C02-score-bad`：`value_sum` 改成 398、象限和 68≠67 → `passed=false`，且 `wrong_fields` 含 `value_sum`
  - `C03-rubric-schema`：权重之和 = 1、`pass_threshold ∈ [0,1]`、指标类型受支持、`submission_layout` 与 task 产物一致
  - `C04-reference-consistency`：参考答案字段集合与判分口径一致、象限之和 = count、`value_mean = value_sum/count`
  - `C05-missing-submission`：产物目录缺 `summary.json` → `problems` 记录缺失、`passed=false`
- 门槛：`python validate/validate.py --case <id> --out-dir <dir>` 退出码 0
- 判定口径：五条全过才算 benchmark 资产可用；评分引擎必须能区分"全对"和"差一点"，
  且规则/参考答案自身要自洽（否则评测结论不可信）
