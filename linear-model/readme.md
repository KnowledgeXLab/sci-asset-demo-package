# linear-model（模型资产示例）

一个最小的 **model** 资产：确定性线性回归模型 `prediction = 1.0 + 0.5·x + 0.25·y`，
权重即 `model/weights.json`，推理脚本只用标准库。

## 目录

```
linear-model/
├── asset.json          # 公共包络（asset_type=model）
├── readme.md           # 本文件
├── model/
│   ├── weights.json    # 权重（系数/截距/容差/训练来源）
│   └── predict.py      # 推理 CLI：--input <csv> --out-dir <dir>
├── payload/samples.csv # 6 条自带样本（推理演示与自检用）
├── usage/readme.md     # 调用说明
└── validate/           # cases.json + validate.py + readme.md
```

## 用法

```bash
python model/predict.py --input payload/samples.csv --out-dir /tmp/out
# → /tmp/out/predictions.csv（id,x,y,prediction）与 /tmp/out/model-info.json（权重摘要）
```

## 模型信息

| 项 | 值 |
|---|---|
| 类型 | 线性回归（`model_type: linear_regression`） |
| 特征 | `x`、`y` |
| 系数 / 截距 | `[0.5, 0.25]` / `1.0` |
| 数值容差 | `1e-09` |
| 适用范围 | 演示用的二维线性关系；超出特征范围不保证外推 |
| 限制 | 不建模非线性、不给不确定性估计 |

## 判定口径

`validate/cases.json` 四条：数值正确（C01）、推理可复现（C02）、缺列报错（C03）、输入缺失报错（C04）。
详细门槛见 `validate/readme.md`。
