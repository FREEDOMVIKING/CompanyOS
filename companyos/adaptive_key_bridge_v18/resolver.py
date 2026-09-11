import json, os, re
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
MAP=ROOT/"config"/"adaptive_key_map_v18.json"
ENVFILE=ROOT/".companyos_secrets"/"adaptive_keys_v18.env"

ALIASES={
 "PUBLISH_STATIC_SITE":["COMPANYOS_STATIC_HOST_TOKEN","CLOUDFLARE_API_TOKEN","CF_API_TOKEN","VERCEL_TOKEN","NETLIFY_AUTH_TOKEN","RENDER_API_KEY"],
 "APPLY_DNS":["COMPANYOS_DNS_API_TOKEN","CLOUDFLARE_API_TOKEN","CF_API_TOKEN","DNS_API_TOKEN","CLOUDFLARE_GLOBAL_API_KEY"],
 "CREATE_STOREFRONT":["COMPANYOS_STOREFRONT_API_TOKEN","SHOPIFY_ACCESS_TOKEN","SHOPIFY_ADMIN_API_ACCESS_TOKEN"],
 "START_OUTREACH":["COMPANYOS_OUTREACH_API_TOKEN","RESEND_API_KEY","SENDGRID_API_KEY","MAILGUN_API_KEY","SMTP_PASSWORD"]
}
BLOCKED=("PRIVATE_KEY","WALLET","SEED","MNEMONIC","RECOVERY_PHRASE")
SEARCH=[
 ROOT/".env",ROOT/"config/.env",ROOT/"config/secrets.env",ROOT/"config/keys.env",
 ROOT/"config/credentials.env",ROOT/"config/connectors_v15.json",
 ROOT/"config/connectors_v16.json",ROOT/"config/connectors_v17.json",ROOT/"config/connectors_v18.json"
]

def now(): return datetime.now(timezone.utc).isoformat()
def safe(n): return not any(x in n.upper() for x in BLOCKED)
def read_env(p):
    d={}
    try:
        for line in Path(p).read_text(errors="ignore").splitlines():
            s=line.strip()
            if s and not s.startswith("#") and "=" in s:
                k,v=s.split("=",1); d[k.strip()]=v.strip().strip('"').strip("'")
    except: pass
    return d
def read_json(p):
    try:return json.loads(Path(p).read_text())
    except:return {}
def flatten(o,p=""):
    d={}
    if isinstance(o,dict):
        for k,v in o.items():
            q=f"{p}.{k}" if p else k
            if isinstance(v,(dict,list)): d.update(flatten(v,q))
            elif isinstance(v,str) and v: d[q]=v
    elif isinstance(o,list):
        for i,v in enumerate(o): d.update(flatten(v,f"{p}[{i}]"))
    return d

class AdaptiveKeyResolverV18:
    def discover(self):
        found={k:[] for k in ALIASES}
        for con,names in ALIASES.items():
            for n in names:
                if safe(n) and os.environ.get(n):
                    found[con].append({"source":"environment","name":n})
        for f in SEARCH:
            if not f.exists(): continue
            if f.suffix==".json":
                vals=flatten(read_json(f))
                for con,names in ALIASES.items():
                    for path,val in vals.items():
                        leaf=re.split(r"[.\[]",path)[-1].rstrip("]")
                        for n in names:
                            if safe(n) and leaf.upper()==n.upper() and val:
                                found[con].append({"source":"json_file","name":n,"path":str(f),"json_key":path})
            else:
                vals=read_env(f)
                for con,names in ALIASES.items():
                    for n in names:
                        if safe(n) and vals.get(n):
                            found[con].append({"source":"env_file","name":n,"path":str(f)})
        return found

    def build_map(self):
        f=self.discover()
        m={"version":18,"updated_at":now(),"connectors":{}}
        for con,items in f.items():
            uniq=[]; seen=set()
            for x in items:
                sig=tuple(sorted(x.items()))
                if sig not in seen: seen.add(sig); uniq.append(x)
            m["connectors"][con]={"resolved":bool(uniq),"selected":uniq[0] if uniq else None,"candidates":uniq}
        MAP.write_text(json.dumps(m,indent=2))
        return m

    def export(self):
        m=self.build_map()
        lines=["# protected CompanyOS adaptive connector bridge","set +x"]
        count=0
        for con,data in m["connectors"].items():
            s=data["selected"]
            if not s: continue
            target=ALIASES[con][0]; value=None
            if s["source"]=="environment": value=os.environ.get(s["name"])
            elif s["source"]=="env_file": value=read_env(s["path"]).get(s["name"])
            elif s["source"]=="json_file": value=flatten(read_json(s["path"])).get(s["json_key"])
            if value:
                lines.append("export %s='%s'"%(target,value.replace("'","'\"'\"'"))); count+=1
        ENVFILE.write_text("\n".join(lines)+"\n"); os.chmod(ENVFILE,0o600)
        return {"resolved_connectors":count,"env_file":str(ENVFILE),"secret_values_printed":False,"wallet_keys_scanned":False}

    def status(self):
        m=self.build_map()
        return {"status":"adaptive_key_bridge_v18_ready",
                "resolved":{k:v["resolved"] for k,v in m["connectors"].items()},
                "candidate_counts":{k:len(v["candidates"]) for k,v in m["connectors"].items()},
                "secret_values_printed":False,"wallet_keys_scanned":False}
