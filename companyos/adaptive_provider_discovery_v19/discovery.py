import json,re
from pathlib import Path
from urllib.parse import urlparse
R=Path.home()/"companyos"
def env():
 d={}
 for x in (R/".env").read_text(errors="ignore").splitlines():
  x=x.strip()
  if x.startswith("export "): x=x[7:]
  if x and not x.startswith("#") and "=" in x:
   k,v=x.split("=",1); d[k.strip()]=v.strip().strip("'\"")
 return d
C={
"PUBLISH_STATIC_SITE":(["COMPANYOS_HOSTING_TOKEN","CLOUDFLARE_API_TOKEN"],["COMPANYOS_HOSTING_DEPLOY_URL"]),
"APPLY_DNS":(["COMPANYOS_DOMAIN_TOKEN","CLOUDFLARE_API_TOKEN"],["COMPANYOS_DOMAIN_API_URL"]),
"CREATE_STOREFRONT":(["COMPANYOS_API_TOKEN"],["COMPANYOS_API_BASE_URL"]),
"START_OUTREACH":(["COMPANYOS_SMTP_PASSWORD"],["COMPANYOS_SMTP_HOST"])}
def first(e,a): return next((x for x in a if e.get(x)),None)
def valid(action,v):
 if not v:return False
 if action=="START_OUTREACH": return bool(re.fullmatch(r"[A-Za-z0-9.-]+",v.split(":")[0]))
 u=urlparse(v); return u.scheme in ("http","https") and bool(u.netloc)
def provider(action,v):
 q=(v or "").lower()
 for n in ("cloudflare","vercel","netlify","namecheap","godaddy","sendgrid","mailgun","resend","gmail"):
  if n in q:return n
 return "generic_smtp" if action=="START_OUTREACH" else "generic"
def discover():
 e=env(); z={"status":"companyos_v19_provider_discovery_ready","secret_values_printed":False,"wallet_private_keys_scanned":False,"connectors":{}}
 for a,(ts,es) in C.items():
  t=first(e,ts); ep=first(e,es); val=e.get(ep,"") if ep else ""
  z["connectors"][a]={"provider":provider(a,val),"token_env":t,"token_present":bool(t),"endpoint_env":ep,"endpoint_present":bool(ep),"endpoint_shape_valid":valid(a,val),"configuration_ready":bool(t and ep and valid(a,val))}
 (R/"ceo_memory/provider_discovery_v19.json").write_text(json.dumps(z,indent=2))
 return z
def build():
 z=discover(); c={"version":19,"global":{"dry_run":True,"network_validation":False},"connectors":{},"policy":{"allow_domain_purchase":False,"allow_wallet_signing":False,"allow_fund_transfer":False,"allow_spending":False}}
 for a,d in z["connectors"].items():
  c["connectors"][a]={"provider":d["provider"],"enabled":d["configuration_ready"],"token_env":d["token_env"],"endpoint_env":d["endpoint_env"],"dry_run":True}
 (R/"config/connectors_v19.json").write_text(json.dumps(c,indent=2)); return c
def validate():
 c=build(); q={a:{"configured":bool(v["enabled"]),"provider":v["provider"],"network_request_sent":False} for a,v in c["connectors"].items()}
 return {"status":"companyos_v19_local_validation_complete","configured_connectors":sum(x["configured"] for x in q.values()),"total_connectors":len(q),"checks":q,"external_actions_executed":False}
