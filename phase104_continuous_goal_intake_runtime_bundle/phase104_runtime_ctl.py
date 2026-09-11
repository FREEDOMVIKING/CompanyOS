#!/usr/bin/env python3
import argparse, json, os, signal, subprocess, sys, time
from dataclasses import asdict
from pathlib import Path
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime

ROOT = Path.home() / ".companyos_runtime"
ROOT.mkdir(parents=True, exist_ok=True)
PID = ROOT / "continuous_goal_runtime.pid"
LOG = ROOT / "continuous_goal_runtime.log"

def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("start")
s.add_argument("--interval", type=int, default=10)
s.add_argument("--max-failures", type=int, default=5)
sub.add_parser("status")
sub.add_parser("stop")
sub.add_parser("once")
args = ap.parse_args()

runtime = ContinuousGoalRuntime(
    interval_seconds=getattr(args, "interval", 10),
    max_failures=getattr(args, "max_failures", 5),
)

if args.cmd == "once":
    state = runtime.cycle(runtime.load())
    print(json.dumps(asdict(state), indent=2))
    print("PHASE104_CONTINUOUS_GOAL_RUNTIME_ONCE: PASS")
elif args.cmd == "status":
    state = runtime.load()
    pid = int(PID.read_text().strip()) if PID.exists() and PID.read_text().strip().isdigit() else 0
    out = asdict(state)
    out["pid"] = pid or None
    out["pid_alive"] = bool(pid and pid_alive(pid))
    print(json.dumps(out, indent=2))
elif args.cmd == "stop":
    runtime.request_stop()
    pid = int(PID.read_text().strip()) if PID.exists() and PID.read_text().strip().isdigit() else 0
    if pid and pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    PID.unlink(missing_ok=True)
    print("PHASE104_CONTINUOUS_GOAL_RUNTIME: STOP_REQUESTED")
else:
    if PID.exists():
        old = PID.read_text().strip()
        if old.isdigit() and pid_alive(int(old)):
            print("PHASE104_CONTINUOUS_GOAL_RUNTIME: ALREADY_RUNNING")
            raise SystemExit(0)

    runtime.stop_path.unlink(missing_ok=True)
    cmd = [
        sys.executable, "-c",
        "from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime; "
        f"ContinuousGoalRuntime(interval_seconds={args.interval}, max_failures={args.max_failures}).run()"
    ]
    env = os.environ.copy()
    home = str(Path.home() / "companyos")
    env["PYTHONPATH"] = home + ":" + str(Path(home) / "companyos") + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    with LOG.open("ab") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    PID.write_text(str(proc.pid))
    time.sleep(1)
    print("PHASE104_CONTINUOUS_GOAL_RUNTIME: STARTED")
    print("PID:", proc.pid)
    print("LOG:", LOG)
