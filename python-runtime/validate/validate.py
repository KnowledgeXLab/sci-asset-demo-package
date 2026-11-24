#!/usr/bin/env python3
"""python-runtime 环境自检。

  python validate/validate.py --case C01-runtime-ok --out-dir <dir>
退出码：0 通过 / 1 不通过 / 2 用法错误
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_MODULES = ["csv", "json", "math", "pathlib", "statistics", "subprocess", "unittest", "hashlib"]


def run_check(out: pathlib.Path, python_version: str | None = None) -> dict:
    """跑 environment/runtime_check.py；python_version 用于模拟低版本（C03）。"""
    out.mkdir(parents=True, exist_ok=True)
    if python_version:
        # 注入一个假 version_info：把版本门槛提高到当前版本之上，模拟"环境不满足"
        shim = out / "shim_run.py"
        shim.write_text(
            "import runpy, sys\n"
            f"sys.version_info = ({python_version.replace('.', ', ')}, 'final', 0)  # type: ignore\n"
            f"import sys as _s; _s.path.insert(0, r'{HERE / 'environment'}')\n"
            f"sys.argv = ['runtime_check.py', '--out-dir', r'{out}']\n"
            f"runpy.run_path(r'{HERE / 'environment' / 'runtime_check.py'}', run_name='__main__')\n",
            encoding="utf-8")
        proc = subprocess.run([sys.executable, str(shim)], capture_output=True, text=True)
    else:
        proc = subprocess.run([sys.executable, str(HERE / "environment" / "runtime_check.py"),
                               "--out-dir", str(out)], capture_output=True, text=True)
    rep = out / "runtime-report.json"
    data = json.loads(rep.read_text(encoding="utf-8")) if rep.is_file() else {}
    return {"rc": proc.returncode, "report": data, "stderr": proc.stderr[-300:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="C01-runtime-ok")
    ap.add_argument("--out-dir", default=str(pathlib.Path(tempfile.gettempdir()) / "python-runtime-check"))
    a = ap.parse_args()
    known = ["C01-runtime-ok", "C02-no-third-party", "C03-python-version-gate", "C04-dockerfile-consistent"]
    if a.case not in known:
        print(f"未知用例 id：{a.case}；可用：{', '.join(known)}", file=sys.stderr)
        return 2

    out = pathlib.Path(a.out_dir)
    if a.case == "C03-python-version-gate":
        r = run_check(out / "c03", python_version="3, 9, 0")
        ok = r["rc"] != 0 and any("版本" in p for p in (r["report"].get("problems") or []))
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok,
                          "rc": r["rc"], "problems": r["report"].get("problems")}, ensure_ascii=False))
        return 0 if ok else 1

    if a.case == "C04-dockerfile-consistent":
        env = json.loads((HERE / "asset.json").read_text(encoding="utf-8"))
        declared = str((env["spec"]["metadata"].get("python_version") or ""))
        dockerfile = (HERE / "environment" / "Dockerfile").read_text(encoding="utf-8")
        lock = (HERE / "environment" / "requirements.lock").read_text(encoding="utf-8")
        m = re.search(r"FROM python:([0-9.]+)", dockerfile)
        image_ver = m.group(1) if m else ""
        deps = [ln.strip() for ln in lock.splitlines()
                if ln.strip() and not ln.strip().startswith("#")]
        ok = bool(declared) and image_ver.startswith(declared.rsplit(".", 1)[0]) and not deps
        print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok,
                          "declared_python": declared, "image": image_ver, "lock_entries": deps},
                         ensure_ascii=False))
        return 0 if ok else 1

    r = run_check(out / a.case)
    rep = r["report"]
    if a.case == "C01-runtime-ok":
        mods = rep.get("stdlib_modules") or {}
        ok = (r["rc"] == 0 and rep.get("ok") is True
              and all(mods.get(m) == "ok" for m in EXPECTED_MODULES)
              and rep.get("network_required") is False)
    else:  # C02
        ok = (r["rc"] == 0 and not (rep.get("third_party_present") or []))
    print(json.dumps({"mode": "self-check", "case": a.case, "ok": ok, "rc": r["rc"],
                      "third_party_present": rep.get("third_party_present"),
                      "python": rep.get("python_version")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
