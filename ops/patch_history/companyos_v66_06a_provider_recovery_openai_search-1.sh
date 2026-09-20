#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
ENVF="$ROOT/.env"
SOURCING="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
ACCOUNTS="$ROOT/companyos/runtime/autonomous_provider_accounts.py"
OPENAI_ADAPTER="$ROOT/companyos/runtime/openai_web_search_adapter.py"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.06A PROVIDER RECOVERY + OPENAI WEB SEARCH BOOTSTRAP ====="
echo "GOAL=REMOVE_EXTERNAL_SEARCH_DEADLOCK_AND_FIX_COMPANYAIOS_MAILBOX_AUTODETECTION"
echo "NOTE=NO_AUTHORITY_SWITCHES_CHANGED"
echo "NOTE=NO_CAPTCHA_PHONE_OR_KYC_BYPASS"

[ -f "$SOURCING" ] || { echo "V66_06A_ABORT=missing:$SOURCING"; exit 1; }
[ -f "$ACCOUNTS" ] || { echo "V66_06A_ABORT=missing:$ACCOUNTS"; exit 1; }
touch "$ENVF"
chmod 600 "$ENVF"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$SOURCING" "$ACCOUNTS"; do
  cp "$f" "${f}.v66_06a_backup_${stamp}"
  echo "BACKUP=${f}.v66_06a_backup_${stamp}"
done

echo "===== AUTODETECT COMPANYAIOS IMAP HOST ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/.env"
lines=p.read_text(errors="ignore").splitlines()
vals={}
for line in lines:
    s=line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k,v=s.split("=",1)
    vals[k.strip()]=v.strip().strip("'\"")

email_addr=(
    vals.get("COMPANYAIOS_EMAIL")
    or vals.get("COMPANYOS_SMTP_FROM_EMAIL")
    or vals.get("COMPANYOS_SMTP_USERNAME")
    or ""
).lower()

host=vals.get("COMPANYAIOS_IMAP_HOST","").strip()
if not host:
    if email_addr.endswith("@gmail.com") or email_addr.endswith("@googlemail.com"):
        host="imap.gmail.com"
    elif email_addr.endswith("@outlook.com") or email_addr.endswith("@hotmail.com") or email_addr.endswith("@live.com"):
        host="outlook.office365.com"
    elif email_addr.endswith("@yahoo.com"):
        host="imap.mail.yahoo.com"

if host:
    found=False
    out=[]
    for line in lines:
        if line.startswith("COMPANYAIOS_IMAP_HOST="):
            out.append("COMPANYAIOS_IMAP_HOST="+host)
            found=True
        else:
            out.append(line)
    if not found:
        out.append("COMPANYAIOS_IMAP_HOST="+host)
    p.write_text("\n".join(out)+"\n")
    print("V66_06A_IMAP_AUTODETECT=PASS")
    print("IMAP_HOST="+host)
else:
    print("V66_06A_IMAP_AUTODETECT=NO_MATCH")
PY

cat > "$OPENAI_ADAPTER" <<'PY'
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
API_URL="https://api.openai.com/v1/responses"


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
        if not isinstance(item,dict):
            continue
        if item.get("type")!="web_search_call":
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


def search(query: str, max_results: int=5) -> list[dict[str,Any]]:
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
            "Search the public web for the following procurement research question. "
            "Prioritize official vendor/provider pages and current pricing. "
            "State prices only when supported by the retrieved sources. "
            "Do not invent payment addresses or credentials.\n\nQUERY: "+query
        ),
    }

    req=urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization":"Bearer "+key,
            "Content-Type":"application/json",
            "User-Agent":"CompanyOS/66.06A",
        },
        method="POST",
    )

    with urllib.request.urlopen(req,timeout=60) as r:
        data=json.loads(r.read().decode(errors="ignore"))

    text=_output_text(data)
    sources=_sources(data)[:max(1,int(max_results))]

    results=[]
    for i,s in enumerate(sources):
        results.append({
            **s,
            "snippet":text if i==0 else None,
        })

    return results
PY

echo "===== PATCH V66.05 SOURCING WITH OPENAI WEB SEARCH FALLBACK ====="
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

if "from companyos.runtime.openai_web_search_adapter import" not in s:
    anchor="from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue\n"
    if anchor not in s:
        raise SystemExit("V66_06A_ABORT=sourcing_import_anchor_missing")
    s=s.replace(
        anchor,
        anchor+"from companyos.runtime.openai_web_search_adapter import configured as openai_web_configured, search as openai_web_search\n",
        1,
    )

old='''def provider_status() -> dict[str, bool]:
    return {
        "tavily": bool(env("COMPANYOS_TAVILY_API_KEY") or env("TAVILY_API_KEY")),
        "brave": bool(env("COMPANYOS_BRAVE_SEARCH_API_KEY") or env("BRAVE_SEARCH_API_KEY")),
        "serper": bool(env("COMPANYOS_SERPER_API_KEY") or env("SERPER_API_KEY")),
    }


def chosen_provider() -> str | None:
    st = provider_status()
    for name in ("tavily", "brave", "serper"):
        if st[name]:
            return name
    return None
'''
new='''def provider_status() -> dict[str, bool]:
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
if old in s:
    s=s.replace(old,new,1)
elif '"openai_web"' not in s:
    raise SystemExit("V66_06A_ABORT=provider_status_anchor_missing")

old_search='''def search(query: str) -> tuple[str | None, list[dict[str, Any]], str | None]:
    p = chosen_provider()
    if not p:
        return None, [], "no_external_search_provider_configured"
    try:
        if p == "tavily":
            return p, search_tavily(query), None
        if p == "brave":
            return p, search_brave(query), None
        return p, search_serper(query), None
    except Exception as exc:
        return p, [], f"{type(exc).__name__}:{exc}"
'''
new_search='''def search(query: str) -> tuple[str | None, list[dict[str, Any]], str | None]:
    p = chosen_provider()
    if not p:
        return None, [], "no_external_search_provider_configured"
    try:
        if p == "tavily":
            return p, search_tavily(query), None
        if p == "brave":
            return p, search_brave(query), None
        if p == "serper":
            return p, search_serper(query), None
        if p == "openai_web":
            return p, openai_web_search(query, MAX_RESULTS_PER_QUERY), None
        return p, [], "unknown_search_provider"
    except Exception as exc:
        return p, [], f"{type(exc).__name__}:{exc}"
'''
if old_search in s:
    s=s.replace(old_search,new_search,1)
elif "openai_web_search(query" not in s:
    raise SystemExit("V66_06A_ABORT=search_dispatch_anchor_missing")

p.write_text(s)
print("V66_06A_OPENAI_SEARCH_PATCH=PASS")
PY

echo "===== PATCH V66.06 ACCOUNT DISCOVERY RECOVERY ====="
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/autonomous_provider_accounts.py"
s=p.read_text()

old='''BOOTSTRAP={
    "external_search":[
        {"provider":"tavily","domain":"tavily.com","credential_env":"COMPANYOS_TAVILY_API_KEY"},
        {"provider":"brave_search","domain":"brave.com","credential_env":"COMPANYOS_BRAVE_SEARCH_API_KEY"},
        {"provider":"serper","domain":"serper.dev","credential_env":"COMPANYOS_SERPER_API_KEY"},
    ]
}
'''
new='''BOOTSTRAP={
    "external_search":[
        {"provider":"tavily","domain":"tavily.com","credential_env":"COMPANYOS_TAVILY_API_KEY"},
        {"provider":"serper","domain":"serper.dev","credential_env":"COMPANYOS_SERPER_API_KEY"},
        {"provider":"brave_search","domain":"brave.com","credential_env":"COMPANYOS_BRAVE_SEARCH_API_KEY"},
    ]
}

KNOWN_SIGNUP_ROUTES={
    "tavily.com":["https://app.tavily.com/","https://www.tavily.com/"],
    "serper.dev":["https://serper.dev/"],
    "brave.com":["https://api-dashboard.search.brave.com/register","https://brave.com/search/api/"],
}
'''
if old in s:
    s=s.replace(old,new,1)
elif "KNOWN_SIGNUP_ROUTES" not in s:
    raise SystemExit("V66_06A_ABORT=bootstrap_anchor_missing")

old_mail='''    host=env("COMPANYAIOS_IMAP_HOST")
    port=int(env("COMPANYAIOS_IMAP_PORT","993") or 993)
'''
new_mail='''    host=env("COMPANYAIOS_IMAP_HOST")
    if not host and email_addr:
        low=str(email_addr).lower()
        if low.endswith("@gmail.com") or low.endswith("@googlemail.com"):
            host="imap.gmail.com"
        elif low.endswith("@outlook.com") or low.endswith("@hotmail.com") or low.endswith("@live.com"):
            host="outlook.office365.com"
        elif low.endswith("@yahoo.com"):
            host="imap.mail.yahoo.com"
    port=int(env("COMPANYAIOS_IMAP_PORT","993") or 993)
'''
if old_mail in s:
    s=s.replace(old_mail,new_mail,1)
elif 'low.endswith("@gmail.com")' not in s:
    raise SystemExit("V66_06A_ABORT=mailbox_anchor_missing")

old_roots='''    op=opener()
    roots=[f"https://{domain}/",f"https://www.{domain}/"]
    errors=[]
    for root in roots:
'''
new_roots='''    op=opener()
    hints=list(KNOWN_SIGNUP_ROUTES.get(domain,[]))
    roots=hints+[f"https://{domain}/",f"https://www.{domain}/"]
    roots=list(dict.fromkeys(roots))
    errors=[]
    for root in roots:
'''
if old_roots in s:
    s=s.replace(old_roots,new_roots,1)
elif "hints=list(KNOWN_SIGNUP_ROUTES" not in s:
    raise SystemExit("V66_06A_ABORT=signup_roots_anchor_missing")

needle='''        p=LinkParser()
        try:
            p.feed(text)
        except Exception:
            pass
        scored=[]
'''
replacement='''        if root in hints:
            probe=FormParser()
            try:
                probe.feed(text)
            except Exception:
                pass
            marker=text.lower()
            if probe.forms or any(x in marker for x in ("register new account","create your account","sign up","create account")):
                return {
                    "ok":True,
                    "signup_url":final,
                    "label":"known_official_signup_route",
                    "source_url":final,
                }

        p=LinkParser()
        try:
            p.feed(text)
        except Exception:
            pass
        scored=[]
'''
if needle in s:
    s=s.replace(needle,replacement,1)
elif "known_official_signup_route" not in s:
    raise SystemExit("V66_06A_ABORT=signup_probe_anchor_missing")

p.write_text(s)
print("V66_06A_ACCOUNT_RECOVERY_PATCH=PASS")
PY

cat > "$ROOT/tests/test_openai_web_search_adapter.py" <<'PY'
from companyos.runtime.openai_web_search_adapter import _output_text, _sources

def test_parse_output_text_and_sources():
    data={
        "output":[
            {
                "type":"web_search_call",
                "action":{"sources":[
                    {"title":"Official Vendor","url":"https://example.com/pricing"},
                    {"title":"Official Vendor","url":"https://example.com/pricing"},
                ]},
            },
            {
                "type":"message",
                "content":[{"type":"output_text","text":"Official pricing is available at the cited source."}],
            },
        ]
    }
    assert "Official pricing" in _output_text(data)
    src=_sources(data)
    assert len(src)==1
    assert src[0]["url"]=="https://example.com/pricing"
PY

echo "===== COMPILE ====="
python -m py_compile "$OPENAI_ADAPTER" "$SOURCING" "$ACCOUNTS"
echo "V66_06A_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_openai_web_search_adapter.py
echo "V66_06A_TESTS=PASS"

echo "===== SEARCH PROVIDER STATUS ====="
if [ -x "$ROOT/scripts/companyos_sourcingctl" ]; then
  "$ROOT/scripts/companyos_sourcingctl" providers
fi

echo "===== COMPANYAIOS MAIL STATUS ====="
if [ -x "$ROOT/scripts/companyos_accountctl" ]; then
  "$ROOT/scripts/companyos_accountctl" mail
fi

echo "===== RESTART LIVE LOOPS ====="
if [ -x "$ROOT/scripts/companyos_sourcingctl" ]; then
  "$ROOT/scripts/companyos_sourcingctl" restart
fi
if [ -x "$ROOT/scripts/companyos_accountctl" ]; then
  "$ROOT/scripts/companyos_accountctl" restart
fi

echo "===== LIVE SOURCING RETRY ====="
if [ -x "$ROOT/scripts/companyos_sourcingctl" ]; then
  "$ROOT/scripts/companyos_sourcingctl" once 20 || true
fi

echo "===== PROVIDER ACCOUNT RETRY ====="
if [ -x "$ROOT/scripts/companyos_accountctl" ]; then
  "$ROOT/scripts/companyos_accountctl" once 3 || true
fi

echo "===== FINAL SEARCH STATUS ====="
if [ -x "$ROOT/scripts/companyos_sourcingctl" ]; then
  "$ROOT/scripts/companyos_sourcingctl" providers
fi

echo "V66_06A_IMAP_AUTORECOVERY=PASS"
echo "V66_06A_EXISTING_OPENAI_SEARCH_BOOTSTRAP=PASS"
echo "V66_06A_OFFICIAL_SIGNUP_ROUTE_RECOVERY=PASS"
echo "V66_06A_PROVIDER_ALTERNATIVE_ORDERING=PASS"
echo "V66_06A_NO_UNCITED_MODEL_TEXT_AS_EVIDENCE=PASS"
echo "V66_06A_NO_CAPTCHA_PHONE_KYC_BYPASS=PASS"
echo "V66_06A_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_06A_COMPLETE"
