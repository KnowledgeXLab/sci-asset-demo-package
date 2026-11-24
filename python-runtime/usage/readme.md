# 使用说明

## 准备

- 有 docker 时：`docker build -t demo/python-runtime -f environment/Dockerfile environment/`
- 无 docker 时：本机 Python ≥ 3.10 即可（环境只依赖标准库），直接跑自检脚本

## 自检

```bash
python environment/runtime_check.py --out-dir <输出目录>
```

产物 `runtime-report.json` 包含：

| 字段 | 含义 |
|---|---|
| `python_version` / `required_python` | 实际与要求的版本 |
| `stdlib_modules` | 8 个必需标准库模块的可用性 |
| `third_party_present` | 检测到的 numpy/pandas/scipy/tensorflow/torch（本例应为空） |
| `network_required` | 是否需要联网（本例 false） |
| `ok` / `problems` | 总体结论与不满足项 |

## 失败语义

自检不满足要求时退出码 1，`problems` 里逐条列出原因（版本不足、标准库缺失等）。
