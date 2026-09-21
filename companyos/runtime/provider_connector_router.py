from __future__ import annotations
import json, os, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any
from companyos.runtime import provider_acquisition_broker as pab
from companyos.integrations.integration_registry import IntegrationRegistry

RT=Path.home()/".companyos_runtime"
STATE=RT/"provider_connector_router_state.json"
META=RT/"provider_discovered_metadata.json"
FREE_CF_MODEL=os.getenv("COMPANYOS_CLOUDFLARE_MODEL","@cf/zai-org/glm-4.7-flash").strip()

def atomic(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    t.replace(path)

def http(url,method="GET",headers=None,payload=None,timeout=25):
    body=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,method=method,data=body,headers={"User-Agent":"CompanyOS/69.27","Accept":"application/json",**({"Content-Type":"application/json"} if body else {}),**(headers or {})})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(3000000).decode("utf-8","replace")
            try: data=json.loads(raw)
            except Exception: data={"raw_preview":raw[:1000]}
            return int(r.status),data,{k.lower():v for k,v in r.headers.items()}
    except urllib.error.HTTPError as e:
        raw=e.read(4000).decode("utf-8","replace")
        try: data=json.loads(raw)
        except Exception: data={"raw_preview":raw[:1000]}
        return int(e.code),data,{k.lower():v for k,v in e.headers.items()}

def secrets(): return pab.discover_credentials()[1]

def metadata():
    try: return json.loads(META.read_text())
    except Exception: return {}

def discover_cf_account():
    sec=secrets().get("cloudflare_workers_ai") or {}
    token=sec.get("CLOUDFLARE_API_TOKEN") or sec.get("CF_API_TOKEN")
    explicit=sec.get("CLOUDFLARE_ACCOUNT_ID") or sec.get("CF_ACCOUNT_ID")
    if explicit:
        m=metadata(); m["cloudflare_account_id"]={"value":explicit,"source":"authorized_env","ts":time.time()}; atomic(META,m)
        return {"available":True,"source":"authorized_env"}
    if not token: return {"available":False,"reason":"token_missing"}
    status,data,_=http("https://api.cloudflare.com/client/v4/accounts?per_page=50",headers={"Authorization":f"Bearer {token}"})
    rows=(data or {}).get("result") if isinstance(data,dict) else []
    ids=[x.get("id") for x in (rows or []) if isinstance(x,dict) and x.get("id")]
    if status==200 and len(ids)==1:
        m=metadata(); m["cloudflare_account_id"]={"value":ids[0],"source":"cloudflare_accounts_api","ts":time.time()}; atomic(META,m)
        return {"available":True,"source":"cloudflare_accounts_api"}
    return {"available":False,"reason":"account_id_not_unambiguous","http_status":status,"account_count":len(ids)}

def cf_account_id():
    sec=secrets().get("cloudflare_workers_ai") or {}
    v=sec.get("CLOUDFLARE_ACCOUNT_ID") or sec.get("CF_ACCOUNT_ID")
    if v: return v
    row=metadata().get("cloudflare_account_id") or {}
    return row.get("value")

def provider_status():
    inventory,private=pab.discover_credentials()
    cfdisc=discover_cf_account()
    cfsec=private.get("cloudflare_workers_ai") or {}
    cf_token=cfsec.get("CLOUDFLARE_API_TOKEN") or cfsec.get("CF_API_TOKEN")
    cf_ready=bool(cf_token and cf_account_id())
    tavily=bool((private.get("tavily") or {}).get("TAVILY_API_KEY"))
    brave=bool((private.get("brave_search") or {}).get("BRAVE_SEARCH_API_KEY") or (private.get("brave_search") or {}).get("BRAVE_API_KEY"))
    caps={
      "web_search":[x for x,v in (("tavily",tavily),("brave_search",brave)) if v],
      "public_code_research":["github_public_rest"],
      "llm_inference":[x for x,v in (("cloudflare_workers_ai",cf_ready),("groq",bool((private.get("groq") or {}).get("GROQ_API_KEY"))),("gemini",bool((private.get("gemini") or {}).get("GEMINI_API_KEY") or (private.get("gemini") or {}).get("GOOGLE_API_KEY"))),("huggingface",bool((private.get("huggingface") or {}).get("HF_TOKEN") or (private.get("huggingface") or {}).get("HUGGINGFACE_TOKEN"))),("openai",bool((private.get("openai") or {}).get("OPENAI_API_KEY") or (private.get("openai") or {}).get("COMPANYOS_OPENAI_API_KEY")))) if v]
    }
    out={"schema":"companyos.provider_connector_router.v69_27","generated_at_unix":time.time(),"capabilities":caps,"cloudflare":{"ready":cf_ready,"account_id_present":bool(cf_account_id()),"model":FREE_CF_MODEL,"discovery":cfdisc},"secret_values_emitted":False,"public_key_harvesting_performed":False,"financial_action_performed":False}
    atomic(STATE,out)
    reg=IntegrationRegistry(Path.home())
    for x in caps["web_search"]: reg.register(x,"research_provider",["web_search","market_research"],True,{"source":"v69.27"})
    for x in caps["public_code_research"]: reg.register(x,"research_provider",["public_code_research","repository_discovery"],True,{"source":"v69.27"})
    for x in caps["llm_inference"]: reg.register(x,"ai_provider",["llm_inference"],True,{"source":"v69.27"})
    return out

def github_public_search(query,max_results=5):
    url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":query,"per_page":max(1,min(10,int(max_results)))})
    status,data,h=http(url)
    if status!=200: raise RuntimeError(f"github_public_http_{status}")
    rows=[{"name":x.get("full_name"),"url":x.get("html_url"),"description":x.get("description"),"stars":x.get("stargazers_count")} for x in (data.get("items") or []) if isinstance(x,dict)]
    return {"provider":"github_public_rest","results":rows,"result_count":len(rows),"rate_remaining":h.get("x-ratelimit-remaining")}

def tavily_search(query,max_results=5):
    key=(secrets().get("tavily") or {}).get("TAVILY_API_KEY")
    if not key: raise RuntimeError("tavily_key_missing")
    status,data,_=http("https://api.tavily.com/search",method="POST",payload={"api_key":key,"query":query,"search_depth":"basic","max_results":max(1,min(8,int(max_results))),"include_answer":False,"include_raw_content":False},timeout=35)
    if status!=200: raise RuntimeError(f"tavily_http_{status}")
    rows=[{"title":x.get("title"),"url":x.get("url"),"content":x.get("content"),"score":x.get("score")} for x in (data.get("results") or []) if isinstance(x,dict)]
    return {"provider":"tavily","results":rows,"result_count":len(rows)}

def brave_search(query,max_results=5):
    sec=secrets().get("brave_search") or {}; key=sec.get("BRAVE_SEARCH_API_KEY") or sec.get("BRAVE_API_KEY")
    if not key: raise RuntimeError("brave_key_missing")
    url="https://api.search.brave.com/res/v1/web/search?"+urllib.parse.urlencode({"q":query,"count":max(1,min(10,int(max_results))),"safesearch":"moderate"})
    status,data,_=http(url,headers={"X-Subscription-Token":key})
    if status!=200: raise RuntimeError(f"brave_http_{status}")
    rows=[{"title":x.get("title"),"url":x.get("url"),"content":x.get("description")} for x in ((data.get("web") or {}).get("results") or []) if isinstance(x,dict)]
    return {"provider":"brave_search","results":rows,"result_count":len(rows)}

def search_web(query,max_results=5):
    available=(provider_status().get("capabilities") or {}).get("web_search") or []
    errors=[]
    for name,fn in (("tavily",tavily_search),("brave_search",brave_search)):
        if name not in available: continue
        try:
            out=fn(query,max_results); out["attempts"]=errors+[{"provider":name,"status":"success"}]; return out
        except Exception as e: errors.append({"provider":name,"status":"failed","error":f"{type(e).__name__}:{str(e)[:300]}"})
    return {"provider":None,"results":[],"result_count":0,"status":"no_usable_web_search_provider","attempts":errors}

if __name__=="__main__": print(json.dumps(provider_status(),indent=2,sort_keys=True))
