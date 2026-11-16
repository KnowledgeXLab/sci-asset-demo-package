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
