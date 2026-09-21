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
      "web_search":[x for x,v in (("tavily",tavily),("brave_search",brave),("public_research_mesh",True)) if v],
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

# COMPANYOS_V69_28_INTERNAL_INFERENCE_ROTATION
def _provider_health_state():
    path=RT/"provider_resource_health.json"
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def _save_provider_health(data):
    atomic(RT/"provider_resource_health.json",data)

def _health_row(name):
    state=_provider_health_state()
    return (state.get("providers") or {}).get(name) or {}

def _cooldown_remaining(name):
    row=_health_row(name)
    try:
        return max(0.0,float(row.get("blocked_until_unix") or 0.0)-time.time())
    except Exception:
        return 0.0

def _mark_provider_success(name,latency_seconds=None):
    state=_provider_health_state()
    rows=state.setdefault("providers",{})
    old=rows.get(name) if isinstance(rows.get(name),dict) else {}
    rows[name]={
        **old,
        "last_success_at_unix":time.time(),
        "last_error":None,
        "consecutive_failures":0,
        "blocked_until_unix":0.0,
        "last_latency_seconds":latency_seconds,
    }
    state["updated_at_unix"]=time.time()
    _save_provider_health(state)

def _mark_provider_failure(name,error):
    text=str(error or "").lower()
    if "429" in text or "rate limit" in text:
        cooldown=900.0
    elif "credit" in text or "quota" in text or "insufficient" in text:
        cooldown=21600.0
    elif "401" in text or "403" in text or "unauthorized" in text or "forbidden" in text:
        cooldown=3600.0
    else:
        cooldown=180.0

    state=_provider_health_state()
    rows=state.setdefault("providers",{})
    old=rows.get(name) if isinstance(rows.get(name),dict) else {}
    failures=int(old.get("consecutive_failures") or 0)+1
    cooldown=min(43200.0,cooldown*min(4,failures))
    rows[name]={
        **old,
        "last_failure_at_unix":time.time(),
        "last_error":str(error)[:1200],
        "consecutive_failures":failures,
        "blocked_until_unix":time.time()+cooldown,
    }
    state["updated_at_unix"]=time.time()
    _save_provider_health(state)

# COMPANYOS_V69_30C_CLOUDFLARE_RESPONSE_PARSER
def _extract_cloudflare_text(result):
    if isinstance(result,str):
        return result.strip()

    if isinstance(result,list):
        parts=[]
        for item in result:
            if isinstance(item,str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item,dict):
                for key in ("text","content","output_text","response"):
                    value=item.get(key)
                    if isinstance(value,str) and value.strip():
                        parts.append(value.strip())
                        break
        return "".join(parts).strip()

    if not isinstance(result,dict):
        return ""

    for key in ("response","text","generated_text","output_text","content"):
        value=result.get(key)
        if isinstance(value,str) and value.strip():
            return value.strip()
        if isinstance(value,(list,dict)):
            text=_extract_cloudflare_text(value)
            if text:
                return text

    choices=result.get("choices")
    if isinstance(choices,list):
        for choice in choices:
            if not isinstance(choice,dict):
                continue

            value=choice.get("text")
            if isinstance(value,str) and value.strip():
                return value.strip()

            message=choice.get("message")
            if isinstance(message,dict):
                text=_extract_cloudflare_text(message.get("content"))
                if text:
                    return text

                reasoning=message.get("reasoning_content")
                if isinstance(reasoning,str) and reasoning.strip():
                    return reasoning.strip()

            delta=choice.get("delta")
            if isinstance(delta,dict):
                text=_extract_cloudflare_text(delta.get("content"))
                if text:
                    return text

    for key in ("result","output","data"):
        nested=result.get(key)
        if isinstance(nested,(dict,list,str)):
            text=_extract_cloudflare_text(nested)
            if text:
                return text

    return ""

def cloudflare_infer(prompt,max_tokens=160):
    sec=secrets().get("cloudflare_workers_ai") or {}
    token=sec.get("CLOUDFLARE_API_TOKEN") or sec.get("CF_API_TOKEN")
    account=cf_account_id()
    if not token:
        raise RuntimeError("cloudflare_token_missing")
    if not account:
        raise RuntimeError("cloudflare_account_id_missing")

    model=FREE_CF_MODEL
    url=(
        "https://api.cloudflare.com/client/v4/accounts/"
        +urllib.parse.quote(str(account),safe="")
        +"/ai/run/"
        +urllib.parse.quote(model,safe="@/._-")
    )
    started=time.time()
    status,data,_=http(
        url,
        method="POST",
        headers={"Authorization":f"Bearer {token}"},
        payload={
            "messages":[{"role":"user","content":str(prompt)}],
            "max_tokens":max(32,min(800,int(max_tokens))),
        },
        timeout=45,
    )
    latency=time.time()-started
    if status!=200 or not bool((data or {}).get("success")):
        raise RuntimeError(f"cloudflare_http_{status}:{json.dumps(data)[:1000]}")
    result=(data or {}).get("result")
    text=_extract_cloudflare_text(result)
    if not text:
        shape={
            "result_type":type(result).__name__,
            "result_keys":sorted(result.keys()) if isinstance(result,dict) else [],
        }
        if isinstance(result,dict):
            choices=result.get("choices")
            if isinstance(choices,list):
                shape["choice_count"]=len(choices)
                shape["choice_keys"]=[
                    sorted(x.keys()) for x in choices[:3] if isinstance(x,dict)
                ]
                shape["message_keys"]=[
                    sorted((x.get("message") or {}).keys())
                    for x in choices[:3]
                    if isinstance(x,dict) and isinstance(x.get("message"),dict)
                ]
        raise RuntimeError(
            "cloudflare_success_without_usable_text:"
            +json.dumps(shape,sort_keys=True)
        )
    return {
        "provider":"cloudflare_workers_ai",
        "model":model,
        "text":text,
        "latency_seconds":round(latency,3),
        "external_action_performed":False,
        "financial_action_performed":False,
    }

def openai_internal_infer(prompt,max_tokens=160):
    from companyos.runtime import openai_web_evidence_fallback as ow

    key,_source=ow.resolve_api_key()
    if not key:
        raise RuntimeError("openai_api_key_missing")

    errors=[]
    for model in ow._ordered_models():
        if ow._model_cooldown_remaining(model)>0:
            errors.append({"model":model,"status":"cooldown_skip"})
            continue
        payload={
            "model":model,
            "input":str(prompt),
            "max_output_tokens":max(32,min(800,int(max_tokens))),
        }
        started=time.time()
        try:
            response=ow._request_json(payload,key,max_attempts=1)
            text=ow._message_text(response)
            ow._mark_model_success(model)
            return {
                "provider":"openai",
                "model":model,
                "text":text,
                "latency_seconds":round(time.time()-started,3),
                "external_action_performed":False,
                "financial_action_performed":False,
            }
        except Exception as exc:
            message=f"{type(exc).__name__}:{str(exc)[:1200]}"
            errors.append({"model":model,"status":"failed","error":message})
            if ow._is_429_error(message):
                ow._mark_model_rate_limited(model,message)
    raise RuntimeError("openai_internal_infer_failed:"+json.dumps(errors)[:1800])

def infer_text(prompt,max_tokens=160):
    status=provider_status()
    available=(status.get("capabilities") or {}).get("llm_inference") or []
    attempts=[]

    for name,fn in (
        ("cloudflare_workers_ai",cloudflare_infer),
        ("openai",openai_internal_infer),
    ):
        if name not in available:
            continue
        remaining=_cooldown_remaining(name)
        if remaining>0:
            attempts.append({
                "provider":name,
                "status":"cooldown_skip",
                "cooldown_remaining_seconds":round(remaining,2),
            })
            continue
        try:
            out=fn(prompt,max_tokens=max_tokens)
            _mark_provider_success(name,out.get("latency_seconds"))
            out["attempts"]=attempts+[{"provider":name,"status":"success"}]
            return out
        except Exception as exc:
            message=f"{type(exc).__name__}:{str(exc)[:1000]}"
            _mark_provider_failure(name,message)
            attempts.append({"provider":name,"status":"failed","error":message})

    return {
        "provider":None,
        "model":None,
        "text":"",
        "status":"no_usable_inference_provider",
        "attempts":attempts,
        "external_action_performed":False,
        "financial_action_performed":False,
    }

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

# COMPANYOS_V69_31_PUBLIC_RESEARCH_MESH
def wikipedia_search(query,max_results=5):
    count=max(1,min(10,int(max_results)))
    url="https://en.wikipedia.org/w/rest.php/v1/search/page?"+urllib.parse.urlencode({
        "q":str(query),
        "limit":count,
    })
    status,data,_=http(
        url,
        headers={
            "User-Agent":"CompanyOS/69.31 autonomous research",
            "Accept":"application/json",
        },
        timeout=25,
    )
    if status!=200:
        raise RuntimeError(f"wikipedia_http_{status}")

    rows=[]
    for x in ((data or {}).get("pages") or [])[:count]:
        if not isinstance(x,dict):
            continue
        title=str(x.get("title") or "").strip()
        key=str(x.get("key") or title.replace(" ","_")).strip()
        excerpt=str(x.get("excerpt") or "").strip()
        description=str(x.get("description") or "").strip()
        content=" ".join(v for v in (description,excerpt) if v).strip()
        rows.append({
            "title":title,
            "url":"https://en.wikipedia.org/wiki/"+urllib.parse.quote(key,safe="()_-'"),
            "content":content,
            "source":"wikipedia",
            "metadata":{
                "matched_title":x.get("matched_title"),
                "description":description,
            },
        })
    return {
        "provider":"wikipedia",
        "results":rows,
        "result_count":len(rows),
    }

def gdelt_search(query,max_results=5):
    count=max(1,min(20,int(max_results)))
    url="https://api.gdeltproject.org/api/v2/doc/doc?"+urllib.parse.urlencode({
        "query":str(query),
        "mode":"ArtList",
        "format":"json",
        "maxrecords":count,
        "sort":"HybridRel",
    })
    status,data,_=http(
        url,
        headers={
            "User-Agent":"CompanyOS/69.31 autonomous research",
            "Accept":"application/json",
        },
        timeout=35,
    )
    if status!=200:
        raise RuntimeError(f"gdelt_http_{status}")

    articles=[]
    if isinstance(data,dict):
        articles=data.get("articles") or data.get("results") or []

    rows=[]
    for x in (articles or [])[:count]:
        if not isinstance(x,dict):
            continue
        link=str(x.get("url") or x.get("url_mobile") or "").strip()
        title=str(x.get("title") or "").strip()
        if not link and not title:
            continue
        rows.append({
            "title":title,
            "url":link,
            "content":str(x.get("domain") or ""),
            "source":"gdelt",
            "metadata":{
                "domain":x.get("domain"),
                "seen_date":x.get("seendate"),
                "language":x.get("language"),
                "source_country":x.get("sourcecountry"),
            },
        })
    return {
        "provider":"gdelt",
        "results":rows,
        "result_count":len(rows),
    }

def public_research_mesh_search(query,max_results=5):
    limit=max(1,min(12,int(max_results)))
    collected=[]
    source_errors=[]
    providers_used=[]

    for name,fn in (
        ("gdelt",gdelt_search),
        ("wikipedia",wikipedia_search),
        ("github_public_rest",github_public_search),
    ):
        try:
            out=fn(query,max_results=limit)
            providers_used.append(name)
            for row in out.get("results") or []:
                if isinstance(row,dict):
                    item=dict(row)
                    item.setdefault("source",name)
                    collected.append(item)
        except Exception as exc:
            source_errors.append({
                "provider":name,
                "error":f"{type(exc).__name__}:{str(exc)[:300]}",
            })

    dedup=[]
    seen=set()
    for row in collected:
        key=(str(row.get("url") or "").strip().lower()
             or str(row.get("title") or row.get("name") or "").strip().lower())
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(row)
        if len(dedup)>=limit:
            break

    return {
        "provider":"public_research_mesh",
        "results":dedup,
        "result_count":len(dedup),
        "providers_used":providers_used,
        "source_errors":source_errors,
        "read_only":True,
        "financial_action_performed":False,
    }

# COMPANYOS_V69_35A_REMOTE_RUNTIME_FABRIC
def search_web(query,max_results=5):
    errors=[]
    remote_allowed=(
        os.getenv("COMPANYOS_ENABLE_REMOTE_FABRIC","1")=="1"
        and os.getenv("COMPANYOS_REMOTE_WORKER_LOCAL_ONLY","0")!="1"
    )
    if remote_allowed:
        try:
            from companyos.runtime import remote_runtime_fabric as rrf
            remote=rrf.search_web_remote(query,max_results=max_results)
            if int(remote.get("result_count") or 0)>0:
                return remote
            errors.append({"provider":"remote_runtime_fabric","status":"empty"})
        except Exception as exc:
            errors.append({
                "provider":"remote_runtime_fabric",
                "status":"unavailable",
                "error":f"{type(exc).__name__}:{str(exc)[:300]}",
            })

    available=(provider_status().get("capabilities") or {}).get("web_search") or []
    for name,fn in (("tavily",tavily_search),("brave_search",brave_search),("public_research_mesh",public_research_mesh_search)):
        if name not in available: continue
        try:
            out=fn(query,max_results); out["attempts"]=errors+[{"provider":name,"status":"success"}]; return out
        except Exception as e: errors.append({"provider":name,"status":"failed","error":f"{type(e).__name__}:{str(e)[:300]}"})
    return {"provider":None,"results":[],"result_count":0,"status":"no_usable_web_search_provider","attempts":errors}

if __name__=="__main__": print(json.dumps(provider_status(),indent=2,sort_keys=True))
