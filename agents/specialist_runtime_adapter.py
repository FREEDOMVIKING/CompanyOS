#!/usr/bin/env python3
import json,os,sys,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_runtime_config.json"
WORK=MEM/"governed_internal_work_results.json"
OUT=MEM/"specialist_runtime_results.json"
STATE=MEM/"specialist_runtime_state.json"
REPORT=MEM/"specialist_runtime_report.json"
HEALTH=MEM/"specialist_runtime_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def call_model(cfg,item):
    import urllib.error

    system=(
        "You are a specialist worker inside CompanyOS. Perform internal, non-destructive reasoning only. "
        "Do not claim to have contacted people, spent money, deployed, published, modified external systems, "
        "or performed actions you cannot verify. Return ONLY valid JSON with keys: summary, findings, "
        "recommendations, risks, next_internal_actions, confidence. confidence must be 0 to 1."
    )

    prompt=json.dumps({
        "action_type":item.get("action_type"),
        "instruction":item.get("instruction"),
        "opportunity_id":item.get("opportunity_id"),
        "execution_boundary":"internal_non_destructive_only"
    })

    body_template={
        "temperature":0.2,
        "messages":[
            {"role":"system","content":system},
            {"role":"user","content":prompt}
        ],
        "response_format":{"type":"json_object"}
    }

    timeout=int(cfg.get("timeout_seconds",120))

    def request_provider(base_url, model, api_key=None):
        body=dict(body_template)
        body["model"]=model

        headers={"Content-Type":"application/json"}
        if api_key:
            headers["Authorization"]=f"Bearer {api_key}"

        req=urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers
        )

        with urllib.request.urlopen(req,timeout=timeout) as r:
            data=json.loads(r.read().decode())

        text=data["choices"][0]["message"]["content"]

        # Try strict JSON first.
        try:
            return json.loads(text)
        except Exception:
            pass

        # Some OpenAI-compatible local models wrap JSON in markdown fences.
        cleaned=text.strip()

        if cleaned.startswith("```"):
            cleaned=cleaned.strip("`").strip()
            if cleaned.lower().startswith("json"):
                cleaned=cleaned[4:].strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Final safe normalization for local-model plain-text responses.
        return {
            "summary": cleaned[:2000] or "Local model returned an empty response.",
            "findings": [],
            "recommendations": [],
            "risks": [],
            "next_internal_actions": [],
            "confidence": 0.5
        }

    # ---------- PRIMARY: OPENAI ----------
    key_env=cfg.get("api_key_env","OPENAI_API_KEY")
    primary_key=os.getenv(key_env,"").strip()
    primary_url=cfg.get("base_url","https://api.openai.com/v1").rstrip("/")
    primary_model=cfg.get("model","gpt-4.1-mini")

    primary_error=None

    if primary_key:
        try:
            result=request_provider(
                primary_url,
                primary_model,
                primary_key
            )
            result["_provider_used"]="openai_primary"
            return result,None

        except urllib.error.HTTPError as e:
            primary_error=f"http_{e.code}"

            fallback_codes=cfg.get(
                "fallback_on_http_codes",
                [408,429,500,502,503,504]
            )

            if e.code not in fallback_codes:
                try:
                    detail=e.read().decode()[:1000]
                except Exception:
                    detail=""
                return None,f"{primary_error}: {detail}"

        except Exception as e:
            primary_error=f"{type(e).__name__}: {e}"

    else:
        primary_error="missing_primary_api_key"

    # ---------- FALLBACK: LOCAL LLAMA.CPP ----------
    if cfg.get("fallback_enabled",False):
        fallback_url=cfg.get(
            "fallback_base_url",
            "http://127.0.0.1:8080/v1"
        ).rstrip("/")

        fallback_model=cfg.get("fallback_model","local")

        try:
            result=request_provider(
                fallback_url,
                fallback_model,
                None
            )

            result["_provider_used"]="local_llama_fallback"
            result["_primary_failure"]=primary_error

            return result,None

        except Exception as e:
            return None,(
                f"primary_failed={primary_error}; "
                f"local_fallback_failed={type(e).__name__}: {e}"
            )

    return None,primary_error or "provider_unavailable"

def run():
    cfg=load(CFG,{})
    rows=load(WORK,{}).get("results",[])
    previous=load(OUT,{"results":[]}).get("results",[])
    done={x.get("work_id") for x in previous if x.get("status")=="completed"}
    maximum=int(cfg.get("maximum_items_per_cycle",5));completed=[];pending=[]

    for item in rows:
        if len(completed)>=maximum:break
        if item.get("status")!="prepared_for_specialist_runtime" or item.get("work_id") in done:continue
        actual,error=call_model(cfg,item)
        if error:
            pending.append({"work_id":item.get("work_id"),"status":"pending","reason":error})
            continue
        result={
          "work_id":item.get("work_id"),"plan_id":item.get("plan_id"),
          "decision_id":item.get("decision_id"),"opportunity_id":item.get("opportunity_id"),
          "action_type":item.get("action_type"),"status":"completed",
          "actual_result":actual,"completed_at":now(),
          "execution_boundary":"internal_non_destructive_only"
        }
        previous.append(result);completed.append(result)

    save(OUT,{"generated_at":now(),"result_count":len(previous),"results":previous})
    report={"generated_at":now(),"completed_count":len(completed),"pending_count":len(pending),
      "completed":completed,"pending":pending,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"completed_count":len(completed),"pending_count":len(pending)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"provider":cfg.get("provider"),
      "api_key_available":bool(os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip())})
    return {"success":True,"status":"specialist_runtime_cycle_complete","report":report}

def status():
    cfg=load(CFG,{})
    return {"success":True,"status":"specialist_runtime_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"config":{
        "provider":cfg.get("provider"),"model":cfg.get("model"),"base_url":cfg.get("base_url"),
        "api_key_env":cfg.get("api_key_env")}}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
