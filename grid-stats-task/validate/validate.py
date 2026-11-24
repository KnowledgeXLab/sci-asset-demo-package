#!/usr/bin/env python3
"""无 docker 的离线自检：在本目录内临时 workspace 跑一次"参考解 + verifier"。

用途：给出 harbor 之外的快速反馈（有 docker 时仍以 tests/test.sh + oracle/nop 为准）。
  python3 validate/validate.py            # 默认拿 solution/solve.py 当被测实现
  python3 validate/validate.py --no-solution   # 只跑 verifier（预期失败，用于确认门槛有效）
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-solution", action="store_true", help="不跑参考解，直接验证门槛会失败")
    args = ap.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="grid-stats-validate-") as tmp:
        ws = Path(tmp)
        (ws / "data").mkdir()
        (ws / "output").mkdir()
        shutil.copy2(TASK / "environment" / "data" / "points.csv", ws / "data" / "points.csv")
        env = dict(os.environ, TBS_WORKSPACE=str(ws), PYTHONDONTWRITEBYTECODE="1")
        rc_sol = 0
        if not args.no_solution:
            rc_sol = subprocess.run([sys.executable, str(TASK / "solution" / "solve.py")], env=env).returncode
        rc_t = subprocess.run([sys.executable, str(TASK / "tests" / "test_summary.py")], env=env).returncode
        print(f"\n参考解 rc={rc_sol}；verifier rc={rc_t}")
        if args.no_solution:
            ok = rc_t != 0
            print("OK：缺产物时 verifier 判不通过（门槛有效）" if ok else "ERROR：缺产物却判通过，门槛失效")
            return 0 if ok else 1
        ok = rc_sol == 0 and rc_t == 0
        print("OK：参考解通过自带 verifier" if ok else "ERROR：参考解未通过 verifier")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
