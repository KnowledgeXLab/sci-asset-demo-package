# grid-samples 自检说明

- 输入：随包交付的 `payload/points.csv`（`id,x,y,value`）与 `metadata.json`（记录数、bbox、grid、value_range）
- 用例：
  - `C01-metadata`：记录数、value 最小/最大值与 metadata 一致
  - `C02-structure`：列集合、首行 id 稳定
  - `C03-read`：CSV 可解析，行数/列数正确
  - `C04-extent`：**声明空间范围与网格完整性**——bbox_x/bbox_y 与实测一致，且 `grid{nx,ny}` 覆盖的格子与实际点集完全相同
- `C05-formula`：**声明公式可复算**——按 `metadata.formula`（`i` 自 1 起、逐行递增）重算 100 行，最大偏差需 ≤ `tolerance`（1e-06）
- 门槛：`python validate/validate.py --case <id> --out-dir <dir>` 退出码 0，且输出 JSON 的 `checks` 全为 true
- 判定口径：任一检查 false 即不通过；`C04-extent` 专门防止"声明 10×10 而实体差一行"这类声明与实体不一致

## 实现说明

- `--case` 默认 `C01-metadata`，与 `cases.json` 的 id 一致；传未知 id 直接 `exit 2`（不会静默跑全部检查）
- 复算 `metadata.formula.expr` 用白名单 AST 求值（只允许算术、`sin/cos/sqrt/exp`、常量 `pi/e`、变量 `x/y/i`），**不用 `eval()`**，避免第三方 `metadata.json` 注入代码
