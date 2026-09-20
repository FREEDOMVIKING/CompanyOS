#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PKG="$ROOT/companyos/adaptive_credential_resolver_v18"
BACKUP="$ROOT/backups/v18_adaptive_resolver_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " CompanyOS V18 - Adaptive Credential Resolver"
echo "============================================================"

test -d "$ROOT/companyos" || { echo "FAIL: $ROOT/companyos not found"; exit 1; }
test -f "$ROOT/.env" || { echo "FAIL: $ROOT/.env not found"; exit 1; }

mkdir -p "$PKG" "$ROOT/.companyos_secrets" "$ROOT/ceo_memory" "$BACKUP"
chmod 700 "$ROOT/.companyos_secrets"

for f in "$ROOT/config/connectors_v18.json" "$ROOT/config/connectors.json" "$ROOT/companyosctl" "$ROOT/companyos_v18ctl"; do
  [ -e "$f" ] && cp -a "$f" "$BACKUP/" || true
done

cat > "$PKG/__init__.py" <<'PY'
from .resolver import AdaptiveCredentialResolverV18
PY

cat > "$PKG/resolver.py" <<'PY'
import json, os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"

MAP={
 "PUBLISH_STATIC_SITE":{"token":"COMPANYOS_HOSTING_TOKEN","endpoint":"COMPANYOS_HOSTING_DEPLOY_URL","alias":"COMPANYOS_STATIC_HOST_TOKEN"},
 "APPLY_DNS":{"token":"COMPANYOS_DOMAIN_TOKEN","endpoint":"COMPANYOS_DOMAIN_API_URL","alias":"COMPANYOS_DNS_API_TOKEN"},
 "CREATE_STOREFRONT":{"token":"COMPANYOS_API_TOKEN","endpoint":"COMPANYOS_API_BASE_URL","alias":"COMPANYOS_STOREFRONT_API_TOKEN"},
 "START_OUTREACH":{"token":"COMPANYOS_SMTP_PASSWORD","endpoint":"COMPANYOS_SMTP_HOST","alias":"COMPANYOS_OUTREACH_API_TOKEN"}
}

OPTIONAL={
 "crm":("COMPANYOS_CRM_TOKEN","COMPANYOS_CRM_API_URL"),
 "accounting":("COMPANYOS_ACCOUNTING_TOKEN","COMPANYOS_ACCOUNTING_API_URL"),
 "banking":("COMPANYOS_BANKING_TOKEN","COMPANYOS_BANKING_HANDOFF_URL"),
 "crypto":("COMPANYOS_CRYPTO_TOKEN","COMPANYOS_CRYPTO_HANDOFF_URL")
}

def now():
    return datetime.now(timezone.utc).isoformat()

def env_file(path):
    d={}
    for line in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        if s.startswith("export "): s=s[7:].strip()
        k,v=s.split("=",1)
        d[k.strip()]=v.strip().strip('"').strip("'")
    return d

def load_json(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def save_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

class AdaptiveCredentialResolverV18:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.env_path=self.root/".env"
        self.cfg_path=self.root/"config/connectors_v18.json"
        self.report_path=self.root/"ceo_memory/adaptive_credential_resolver_v18.json"
        self.runtime_env=self.root/".companyos_secrets/adaptive_runtime_v18.env"

    def inspect(self):
        env=env_file(self.env_path)
        result={"status":"adaptive_credential_resolver_v18_ready","updated_at":now(),"connectors":{},"optional":{}}
        for action,m in MAP.items():
            tp=bool(env.get(m["token"])); ep=bool(env.get(m["endpoint"]))
            result["connectors"][action]={
                "token_env":m["token"],"token_present":tp,
                "endpoint_env":m["endpoint"],"endpoint_present":ep,
                "ready":bool(tp and ep)
            }
        for name,(t,e) in OPTIONAL.items():
            result["optional"][name]={"token_present":bool(env.get(t)),"endpoint_present":bool(env.get(e)),"ready":bool(env.get(t) and env.get(e))}
        result["wallet_private_keys_scanned"]=False
        result["secret_values_printed"]=False
        save_json(self.report_path,result)
        return result

    def patch_config(self):
        env=env_file(self.env_path)
        cfg=load_json(self.cfg_path,{"version":18,"connectors":{},"policy":{}})
        cfg.setdefault("connectors",{})
        changed={}
        for action,m in MAP.items():
            ready=bool(env.get(m["token"]) and env.get(m["endpoint"]))
            spec=cfg["connectors"].setdefault(action,{})
            spec["provider"]="legacy_companyos_adapter"
            spec["enabled"]=ready
            spec["required_env"]=[m["token"],m["endpoint"]]
            spec["legacy_token_env"]=m["token"]
            spec["legacy_endpoint_env"]=m["endpoint"]
            spec["adaptive_mapping"]=True
            changed[action]={"enabled":ready,"token_present":bool(env.get(m["token"])),"endpoint_present":bool(env.get(m["endpoint"]))}
        cfg.setdefault("policy",{})
        cfg["policy"]["allow_domain_purchase"]=False
        cfg["policy"]["allow_wallet_signing"]=False
        cfg["policy"]["allow_fund_transfer"]=False
        cfg["policy"]["allow_spending"]=False
        cfg["adaptive_credential_resolver"]="v18"
        save_json(self.cfg_path,cfg)
        return {"patched":True,"connectors":changed,"config_path":str(self.cfg_path)}

    def write_runtime_env(self):
        env=env_file(self.env_path)
        lines=["# CompanyOS V18 adaptive runtime aliases","set +x"]
        mapped=0
        for action,m in MAP.items():
            val=env.get(m["token"])
            if val:
                lines.append("export %s='%s'"%(m["alias"],val.replace("'","'\"'\"'")))
                mapped+=1
        self.runtime_env.write_text("\n".join(lines)+"\n",encoding="utf-8")
        os.chmod(self.runtime_env,0o600)
        return {"mapped_tokens":mapped,"runtime_env":str(self.runtime_env),"secret_values_printed":False}

    def apply(self):
        return {"inspect":self.inspect(),"patch":self.patch_config(),"runtime_env":self.write_runtime_env()}
PY

cat > "$ROOT/adaptive_resolver_v18ctl" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/"companyos"))
from companyos.adaptive_credential_resolver_v18.resolver import AdaptiveCredentialResolverV18
r=AdaptiveCredentialResolverV18()
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
if cmd=="status": out=r.inspect()
elif cmd=="apply": out=r.apply()
elif cmd=="patch": out=r.patch_config()
elif cmd=="runtime-env": out=r.write_runtime_env()
else: raise SystemExit("usage: adaptive_resolver_v18ctl {status|apply|patch|runtime-env}")
print(json.dumps(out,indent=2))
PY
chmod +x "$ROOT/adaptive_resolver_v18ctl"

cat > "$ROOT/load_companyos_adaptive_v18.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
python "$ROOT/adaptive_resolver_v18ctl" runtime-env >/dev/null
set +x
. "$ROOT/.companyos_secrets/adaptive_runtime_v18.env"
echo "Adaptive CompanyOS connector credentials loaded without printing secret values."
SH
chmod +x "$ROOT/load_companyos_adaptive_v18.sh"

echo "[1/5] Compile"
python -m py_compile "$PKG"/*.py "$ROOT/adaptive_resolver_v18ctl"
echo "PASS compile"

echo "[2/5] Inspect existing CompanyOS credentials"
python "$ROOT/adaptive_resolver_v18ctl" status

echo "[3/5] Apply legacy-to-V18 mappings"
python "$ROOT/adaptive_resolver_v18ctl" apply

echo "[4/5] Protected secret bridge"
chmod 600 "$ROOT/.companyos_secrets/adaptive_runtime_v18.env"
python - <<'PY'
from pathlib import Path
import stat
p=Path.home()/"companyos/.companyos_secrets/adaptive_runtime_v18.env"
mode=stat.S_IMODE(p.stat().st_mode)
assert mode==0o600, oct(mode)
print("PASS protected runtime env:", oct(mode))
PY

echo "[5/5] Load aliases and refresh V18"
cd "$ROOT"
set +x
. "$ROOT/load_companyos_adaptive_v18.sh"
bash companyosctl restart
bash companyosctl cycle
bash companyosctl status

echo
echo "V18 ADAPTIVE CREDENTIAL RESOLVER INSTALLED"
echo "Backup: $BACKUP"
echo
echo "Commands:"
echo "  cd ~/companyos"
echo "  python adaptive_resolver_v18ctl status"
echo "  . ./load_companyos_adaptive_v18.sh"
echo "  bash companyosctl env-check"
echo "  bash companyosctl status"
echo
echo "Existing CompanyOS connector credentials are reused."
echo "SMTP is preserved."
echo "Crypto remains unresolved if COMPANYOS_CRYPTO_TOKEN is missing."
echo "Wallet/private/seed credentials are not scanned or repurposed."
