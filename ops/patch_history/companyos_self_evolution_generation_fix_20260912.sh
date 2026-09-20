#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/self_evolution_generation_fix_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"

echo "============================================================"
echo " CompanyOS Self-Evolution Generation Fix"
echo " Fixes empty/no-op candidate generation"
echo "============================================================"

for f in companyos/runtime/self_evolution_engine.py scripts/companyos_adaptive_self_build.py; do
  if [ -f "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/self_evolution_engine.py")
s = p.read_text()

start_marker = "def _generate_candidate(worktree: Path, goal: str) -> dict:\n"
end_marker = "\ndef _commit_candidate("

if start_marker not in s or end_marker not in s:
    raise SystemExit("ERROR: self-evolution generation function anchors not found")

if "def _direct_generate_candidate(" not in s:
    helper = '''
def _direct_generate_candidate(worktree: Path, goal: str) -> dict:
    adapter = worktree / "scripts" / "companyos_local_ai_adapter.py"
    if not adapter.exists():
        return {"ok": False, "reason": "local_ai_adapter_missing"}

    if str(worktree / "scripts") not in sys.path:
        sys.path.insert(0, str(worktree / "scripts"))

    try:
        from companyos_local_ai_adapter import model_request, extract_json
    except Exception as exc:
        return {
            "ok": False,
            "reason": "local_ai_adapter_import_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }

    candidates = []
    for base in ("companyos", "companyos_modules", "scripts", "tests"):
        root = worktree / base
        if not root.exists():
            continue
        for fp in root.rglob("*.py"):
            rel = str(fp.relative_to(worktree)).replace("\\\\", "/")
            allowed, _ = path_allowed(rel)
            if not allowed:
                continue
            try:
                if fp.stat().st_size > 120000:
                    continue
            except Exception:
                continue
            candidates.append(rel)

    candidates = sorted(set(candidates))[:120]

    prompt = f"""
You are the code-generation stage inside CompanyOS self-evolution.

Goal:
{goal}

Produce ONE concrete source-code improvement inside the isolated git worktree.

Hard requirements:
1. Return JSON only.
2. Do not return not_run, skip, no-op, or an empty change.
3. Change exactly one file.
4. Prefer an existing file from the candidate list.
5. Allowed actions are replace or create.
6. Never touch wallet, finance, payment, credentials, approvals, governance,
   connectors, deployment gates, supervisor code, or the self-evolution guard.
7. Return complete file content, not a patch fragment.
8. Keep it focused and under 600 changed lines.
9. Python must compile.
10. Prefer measurable improvements to reliability, observability,
    opportunity-to-execution conversion, validation, or recovery.

Return exactly:
{{
  "path": "relative/file.py",
  "action": "replace",
  "content": "complete file contents"
}}

Candidate files:
{json.dumps(candidates, indent=2)}
""".strip()

    try:
        raw = model_request(prompt)
        plan = extract_json(raw)
    except Exception as exc:
        return {
            "ok": False,
            "reason": "model_generation_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }

    if not isinstance(plan, dict):
        return {"ok": False, "reason": "plan_not_object"}

    rel = str(plan.get("path") or "").strip().replace("\\\\", "/")
    action = str(plan.get("action") or "replace").strip().lower()
    content = str(plan.get("content") or "")

    if action not in {"replace", "create"}:
        action = "replace" if (worktree / rel).exists() else "create"

    if not rel or not content.strip():
        return {"ok": False, "reason": "empty_direct_plan"}

    allowed, why = path_allowed(rel)
    if not allowed:
        return {
            "ok": False,
            "reason": "direct_plan_path_rejected",
            "path": rel,
            "guard_reason": why,
        }

    target = worktree / rel
    if action == "replace" and not target.exists():
        return {
            "ok": False,
            "reason": "replace_target_missing",
            "path": rel,
        }

    if rel.endswith(".py"):
        try:
            compile(content, rel, "exec")
        except Exception as exc:
            return {
                "ok": False,
                "reason": "generated_python_invalid",
                "error": f"{type(exc).__name__}: {exc}",
            }

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\\n", encoding="utf-8")

    return {
        "ok": True,
        "status": "direct_candidate_written",
        "path": rel,
        "action": action,
    }


'''
    s = s.replace(start_marker, helper + start_marker, 1)

start = s.index(start_marker)
end = s.index(end_marker, start)

replacement = '''def _generate_candidate(worktree: Path, goal: str) -> dict:
    script = worktree / "scripts" / "companyos_adaptive_self_build.py"
    legacy = {"ok": False, "reason": "adaptive_self_build_script_missing"}

    if script.exists():
        fake_home = worktree.parent / "home"
        fake_home.mkdir(parents=True, exist_ok=True)
        home_repo = fake_home / "companyos"
        if home_repo.exists() or home_repo.is_symlink():
            home_repo.unlink()
        home_repo.symlink_to(worktree, target_is_directory=True)

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["COMPANYOS_SELF_BUILD_GOAL"] = goal
        env["PYTHONPATH"] = os.pathsep.join([
            str(worktree),
            str(worktree / "scripts"),
            env.get("PYTHONPATH", ""),
        ]).strip(os.pathsep)
        env["COMPANYOS_SELF_BUILD_EXTERNAL_ACTIONS"] = "0"

        try:
            proc = _run(
                [sys.executable, str(script)],
                cwd=worktree,
                timeout=int(os.getenv("COMPANYOS_SELF_EVOLUTION_GENERATION_TIMEOUT", "420")),
                env=env,
            )
            legacy = {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-5000:],
                "stderr_tail": (proc.stderr or "")[-5000:],
            }
        except Exception as exc:
            legacy = {
                "ok": False,
                "reason": "legacy_builder_exception",
                "error": f"{type(exc).__name__}: {exc}",
            }

    changed = _changed_files(worktree)
    legacy_text = json.dumps(legacy).lower()
    legacy_noop = (
        not changed
        or "not_run" in legacy_text
        or "no_changes" in legacy_text
        or "no change" in legacy_text
    )

    if legacy.get("ok") and changed and not legacy_noop:
        return {
            "ok": True,
            "generator": "legacy_self_builder",
            "legacy": legacy,
            "changed_files": changed,
        }

    fallback = _direct_generate_candidate(worktree, goal)
    changed_after = _changed_files(worktree)

    return {
        "ok": bool(fallback.get("ok")) and bool(changed_after),
        "generator": "direct_fallback",
        "legacy": legacy,
        "fallback": fallback,
        "changed_files": changed_after,
    }
'''

s = s[:start] + replacement + s[end:]
p.write_text(s)
print("SELF_EVOLUTION_ENGINE_PATCHED")
PY

python - <<'PY'
from pathlib import Path

p = Path("scripts/companyos_adaptive_self_build.py")
s = p.read_text()

marker = "Return exactly one change. Never modify __pycache__, .pyc, archives, models, backups, or generated files.\n"
extra = (
    marker
    + "You MUST produce one concrete source-code change. Do not return not_run, skip, no-op, or an empty changes list.\n"
    + "If the ideal improvement is too large, implement the smallest useful first slice instead.\n"
)

if "You MUST produce one concrete source-code change." not in s:
    if marker not in s:
        raise SystemExit("ERROR: adaptive builder prompt marker not found")
    s = s.replace(marker, extra, 1)
    p.write_text(s)
    print("LEGACY_SELF_BUILDER_PROMPT_HARDENED")
else:
    print("LEGACY_SELF_BUILDER_PROMPT_ALREADY_HARDENED")
PY

echo "[TEST] syntax..."
python -m py_compile companyos/runtime/self_evolution_engine.py scripts/companyos_adaptive_self_build.py

echo "[TEST] guard..."
python -m unittest tests.test_self_evolution_guard

source "$HOME/.companyos_launch_env"

echo "[TEST] diagnosis..."
scripts/companyos_evolutionctl diagnose >/tmp/companyos_evolution_diagnose.json
python -m json.tool /tmp/companyos_evolution_diagnose.json | tail -80

echo "[SECURITY] secret scan..."
for secret_name in OPENAI_API_KEY CLOUDFLARE_API_TOKEN SOLANA_PRIVATE_KEY SMTP_PASSWORD; do
  secret="${!secret_name:-}"
  if [ -n "$secret" ]; then
    if git grep -nF "$secret" -- . ':!*.log' ':!.companyos_runtime' 2>/dev/null | head -1 | grep -q .; then
      echo "ERROR: value of $secret_name found in source; refusing commit"
      exit 1
    fi
  fi
done
echo "SECRET_SCAN=PASS"

git add -- companyos/runtime/self_evolution_engine.py scripts/companyos_adaptive_self_build.py

if ! git diff --cached --quiet; then
  git commit -m "Fix self-evolution no-op candidate generation"
fi

BRANCH="$(git branch --show-current)"
if [ -n "$BRANCH" ]; then
  git push origin "$BRANCH" || echo "WARNING: push failed; local generation fix remains installed"
fi

if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi

sleep 5

echo
echo "================ GENERATION FIX STATUS ================"
scripts/companyos_evolutionctl status | tail -120

echo
echo "Backup: $BACKUP"
echo "Next test:"
echo "  scripts/companyos_evolutionctl once"
echo
echo "COMPANYOS_SELF_EVOLUTION_GENERATION_FIX=PASS"
