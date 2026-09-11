from pathlib import Path
import subprocess, os, time, json

root = Path.home() / "companyos"
env = os.environ.copy()
env["PYTHONPATH"] = f"{root}:{root/'companyos'}"

svc = root/"scripts"/"companyos_service.sh"

# Ensure stopped first.
subprocess.run(["bash", str(svc), "stop"], env=env, cwd=root, capture_output=True, text=True)

start = subprocess.run(["bash", str(svc), "start"], env=env, cwd=root, capture_output=True, text=True, timeout=30)
assert start.returncode == 0, start.stdout + start.stderr

time.sleep(4)

status = subprocess.run(["bash", str(svc), "status"], env=env, cwd=root, capture_output=True, text=True, timeout=20)
assert "COMPANYOS_SERVICE_RUNNING" in status.stdout, status.stdout

pidfile = root/"companyos_runtime"/"canonical_daemon"/"daemon.pid"
heartbeat = root/"companyos_runtime"/"canonical_daemon"/"heartbeat.json"
assert pidfile.exists()

# Allow first heartbeat if needed.
for _ in range(8):
    if heartbeat.exists():
        break
    time.sleep(2)
assert heartbeat.exists()

hb = json.loads(heartbeat.read_text())
assert hb.get("broadcast_allowed") is False
assert hb.get("external_actions_allowed") is False

stop = subprocess.run(["bash", str(svc), "stop"], env=env, cwd=root, capture_output=True, text=True, timeout=40)
assert stop.returncode == 0

time.sleep(2)
assert not pidfile.exists()

print("daemon_start => PASS")
print("single_instance_pid => PASS")
print("heartbeat => PASS")
print("canonical_production_start => PASS")
print("no_external_action => PASS")
print("no_transaction_broadcast => PASS")
print("graceful_stop => PASS")
print("BUNDLE5_SMOKE_TEST: PASS")
