#!/usr/bin/env python3
"""环境自检：确认本环境满足资产运行要求（python 版本、标准库模块、无net依赖）。

  python environment/runtime_check.py --out-dir <dir>
产物：<dir>/runtime-report.json
退出码：0 通过 / 1 不满足要求
"""
import argparse
import importlib
import importlib.util
import json
import pathlib
import platform
import sys

REQUIRED_PY = (3, 10)
STDLIB_MODULES = ["csv", "json", "math", "pathlib", "statistics", "subprocess", "unittest", "hashlib"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    a = ap.parse_args()
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    problems = []
    ver = ".".join(str(x) for x in sys.version_info[:3])      # 用 version_info 而非 platform，便于测试时模拟
    if sys.version_info[:2] < REQUIRED_PY:
        problems.append(f"python 版本不满足：需要 >= {'.'.join(map(str, REQUIRED_PY))}，实际 {ver}")

    modules = {}
    for name in STDLIB_MODULES:
        try:
            importlib.import_module(name)
            modules[name] = "ok"
        except Exception as exc:  # noqa: BLE001
            modules[name] = f"missing: {exc}"
            problems.append(f"标准库模块不可用：{name}")

    third_party = sorted(
        name for name in ("numpy", "pandas", "scipy", "tensorflow", "torch")
        if importlib.util.find_spec(name) is not None
    )

    report = {
        "environment_type": "container",
        "os": platform.platform(),
        "python_version": ver,
        "required_python": ">=" + ".".join(map(str, REQUIRED_PY)),
        "stdlib_modules": modules,
        "third_party_present": third_party,
        "network_required": False,
        "ok": not problems,
        "problems": problems,
    }
    (out / "runtime-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "python": report["python_version"],
                      "problems": problems}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
