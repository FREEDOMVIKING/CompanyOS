#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PKG="$ROOT/companyos/adaptive_connector_activation_v20"
BACKUP="$ROOT/backups/v20_connector_activation_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " CompanyOS V20 - Adaptive Connector Mapping + Activation"
echo "============================================================"

test -d "$ROOT/companyos" || { echo "FAIL: $ROOT/companyos missing"; exit 1; }
test -f "$ROOT/.env" || { echo "FAIL: $ROOT/.env missing"; exit 1; }

mkdir -p "$PKG" "$ROOT/config" "$ROOT/ceo_memory" "$BACKUP"

for f in "$ROOT/.env" "$ROOT/config/connectors.json" "$ROOT/config/connectors_v18.json" "$ROOT/config/connectors_v19.json"; do
  [ -e "$f" ] && cp -a "$f" "$BACKUP/" || true
done

cat > "$PKG/__init__.py" <<'PY'
from .activation import AdaptiveConnectorActivationV20
PY

cat > "$PKG/activation.py" <<'PY'
import json, re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"

MAP={
 "PUBLISH_STATIC_SITE":("hosting","COMPANYOS_HOSTING_TOKEN","COMPANYOS_HOSTING_DEPLOY_URL"),
 "APPLY_DNS":("domains","COMPANYOS_DOMAIN_TOKEN","COMPANYOS_DOMAIN_API_URL"),
 "CREATE_STOREFRONT":("rest_api","COMPANYOS_API_TOKEN","COMPANYOS_API_BASE_URL"),
 "START_OUTREACH":("smtp","COMPANYOS_SMTP_PASSWORD","COMPANYOS_SMTP_HOST"),
}

def now(): return datetime.now(timezone.utc).isoformat()

def parse_env(path):
 d={}
 for line in Path(path).read_text(errors="ignore").splitlines():
  s=line.strip()
  if not s or s.startswith("#") or "=" not in s: continue
  if s.startswith("export "): s=s[7:].strip()
  k,v=s.split("=",1)
  d[k.strip()]=v.strip().strip("'").strip('"')
 return d

def read_json(path,default):
 try:return json.loads(Path(path).read_text())
 except:return default

def write_json(path,obj):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2,sort_keys=True))

def provider(action,endpoint):
 q=(endpoint or "").lower()
 if action=="START_OUTREACH":
  if "smtp.gmail.com" in q:return "gmail_smtp"
  if "sendgrid" in q:return "sendgrid"
  if "mailgun" in q:return "mailgun"
  return "generic_smtp"
 for name in ("cloudflare","vercel","netlify","namecheap","godaddy","shopify"):
  if name in q:return name
 return "legacy_companyos_adapter"

def endpoint_ok(action,value):
 if not value:return False
 if action=="START_OUTREACH":
  return bool(re.fullmatch(r"[A-Za-z0-9.-]+",value.split(":")[0]))
 u=urlparse(value)
 return u.scheme in ("http","https") and bool(u.netloc)

class AdaptiveConnectorActivationV20:
 def __init__(self,root=ROOT):
  self.root=Path(root)
  self.env_path=self.root/".env"
  self.legacy_path=self.root/"config/connectors.json"
  self.v20_path=self.root/"config/connectors_v20.json"

 def inspect(self):
  env=parse_env(self.env_path)
  legacy=read_json(self.legacy_path,{})
  out={"status":"companyos_v20_connector_mapping_ready","updated_at":now(),
       "secret_values_printed":False,"wallet_private_keys_scanned":False,"connectors":{}}
  for action,(section,token_env,endpoint_env) in MAP.items():
   sec=legacy.get(section,{}) if isinstance(legacy,dict) else {}
   token_present=bool(env.get(token_env))
   endpoint_present=bool(env.get(endpoint_env))
   ep=env.get(endpoint_env,"")
   ok=endpoint_ok(action,ep)
   out["connectors"][action]={
    "legacy_section":section,
    "provider":provider(action,ep),
    "token_env":token_env,
    "token_present":token_present,
    "endpoint_env":endpoint_env,
    "endpoint_present":endpoint_present,
    "endpoint_shape_valid":ok,
    "legacy_enabled":bool(sec.get("enabled",False)) if isinstance(sec,dict) else False,
    "legacy_dry_run":sec.get("dry_run") if isinstance(sec,dict) else None,
    "configuration_ready":bool(token_present and endpoint_present and ok)
   }
  write_json(self.root/"ceo_memory/connector_mapping_v20.json",out)
  return out

 def build_config(self):
  info=self.inspect()
  cfg={"version":20,"generated_at":now(),
       "global":{"activation_mode":"validated_mapping","network_validation":False,"external_execution":False},
       "connectors":{},
       "policy":{"allow_nonfinancial_connector_activation":True,
                 "allow_domain_purchase":False,"allow_wallet_signing":False,
                 "allow_fund_transfer":False,"allow_spending":False}}
  for action,d in info["connectors"].items():
   cfg["connectors"][action]={
    "provider":d["provider"],"enabled":d["configuration_ready"],
    "token_env":d["token_env"],"endpoint_env":d["endpoint_env"],
    "network_validation":False,"external_execution":False
   }
  write_json(self.v20_path,cfg)
  return cfg

 def validate(self):
  cfg=self.build_config()
  checks={a:{"configured":bool(v["enabled"]),"provider":v["provider"],
             "network_request_sent":False,"external_action_executed":False}
          for a,v in cfg["connectors"].items()}
  result={"status":"companyos_v20_local_validation_complete",
          "configured_connectors":sum(1 for x in checks.values() if x["configured"]),
          "total_connectors":len(checks),"checks":checks,
          "secret_values_printed":False,"external_actions_executed":False}
  write_json(self.root/"ceo_memory/connector_validation_v20.json",result)
  return result

 def plan(self):
  v=self.validate()
  plan={"status":"companyos_v20_activation_plan_ready",
        "ready_connectors":[a for a,x in v["checks"].items() if x["configured"]],
        "blocked_connectors":[a for a,x in v["checks"].items() if not x["configured"]],
        "financial_actions_blocked":True,"external_execution_enabled":False}
  write_json(self.root/"ceo_memory/connector_activation_plan_v20.json",plan)
  return plan
PY

cat > "$ROOT/companyos_v20ctl" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/"companyos"))
from companyos.adaptive_connector_activation_v20.activation import AdaptiveConnectorActivationV20
x=AdaptiveConnectorActivationV20()
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
if cmd=="status": out=x.inspect()
elif cmd=="build-config": out=x.build_config()
elif cmd=="validate": out=x.validate()
elif cmd=="plan": out=x.plan()
else: raise SystemExit("usage: companyos_v20ctl {status|build-config|validate|plan}")
print(json.dumps(out,indent=2))
PY
chmod +x "$ROOT/companyos_v20ctl"

echo "[1/5] Compile"
python -m py_compile "$PKG"/*.py "$ROOT/companyos_v20ctl"
echo "PASS compile"

echo "[2/5] Adaptive mapping"
python "$ROOT/companyos_v20ctl" status

echo "[3/5] Build config"
python "$ROOT/companyos_v20ctl" build-config >/dev/null
echo "PASS config"

echo "[4/5] Validate"
python "$ROOT/companyos_v20ctl" validate

echo "[5/5] Activation plan"
python "$ROOT/companyos_v20ctl" plan

echo
echo "V20 ADAPTIVE CONNECTOR ACTIVATION INSTALLED"
echo "Backup: $BACKUP"
echo
echo "Run:"
echo "  cd ~/companyos"
echo "  python companyos_v20ctl status"
echo "  python companyos_v20ctl validate"
echo "  python companyos_v20ctl plan"
echo
echo "No secret values printed."
echo "No wallet/private/seed credentials scanned."
echo "No external actions or financial operations executed."
