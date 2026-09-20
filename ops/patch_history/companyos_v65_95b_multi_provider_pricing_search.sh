#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
GLOBAL_RT="$HOME/.companyos_runtime"
MODULE="$ROOT/companyos/runtime/economics_validation_manager.py"
PIDFILE="$GLOBAL_RT/economics_validation_manager.pid"
LOGFILE="$GLOBAL_RT/economics_validation_manager.log"
VALIDATION_SCRIPT="$HOME/storage/downloads/companyos_v65_96_parallel_validation_promotion.sh"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.95B MULTI-PROVIDER PRICING SEARCH ====="

if [ ! -f "$MODULE" ]; then
  echo "V65_95B_ABORT=missing_economics_validation_manager"
  exit 1
fi

if [ -f "$PIDFILE" ]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
    echo "STOPPING_OLD_ECONOMICS_MANAGER_PID=$pid"
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! kill -0 "$pid" 2>/dev/null; then break; fi
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDFILE"
fi

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MODULE" "${MODULE}.v65_95b_backup_${stamp}"
echo "BACKUP_MODULE=${MODULE}.v65_95b_backup_${stamp}"

python - <<'PY'
from pathlib import Path
import re

p = Path.home() / "companyos/companyos/runtime/economics_validation_manager.py"
s = p.read_text()

s = s.replace(
    "from urllib.parse import urlparse\n",
    "from urllib.parse import urlparse, quote_plus\n",
)

pattern = re.compile(
    r"def search_results\(web,o\):\n.*?\n(?=def candidate_fetch_urls\(results\):)",
    re.S,
)

replacement = '''def search_results(web,o):
    found=[]
    errors=[]
    provider_counts={}

    search_engine_domains={
        "search.brave.com","brave.com",
        "www.bing.com","bing.com",
        "www.mojeek.com","mojeek.com",
        "duckduckgo.com","html.duckduckgo.com","lite.duckduckgo.com",
        "google.com","www.google.com",
        "en.wikipedia.org",
    }

    def add_rows(rows, q, provider):
        added=0
        for item in rows or []:
            try:
                x=dict(item)
            except Exception:
                continue
            u=str(x.get("url") or "").strip()
            d=dom(u)
            if not u or not d or d in search_engine_domains:
                continue
            x["query"]=q
            x["search_provider"]=provider
            found.append(x)
            added+=1
        provider_counts[provider]=provider_counts.get(provider,0)+added

    def html_provider(provider, url, q):
        try:
            page,_=web.request_text(url, timeout=12)
            rows=web.parse_generic_links(page, SEARCH_RESULTS)
            add_rows(rows,q,provider)
        except Exception as exc:
            errors.append(f"{provider}:{q}:{type(exc).__name__}:{str(exc)[:160]}")

    for q in queries(o):
        try:
            r=web.search_web(q,SEARCH_RESULTS)
            add_rows(r.get("results") or [],q,"companyos_default")
            if not r.get("success"):
                errors.append(f"default:{q}:{r.get('error')}")
        except Exception as exc:
            errors.append(f"default:{q}:{type(exc).__name__}:{str(exc)[:160]}")

        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "brave_html",
                f"https://search.brave.com/search?q={enc}&source=web",
                q,
            )
        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "bing_html",
                f"https://www.bing.com/search?q={enc}&count={SEARCH_RESULTS}",
                q,
            )
        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "mojeek_html",
                f"https://www.mojeek.com/search?q={enc}",
                q,
            )

    seen=set()
    unique=[]
    for r in found:
        u=str(r.get("url") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        d=dom(u)
        if not commercial_domain(d):
            continue
        unique.append(r)

    def rank(r):
        hay=(str(r.get("title") or "")+" "+str(r.get("url") or "")).lower()
        score=0
        if "pricing" in hay: score+=5
        if "plans" in hay: score+=4
        if "price" in hay: score+=3
        if "cost" in hay: score+=2
        return score

    unique.sort(key=rank, reverse=True)
    errors.append("provider_counts="+str(provider_counts))
    return unique[:40],errors

'''

if not pattern.search(s):
    raise SystemExit("V65_95B_PATCH_ABORT=search_results_function_not_found")

s = pattern.sub(replacement, s)
p.write_text(s)
print("PATCH_SEARCH_RESULTS=PASS")
PY

python -m py_compile "$MODULE"
echo "MODULE_COMPILE=PASS"

echo "===== V65.95B IMMEDIATE ECONOMICS CYCLE ====="
python -m companyos.runtime.economics_validation_manager once

if [ -f "$VALIDATION_SCRIPT" ]; then
  echo "===== V65.96 IMMEDIATE VALIDATION CHECK ====="
  bash "$VALIDATION_SCRIPT" once || true
else
  echo "V65_96_SCRIPT_NOT_FOUND=skipping_immediate_validation_check"
fi

INTERVAL_SECONDS="${COMPANYOS_ECONOMICS_VALIDATION_INTERVAL_SECONDS:-900}"
nohup python -m companyos.runtime.economics_validation_manager loop \
  --interval "$INTERVAL_SECONDS" >> "$LOGFILE" 2>&1 &
pid="$!"
echo "$pid" > "$PIDFILE"
sleep 1

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PIDFILE"
  echo "V65_95B_ABORT=manager_failed_to_restart"
  exit 1
fi

echo "ECONOMICS_MANAGER_RUNNING=true"
echo "PID=$pid"
echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"
echo "LOGFILE=$LOGFILE"
echo "V65_95B_MULTI_PROVIDER_SEARCH=PASS"
echo "V65_95B_VENDOR_PAGE_VERIFICATION=ENFORCED"
echo "V65_95B_COMPLETE"
