#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PKG="$ROOT/companyos/live_provider_health_v22"
BACKUP="$ROOT/backups/v22_live_provider_health_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " CompanyOS V22 - Live Provider Health Validation"
echo "============================================================"

test -d "$ROOT/companyos" || { echo "FAIL: $ROOT/companyos missing"; exit 1; }
test -f "$ROOT/.env" || { echo "FAIL: $ROOT/.env missing"; exit 1; }

mkdir -p "$PKG" "$ROOT/ceo_memory" "$ROOT/config" "$BACKUP"

for f in \
  "$ROOT/.env" \
  "$ROOT/config/providers_v21.json" \
  "$ROOT/config/connectors_v20.json" \
  "$ROOT/companyos_v21ctl" \
  "$ROOT/companyosctl"
do
  [ -e "$f" ] && cp -a "$f" "$BACKUP/" || true
done

cat > "$PKG/__init__.py" <<'PY'
from .health import LiveProviderHealthV22
PY

cat > "$PKG/health.py" <<'PY'
from __future__ import annotations
import json, socket, ssl, smtplib, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"

def now():
    return datetime.now(timezone.utc).isoformat()

def parse_env(path):
    d={}
    for line in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s=s[7:].strip()
        k,v=s.split("=",1)
        d[k.strip()]=v.strip().strip("'").strip('"')
    return d

def save(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

class LiveProviderHealthV22:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.env=parse_env(self.root/".env")
        self.report=self.root/"ceo_memory/live_provider_health_v22.json"

    def smtp_probe(self):
        host=self.env.get("COMPANYOS_SMTP_HOST","")
        port=int(self.env.get("COMPANYOS_SMTP_PORT","587") or 587)
        user=self.env.get("COMPANYOS_SMTP_USERNAME","")
        password=self.env.get("COMPANYOS_SMTP_PASSWORD","")

        result={
            "provider":"gmail_smtp" if "gmail" in host.lower() else "generic_smtp",
            "host_present":bool(host),
            "port":port,
            "username_present":bool(user),
            "password_present":bool(password),
            "tcp_connect":False,
            "tls_ready":False,
            "auth_ok":False,
            "message_sent":False,
            "latency_ms":None,
            "error":None,
        }

        if not all((host,user,password)):
            result["error"]="missing_smtp_configuration"
            return result

        started=time.time()
        try:
            with smtplib.SMTP(host,port,timeout=12) as smtp:
                smtp.ehlo()
                result["tcp_connect"]=True
                if smtp.has_extn("starttls"):
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                    result["tls_ready"]=True
                elif port==465:
                    result["tls_ready"]=True
                smtp.login(user,password)
                result["auth_ok"]=True
        except Exception as e:
            result["error"]=f"{type(e).__name__}: {e}"
        result["latency_ms"]=round((time.time()-started)*1000,2)
        return result

    def run(self):
        smtp=self.smtp_probe()
        status="HEALTHY" if smtp["auth_ok"] else "DEGRADED"
        out={
            "status":"companyos_v22_live_provider_health_complete",
            "updated_at":now(),
            "providers":{
                "START_OUTREACH":{
                    "health_state":status,
                    "provider":smtp["provider"],
                    "tcp_connect":smtp["tcp_connect"],
                    "tls_ready":smtp["tls_ready"],
                    "auth_ok":smtp["auth_ok"],
                    "message_sent":False,
                    "latency_ms":smtp["latency_ms"],
                    "error":smtp["error"],
                }
            },
            "network_requests_sent":True,
            "customer_messages_sent":False,
            "external_business_actions_executed":False,
            "financial_actions_executed":False,
            "secret_values_printed":False
        }
        save(self.report,out)
        return out

    def recovery_plan(self):
        health=self.run()
        p=health["providers"]["START_OUTREACH"]
        if p["health_state"]=="HEALTHY":
            action="READY_FOR_NON_SENDING_OUTREACH_TESTS"
            retry=False
        else:
            action="RETRY_WITH_BACKOFF"
            retry=True
        plan={
            "status":"companyos_v22_recovery_plan_ready",
            "provider":"START_OUTREACH",
            "health_state":p["health_state"],
            "recommended_action":action,
            "retry_enabled":retry,
            "retry_schedule_seconds":[30,120,600] if retry else [],
            "send_customer_email":False
        }
        save(self.root/"ceo_memory/provider_recovery_plan_v22.json",plan)
        return plan
PY

cat > "$ROOT/companyos_v22ctl" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/"companyos"))
from companyos.live_provider_health_v22.health import LiveProviderHealthV22

x=LiveProviderHealthV22()
cmd=sys.argv[1] if len(sys.argv)>1 else "health"
if cmd=="health":
    out=x.run()
elif cmd=="recovery":
    out=x.recovery_plan()
else:
    raise SystemExit("usage: companyos_v22ctl {health|recovery}")
print(json.dumps(out,indent=2))
PY
chmod +x "$ROOT/companyos_v22ctl"

cat > "$ROOT/companyos_v22_summary.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
python companyos_v22ctl health
python companyos_v22ctl recovery
echo
echo "Current CompanyOS runtime:"
bash companyosctl status || true
SH
chmod +x "$ROOT/companyos_v22_summary.sh"

echo "[1/4] Compile"
python -m py_compile "$PKG"/*.py "$ROOT/companyos_v22ctl"
echo "PASS compile"

echo "[2/4] Live SMTP provider health check"
python "$ROOT/companyos_v22ctl" health

echo "[3/4] Recovery plan"
python "$ROOT/companyos_v22ctl" recovery

echo "[4/4] Verify current runtime"
cd "$ROOT"
bash companyosctl status || true

echo
echo "============================================================"
echo " V22 LIVE PROVIDER HEALTH VALIDATION INSTALLED"
echo "============================================================"
echo "Backup: $BACKUP"
echo
echo "Run:"
echo "  cd ~/companyos"
echo "  python companyos_v22ctl health"
echo "  python companyos_v22ctl recovery"
echo "  bash companyos_v22_summary.sh"
echo
echo "This health check authenticates to SMTP but sends NO email."
echo "No secret values are printed."
echo "No wallet/private/seed credentials are scanned."
echo "No purchases, transfers, or financial operations are executed."
