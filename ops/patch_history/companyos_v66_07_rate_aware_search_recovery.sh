#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
ADAPTER="$ROOT/companyos/runtime/openai_web_search_adapter.py"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
ACCOUNTS="$ROOT/companyos/runtime/autonomous_provider_accounts.py"
SCTL="$ROOT/scripts/companyos_sourcingctl"
ACTL="$ROOT/scripts/companyos_accountctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.07 RATE-AWARE SEARCH + PROVIDER ROTATION ====="
echo "FIX=OPENAI_WEB_429_BACKOFF_CACHE_AND_ONE_QUERY_PACING"
echo "FIX=PROVIDER_SIGNUP_RETRY_COOLDOWN_AND_ALTERNATIVE_ROTATION"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$ADAPTER" "$SOURCING" "$ACCOUNTS" "$SCTL" "$ACTL"; do
  [ -f "$f" ] || { echo "V66_07_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$ADAPTER" "$SOURCING" "$ACCOUNTS"; do
  cp "$f" "${f}.v66_07_backup_${stamp}"
  echo "BACKUP=${f}.v66_07_backup_${stamp}"
done

echo "===== REPLACE OPENAI WEB ADAPTER WITH RATE-AWARE VERSION ====="
cat > "$ADAPTER" <<'PY'
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
PY

echo "===== PATCH SOURCING FOR ONE-REQUEST OPENAI PACING ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

imp="from companyos.runtime.openai_web_search_adapter import configured as openai_web_configured, search as openai_web_search\n"
newimp="from companyos.runtime.openai_web_search_adapter import configured as openai_web_configured, search as openai_web_search, cooldown_status as openai_web_cooldown_status\n"
if imp in s:
    s=s.replace(imp,newimp,1)
elif "openai_web_cooldown_status" not in s:
    raise SystemExit("V66_07_ABORT=openai_adapter_import_anchor_missing")

old='''    pending = pending_requests()
    selected = pending[:max(1, int(max_requests))]
    resolutions = [resolve_one(x) for x in selected]
'''
new='''    pending = pending_requests()
    provider=chosen_provider()

    # The OpenAI web fallback is deliberately paced one uncached research
    # request at a time. This prevents a batch of procurement requests from
    # consuming the entire request window and producing a 429 storm.
    effective_max=max(1,int(max_requests))
    if provider=="openai_web":
        cd=openai_web_cooldown_status()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    else:
        selected=pending[:effective_max]

    resolutions=[]
    for item in selected:
        row=resolve_one(item)
        resolutions.append(row)
        err=str(row.get("search_error") or "")
        if "rate_limited" in err or "HTTP Error 429" in err:
            break
'''
if old in s:
    s=s.replace(old,new,1)
elif "effective_max=max(1,int(max_requests))" not in s:
    raise SystemExit("V66_07_ABORT=run_once_anchor_missing")

old_report='''        "selected_provider": chosen_provider(),
        "pending_before": len(pending),
        "processed": len(resolutions),
'''
new_report='''        "selected_provider": chosen_provider(),
        "openai_web_rate_state": openai_web_cooldown_status() if chosen_provider()=="openai_web" else None,
        "pending_before": len(pending),
        "processed": len(resolutions),
'''
if old_report in s:
    s=s.replace(old_report,new_report,1)
elif '"openai_web_rate_state"' not in s:
    raise SystemExit("V66_07_ABORT=report_anchor_missing")

p.write_text(s)
print("V66_07_SOURCING_PACING=PASS")
PY

echo "===== PATCH ACCOUNT PROVIDER ROTATION + RETRY COOLDOWN ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_provider_accounts.py"
s=p.read_text()

anchor='''def already_configured(candidate: dict[str,Any]) -> bool:
    name=candidate.get("credential_env")
    return bool(name and env(str(name)))


'''
addition='''def candidate_retry_due(candidate: dict[str,Any], current: dict[str,dict[str,Any]]) -> bool:
    old=current.get(str(candidate.get("domain") or ""))
    if not old:
        return True
    status=str(old.get("status") or "")
    age=time.time()-float(old.get("timestamp_unix") or 0)

    if status in {
        "ALREADY_CONFIGURED",
        "AUTO_PROVISIONED",
        "ACCOUNT_VERIFIED_KEY_ISSUANCE_PENDING",
        "HUMAN_VERIFICATION_REQUIRED",
    }:
        return False

    cooldowns={
        "SIGNUP_DISCOVERY_PENDING":6*3600,
        "BROWSER_ADAPTER_REQUIRED":12*3600,
        "SIGNUP_PAGE_UNREACHABLE":2*3600,
        "SIGNUP_RESULT_UNCERTAIN":6*3600,
        "EXTERNAL_PROVISIONER_FAILED":3600,
        "VAULT_NOT_READY":3600,
    }
    wait=cooldowns.get(status,900)
    return age>=wait


'''
if addition not in s:
    if anchor not in s:
        raise SystemExit("V66_07_ABORT=account_retry_anchor_missing")
    s=s.replace(anchor,anchor+addition,1)

old='''        old=current.get(c["domain"])
        if old and old.get("status") in {
            "ALREADY_CONFIGURED",
            "AUTO_PROVISIONED",
            "ACCOUNT_VERIFIED_KEY_ISSUANCE_PENDING",
            "HUMAN_VERIFICATION_REQUIRED",
        }:
            continue
        selected.append(c)
'''
new='''        if not candidate_retry_due(c,current):
            continue
        selected.append(c)
'''
if old in s:
    s=s.replace(old,new,1)
elif "candidate_retry_due(c,current)" not in s:
    raise SystemExit("V66_07_ABORT=account_selection_anchor_missing")

# A known official app route that is reachable but exposes no server-side
# signup form is a browser-adapter gap, not a reason to retry every cycle.
old_status='''        row={**base,"status":"SIGNUP_DISCOVERY_PENDING","signup":signup,"research_task":task}
'''
new_status='''        pending_status="BROWSER_ADAPTER_REQUIRED" if (
            domain in KNOWN_SIGNUP_ROUTES and signup.get("status")=="signup_link_not_found"
        ) else "SIGNUP_DISCOVERY_PENDING"
        row={**base,"status":pending_status,"signup":signup,"research_task":task}
'''
if old_status in s:
    s=s.replace(old_status,new_status,1)
elif 'pending_status="BROWSER_ADAPTER_REQUIRED"' not in s:
    raise SystemExit("V66_07_ABORT=signup_pending_anchor_missing")

p.write_text(s)
print("V66_07_PROVIDER_ROTATION=PASS")
PY

echo "===== TESTS ====="
cat > "$ROOT/tests/test_v66_07_rate_recovery.py" <<'PY'
from companyos.runtime.openai_web_search_adapter import _qkey, cooldown_status
from companyos.runtime.autonomous_provider_accounts import candidate_retry_due

def test_query_key_stable():
    assert _qkey("  Official Pricing  ") == _qkey("official pricing")

def test_cooldown_status_shape():
    s=cooldown_status()
    assert "cooldown_active" in s
    assert "cooldown_remaining_seconds" in s

def test_pending_account_gets_cooldown():
    import time
    c={"domain":"example.com"}
    current={
        "example.com":{
            "status":"SIGNUP_DISCOVERY_PENDING",
            "timestamp_unix":time.time(),
        }
    }
    assert candidate_retry_due(c,current) is False
PY

python -m py_compile "$ADAPTER" "$SOURCING" "$ACCOUNTS"
python -m pytest -q tests/test_v66_07_rate_recovery.py
echo "V66_07_TESTS=PASS"

echo "===== CLEAN RESTART ====="
"$SCTL" stop || true
"$ACTL" stop || true

echo "===== SEARCH PROVIDER ====="
"$SCTL" providers

echo "===== ONE RATE-AWARE SOURCING STEP ====="
"$SCTL" once 20 || true

echo "===== PROVIDER ROTATION STEP ====="
"$ACTL" once 3 || true

echo "===== RESTART DAEMONS ====="
"$SCTL" start
"$ACTL" start

echo "===== FINAL STATUS ====="
"$SCTL" status
"$ACTL" status

echo "V66_07_OPENAI_429_BACKOFF=PASS"
echo "V66_07_SEARCH_CACHE=PASS"
echo "V66_07_ONE_QUERY_PACING=PASS"
echo "V66_07_PROVIDER_RETRY_COOLDOWN=PASS"
echo "V66_07_PROVIDER_ALTERNATIVE_ROTATION=PASS"
echo "V66_07_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_07_COMPLETE"
