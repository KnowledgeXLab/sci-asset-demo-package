# python-runtime（环境资产示例）

一个最小的 **environment** 资产：声明运行示例资产所需的可复现环境——Python ≥ 3.10、仅标准库、
无网络、1 CPU / 1 GB。镜像定义在 `environment/Dockerfile`，依赖锁定文件为空（无第三方包）。

## 目录

```
python-runtime/
├── asset.json                    # 公共包络（asset_type=environment）
├── readme.md                     # 本文件
├── environment/
│   ├── Dockerfile                # 环境定义（python:3.12-slim，不装第三方包）
│   ├── requirements.lock         # 依赖锁定文件（本例为空）
│   └── runtime_check.py          # 环境自检：python 版本 / 标准库 / 第三方包 / 网络依赖
├── usage/readme.md               # 使用说明
└── validate/                     # cases.json + validate.py + readme.md
```

## 用法

```bash
python environment/runtime_check.py --out-dir /tmp/env
# → /tmp/env/runtime-report.json：python 版本、标准库模块状态、是否出现第三方包、是否需要网络
```

## 声明的环境

| 项 | 值 |
|---|---|
| 环境类型 | 容器（`environment_type: container`） |
| 操作系统 | Linux（`python:3.12-slim` 基础镜像） |
| Python | `>= 3.10`（镜像内 3.12） |
| 依赖 | 无第三方包（`requirements.lock` 为空） |
| 资源 | 1 CPU / 1024 MB / 2048 MB 存储 / 0 GPU |
| 网络 | 不需要（`network_access: none`） |

## 判定口径

`validate/cases.json` 四条：环境自检通过（C01）、无第三方包（C02）、版本门槛生效（C03）、
Dockerfile 与声明一致（C04）。详细门槛见 `validate/readme.md`。
