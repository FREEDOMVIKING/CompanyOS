from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"/"procurement"
STATE=RT/"tavily_keyless_state.json"
CACHE=RT/"tavily_keyless_cache.json"
RT.mkdir(parents=True,exist_ok=True)


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save(path: Path, data: Any) -> None:
    import os, tempfile
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


def configured() -> bool:
    try:
        from tavily import TavilyClient
        TavilyClient()
        return True
    except Exception:
        return False


def state() -> dict[str,Any]:
    st=_load(STATE,{
        "mode":"keyless",
        "available":configured(),
        "cooldown_until_unix":0.0,
        "last_error":None,
        "last_success_unix":None,
    })
    st["available"]=configured()
    st["cooldown_active"]=time.time() < float(st.get("cooldown_until_unix") or 0)
    st["cooldown_remaining_seconds"]=max(
        0,
        int(float(st.get("cooldown_until_unix") or 0)-time.time())
    )
    return st


def _cache_key(query: str) -> str:
    import hashlib
    norm=" ".join(str(query).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()


def cached(query: str, max_age_seconds: int=86400) -> list[dict[str,Any]]|None:
    data=_load(CACHE,{"entries":{}})
    row=(data.get("entries") or {}).get(_cache_key(query))
    if not row:
        return None
    if time.time()-float(row.get("timestamp_unix") or 0) > max_age_seconds:
        return None
    r=row.get("results")
    return r if isinstance(r,list) else None


def _cache(query: str, results: list[dict[str,Any]]) -> None:
    data=_load(CACHE,{"entries":{}})
    entries=data.setdefault("entries",{})
    entries[_cache_key(query)]={
        "timestamp_unix":time.time(),
        "results":results,
    }
    if len(entries)>500:
        rows=sorted(
            entries.items(),
            key=lambda kv:float((kv[1] or {}).get("timestamp_unix") or 0),
            reverse=True,
        )[:500]
        data["entries"]=dict(rows)
    _save(CACHE,data)


def _set_success():
    _save(STATE,{
        "mode":"keyless",
        "available":True,
        "cooldown_until_unix":0.0,
        "last_error":None,
        "last_success_unix":time.time(),
    })


def _set_limit(exc: Exception):
    retry=getattr(exc,"retry_after_seconds",None)
    try:
        retry=int(retry) if retry is not None else 3600
    except Exception:
        retry=3600
    retry=max(60,min(retry,24*3600))
    _save(STATE,{
        "mode":"keyless",
        "available":True,
        "cooldown_until_unix":time.time()+retry,
        "last_error":f"{type(exc).__name__}:{exc}",
        "last_success_unix":_load(STATE,{}).get("last_success_unix"),
    })


def search(query: str, max_results: int=5) -> list[dict[str,Any]]:
    hit=cached(query)
    if hit is not None:
        return hit[:max(1,int(max_results))]

    st=state()
    if st["cooldown_active"]:
        raise RuntimeError(
            f"tavily_keyless_rate_limited:cooldown_remaining_seconds={st['cooldown_remaining_seconds']}"
        )

    try:
        from tavily import TavilyClient, TavilyKeylessLimitError
    except Exception as exc:
        raise RuntimeError(f"tavily_sdk_unavailable:{exc}") from exc

    try:
        client=TavilyClient()
        data=client.search(
            query,
            search_depth="basic",
            max_results=max(1,min(int(max_results),5)),
            include_answer=False,
            include_raw_content=False,
        )
    except TavilyKeylessLimitError as exc:
        _set_limit(exc)
        raise RuntimeError(
            f"tavily_keyless_rate_limited:retry_after_seconds={getattr(exc,'retry_after_seconds',None)}"
        ) from exc

    if not isinstance(data,dict):
        try:
            data=dict(data)
        except Exception:
            data={}

    results=[]
    for x in data.get("results") or []:
        if not isinstance(x,dict):
            continue
        url=x.get("url")
        if not url:
            continue
        results.append({
            "title":x.get("title") or url,
            "url":url,
            "snippet":x.get("content"),
            "score":x.get("score"),
            "provider":"tavily_keyless",
        })

    if results:
        _cache(query,results)
        _set_success()
    return results
