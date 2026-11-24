# 调用说明

## 准备

无需安装依赖：`model/predict.py` 只用 Python 标准库（≥ 3.10）。权重随包（`model/weights.json`）。

## 调用

```bash
python model/predict.py --input <输入 CSV> --out-dir <输出目录>
```

输入要求：CSV，至少含 `x`、`y` 两列（`id` 可选，会原样带出）。

产物：

| 文件 | 内容 |
|---|---|
| `predictions.csv` | `id,x,y,prediction`，`prediction` 固定 6 位小数 |
| `model-info.json` | 使用的权重摘要：`model_type`/`features`/`coef`/`intercept`/`tolerance`/`rows`/`weights_sha256_prefix` |

## 失败语义

| 情况 | 退出码 | `error.json` 的 `error` |
|---|---|---|
| 输入文件不存在 | 3 | `input_not_found` |
| 缺 `x` 或 `y` 列 | 2 | `bad_columns` |
| `x`/`y` 含非数值 | 2 | `bad_value` |
| 权重文件不可读/结构不合法 | 4 | `weights_invalid` |
