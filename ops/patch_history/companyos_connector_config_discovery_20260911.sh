#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
ENVFILE="$HOME/.companyos_launch_env"
cd "$ROOT"

echo "===== COMPANYOS CREDENTIAL / CONNECTOR LOCATOR ====="

if [ -f "$ENVFILE" ]; then
  echo "FOUND: $ENVFILE"
  . "$ENVFILE"
else
  echo "MISSING: $ENVFILE"
fi

python - <<'PY'
import os, re
from pathlib import Path

home = Path.home()
root = home / "companyos"

wanted = [
    "OPENAI_API_KEY","SMTP_HOST","SMTP_PORT","SMTP_USERNAME","SMTP_PASSWORD","SMTP_FROM",
    "VERCEL_TOKEN","SOLANA_RPC_URL","SOLANA_PRIVATE_KEY",
    "COMPANYOS_ENABLE_LIVE_FINANCE","COMPANYOS_DAILY_FINANCE_CAP_USD",
    "COMPANYOS_SINGLE_FINANCE_CAP_USD","COMPANYOS_MIN_TRANSACTION_AMOUNT",
]

print("===== ENVIRONMENT PRESENCE (VALUES REDACTED) =====")
for key in wanted:
    print(f"{key}: {'SET' if os.getenv(key) else 'MISSING'}")

print()
print("===== ENV VARIABLE NAMES REFERENCED BY CODE =====")
pattern = re.compile(r'(?:os\.getenv|os\.environ\.get)\(\s*["\']([A-Z][A-Z0-9_]+)["\']')
seen = set()
for p in root.rglob("*.py"):
    if ".git" in p.parts or "backups" in p.parts:
        continue
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for m in pattern.finditer(txt):
        name = m.group(1)
        if any(x in name for x in ("OPENAI","SMTP","VERCEL","SOLANA","FINANCE","HOSTING","EMAIL","GITHUB")):
            seen.add((name, str(p.relative_to(root))))
for name, path in sorted(seen):
    print(f"{name} <- {path}")

print()
print("===== LOCAL CONFIG FILES WITH CONNECTOR REFERENCES =====")
interesting = ("openai","smtp","vercel","solana","hosting","email")
hits = []
for p in root.rglob("*"):
    if not p.is_file():
        continue
    if ".git" in p.parts or "backups" in p.parts or "__pycache__" in p.parts:
        continue
    try:
        if p.stat().st_size > 2_000_000:
            continue
    except Exception:
        continue
    if p.suffix.lower() not in {".json",".env",".ini",".toml",".yaml",".yml",".txt",".conf"}:
        continue
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        continue
    keys = [k for k in interesting if k in txt]
    if keys:
        hits.append((str(p.relative_to(root)), keys))
for path, keys in hits[:80]:
    print(path, "keys=" + ",".join(keys))
PY

echo
echo "===== PATCH SUPERVISOR TO LOAD LOCAL ENV AUTOMATICALLY ====="
python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/service_supervisor.py")
s = p.read_text(encoding="utf-8")

marker = '        root = Path.home() / "companyos"\n        self.root = root\n'
replacement = '''        root = Path.home() / "companyos"
        self.root = root

        env_file = Path.home() / ".companyos_launch_env"
        if env_file.exists():
            try:
                for raw in env_file.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[7:].strip()
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    value = value.replace("\\ ", " ")
                    if key and key not in os.environ:
                        os.environ[key] = value
            except Exception:
                pass
'''

if replacement not in s:
    if marker not in s:
        raise SystemExit("service_supervisor init anchor not found")
    s = s.replace(marker, replacement, 1)
    p.write_text(s, encoding="utf-8")
    print("patched service_supervisor.py")
else:
    print("already patched")
PY

python -m py_compile companyos/runtime/service_supervisor.py

echo
echo "===== RESTART ====="
[ ! -f "$ENVFILE" ] || . "$ENVFILE"
./scripts/companyosctl restart
sleep 4

echo
echo "===== HEALTH ====="
./scripts/companyosctl health

echo
echo "===== COMMIT PATCH ====="
git add companyos/runtime/service_supervisor.py
git commit -m "Load local launch environment in CompanyOS supervisor" || true
git push origin HEAD
git push origin HEAD:main || true

echo
echo "COMPANYOS_CONNECTOR_CONFIG_DISCOVERY=COMPLETE"
