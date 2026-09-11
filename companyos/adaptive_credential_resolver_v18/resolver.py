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
