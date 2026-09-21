from __future__ import annotations

import json
import os
import re
import time
import random
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from companyos.runtime import targeted_public_evidence_research as base

RT = Path.home()/".companyos_runtime"
RESEARCH_DIR = RT/"canonical_research_outputs"
STATE = RT/"openai_web_evidence_fallback_state.json"
RATE_STATE = RT/"openai_web_search_model_rate_state.json"

API_URL = os.getenv("COMPANYOS_OPENAI_RESPONSES_URL","https://api.openai.com/v1/responses").strip()
MODEL = os.getenv("COMPANYOS_RESEARCH_OPENAI_MODEL","gpt-5.6-luna").strip()
MODEL_CANDIDATES = tuple(
    x.strip() for x in os.getenv(
        "COMPANYOS_RESEARCH_OPENAI_MODELS",
        "gpt-5.6-luna,gpt-5.6-terra,gpt-5.6-sol",
    ).split(",") if x.strip()
)
TIMEOUT = max(15, int(os.getenv("COMPANYOS_OPENAI_WEB_SEARCH_TIMEOUT_SECONDS","90")))

ENV_NAMES = (
    "OPENAI_API_KEY",
    "COMPANYOS_OPENAI_API_KEY",
    "OPENAI_KEY",
)

ENV_FILES = (
    Path.home()/"companyos/.env",
    Path.home()/".companyos_runtime/.env",
    Path.home()/".config/companyos/.env",
)

def _env_file_value(path: Path, name: str) -> str | None:
    try:
        text=path.read_text(encoding="utf-8")
    except Exception:
        return None
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        if k.strip()!=name:
            continue
        v=v.strip().strip('"').strip("'")
        return v or None
    return None

def resolve_api_key() -> tuple[str | None, str | None]:
    for name in ENV_NAMES:
        value=os.getenv(name,"").strip()
        if value:
            return value, f"env:{name}"
    for path in ENV_FILES:
        for name in ENV_NAMES:
            value=_env_file_value(path,name)
            if value:
                return value, f"file:{path.name}:{name}"
    return None,None

# COMPANYOS_V69_24_RATE_LIMIT_BACKOFF
def _retry_delay_from_error(exc, detail: str, attempt: int) -> float:
    header=None
    try:
        header=exc.headers.get("Retry-After")
    except Exception:
        pass
    if header:
        try:
            return max(0.5, min(60.0, float(header)))
        except Exception:
            pass

    m=re.search(r"try again in\s+([0-9.]+)\s*(ms|milliseconds?|s|seconds?)", detail, re.I)
    if m:
        value=float(m.group(1))
        unit=m.group(2).lower()
        if unit.startswith("m"):
            value/=1000.0
        return max(0.5, min(60.0, value))

    return min(30.0, 1.5*(2**attempt))

def _request_json(payload: dict[str,Any], api_key: str, max_attempts: int | None = None) -> dict[str,Any]:
    body=json.dumps(payload).encode("utf-8")
    if max_attempts is None:
        max_attempts=max(1,int(os.getenv("COMPANYOS_OPENAI_WEB_SEARCH_MAX_ATTEMPTS","6")))
    else:
        max_attempts=max(1,int(max_attempts))

    last_error=None
    for attempt in range(max_attempts):
        req=urllib.request.Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Authorization":f"Bearer {api_key}",
                "Content-Type":"application/json",
                "Accept":"application/json",
            },
        )
        try:
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                raw=r.read(5_000_000).decode("utf-8","replace")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            detail=""
            try:
                detail=exc.read(4000).decode("utf-8","replace")
            except Exception:
                pass

            last_error=f"openai_http_{exc.code}:{detail[:900]}"
            if exc.code!=429 or attempt>=max_attempts-1:
                raise RuntimeError(last_error) from exc

            delay=_retry_delay_from_error(exc,detail,attempt)
            delay+=random.uniform(0.15,0.65)
            print(
                "OPENAI_429_RETRY "
                f"attempt={attempt+1}/{max_attempts} "
                f"sleep_seconds={delay:.2f}",
                flush=True,
            )
            time.sleep(delay)

    raise RuntimeError(last_error or "openai_request_failed")

# COMPANYOS_V69_25_MODEL_AWARE_FALLBACK
def _parse_reset_seconds(detail: str) -> float | None:
    text=str(detail or "").lower()

    # Milliseconds must be recognized before the compact h/m/s parser,
    # otherwise "2039ms" can be misread as 2039 minutes.
    ms=re.search(r"try again in\s+([0-9.]+)\s*(ms|milliseconds?)\b", text, re.I)
    if ms:
        return float(ms.group(1))/1000.0

    compact=re.search(r"try again in\s+((?:[0-9.]+\s*[dhms]\s*)+)", text, re.I)
    if compact:
        chunk=compact.group(1)
        total=0.0
        for value,unit in re.findall(r"([0-9.]+)\s*([dhms])", chunk, re.I):
            value=float(value)
            unit=unit.lower()
            if unit=="d":
                total += value*86400.0
            elif unit=="h":
                total += value*3600.0
            elif unit=="m":
                total += value*60.0
            elif unit=="s":
                total += value
        if total>0:
            return total

    return None

def _rate_state() -> dict[str,Any]:
    try:
        value=json.loads(RATE_STATE.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except Exception:
        return {}

def _save_rate_state(state: dict[str,Any]) -> None:
    base.atomic(RATE_STATE,state)

def _is_429_error(message: str) -> bool:
    text=str(message or "").lower()
    return "openai_http_429" in text or '"code":"rate_limit_exceeded"' in text or "rate limit" in text

def _mark_model_rate_limited(model: str, message: str) -> dict[str,Any]:
    state=_rate_state()
    models=state.setdefault("models",{})
    reset=_parse_reset_seconds(message)
    cooldown=max(30.0, float(reset if reset is not None else 300.0))
    now=time.time()
    models[model]={
        "rate_limited_at_unix":now,
        "reset_seconds":reset,
        "blocked_until_unix":now+cooldown,
        "last_error":str(message)[:1200],
    }
    state["updated_at_unix"]=now
    _save_rate_state(state)
    return models[model]

def _mark_model_success(model: str) -> None:
    state=_rate_state()
    models=state.setdefault("models",{})
    prior=models.get(model) if isinstance(models.get(model),dict) else {}
    models[model]={
        **prior,
        "last_success_at_unix":time.time(),
        "blocked_until_unix":0.0,
        "last_error":None,
    }
    state["updated_at_unix"]=time.time()
    _save_rate_state(state)

def _model_cooldown_remaining(model: str) -> float:
    state=_rate_state()
    row=(state.get("models") or {}).get(model) or {}
    try:
        return max(0.0,float(row.get("blocked_until_unix") or 0.0)-time.time())
    except Exception:
        return 0.0

def _ordered_models() -> list[str]:
    out=[]
    for model in (MODEL, *MODEL_CANDIDATES):
        if model and model not in out:
            out.append(model)
    return out

def _web_search_once(candidate: dict[str,Any], requirement: str, anchors: list[str], api_key: str) -> tuple[dict[str,Any] | None,list[dict[str,Any]],list[dict[str,Any]]]:
    attempts=[]
    for model in _ordered_models():
        remaining=_model_cooldown_remaining(model)
        if remaining>0:
            attempts.append({
                "model":model,
                "status":"cooldown_skip",
                "cooldown_remaining_seconds":round(remaining,2),
            })
            print(
                f"MODEL_COOLDOWN_SKIP model={model} remaining_seconds={remaining:.1f}",
                flush=True,
            )
            continue

        payload={
            "model":model,
            "tools":[{"type":"web_search","search_context_size":"low"}],
            "input":_prompt(candidate,requirement,anchors),
            "max_output_tokens":800,
        }

        try:
            response=_request_json(payload,api_key,max_attempts=1)
            _mark_model_success(model)
            attempts.append({
                "model":model,
                "status":"success",
                "response_id":response.get("id"),
            })
            return response,attempts,[]
        except Exception as exc:
            message=f"{type(exc).__name__}:{str(exc)[:1400]}"
            if _is_429_error(message):
                cooldown=_mark_model_rate_limited(model,message)
                attempts.append({
                    "model":model,
                    "status":"rate_limited",
                    "reset_seconds":cooldown.get("reset_seconds"),
                    "blocked_until_unix":cooldown.get("blocked_until_unix"),
                    "error":message,
                })
                print(
                    f"MODEL_RATE_LIMITED model={model} reset_seconds={cooldown.get('reset_seconds')}",
                    flush=True,
                )
                continue

            attempts.append({
                "model":model,
                "status":"error",
                "error":message,
            })
            continue

    return None,attempts,[{"error":"all_models_unavailable_or_failed"}]

def _message_text(response: dict[str,Any]) -> str:
    if isinstance(response.get("output_text"),str) and response.get("output_text"):
        return response["output_text"]
    parts=[]
    for item in response.get("output") or []:
        if not isinstance(item,dict) or item.get("type")!="message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content,dict):
                continue
            if content.get("type")=="output_text" and isinstance(content.get("text"),str):
                parts.append(content["text"])
    return "\n".join(parts).strip()

def _annotation_rows(response: dict[str,Any]) -> list[dict[str,Any]]:
    rows=[]
    text=_message_text(response)

    for item in response.get("output") or []:
        if not isinstance(item,dict) or item.get("type")!="message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content,dict):
                continue
            local_text=str(content.get("text") or "")
            for ann in content.get("annotations") or []:
                if not isinstance(ann,dict) or ann.get("type")!="url_citation":
                    continue
                url=str(ann.get("url") or "").strip()
                if not url.startswith(("http://","https://")):
                    continue
                title=str(ann.get("title") or "").strip()
                try:
                    start=int(ann.get("start_index") or 0)
                    end=int(ann.get("end_index") or start)
                except Exception:
                    start=end=0
                before=local_text[max(0,start-700):max(start,end)]
                if not before.strip():
                    before=text[:1800]
                context=re.sub(r"\s+"," ",before).strip()[-1500:]
                rows.append({"url":url,"title":title,"context":context})

    out=[]
    seen=set()
    for row in rows:
        key=(row["url"],row["context"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out

def _domain(url: str) -> str:
    try:
        d=urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""
    return d[4:] if d.startswith("www.") else d

def _prompt(candidate: dict[str,Any], requirement: str, anchors: list[str]) -> str:
    market=str(candidate.get("market") or candidate.get("sector") or "")
    customer=str(candidate.get("target_customer") or "")
    problem=str(candidate.get("problem") or "")
    offer=str(candidate.get("offer") or "")
    business_model=str(candidate.get("business_model") or "")

    if requirement=="pricing":
        focus=(
            "Find attributable public evidence of actual prices, pricing plans, fees, "
            "subscription amounts, contract costs, or closely comparable market pricing."
        )
    else:
        focus=(
            "Find attributable public evidence of buyer demand: real customers, named users, "
            "case studies, adoption, testimonials, purchasing activity, or clear customer use."
        )

    return f'''
You are doing read-only market research for an internal business evaluation.
Use web search. Do not contact anyone and do not perform any transaction.

Market: {market}
Target customer: {customer}
Problem: {problem}
Offer concept: {offer}
Business model: {business_model}
Evidence requirement: {requirement}
Candidate concept anchors: {", ".join(anchors)}

{focus}

Rules:
- Use only observable public web evidence.
- Do not invent URLs, prices, customers, dates, quotes, adoption claims, or numbers.
- Prefer primary/vendor/customer sources and current sources when possible.
- Every material claim must be supported by web citations.
- Focus on evidence that directly matches at least two candidate concept anchors.
- If strong evidence cannot be found, say so instead of filling gaps.
- Return a concise evidence memo only.
'''.strip()

def research_candidate(candidate_name: str, requirements: list[str]) -> dict[str,Any]:
    candidate_path,candidate=base.candidate_payload(candidate_name)
    if not candidate_path or not candidate:
        raise RuntimeError("candidate_not_found")

    anchors=base.candidate_terms(candidate,candidate_name)
    if len(anchors)<2:
        raise RuntimeError("candidate_anchor_set_too_small")

    api_key,key_source=resolve_api_key()
    started=time.time()
    source_rows=[]
    calls=[]
    provider_errors=[]
    selected_models={}

    if not api_key:
        provider_errors.append("openai_api_key_not_found")
    else:
        for requirement in requirements:
            response,attempts,errors=_web_search_once(
                candidate,
                requirement,
                anchors,
                api_key,
            )

            call={
                "requirement":requirement,
                "attempts":attempts,
            }

            if response is None:
                call["status"]="failed"
                call["errors"]=errors
                provider_errors.append(
                    f"{requirement}:all_models_unavailable_or_failed"
                )
                calls.append(call)
                continue

            memo=_message_text(response)
            citations=_annotation_rows(response)
            model=str(response.get("model") or "")
            selected_models[requirement]=model

            call.update({
                "status":response.get("status") or "completed",
                "response_id":response.get("id"),
                "model":model,
                "citation_count":len(citations),
                "memo_chars":len(memo),
            })
            calls.append(call)

            for citation in citations:
                domain=_domain(citation["url"]) or "openai_web_search"
                context=citation.get("context") or memo[:1500]
                source_rows.append({
                    "source":domain,
                    "publisher":domain,
                    "url":citation["url"],
                    "title":citation.get("title") or "",
                    "summary":context,
                    "observed_at":time.time(),
                    "evidence_method":"openai_responses_web_search",
                    "research_model":model,
                })

    dedup=[]
    seen=set()
    for row in source_rows:
        key=(row.get("url"),row.get("summary"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    source_rows=dedup

    provider_error=";".join(provider_errors) if provider_errors else None

    artifact={
        "schema":"companyos.openai_web_evidence_fallback.v69_25",
        "candidate_name":candidate_name,
        "candidate_source":str(candidate_path),
        "candidate_anchors":anchors,
        "requirements_requested":requirements,
        "model_candidates":_ordered_models(),
        "selected_models":selected_models,
        "api_key_available":bool(api_key),
        "api_key_source":key_source,
        "provider_error":provider_error,
        "calls":calls,
        "source_rows":source_rows,
        "source_row_count":len(source_rows),
        "rate_state":_rate_state(),
        "started_at_unix":started,
        "finished_at_unix":time.time(),
        "external_action_performed":False,
        "financial_action_performed":False,
        "deployment_performed":False,
    }

    RESEARCH_DIR.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r"[^a-z0-9]+","_",candidate_name.lower()).strip("_")[:80] or "candidate"
    out=RESEARCH_DIR/f"openai_web_evidence_v69_25_{safe}_{int(started*1000)}.json"
    base.atomic(out,artifact)

    state={
        "schema":"companyos.openai_web_evidence_fallback_state.v69_25",
        "healthy":provider_error is None,
        "candidate_name":candidate_name,
        "requirements_requested":requirements,
        "artifact":str(out),
        "source_row_count":len(source_rows),
        "model_candidates":_ordered_models(),
        "selected_models":selected_models,
        "api_key_available":bool(api_key),
        "api_key_source":key_source,
        "provider_error":provider_error,
        "calls":calls,
        "rate_state":_rate_state(),
        "updated_at":time.time(),
    }
    base.atomic(STATE,state)
    return state

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate",required=True)
    parser.add_argument("--requirements",nargs="+",default=["pricing","buyer_demand"])
    args=parser.parse_args()
    print(json.dumps(research_candidate(args.candidate,args.requirements),indent=2,sort_keys=True))
