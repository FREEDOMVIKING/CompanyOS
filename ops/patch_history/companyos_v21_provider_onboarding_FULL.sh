#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PKG="$ROOT/companyos/provider_onboarding_v21"
BACKUP="$ROOT/backups/v21_provider_onboarding_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " CompanyOS V21 - Provider Onboarding + Health Registry"
echo "============================================================"

test -d "$ROOT/companyos" || { echo "FAIL: $ROOT/companyos missing"; exit 1; }
test -f "$ROOT/.env" || { echo "FAIL: $ROOT/.env missing"; exit 1; }

mkdir -p "$PKG" "$ROOT/config" "$ROOT/ceo_memory" "$BACKUP"

for f in \
  "$ROOT/.env" \
  "$ROOT/config/connectors.json" \
  "$ROOT/config/connectors_v18.json" \
  "$ROOT/config/connectors_v19.json" \
  "$ROOT/config/connectors_v20.json" \
  "$ROOT/companyosctl" \
  "$ROOT/companyos_v20ctl"
do
  [ -e "$f" ] && cp -a "$f" "$BACKUP/" || true
done

cat > "$PKG/__init__.py" <<'PY'
from .core import ProviderOnboardingV21
PY

cat > "$PKG/core.py" <<'PY'
from __future__ import annotations
import json, re, socket, ssl, urllib.request
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"

CONNECTORS={
 "PUBLISH_STATIC_SITE":{
   "token_env":"COMPANYOS_HOSTING_TOKEN",
   "endpoint_env":"COMPANYOS_HOSTING_DEPLOY_URL",
   "kind":"https",
   "providers":["cloudflare","vercel","netlify","github_pages","generic_static_host"]
 },
 "APPLY_DNS":{
   "token_env":"COMPANYOS_DOMAIN_TOKEN",
   "endpoint_env":"COMPANYOS_DOMAIN_API_URL",
   "kind":"https",
   "providers":["cloudflare","namecheap","godaddy","generic_dns"]
 },
 "CREATE_STOREFRONT":{
   "token_env":"COMPANYOS_API_TOKEN",
   "endpoint_env":"COMPANYOS_API_BASE_URL",
   "kind":"https",
   "providers":["shopify","woocommerce","generic_rest_storefront"]
 },
 "START_OUTREACH":{
   "token_env":"COMPANYOS_SMTP_PASSWORD",
   "endpoint_env":"COMPANYOS_SMTP_HOST",
   "kind":"smtp",
   "providers":["gmail_smtp","sendgrid_smtp","mailgun_smtp","generic_smtp"]
 }
}

def now():
    return datetime.now(timezone.utc).isoformat()

def parse_env(path):
    d={}
    p=Path(path)
    if not p.exists(): return d
    for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        if s.startswith("export "): s=s[7:].strip()
        k,v=s.split("=",1)
        d[k.strip()]=v.strip().strip("'").strip('"')
    return d

def load_json(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def save_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def provider_from_endpoint(action,endpoint):
    q=(endpoint or "").lower()
    if action=="START_OUTREACH":
        if "smtp.gmail.com" in q:return "gmail_smtp"
        if "sendgrid" in q:return "sendgrid_smtp"
        if "mailgun" in q:return "mailgun_smtp"
        return "generic_smtp"
    if "cloudflare" in q:return "cloudflare"
    if "vercel" in q:return "vercel"
    if "netlify" in q:return "netlify"
    if "github" in q:return "github_pages"
    if "namecheap" in q:return "namecheap"
    if "godaddy" in q:return "godaddy"
    if "shopify" in q:return "shopify"
    if "woocommerce" in q:return "woocommerce"
    if action=="PUBLISH_STATIC_SITE":return "generic_static_host"
    if action=="APPLY_DNS":return "generic_dns"
    if action=="CREATE_STOREFRONT":return "generic_rest_storefront"
    return "generic"

def endpoint_shape_ok(kind,value):
    if not value:return False
    if kind=="smtp":
        return bool(re.fullmatch(r"[A-Za-z0-9.-]+",value.split(":")[0]))
    u=urlparse(value)
    return u.scheme in ("http","https") and bool(u.netloc)

class ProviderOnboardingV21:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.env_path=self.root/".env"
        self.cfg_path=self.root/"config/providers_v21.json"
        self.report_path=self.root/"ceo_memory/provider_onboarding_v21.json"

    def inspect(self):
        env=parse_env(self.env_path)
        out={
          "status":"companyos_v21_provider_onboarding_ready",
          "updated_at":now(),
          "secret_values_printed":False,
          "wallet_private_keys_scanned":False,
          "providers":{}
        }
        for action,spec in CONNECTORS.items():
            token=bool(env.get(spec["token_env"]))
            endpoint=env.get(spec["endpoint_env"],"")
            shape=endpoint_shape_ok(spec["kind"],endpoint)
            out["providers"][action]={
              "provider":provider_from_endpoint(action,endpoint),
              "token_env":spec["token_env"],
              "token_present":token,
              "endpoint_env":spec["endpoint_env"],
              "endpoint_present":bool(endpoint),
              "endpoint_shape_valid":shape,
              "configuration_ready":bool(token and endpoint and shape),
              "health_state":"NOT_TESTED"
            }
        save_json(self.report_path,out)
        return out

    def build_registry(self):
        info=self.inspect()
        reg={
          "version":21,
          "generated_at":now(),
          "global":{
            "network_health_checks":False,
            "external_execution":False,
            "retry_limit":3,
            "cooldown_seconds":30
          },
          "providers":{},
          "policy":{
            "allow_nonfinancial_health_checks":True,
            "allow_domain_purchase":False,
            "allow_wallet_signing":False,
            "allow_fund_transfer":False,
            "allow_spending":False
          }
        }
        for action,d in info["providers"].items():
            reg["providers"][action]={
              "provider":d["provider"],
              "enabled":d["configuration_ready"],
              "token_env":d["token_env"],
              "endpoint_env":d["endpoint_env"],
              "health_state":"CONFIGURED_UNTESTED" if d["configuration_ready"] else "BLOCKED_CONFIG",
              "network_health_checks":False,
              "external_execution":False,
              "retry_limit":3
            }
        save_json(self.cfg_path,reg)
        return reg

    def local_health(self):
        reg=self.build_registry()
        out={
          "status":"companyos_v21_local_health_complete",
          "updated_at":now(),
          "providers":{},
          "network_requests_sent":False,
          "external_actions_executed":False
        }
        for action,s in reg["providers"].items():
            state="CONFIGURED_UNTESTED" if s["enabled"] else "BLOCKED_CONFIG"
            out["providers"][action]={
              "provider":s["provider"],
              "enabled":s["enabled"],
              "health_state":state,
              "retry_limit":s["retry_limit"]
            }
        save_json(self.root/"ceo_memory/provider_health_v21.json",out)
        return out

    def onboarding_plan(self):
        health=self.local_health()
        ready=[]; blocked=[]
        for action,d in health["providers"].items():
            (ready if d["enabled"] else blocked).append(action)
        plan={
          "status":"companyos_v21_onboarding_plan_ready",
          "ready_for_network_health_check":ready,
          "blocked_on_configuration":blocked,
          "external_execution_enabled":False,
          "financial_actions_blocked":True,
          "next_stage":"provider_network_health_validation"
        }
        save_json(self.root/"ceo_memory/provider_onboarding_plan_v21.json",plan)
        return plan
PY

cat > "$ROOT/companyos_v21ctl" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/"companyos"))
from companyos.provider_onboarding_v21.core import ProviderOnboardingV21
x=ProviderOnboardingV21()
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
if cmd=="status": out=x.inspect()
elif cmd=="build-registry": out=x.build_registry()
elif cmd=="health": out=x.local_health()
elif cmd=="plan": out=x.onboarding_plan()
else: raise SystemExit("usage: companyos_v21ctl {status|build-registry|health|plan}")
print(json.dumps(out,indent=2))
PY
chmod +x "$ROOT/companyos_v21ctl"

cat > "$ROOT/companyos_v21_summary.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
python companyos_v21ctl status
python companyos_v21ctl health
python companyos_v21ctl plan
echo
echo "Current CompanyOS runtime:"
bash companyosctl status || true
SH
chmod +x "$ROOT/companyos_v21_summary.sh"

echo "[1/5] Compile"
python -m py_compile "$PKG"/*.py "$ROOT/companyos_v21ctl"
echo "PASS compile"

echo "[2/5] Provider inspection"
python "$ROOT/companyos_v21ctl" status

echo "[3/5] Build provider registry"
python "$ROOT/companyos_v21ctl" build-registry >/dev/null
echo "PASS registry"

echo "[4/5] Local health state"
python "$ROOT/companyos_v21ctl" health

echo "[5/5] Onboarding plan"
python "$ROOT/companyos_v21ctl" plan

echo
echo "============================================================"
echo " V21 PROVIDER ONBOARDING INSTALLED"
echo "============================================================"
echo "Backup: $BACKUP"
echo
echo "Run:"
echo "  cd ~/companyos"
echo "  python companyos_v21ctl status"
echo "  python companyos_v21ctl health"
echo "  python companyos_v21ctl plan"
echo "  bash companyos_v21_summary.sh"
echo
echo "No credential values are printed."
echo "No wallet/private/seed credentials are scanned."
echo "No purchases, transfers, or external actions are executed."
