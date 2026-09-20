from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"/"procurement"
API_URL="https://api.openai.com/v1/responses"
CACHE=RT/"openai_web_cache.json"
RATE=RT/"openai_web_rate_state.json"
RT.mkdir(parents=True,exist_ok=True)


def _dotenv() -> dict[str,str]:
    p=ROOT/".env"
    out={}
    if not p.exists():
        return out
    for line in p.read_text(errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k,v=s.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def api_key() -> str|None:
    return os.environ.get("OPENAI_API_KEY") or _dotenv().get("OPENAI_API_KEY")


def configured() -> bool:
    return bool(api_key())


def _output_text(data: dict[str,Any]) -> str:
    pieces=[]
    for item in data.get("output") or []:
        if not isinstance(item,dict) or item.get("type")!="message":
            continue
        for c in item.get("content") or []:
            if isinstance(c,dict) and c.get("type")=="output_text":
                t=c.get("text")
                if t:
                    pieces.append(str(t))
    return "\n".join(pieces).strip()


def _sources(data: dict[str,Any]) -> list[dict[str,Any]]:
    out=[]
    seen=set()
    for item in data.get("output") or []:
        if not isinstance(item,dict) or item.get("type")!="web_search_call":
            continue
        action=item.get("action") or {}
        for s in action.get("sources") or []:
            if not isinstance(s,dict):
                continue
            url=s.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({
                "title":s.get("title") or s.get("name") or url,
                "url":url,
                "provider":"openai_web",
                "score":None,
            })
    return out


def _qkey(query: str) -> str:
    norm=" ".join(str(query).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()


def cooldown_status() -> dict[str,Any]:
    st=_load(RATE,{
        "consecutive_429":0,
        "next_allowed_unix":0.0,
        "last_error":None,
    })
    now=time.time()
    next_allowed=float(st.get("next_allowed_unix") or 0.0)
    return {
        **st,
        "cooldown_active":now < next_allowed,
        "cooldown_remaining_seconds":max(0,int(next_allowed-now)),
    }


def _set_success() -> None:
    _save(RATE,{
        "consecutive_429":0,
        "next_allowed_unix":time.time()+30,
        "last_error":None,
        "updated_at_unix":time.time(),
    })


def _set_429(retry_after: int|None, error: str) -> int:
    st=_load(RATE,{})
    count=int(st.get("consecutive_429") or 0)+1
    # Conservative backoff. If the service supplies Retry-After, honor it.
    calculated=min(3600,max(60,60*(2**min(count-1,5))))
    wait=max(calculated,int(retry_after or 0))
    _save(RATE,{
        "consecutive_429":count,
        "next_allowed_unix":time.time()+wait,
        "last_error":error,
        "updated_at_unix":time.time(),
    })
    return wait


def cached(query: str, max_age_seconds: int=7*86400) -> list[dict[str,Any]]|None:
    c=_load(CACHE,{"entries":{}})
    row=(c.get("entries") or {}).get(_qkey(query))
    if not row:
        return None
    if time.time()-float(row.get("timestamp_unix") or 0) > max_age_seconds:
        return None
    results=row.get("results")
    return results if isinstance(results,list) else None


def _cache(query: str, results: list[dict[str,Any]]) -> None:
    c=_load(CACHE,{"entries":{}})
    entries=c.setdefault("entries",{})
    entries[_qkey(query)]={
        "timestamp_unix":time.time(),
        "query_hash":_qkey(query),
        "results":results,
    }
    # Bound cache size.
    if len(entries)>500:
        rows=sorted(entries.items(),key=lambda kv:float((kv[1] or {}).get("timestamp_unix") or 0),reverse=True)[:500]
        c["entries"]=dict(rows)
    _save(CACHE,c)


def search(query: str, max_results: int=5) -> list[dict[str,Any]]:
    hit=cached(query)
    if hit is not None:
        return hit[:max(1,int(max_results))]

    st=cooldown_status()
    if st["cooldown_active"]:
        raise RuntimeError(
            f"openai_web_rate_limited:cooldown_remaining_seconds={st['cooldown_remaining_seconds']}"
        )

    key=api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY_missing")

    model=(
        os.environ.get("COMPANYOS_OPENAI_WEB_MODEL")
        or _dotenv().get("COMPANYOS_OPENAI_WEB_MODEL")
        or "gpt-5.6-luna"
    )

    payload={
        "model":model,
        "tools":[{"type":"web_search","search_context_size":"low"}],
        "include":["web_search_call.action.sources"],
        "input":(
            "Search the public web for this procurement research question. "
            "Prioritize official vendor/provider pages and current pricing. "
            "Only state prices supported by retrieved sources. "
            "Do not invent payment addresses or credentials.\n\nQUERY: "+query
        ),
    }

    req=urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization":"Bearer "+key,
            "Content-Type":"application/json",
            "User-Agent":"CompanyOS/66.07",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            data=json.loads(r.read().decode(errors="ignore"))
    except urllib.error.HTTPError as exc:
        if exc.code==429:
            retry=None
            try:
                raw=exc.headers.get("Retry-After")
                retry=int(float(raw)) if raw else None
            except Exception:
                retry=None
            wait=_set_429(retry,f"HTTP {exc.code}")
            raise RuntimeError(f"openai_web_rate_limited:retry_after_seconds={wait}") from exc
        raise

    text=_output_text(data)
    sources=_sources(data)[:max(1,int(max_results))]
    results=[]
    for i,s in enumerate(sources):
        results.append({**s,"snippet":text if i==0 else None})

    _cache(query,results)
    _set_success()
    return results
