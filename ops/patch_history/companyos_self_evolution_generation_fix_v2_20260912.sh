#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/self_evolution_generation_fix_v2_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"
cp -a companyos/runtime/self_evolution_engine.py "$BACKUP/self_evolution_engine.py"

echo "CompanyOS Self-Evolution Generation Fix V2"

python - <<'PY'
from pathlib import Path
import re

p = Path("companyos/runtime/self_evolution_engine.py")
s = p.read_text()

m = re.search(r'(?m)^def\s+_generate_candidate\s*\([^\n]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n', s)
if not m:
    raise SystemExit("ERROR: could not locate _generate_candidate")

start = m.start()
n = re.search(r'(?m)^(?:def|class)\s+\w+', s[m.end():])
end = len(s) if not n else m.end() + n.start()

helper = '''
def _direct_generate_candidate(worktree: Path, goal: str) -> dict:
    scripts_dir = worktree / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from companyos_local_ai_adapter import model_request, extract_json
    except Exception as exc:
        return {"ok": False, "reason": "local_ai_adapter_import_failed", "error": f"{type(exc).__name__}: {exc}"}

    candidates = []
    for base in ("companyos", "companyos_modules", "scripts", "tests"):
        root = worktree / base
        if not root.exists():
            continue
        for fp in root.rglob("*.py"):
            try:
                rel = str(fp.relative_to(worktree)).replace("\\\\", "/")
                allowed, _ = path_allowed(rel)
                if allowed and fp.stat().st_size <= 120000:
                    candidates.append(rel)
            except Exception:
                pass
    candidates = sorted(set(candidates))[:120]

    prompt = f"""
You are the code-generation stage inside CompanyOS self-evolution.

Goal:
{goal}

Produce ONE concrete source-code improvement in the isolated git worktree.

Rules:
- Return JSON only.
- Do not return not_run, skipped, no-op, or empty output.
- Change exactly one file.
- Prefer an existing file from the candidate list.
- Allowed actions: replace or create.
- Never touch wallet, finance, payments, credentials, approvals, governance,
  connectors, deployment gates, supervisor code, or the self-evolution guard.
- Return complete file content, not a diff fragment.
- Keep the change focused and under 600 changed lines.
- Python must compile.
- Prefer measurable improvements to reliability, observability,
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
        return {"ok": False, "reason": "model_generation_failed", "error": f"{type(exc).__name__}: {exc}"}

    if not isinstance(plan, dict):
        return {"ok": False, "reason": "plan_not_object"}

    rel = str(plan.get("path") or "").strip().replace("\\\\", "/")
    action = str(plan.get("action") or "replace").strip().lower()
    content = str(plan.get("content") or "")

    if not rel or not content.strip():
        return {"ok": False, "reason": "empty_direct_plan"}

    if action not in {"replace", "create"}:
        action = "replace" if (worktree / rel).exists() else "create"

    allowed, why = path_allowed(rel)
    if not allowed:
        return {"ok": False, "reason": "direct_plan_path_rejected", "path": rel, "guard_reason": why}

    target = worktree / rel
    if action == "replace" and not target.exists():
        return {"ok": False, "reason": "replace_target_missing", "path": rel}

    if rel.endswith(".py"):
        try:
            compile(content, rel, "exec")
        except Exception as exc:
            return {"ok": False, "reason": "generated_python_invalid", "error": f"{type(exc).__name__}: {exc}"}

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\\n", encoding="utf-8")
    return {"ok": True, "status": "direct_candidate_written", "path": rel, "action": action}


'''

replacement = '''def _generate_candidate(worktree: Path, goal: str) -> dict:
    script = worktree / "scripts" / "companyos_adaptive_self_build.py"
    legacy = {"ok": False, "reason": "adaptive_self_build_missing"}

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

    if legacy.get("ok") and changed and "not_run" not in legacy_text and "no_changes" not in legacy_text and "no change" not in legacy_text:
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

prefix = s[:start]
if "def _direct_generate_candidate(" not in s:
    prefix += helper

s2 = prefix + replacement + s[end:]
p.write_text(s2)
print("PATCHED_CURRENT_GENERATOR=YES")
PY

python -m py_compile companyos/runtime/self_evolution_engine.py
python -m unittest tests.test_self_evolution_guard

source "$HOME/.companyos_launch_env"

echo "SECRET_SCAN..."
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

git add -- companyos/runtime/self_evolution_engine.py
if ! git diff --cached --quiet; then
  git commit -m "Fix self-evolution empty candidate fallback"
fi

BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi
sleep 5

grep -n -E '^def _direct_generate_candidate|^def _generate_candidate' companyos/runtime/self_evolution_engine.py || true

echo "COMPANYOS_SELF_EVOLUTION_GENERATION_FIX_V2=PASS"
