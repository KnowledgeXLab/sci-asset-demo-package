# 使用说明

## 读取

`trajectory.json` 是单个 JSON 文件，顶层字段：

| 字段 | 含义 |
|---|---|
| `format` / `conforms_to` | 轨迹格式（ATIF）与规范地址 |
| `task` | 关联任务（asset id + 名称） |
| `agent` | 执行者信息（harness / model / backend） |
| `environment_id` | 运行环境资产 id |
| `run` | 运行状态、trial 数、reward、起止时间 |
| `steps` | 有序事件：`role` ∈ user/agent/environment，`type` ∈ message/plan/tool_call/tool_result/verification/final |
| 每步 `timestamp` | ISO 8601，必须严格递增 |

最终结果在最后一个 `final` 步的 `result_summary` 里，与关联任务的验收口径一致。

## 校验

```bash
python validate/validate.py --case C01-structure           # 结构
python validate/validate.py --case C02-outcome-consistency # 结果自洽
python validate/validate.py --case C03-evidence-linked     # 证据链
python validate/validate.py --case C04-broken-step         # 门槛有效性
# 校验第三方轨迹（目录内需有 trajectory.json）
python validate/validate.py --artifact <目录>
```
