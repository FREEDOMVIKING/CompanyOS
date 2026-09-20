#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/self_evolution_generation_fix_v4_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"
cp -a companyos/runtime/self_evolution_engine.py "$BACKUP/self_evolution_engine.py"

echo "CompanyOS Self-Evolution Generation Fix V4"

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/self_evolution_engine.py")
s = p.read_text()

old1 = "    try:\n        raw = model_request(prompt)\n        plan = extract_json(raw)\n    except Exception as exc:\n        return {\n            \"ok\": False,\n            \"reason\": \"model_generation_failed\",\n            \"error\": f\"{type(exc).__name__}: {exc}\",\n        }\n"
old2 = "    try:\n        raw = model_request(prompt)\n        plan = extract_json(raw)\n    except Exception as exc:\n        return {\"ok\": False, \"reason\": \"model_generation_failed\", \"error\": f\"{type(exc).__name__}: {exc}\"}\n"

new = "    try:\n        raw = model_request(prompt)\n        if isinstance(raw, dict):\n            if isinstance(raw.get(\"response\"), dict):\n                plan = raw[\"response\"]\n            elif isinstance(raw.get(\"result\"), dict):\n                plan = raw[\"result\"]\n            elif isinstance(raw.get(\"data\"), dict):\n                plan = raw[\"data\"]\n            else:\n                plan = raw\n        elif isinstance(raw, str):\n            plan = extract_json(raw)\n        else:\n            plan = extract_json(str(raw))\n    except Exception as exc:\n        return {\n            \"ok\": False,\n            \"reason\": \"model_generation_failed\",\n            \"error\": f\"{type(exc).__name__}: {exc}\",\n            \"response_type\": type(raw).__name__ if \"raw\" in locals() else None,\n        }\n"

if old1 in s:
    s = s.replace(old1, new, 1)
elif old2 in s:
    s = s.replace(old2, new, 1)
else:
    raise SystemExit("ERROR: exact current model parsing block not found")

p.write_text(s)
print("MODEL_RESPONSE_HANDLER_PATCHED=YES")
PY

python -m py_compile companyos/runtime/self_evolution_engine.py
python -m unittest tests.test_self_evolution_guard

source "$HOME/.companyos_launch_env"

for secret_name in OPENAI_API_KEY CLOUDFLARE_API_TOKEN SOLANA_PRIVATE_KEY SMTP_PASSWORD; do
  secret="${!secret_name:-}"
  if [ -n "$secret" ]; then
    if git grep -nF "$secret" -- . ':!*.log' ':!.companyos_runtime' 2>/dev/null | head -1 | grep -q .; then
      echo "ERROR: value of $secret_name found in source"
      exit 1
    fi
  fi
done
echo "SECRET_SCAN=PASS"

git add -- companyos/runtime/self_evolution_engine.py
if ! git diff --cached --quiet; then
  git commit -m "Handle dict responses in self-evolution generator"
fi

BRANCH="$(git branch --show-current)"
if [ -n "$BRANCH" ]; then
  git push origin "$BRANCH" || echo "WARNING: push failed; local V4 fix remains installed"
fi

if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi
sleep 5

echo
echo "SUPERVISOR:"
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/".companyos_runtime"/"service_supervisor_state.json"
d=json.loads(p.read_text()) if p.exists() else {}
for name,row in (d.get("services") or {}).items():
    print(f"{name}: running={row.get('running')} failures={row.get('consecutive_failures',0)}")
PY

echo
echo "COMPANYOS_SELF_EVOLUTION_GENERATION_FIX_V4=PASS"
echo "Next: scripts/companyos_evolutionctl once"
