#!/usr/bin/env python3
"""在副本里逐 case 跑资产自带的 validate/validate.py，原始记录写回 run 目录。

用法：
    python3 scripts/run_cases.py --work-copy <WC> --run <run 目录> [--assets a,b] [--json-out x.json]

每个 case 保存：stdout / stderr / 退出码 / 耗时 / 命令 / 输出目录。
grid-stats-task 的用例是 harbor 双 trial，由 harbor_run.py 执行，本脚本跳过。
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time

HARBOR_ASSETS = {"grid-stats-task"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-copy", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--assets", default="")
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()

    wc = pathlib.Path(a.work_copy).resolve()
    run = pathlib.Path(a.run).resolve()
    only = {x.strip() for x in a.assets.split(",") if x.strip()}

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LC_ALL"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"

    assets = sorted(p.name for p in wc.iterdir()
                    if p.is_dir() and (p / "asset.json").is_file() and not (p / ".mounted-external.json").is_file())
    results = []
    for asset in assets:
        if only and asset not in only:
            continue
        cj = wc / asset / "validate" / "cases.json"
        vp = wc / asset / "validate" / "validate.py"
        if not cj.is_file() or not vp.is_file():
            results.append({"asset": asset, "case_id": None, "status": "skipped",
                            "reason": "缺 validate/cases.json 或 validate.py"})
            continue
        cases = json.loads(cj.read_text(encoding="utf-8")).get("cases", [])
        if asset in HARBOR_ASSETS:
            for c in cases:
                results.append({"asset": asset, "case_id": c["id"], "title": c.get("title", ""),
                                "expected_kind": c.get("expected_kind"), "kind": c.get("kind"),
                                "status": "delegated_harbor", "entrypoint": c.get("entrypoint"),
                                "note": "由 harbor_run.py 执行 oracle/nop 双 trial"})
            continue
        for c in cases:
            cid = c["id"]
            out = run / "validation-run" / asset / cid
            work = out / "work"
            work.mkdir(parents=True, exist_ok=True)
            cmd = [sys.executable, str(vp), "--case", cid, "--out-dir", str(work)]
            t0 = time.time()
            p = subprocess.run(cmd, cwd=str(wc / asset), capture_output=True, text=True, env=env)
            dur = round(time.time() - t0, 3)
            (out / "stdout.log").write_text(p.stdout, encoding="utf-8")
            (out / "stderr.log").write_text(p.stderr, encoding="utf-8")
            rec = {
                "asset": asset, "case_id": cid, "title": c.get("title", ""), "kind": c.get("kind"),
                "expected_kind": c.get("expected_kind"), "entrypoint": "validate/validate.py",
                "command": " ".join(cmd), "exit_code": p.returncode, "duration_s": dur,
                "status": "pass" if p.returncode == 0 else "fail",
                "stdout_tail": p.stdout.strip()[-1200:], "stderr_tail": p.stderr.strip()[-800:],
                "evidence": {"stdout": str((out / "stdout.log").relative_to(run)),
                             "stderr": str((out / "stderr.log").relative_to(run)),
                             "out_dir": str(work.relative_to(run))},
                "executed_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            results.append(rec)
            print(f"[{'OK  ' if p.returncode == 0 else 'FAIL'}] {asset}/{cid} rc={p.returncode} {dur}s", flush=True)

    doc = {"tool": "run_cases.py", "work_copy": str(wc), "run": str(run),
           "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "total": len(results),
           "pass": sum(1 for r in results if r["status"] == "pass"),
           "fail": sum(1 for r in results if r["status"] == "fail"),
           "results": results}
    dst = pathlib.Path(a.json_out) if a.json_out else run / "cases-selfcheck.json"
    dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n合计 {len(results)} 例：pass {doc['pass']} / fail {doc['fail']} / 其它 {len(results) - doc['pass'] - doc['fail']}")
    print(f"记录：{dst}")
    return 0 if doc["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
