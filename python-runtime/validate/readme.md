# python-runtime 环境自检说明

- 自检输入：本机实际 Python 环境（无 docker 也能跑）；C03 用 shim 模拟低版本
- 用例：
  - `C01-runtime-ok`：`runtime_check.py` 退出码 0、`runtime-report.json` 的 `ok=true`、8 个标准库模块全 `ok`、`network_required=false`
  - `C02-no-third-party`：`third_party_present` 为空（声明的依赖锁为空，环境里不应混入第三方包）
  - `C03-python-version-gate`：模拟 python 3.9 → 退出码 1，`problems` 含版本原因（证明版本门槛真的生效）
  - `C04-dockerfile-consistent`：`Dockerfile` 的 `FROM python:x.y` 与 `asset.json` 声明的 `python_version` 同系列，且 `requirements.lock` 无实际依赖
- 门槛：`python validate/validate.py --case <id> --out-dir <dir>` 退出码 0
- 判定口径：四条全过才算环境资产可用；版本门槛失效或声明与 Dockerfile 不一致均不通过
