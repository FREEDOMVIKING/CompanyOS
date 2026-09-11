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
