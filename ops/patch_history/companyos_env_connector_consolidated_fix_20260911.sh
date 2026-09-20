#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
ENVFILE="$HOME/.companyos_launch_env"
cd "$ROOT"

echo "===== COMPANYOS ENV + CONNECTOR CONSOLIDATED FIX ====="

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/service_supervisor.py")
s = p.read_text(encoding="utf-8")

if "def _load_launch_env_file(" not in s:
    insert_after = "class ServiceSupervisor:\n"
    helper = '''class ServiceSupervisor:
    @staticmethod
    def _load_launch_env_file(path: Path) -> None:
        import shlex
        if not path.exists():
            return
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parts = shlex.split(line, posix=True)
            except Exception:
                continue
            if not parts:
                continue
            if parts[0] == "export":
                parts = parts[1:]
            if not parts:
                continue
            token = parts[0]
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value

'''
    if insert_after not in s:
        raise SystemExit("class ServiceSupervisor anchor not found")
    s = s.replace(insert_after, helper, 1)

anchor = '''        self.root = (Path.home() / "companyos").resolve()
        self.runtime_root = self.root / ".companyos_runtime"
'''
replacement = '''        self.root = (Path.home() / "companyos").resolve()
        self._load_launch_env_file(Path.home() / ".companyos_launch_env")
        self.runtime_root = self.root / ".companyos_runtime"
'''
if replacement not in s:
    if anchor not in s:
        raise SystemExit("current ServiceSupervisor __init__ anchor not found")
    s = s.replace(anchor, replacement, 1)

p.write_text(s, encoding="utf-8")
print("Patched service_supervisor.py to load ~/.companyos_launch_env")
PY

python -m py_compile companyos/runtime/service_supervisor.py

echo
echo "===== VERIFY ENV FILE WITHOUT PRINTING SECRETS ====="
python - <<'PY'
from pathlib import Path
import shlex

path = Path.home() / ".companyos_launch_env"
wanted = {
    "OPENAI_API_KEY",
    "SMTP_HOST","SMTP_PORT","SMTP_USERNAME","SMTP_PASSWORD","SMTP_FROM",
    "VERCEL_TOKEN","SOLANA_RPC_URL","SOLANA_PRIVATE_KEY",
    "COMPANYOS_ENABLE_LIVE_FINANCE","COMPANYOS_DAILY_FINANCE_CAP_USD",
    "COMPANYOS_SINGLE_FINANCE_CAP_USD","COMPANYOS_MIN_TRANSACTION_AMOUNT",
}
found = {}
if path.exists():
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line, posix=True)
        except Exception:
            continue
        if parts and parts[0] == "export":
            parts = parts[1:]
        if not parts or "=" not in parts[0]:
            continue
        k,v = parts[0].split("=",1)
        if k in wanted:
            found[k] = bool(v)

for k in sorted(wanted):
    print(f"{k}: {'SET' if found.get(k) else 'MISSING'}")
PY

echo
echo "===== LOCATE CONNECTOR READINESS LOGIC ====="
grep -RIl   --exclude-dir=.git   --exclude-dir=backups   --exclude-dir=__pycache__   -E 'configured_count|connector.*configured|VERCEL_TOKEN|SMTP_HOST|OPENAI_API_KEY'   companyos scripts 2>/dev/null | head -80 || true

echo
echo "===== RESTART WITH ENV AUTO-LOADER ====="
if [ -f "$ENVFILE" ]; then
  . "$ENVFILE"
fi

./scripts/companyosctl restart
sleep 5

echo
echo "===== HEALTH ====="
./scripts/companyosctl health

echo
echo "===== DASHBOARD CONNECTOR SNAPSHOT ====="
python - <<'PY'
import json, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=5) as r:
        x = json.loads(r.read().decode("utf-8"))
    connectors = x.get("connectors", {})
    print(json.dumps(connectors, indent=2, sort_keys=True, default=str))
except Exception as exc:
    print("dashboard_status_error:", type(exc).__name__, str(exc))
PY

echo
echo "===== CONNECTOR READINESS COMMANDS ====="
if [ -x ./scripts/companyos_connectorctl ]; then
  ./scripts/companyos_connectorctl || true
fi

echo
echo "===== COMMIT + PUSH SAFE LOADER PATCH ====="
git add companyos/runtime/service_supervisor.py
git commit -m "Load CompanyOS local launch environment in supervisor" || true
git push origin HEAD
git push origin HEAD:main || true

echo
echo "COMPANYOS_ENV_CONNECTOR_FIX=COMPLETE"
