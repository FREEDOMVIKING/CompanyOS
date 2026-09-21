from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from companyos.runtime import targeted_public_evidence_research as base

RT = Path.home()/".companyos_runtime"
RESEARCH_DIR = RT/"canonical_research_outputs"
STATE = RT/"openai_web_evidence_fallback_state.json"

API_URL = os.getenv("COMPANYOS_OPENAI_RESPONSES_URL","https://api.openai.com/v1/responses").strip()
MODEL = os.getenv("COMPANYOS_RESEARCH_OPENAI_MODEL","gpt-5.6-luna").strip()
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

def _request_json(payload: dict[str,Any], api_key: str) -> dict[str,Any]:
    body=json.dumps(payload).encode("utf-8")
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
            detail=exc.read(2000).decode("utf-8","replace")
        except Exception:
            pass
        raise RuntimeError(f"openai_http_{exc.code}:{detail[:600]}") from exc

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
    provider_error=None

    if not api_key:
        provider_error="openai_api_key_not_found"
    else:
        for requirement in requirements:
            payload={
                "model":MODEL,
                "tools":[{"type":"web_search","search_context_size":"medium"}],
                "input":_prompt(candidate,requirement,anchors),
                "max_output_tokens":2200,
            }
            try:
                response=_request_json(payload,api_key)
                memo=_message_text(response)
                citations=_annotation_rows(response)
                calls.append({
                    "requirement":requirement,
                    "response_id":response.get("id"),
                    "model":response.get("model") or MODEL,
                    "citation_count":len(citations),
                    "memo_chars":len(memo),
                    "status":response.get("status"),
                })

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
                    })
            except Exception as exc:
                provider_error=f"{type(exc).__name__}:{str(exc)[:700]}"
                calls.append({"requirement":requirement,"status":"error","error":provider_error})
                break

    dedup=[]
    seen=set()
    for row in source_rows:
        key=(row.get("url"),row.get("summary"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    source_rows=dedup

    artifact={
        "schema":"companyos.openai_web_evidence_fallback.v69_23",
        "candidate_name":candidate_name,
        "candidate_source":str(candidate_path),
        "candidate_anchors":anchors,
        "requirements_requested":requirements,
        "model":MODEL,
        "api_key_available":bool(api_key),
        "api_key_source":key_source,
        "provider_error":provider_error,
        "calls":calls,
        "source_rows":source_rows,
        "source_row_count":len(source_rows),
        "started_at_unix":started,
        "finished_at_unix":time.time(),
        "external_action_performed":False,
        "financial_action_performed":False,
        "deployment_performed":False,
    }

    RESEARCH_DIR.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r"[^a-z0-9]+","_",candidate_name.lower()).strip("_")[:80] or "candidate"
    out=RESEARCH_DIR/f"openai_web_evidence_v69_23_{safe}_{int(started*1000)}.json"
    base.atomic(out,artifact)

    state={
        "schema":"companyos.openai_web_evidence_fallback_state.v69_23",
        "healthy":provider_error is None,
        "candidate_name":candidate_name,
        "requirements_requested":requirements,
        "artifact":str(out),
        "source_row_count":len(source_rows),
        "api_key_available":bool(api_key),
        "api_key_source":key_source,
        "provider_error":provider_error,
        "calls":calls,
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
