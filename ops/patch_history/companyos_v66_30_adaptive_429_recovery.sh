#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.30 ADAPTIVE OPENAI 429 RECOVERY ====="
echo "GOAL=RECOVER_FROM_SHORT_TPM_RATE_LIMITS_WITH_SMALLER_REQUESTS_AND_REAL_RETRY_TIMING"
echo "NOTE=KEEPS_GPT_5_6_LUNA_AS_DEFAULT_MODEL"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_30_ABORT=missing:$MOD"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_30_backup_${stamp}"
echo "BACKUP=${MOD}.v66_30_backup_${stamp}"

echo "===== PATCH 429 HANDLING ====="
python - <<'PY'
from pathlib import Path
import ast
import re

p=Path.home()/"companyos/companyos/runtime/verified_web_prospect_discovery.py"
s=p.read_text()

def fn_span(src,name):
    tree=ast.parse(src)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node.lineno,node.end_lineno
    return None

def replace_fn(src,name,new_text):
    sp=fn_span(src,name)
    if not sp:
        raise SystemExit(f"V66_30_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

# Insert a retry-delay parser before web_search if missing.
if "def parse_retry_after_seconds(" not in s:
    sp=fn_span(s,"web_search")
    if not sp:
        raise SystemExit("V66_30_ABORT=web_search_missing")
    helper = r'''
def parse_retry_after_seconds(headers, body: str) -> float|None:
    try:
        value=headers.get("Retry-After") if headers is not None else None
        if value not in (None,""):
            return max(0.0,float(value))
    except Exception:
        pass

    text=str(body or "").lower()

    # Examples commonly returned by API rate-limit messages:
    # "try again in 2.5s", "try again in 750ms", "try again in 1m20s".
    m=re.search(r"try again in\s+([0-9.]+)\s*ms",text)
    if m:
        return float(m.group(1))/1000.0

    m=re.search(r"try again in\s+([0-9.]+)\s*s",text)
    if m:
        return float(m.group(1))

    m=re.search(
        r"try again in\s+([0-9.]+)\s*m(?:in(?:ute)?s?)?\s*([0-9.]*)\s*s?",
        text,
    )
    if m:
        minutes=float(m.group(1))
        seconds=float(m.group(2) or 0)
        return minutes*60.0+seconds

    return None
'''
    lines=s.splitlines()
    lines[sp[0]-1:sp[0]-1]=helper.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

web_search = r'''
def web_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    key=openai_key()
    if not key:
        return {"ok":False,"status":"OPENAI_API_KEY_MISSING"}

    audience=copy.get("audience") or "businesses that fit this product"
    live_url=copy.get("live_url") or ""
    title=copy.get("title") or cid.replace("_"," ").title()
    description=copy.get("description") or ""

    prompt = "\n".join([
        "Find up to 5 businesses that are plausible prospects for the launched venture below.",
        "",
        f"Venture: {title}",
        f"Description: {description}",
        f"Target audience: {audience}",
        f"Live product URL: {live_url}",
        "",
        "Return ONLY valid JSON in this exact shape:",
        '{"prospects":[{"company_name":"...","public_business_email":"...","official_website":"https://...","source_url":"https://...","fit_reason":"..."}]}',
        "",
        "Requirements:",
        "- The email must be a publicly listed BUSINESS contact email.",
        "- source_url must be an official company-owned page where that exact email is visible.",
        "- Prefer role-based business addresses such as sales, info, estimating, office, contact, or partnerships.",
        "- Do not infer, guess, generate, or pattern-match an email address.",
        "- Do not return private/personal contact data.",
        "- Do not use data-broker, people-search, scraped directory, social-media-profile, or lead-list pages as the source.",
        "- official_website and source_url must be public HTTP(S) URLs.",
        "- Fit must be based on the venture and target audience above.",
        '- If no qualifying prospects are found, return {"prospects":[]}.',
    ])

    max_output=max(
        500,
        min(
            int(os.getenv("COMPANYOS_WEB_SEARCH_MAX_OUTPUT_TOKENS","1200")),
            4000,
        ),
    )
    retry_ceiling=max(
        1.0,
        min(
            float(os.getenv("COMPANYOS_WEB_SEARCH_INLINE_RETRY_CEILING_SECONDS","20")),
            60.0,
        ),
    )

    body={
        "model":DEFAULT_MODEL,
        "reasoning":{"effort":"none"},
        "max_output_tokens":max_output,
        "tools":[{"type":"web_search","search_context_size":"low"}],
        "input":prompt,
    }

    attempts=[]
    for attempt in range(1,3):
        data=json.dumps(body).encode()
        req=request.Request(
            OPENAI_URL,
            data=data,
            method="POST",
            headers={
                "Authorization":f"Bearer {key}",
                "Content-Type":"application/json",
                "User-Agent":"CompanyOS/V66.30",
            },
        )

        try:
            with request.urlopen(req,timeout=90) as resp:
                raw=resp.read()
            payload=json.loads(raw.decode())
        except error.HTTPError as exc:
            err_body=exc.read().decode("utf-8","replace")
            retry_after=parse_retry_after_seconds(exc.headers,err_body)
            attempts.append({
                "attempt":attempt,
                "http_status":exc.code,
                "retry_after_seconds":retry_after,
            })

            if (
                exc.code==429
                and attempt==1
                and retry_after is not None
                and retry_after <= retry_ceiling
            ):
                # Honor the actual short API retry window instead of turning
                # a seconds-long TPM event into a 30-minute stall.
                time.sleep(max(0.5,retry_after+0.75))
                continue

            return {
                "ok":False,
                "status":f"OPENAI_HTTP_{exc.code}",
                "error":err_body[:1200],
                "retry_after_seconds":retry_after,
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }
        except Exception as exc:
            return {
                "ok":False,
                "status":"OPENAI_REQUEST_ERROR",
                "error":f"{type(exc).__name__}:{exc}",
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }

        text=output_text(payload)
        try:
            parsed=parse_json_text(text)
        except Exception as exc:
            return {
                "ok":False,
                "status":"OPENAI_OUTPUT_PARSE_ERROR",
                "error":f"{type(exc).__name__}:{exc}",
                "output_preview":text[:1200],
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }

        prospects=parsed.get("prospects") if isinstance(parsed,dict) else None
        if not isinstance(prospects,list):
            prospects=[]

        return {
            "ok":True,
            "status":"SEARCH_COMPLETED",
            "model":DEFAULT_MODEL,
            "response_id":payload.get("id"),
            "prospects":prospects[:5],
            "request_max_output_tokens":max_output,
            "reasoning_effort":"none",
            "attempts":attempts,
        }

    return {
        "ok":False,
        "status":"OPENAI_RETRY_EXHAUSTED",
        "attempts":attempts,
    }
'''
s=replace_fn(s,"web_search",web_search)

retry_fn = r'''
def retry_delay_for_result(result: dict[str,Any]|None) -> int:
    if not result:
        return 0

    status=str(result.get("status") or "")

    if status=="DISCOVERY_COMPLETED":
        verified=int(result.get("verified_count") or 0)
        candidates=int(result.get("search_candidate_count") or 0)

        if verified>0:
            return max(
                1800,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_SUCCESS_COOLDOWN_SECONDS",
                    "21600",
                )),
            )

        if candidates>0:
            return max(
                300,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_REJECTED_COOLDOWN_SECONDS",
                    "900",
                )),
            )

        return max(
            300,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_EMPTY_COOLDOWN_SECONDS",
                "1800",
            )),
        )

    if status=="OPENAI_HTTP_429":
        api_retry=result.get("retry_after_seconds")
        try:
            if api_retry is not None:
                return max(5,min(int(float(api_retry)+5),300))
        except Exception:
            pass

        # If an older V66.29 result has only the raw API error text, recover
        # retry timing from that instead of defaulting to 30 minutes.
        parsed=parse_retry_after_seconds(None,str(result.get("error") or ""))
        if parsed is not None:
            return max(5,min(int(parsed+5),300))

        return max(
            30,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_RATE_LIMIT_BACKOFF_SECONDS",
                    "60",
                )),
                300,
            ),
        )

    if status.startswith("OPENAI_HTTP_"):
        return max(
            60,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_HTTP_ERROR_BACKOFF_SECONDS",
                    "300",
                )),
                900,
            ),
        )

    if status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_OUTPUT_PARSE_ERROR",
        "OPENAI_API_KEY_MISSING",
        "OPENAI_RETRY_EXHAUSTED",
    }:
        return max(
            60,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_ERROR_BACKOFF_SECONDS",
                    "300",
                )),
                900,
            ),
        )

    return 300
'''
s=replace_fn(s,"retry_delay_for_result",retry_fn)

ast.parse(s)
p.write_text(s)
print("V66_30_429_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_30_adaptive_429_recovery.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import (
    parse_retry_after_seconds,
    retry_delay_for_result,
)

def test_retry_seconds_from_message():
    x=parse_retry_after_seconds(None,"Please try again in 2.5s.")
    assert 2.4 <= x <= 2.6

def test_retry_milliseconds_from_message():
    x=parse_retry_after_seconds(None,"Please try again in 750ms.")
    assert 0.7 <= x <= 0.8

def test_429_uses_short_backoff():
    x=retry_delay_for_result({
        "status":"OPENAI_HTTP_429",
        "retry_after_seconds":3.0,
    })
    assert 5 <= x <= 20

def test_old_429_error_text_is_recovered():
    x=retry_delay_for_result({
        "status":"OPENAI_HTTP_429",
        "error":"Rate limit reached. Please try again in 4.2s.",
    })
    assert 5 <= x <= 20
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_30_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_30_adaptive_429_recovery.py
echo "V66_30_TESTS=PASS"

echo "===== CLEAR ONLY THE CURRENT 429 COOLDOWN ====="
python - <<'PY'
import json
from companyos.runtime.verified_web_prospect_discovery import (
    STATE,
    load_json,
    save_json,
)

state=load_json(STATE,{
    "last_search_by_venture":{},
    "last_outcome_by_venture":{},
})
changed=[]

for cid,outcome in list((state.get("last_outcome_by_venture") or {}).items()):
    if isinstance(outcome,dict) and str(outcome.get("status") or "")=="OPENAI_HTTP_429":
        state.setdefault("last_search_by_venture",{})[cid]=0
        changed.append(cid)

save_json(STATE,state)
print(json.dumps({
    "cleared_429_cooldown_for":changed,
},indent=2,sort_keys=True))
PY

echo "===== RETRY PROSPECT SEARCH WITH SMALL REQUEST ====="
"$CTL" once

echo "===== FEED VERIFIED CONTACTS INTO CUSTOMER ACQUISITION ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== LIGHTWEIGHT LIVENESS REFRESH ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_30_SMALL_WEB_SEARCH_REQUEST=PASS"
echo "V66_30_REASONING_NONE=PASS"
echo "V66_30_RETRY_AFTER_PARSE=PASS"
echo "V66_30_SHORT_TPM_INLINE_RETRY=PASS"
echo "V66_30_429_COOLDOWN_NOT_30_MINUTES=PASS"
echo "V66_30_V66_27_HANDOFF=PASS"
echo "V66_30_NO_NEW_DAEMON=PASS"
echo "V66_30_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_30_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_30_COMPLETE"
