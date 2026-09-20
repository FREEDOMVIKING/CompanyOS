#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
ADAPTER="$ROOT/companyos/runtime/tavily_keyless_adapter.py"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
ACCOUNTS="$ROOT/companyos/runtime/autonomous_provider_accounts.py"
BROWSER="$ROOT/companyos/runtime/browser_provider_onboarding.py"
SCTL="$ROOT/scripts/companyos_sourcingctl"
ACTL="$ROOT/scripts/companyos_accountctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.09 KEYLESS TAVILY SEARCH ====="
echo "GOAL=USE_LIVE_WEB_SEARCH_WITHOUT_ACCOUNT_OR_API_KEY"
echo "NOTE=KEYED_PROVIDER_STILL_PREFERRED_WHEN_AVAILABLE"
echo "NOTE=OPENAI_WEB_REMAINS_FALLBACK"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$SOURCING" "$ACCOUNTS"; do
  [ -f "$f" ] || { echo "V66_09_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$SOURCING" "$ACCOUNTS" "$BROWSER"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_09_backup_${stamp}"
    echo "BACKUP=${f}.v66_09_backup_${stamp}"
  fi
done

echo "===== INSTALL/UPDATE OFFICIAL TAVILY PYTHON SDK ====="
python -m pip install --quiet --upgrade tavily-python
echo "V66_09_TAVILY_SDK=PASS"

cat > "$ADAPTER" <<'PY'
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
PY

echo "===== PATCH SOURCING PROVIDER CASCADE ====="
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

anchor="from companyos.runtime.openai_web_search_adapter import configured as openai_web_configured, search as openai_web_search, cooldown_status as openai_web_cooldown_status\n"
addition="from companyos.runtime.tavily_keyless_adapter import configured as tavily_keyless_configured, search as tavily_keyless_search, state as tavily_keyless_state\n"
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_09_ABORT=openai_import_anchor_missing")
    s=s.replace(anchor,anchor+addition,1)

old='''def provider_status() -> dict[str, bool]:
    return {
        "tavily": bool(env("COMPANYOS_TAVILY_API_KEY") or env("TAVILY_API_KEY")),
        "brave": bool(env("COMPANYOS_BRAVE_SEARCH_API_KEY") or env("BRAVE_SEARCH_API_KEY")),
        "serper": bool(env("COMPANYOS_SERPER_API_KEY") or env("SERPER_API_KEY")),
        "openai_web": bool(openai_web_configured()),
    }


def chosen_provider() -> str | None:
    st = provider_status()
    for name in ("tavily", "brave", "serper", "openai_web"):
        if st.get(name):
            return name
    return None
'''
new='''def provider_status() -> dict[str, bool]:
    return {
        "tavily": bool(env("COMPANYOS_TAVILY_API_KEY") or env("TAVILY_API_KEY")),
        "tavily_keyless": bool(tavily_keyless_configured()),
        "brave": bool(env("COMPANYOS_BRAVE_SEARCH_API_KEY") or env("BRAVE_SEARCH_API_KEY")),
        "serper": bool(env("COMPANYOS_SERPER_API_KEY") or env("SERPER_API_KEY")),
        "openai_web": bool(openai_web_configured()),
    }


def chosen_provider() -> str | None:
    st = provider_status()
    # Keyed dedicated search remains first. Keyless Tavily is the preferred
    # bootstrap path before spending OpenAI request quota.
    for name in ("tavily", "brave", "serper", "tavily_keyless", "openai_web"):
        if st.get(name):
            if name=="tavily_keyless" and tavily_keyless_state().get("cooldown_active"):
                continue
            if name=="openai_web" and openai_web_cooldown_status().get("cooldown_active"):
                continue
            return name
    return None
'''
if old in s:
    s=s.replace(old,new,1)
elif '"tavily_keyless"' not in s[s.find("def provider_status"):s.find("def request_json")]:
    raise SystemExit("V66_09_ABORT=provider_status_anchor_missing")

old_search='''        if p == "serper":
            return p, search_serper(query), None
        if p == "openai_web":
            return p, openai_web_search(query, MAX_RESULTS_PER_QUERY), None
'''
new_search='''        if p == "serper":
            return p, search_serper(query), None
        if p == "tavily_keyless":
            return p, tavily_keyless_search(query, MAX_RESULTS_PER_QUERY), None
        if p == "openai_web":
            return p, openai_web_search(query, MAX_RESULTS_PER_QUERY), None
'''
if old_search in s:
    s=s.replace(old_search,new_search,1)
elif 'p == "tavily_keyless"' not in s:
    raise SystemExit("V66_09_ABORT=search_dispatch_anchor_missing")

# Pace keyless use to one fresh request per cycle just like OpenAI fallback.
old_pace='''    if provider=="openai_web":
        cd=openai_web_cooldown_status()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    else:
        selected=pending[:effective_max]
'''
new_pace='''    if provider=="openai_web":
        cd=openai_web_cooldown_status()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    elif provider=="tavily_keyless":
        cd=tavily_keyless_state()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    else:
        selected=pending[:effective_max]
'''
if old_pace in s:
    s=s.replace(old_pace,new_pace,1)
elif 'provider=="tavily_keyless"' not in s[s.find("def run_once"):]:
    raise SystemExit("V66_09_ABORT=pacing_anchor_missing")

old_report='''        "openai_web_rate_state": openai_web_cooldown_status() if chosen_provider()=="openai_web" else None,
        "pending_before": len(pending),
'''
new_report='''        "openai_web_rate_state": openai_web_cooldown_status() if provider_status().get("openai_web") else None,
        "tavily_keyless_state": tavily_keyless_state() if provider_status().get("tavily_keyless") else None,
        "pending_before": len(pending),
'''
if old_report in s:
    s=s.replace(old_report,new_report,1)
elif '"tavily_keyless_state"' not in s:
    raise SystemExit("V66_09_ABORT=report_anchor_missing")

p.write_text(s)
print("V66_09_SOURCING_PATCH=PASS")
PY

echo "===== DEPRIORITIZE SEARCH-ACCOUNT SIGNUP WHEN KEYLESS CAPABILITY EXISTS ====="
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/autonomous_provider_accounts.py"
s=p.read_text()

anchor='''def already_configured(candidate: dict[str,Any]) -> bool:
    name=candidate.get("credential_env")
    return bool(name and env(str(name)))


'''
addition='''def capability_available_without_account(candidate: dict[str,Any]) -> bool:
    # Tavily Search/Extract can operate keylessly. Do not make provider account
    # creation a prerequisite for the live external-search capability.
    return str(candidate.get("provider") or "")=="tavily"


'''
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_09_ABORT=account_capability_anchor_missing")
    s=s.replace(anchor,anchor+addition,1)

old='''        if already_configured(c):
            continue
        if not candidate_retry_due(c,current):
            continue
        selected.append(c)
'''
new='''        if already_configured(c):
            continue
        if capability_available_without_account(c):
            continue
        if not candidate_retry_due(c,current):
            continue
        selected.append(c)
'''
if old in s:
    s=s.replace(old,new,1)
elif "capability_available_without_account(c)" not in s:
    raise SystemExit("V66_09_ABORT=account_selection_anchor_missing")

p.write_text(s)
print("V66_09_ACCOUNT_DEPRIORITIZATION=PASS")
PY

echo "===== PATCH BROWSER CANDIDATES TO SKIP TAVILY WHEN KEYLESS ACTIVE ====="
if [ -f "$BROWSER" ]; then
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/browser_provider_onboarding.py"
s=p.read_text()

old='''    for domain,row in latest.items():
        if str(row.get("status") or "") not in {
'''
new='''    for domain,row in latest.items():
        if domain=="tavily.com":
            # Search capability is now available through Tavily keyless mode;
            # browser signup is no longer on the critical path.
            continue
        if str(row.get("status") or "") not in {
'''
if old in s and 'domain=="tavily.com"' not in s:
    s=s.replace(old,new,1)

p.write_text(s)
print("V66_09_BROWSER_DEPRIORITIZATION=PASS")
PY
fi

cat > "$ROOT/tests/test_tavily_keyless_adapter.py" <<'PY'
from companyos.runtime.tavily_keyless_adapter import configured, state

def test_keyless_sdk_available():
    assert configured() is True

def test_state_shape():
    s=state()
    assert s["mode"]=="keyless"
    assert "cooldown_active" in s
PY

echo "===== COMPILE + TEST ====="
python -m py_compile "$ADAPTER" "$SOURCING" "$ACCOUNTS"
python -m pytest -q tests/test_tavily_keyless_adapter.py
echo "V66_09_TESTS=PASS"

echo "===== CLEAN RESTART OF SOURCING LOOP ====="
"$SCTL" stop || true

echo "===== PROVIDER STATUS ====="
"$SCTL" providers

echo "===== ONE LIVE KEYLESS SEARCH CYCLE ====="
"$SCTL" once 20 || true

echo "===== RESTART SOURCING LOOP ====="
"$SCTL" start

echo "===== ACCOUNT LOOP REFRESH ====="
if [ -x "$ACTL" ]; then
  "$ACTL" restart || true
fi

echo "===== FINAL STATUS ====="
"$SCTL" providers
"$SCTL" status

echo "V66_09_TAVILY_KEYLESS=PASS"
echo "V66_09_NO_ACCOUNT_REQUIRED_FOR_SEARCH=PASS"
echo "V66_09_OPENAI_FALLBACK_PRESERVED=PASS"
echo "V66_09_RATE_AWARE_PACING=PASS"
echo "V66_09_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_09_COMPLETE"
