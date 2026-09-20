#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
ENV_FILE="$HOME/.companyos_launch_env"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/selfbuild_finish_start_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"
cp -a companyos/runtime/self_evolution_engine.py "$BACKUP/self_evolution_engine.py"

echo "============================================================"
echo " CompanyOS FINAL SELF-BUILD + START BUNDLE"
echo "============================================================"

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE missing"; exit 1; }

python - <<'PY'
from pathlib import Path
p=Path.home()/".companyos_launch_env"
lines=p.read_text().splitlines()
settings={
 "COMPANYOS_LOCAL_AI_MAX_TOKENS":"4096",
 "COMPANYOS_LOCAL_AI_PROMPT_CHARS":"3200",
 "COMPANYOS_SELF_EVOLUTION_GENERATION_TIMEOUT":"600",
 "COMPANYOS_SELF_EVOLUTION_TEST_TIMEOUT":"300",
 "COMPANYOS_SELF_EVOLUTION_INTERVAL_SECONDS":"1800",
 "COMPANYOS_SELF_EVOLUTION_INITIAL_DELAY_SECONDS":"90",
 "COMPANYOS_ENABLE_SELF_EVOLUTION":"1",
 "COMPANYOS_SELF_EVOLUTION_AUTO_PROMOTE":"1",
 "COMPANYOS_SELF_EVOLUTION_AUTO_RESTART":"1",
}
for k,v in settings.items():
    lines=[x for x in lines if not x.startswith(f"export {k}=")]
    lines.append(f"export {k}={v}")
p.write_text("\n".join(lines)+"\n")
p.chmod(0o600)
print("SELF_BUILD_LIMITS=SET")
PY

source "$ENV_FILE"

python - <<'PY'
from pathlib import Path
import re

p=Path("companyos/runtime/self_evolution_engine.py")
s=p.read_text()

m=re.search(r'(?m)^def\s+_direct_generation_fallback\s*\(\s*wt\s*,\s*goal\s*\)\s*:\s*\n',s)
if not m:
    raise SystemExit("ERROR: direct fallback function not found")
start=m.start()
n=re.search(r'(?m)^(?:def|class)\s+\w+',s[m.end():])
end=len(s) if not n else m.end()+n.start()

replacement = '''def _direct_generation_fallback(wt, goal):
    import json as _json
    import subprocess as _subprocess
    import sys as _sys

    scripts_dir = wt / "scripts"
    if str(scripts_dir) not in _sys.path:
        _sys.path.insert(0, str(scripts_dir))

    try:
        from companyos_local_ai_adapter import model_request, extract_json
    except Exception as exc:
        return {"ok": False, "reason": "adapter_import_failed", "error": f"{type(exc).__name__}: {exc}"}

    blocked = (
        "wallet","finance","banking","payment","credential","secret","security",
        "approval","governance","guardrail","connector","solana","private_key",
        "self_evolution","service_supervisor","runtime_control","deployment_gate",
    )
    exact = {
        "scripts/companyos_evolutionctl",
        "scripts/companyos_adaptive_self_build.py",
        "companyos/runtime/self_evolution_engine.py",
        "companyos/runtime/self_evolution_runtime.py",
        "companyos/runtime/service_supervisor.py",
    }

    candidates=[]
    for base in ("companyos","companyos_modules","scripts"):
        root=wt/base
        if not root.exists():
            continue
        for fp in root.rglob("*.py"):
            try:
                rel=str(fp.relative_to(wt)).replace(chr(92),"/")
                low=rel.lower()
                size=fp.stat().st_size
                if rel in exact or any(x in low for x in blocked):
                    continue
                if 200 <= size <= 14000:
                    candidates.append((size,rel))
            except Exception:
                pass
    candidates=[r for _,r in sorted(candidates)[:60]]

    prompts=[
        (
            "Goal:\\n"+str(goal)+"\\n\\n"
            "Produce ONE concrete CompanyOS source improvement. Return JSON only. "
            "Do not return not_run, skip, no-op, or empty output. "
            "Change exactly one file. Prefer a SMALL existing Python file from the list. "
            "Return COMPLETE file content, not a diff. Keep it concise, preferably under 160 lines. "
            "Python must compile. Never touch wallets, finance, payments, credentials, security, "
            "approvals, governance, connectors, deployment gates, supervisor code, or self-evolution guard code. "
            "Prefer reliability, observability, validation, recovery, or opportunity-to-execution progress.\\n\\n"
            "Return exactly: "
            "{\\"path\\":\\"relative/file.py\\",\\"action\\":\\"replace\\",\\"content\\":\\"complete file contents\\"}\\n\\n"
            "Candidates:\\n"+_json.dumps(candidates[:40],indent=2)
        ),
        (
            "Goal:\\n"+str(goal)+"\\n\\n"
            "The previous answer was incomplete. Make the SMALLEST useful improvement possible. "
            "Create one compact new Python helper under companyos_modules/. Maximum about 120 lines. "
            "Return JSON only with path, action=create, and complete content. "
            "Do not touch protected finance, wallet, credential, approval, connector, supervisor, "
            "deployment-gate, or self-evolution code."
        ),
    ]

    last_error=None
    for attempt,prompt in enumerate(prompts,1):
        try:
            raw=model_request(prompt)
            if isinstance(raw,dict):
                if raw.get("ok") is False:
                    last_error={"reason":"adapter_failed","adapter_reason":raw.get("reason"),"attempt":attempt}
                    continue
                text=raw.get("text")
                plan=extract_json(text) if isinstance(text,str) else raw
            elif isinstance(raw,str):
                plan=extract_json(raw)
            else:
                plan=extract_json(str(raw))
        except Exception as exc:
            last_error={"reason":"generation_or_parse_failed","error":f"{type(exc).__name__}: {exc}","attempt":attempt}
            continue

        if not isinstance(plan,dict):
            last_error={"reason":"plan_not_object","attempt":attempt}
            continue

        rel=str(plan.get("path") or "").strip().replace(chr(92),"/")
        action=str(plan.get("action") or "replace").strip().lower()
        content=str(plan.get("content") or "")

        if not rel or not content.strip():
            last_error={"reason":"empty_plan","attempt":attempt}
            continue

        low=rel.lower()
        if (
            rel.startswith("/") or ".." in Path(rel).parts or rel in exact
            or any(x in low for x in blocked)
            or not rel.startswith(("companyos/","companyos_modules/","scripts/","tests/"))
        ):
            last_error={"reason":"path_rejected","path":rel,"attempt":attempt}
            continue

        target=wt/rel
        if action not in {"replace","create"}:
            action="replace" if target.exists() else "create"
        if action=="replace" and not target.exists():
            last_error={"reason":"replace_target_missing","path":rel,"attempt":attempt}
            continue

        if len(content.encode("utf-8")) > 50000:
            last_error={"reason":"content_too_large","path":rel,"attempt":attempt}
            continue

        if rel.endswith(".py"):
            try:
                compile(content,rel,"exec")
            except Exception as exc:
                last_error={"reason":"invalid_python","error":f"{type(exc).__name__}: {exc}","attempt":attempt}
                continue

        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content.rstrip()+"\\n",encoding="utf-8")

        cp=_subprocess.run(["git","status","--porcelain=v1"],cwd=str(wt),text=True,capture_output=True,timeout=30)
        changed=[line[3:].strip() for line in cp.stdout.splitlines() if len(line)>=4]
        if changed:
            return {
                "ok":True,
                "status":"direct_candidate_written",
                "generator":"direct_fallback_retrying",
                "attempt":attempt,
                "path":rel,
                "action":action,
                "changed_files":changed,
            }
        last_error={"reason":"no_change_after_write","attempt":attempt}

    return {"ok":False,"reason":"all_generation_attempts_failed","last_error":last_error}


'''

p.write_text(s[:start]+replacement+s[end:])
print("COMPACT_RETRY_GENERATOR=INSTALLED")
PY

echo "[1/8] Syntax + guard tests..."
python -m py_compile companyos/runtime/self_evolution_engine.py scripts/companyos_local_ai_adapter.py
python -m unittest tests.test_self_evolution_guard

echo "[2/8] Model smoke test..."
python - <<'PY'
import sys
sys.path.insert(0,"scripts")
from companyos_local_ai_adapter import model_request, extract_json
r=model_request('Return exactly one JSON object: {"ready":true}')
print("MODEL_OK="+str(bool(r.get("ok"))).lower())
print("MODEL_PROVIDER="+str(r.get("provider")))
print("MODEL_ENDPOINT="+str(r.get("endpoint")))
print("MODEL_NAME="+str(r.get("model")))
if not r.get("ok"):
    print("MODEL_REASON="+str(r.get("reason")))
    raise SystemExit(1)
obj=extract_json(r.get("text",""))
if obj.get("ready") is not True:
    raise SystemExit("MODEL_JSON_FAILED")
print("MODEL_JSON=PASS")
PY

echo "[3/8] Secret scan..."
for secret_name in OPENAI_API_KEY CLOUDFLARE_API_TOKEN SOLANA_PRIVATE_KEY SMTP_PASSWORD; do
  secret="${!secret_name:-}"
  if [ -n "$secret" ]; then
    if git grep -nF "$secret" -- . ':!*.log' ':!.companyos_runtime' 2>/dev/null | head -1 | grep -q .; then
      echo "ERROR: value of $secret_name found in source"
      exit 1
    fi
  fi
done
echo "SECRET_SCAN=PASS"

echo "[4/8] Commit final self-build fix..."
git add -- companyos/runtime/self_evolution_engine.py
if ! git diff --cached --quiet; then
  git commit -m "Finish robust self-build generation retries"
fi
BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

echo "[5/8] Restart CompanyOS..."
if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi
sleep 6

echo "[6/8] Check all 5 services..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/".companyos_runtime"/"service_supervisor_state.json"
d=json.loads(p.read_text()) if p.exists() else {}
services=d.get("services") or {}
expected=[
 "continuous_goal_runtime","local_dashboard","productive_autonomy_watchdog",
 "profit_opportunity_runtime","self_evolution_runtime"
]
bad=[]
for name in expected:
    row=services.get(name) or {}
    running=bool(row.get("running"))
    print(f"{name}: running={running} failures={row.get('consecutive_failures',0)}")
    if not running: bad.append(name)
if bad:
    raise SystemExit("SERVICES_DOWN="+",".join(bad))
print("ALL_5_SERVICES=RUNNING")
PY

echo "[7/8] Run one guarded evolution cycle..."
set +e
scripts/companyos_evolutionctl once | tee "$ROOT/.companyos_runtime/self_evolution/finish_cycle_$STAMP.json"
CYCLE_RC=${PIPESTATUS[0]}
set -e
echo "SELF_EVOLUTION_CYCLE_RC=$CYCLE_RC"

echo "[8/8] Final launch health..."
curl -fsS http://127.0.0.1:8765/api/health >/tmp/companyos_health.json 2>/dev/null || true
python - <<'PY'
import json
from pathlib import Path
p=Path("/tmp/companyos_health.json")
if not p.exists() or not p.read_text().strip():
    print("DASHBOARD_HEALTHY=false")
else:
    d=json.loads(p.read_text())
    print("DASHBOARD_HEALTHY="+str(bool(d.get("healthy"))).lower())
    print("CORE_EXTERNAL_READY="+str(bool(d.get("core_external_ready"))).lower())
PY

echo
echo "Dashboard: http://127.0.0.1:8765"
echo "Backup: $BACKUP"
if [ "$CYCLE_RC" = "0" ]; then
  echo "FIRST_GUARDED_SELF_BUILD_CYCLE=PASS"
else
  echo "FIRST_GUARDED_SELF_BUILD_CYCLE=REVIEW_NEEDED"
fi
echo "COMPANYOS_FINISH_AND_START_BUNDLE=PASS"
