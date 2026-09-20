#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/self_evolution_generation_fix_v3_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"
cp -a companyos/runtime/self_evolution_engine.py "$BACKUP/self_evolution_engine.py"

echo "============================================================"
echo " CompanyOS Self-Evolution Generation Fix V3"
echo " Targets current generate(wt, goal) function"
echo "============================================================"

python - <<'PY'
from pathlib import Path
import re

p = Path("companyos/runtime/self_evolution_engine.py")
s = p.read_text()

m = re.search(r'(?m)^def\s+generate\s*\(\s*wt\s*,\s*goal\s*\)\s*:\s*\n', s)
if not m:
    raise SystemExit("ERROR: current generate(wt, goal) function not found")

start = m.start()
n = re.search(r'(?m)^(?:def|class)\s+\w+', s[m.end():])
end = len(s) if not n else m.end() + n.start()

helper = """
def _direct_generation_fallback(wt, goal):
    import json as _json
    import subprocess as _subprocess
    import sys as _sys

    scripts_dir = wt / "scripts"
    if str(scripts_dir) not in _sys.path:
        _sys.path.insert(0, str(scripts_dir))

    try:
        from companyos_local_ai_adapter import model_request, extract_json
    except Exception as exc:
        return {
            "ok": False,
            "reason": "local_ai_adapter_import_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }

    blocked_words = (
        "wallet", "finance", "banking", "payment", "credential", "secret",
        "security", "approval", "governance", "guardrail", "connector",
        "solana", "private_key", "self_evolution", "service_supervisor",
        "runtime_control", "deployment_gate",
    )
    blocked_exact = {
        "scripts/companyos_evolutionctl",
        "scripts/companyos_adaptive_self_build.py",
        "companyos/runtime/self_evolution_engine.py",
        "companyos/runtime/self_evolution_runtime.py",
        "companyos/runtime/service_supervisor.py",
    }

    candidates = []
    for base in ("companyos", "companyos_modules", "scripts", "tests"):
        root = wt / base
        if not root.exists():
            continue
        for fp in root.rglob("*.py"):
            try:
                rel = str(fp.relative_to(wt)).replace(chr(92), "/")
                low = rel.lower()
                if rel in blocked_exact or any(word in low for word in blocked_words):
                    continue
                if fp.stat().st_size > 120000:
                    continue
                candidates.append(rel)
            except Exception:
                continue

    candidates = sorted(set(candidates))[:120]

    prompt = (
        "You are the code-generation stage inside CompanyOS self-evolution.\\n\\n"
        "Goal:\\n" + str(goal) + "\\n\\n"
        "The previous adaptive builder returned a no-op. Produce ONE real, useful "
        "source-code improvement inside this isolated git worktree.\\n\\n"
        "Rules:\\n"
        "1. Return JSON only.\\n"
        "2. Do NOT return not_run, skipped, no-op, or empty output.\\n"
        "3. Change exactly ONE file.\\n"
        "4. Prefer an existing file from the candidate list.\\n"
        "5. Allowed action is replace or create.\\n"
        "6. Return COMPLETE file content, not a diff fragment.\\n"
        "7. Python must compile.\\n"
        "8. Keep the change focused and under roughly 600 changed lines.\\n"
        "9. Never touch wallet, finance, payment, credentials, security, approvals, "
        "governance, connectors, deployment gates, supervisor code, or self-evolution guard code.\\n"
        "10. Prefer opportunity-to-execution conversion, reliability, validation, "
        "observability, recovery, or measurable progress.\\n\\n"
        "Return exactly this JSON shape:\\n"
        "{\\"path\\":\\"relative/file.py\\",\\"action\\":\\"replace\\",\\"content\\":\\"complete file contents\\"}\\n\\n"
        "Candidate files:\\n" + _json.dumps(candidates, indent=2)
    )

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

    rel = str(plan.get("path") or "").strip().replace(chr(92), "/")
    action = str(plan.get("action") or "replace").strip().lower()
    content = str(plan.get("content") or "")

    if not rel or not content.strip():
        return {"ok": False, "reason": "empty_direct_plan"}

    low = rel.lower()
    if (
        rel.startswith("/")
        or ".." in Path(rel).parts
        or rel in blocked_exact
        or any(word in low for word in blocked_words)
        or not rel.startswith(("companyos/", "companyos_modules/", "scripts/", "tests/"))
    ):
        return {
            "ok": False,
            "reason": "direct_plan_path_rejected",
            "path": rel,
        }

    target = wt / rel
    if action not in {"replace", "create"}:
        action = "replace" if target.exists() else "create"

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

    check = _subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(wt),
        text=True,
        capture_output=True,
        timeout=30,
    )
    changed = [
        line[3:].strip()
        for line in check.stdout.splitlines()
        if len(line) >= 4
    ]

    return {
        "ok": bool(changed),
        "status": "direct_candidate_written" if changed else "direct_candidate_no_change",
        "generator": "direct_fallback",
        "path": rel,
        "action": action,
        "changed_files": changed,
    }


"""

replacement = """
def generate(wt, goal):
    import subprocess as _subprocess

    script = wt / "scripts" / "companyos_adaptive_self_build.py"
    legacy = {"ok": False, "reason": "adaptive_self_build_missing"}

    if script.exists():
        fake_home = wt.parent / "home"
        fake_home.mkdir(parents=True, exist_ok=True)
        home_repo = fake_home / "companyos"
        if home_repo.exists() or home_repo.is_symlink():
            home_repo.unlink()
        home_repo.symlink_to(wt, target_is_directory=True)

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["COMPANYOS_SELF_BUILD_GOAL"] = goal
        env["COMPANYOS_SELF_BUILD_EXTERNAL_ACTIONS"] = "0"
        env["PYTHONPATH"] = os.pathsep.join([
            str(wt),
            str(wt / "scripts"),
            env.get("PYTHONPATH", ""),
        ]).strip(os.pathsep)

        try:
            proc = _subprocess.run(
                [sys.executable, str(script)],
                cwd=str(wt),
                env=env,
                text=True,
                capture_output=True,
                timeout=int(
                    os.getenv(
                        "COMPANYOS_SELF_EVOLUTION_GENERATION_TIMEOUT",
                        "420",
                    )
                ),
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

    status = _subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(wt),
        text=True,
        capture_output=True,
        timeout=30,
    )
    changed = [
        line[3:].strip()
        for line in status.stdout.splitlines()
        if len(line) >= 4
    ]

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

    fallback = _direct_generation_fallback(wt, goal)

    status2 = _subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(wt),
        text=True,
        capture_output=True,
        timeout=30,
    )
    changed_after = [
        line[3:].strip()
        for line in status2.stdout.splitlines()
        if len(line) >= 4
    ]

    return {
        "ok": bool(fallback.get("ok")) and bool(changed_after),
        "generator": "direct_fallback",
        "legacy": legacy,
        "fallback": fallback,
        "changed_files": changed_after,
    }


"""

prefix = s[:start]
if "def _direct_generation_fallback(" not in s:
    prefix += helper

p.write_text(prefix + replacement + s[end:])
print("PATCHED_GENERATE_WT_GOAL=YES")
PY

echo "[1/5] Syntax check..."
python -m py_compile companyos/runtime/self_evolution_engine.py

echo "[2/5] Guard tests..."
python -m unittest tests.test_self_evolution_guard

source "$HOME/.companyos_launch_env"

echo "[3/5] Secret scan..."
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

echo "[4/5] Commit/push..."
git add -- companyos/runtime/self_evolution_engine.py
if ! git diff --cached --quiet; then
  git commit -m "Fix no-op self-evolution generation fallback"
fi

BRANCH="$(git branch --show-current)"
if [ -n "$BRANCH" ]; then
  git push origin "$BRANCH" || echo "WARNING: push failed; local fix remains installed"
fi

echo "[5/5] Restart..."
if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi
sleep 5

echo
grep -n -E '^def _direct_generation_fallback|^def generate\\(' companyos/runtime/self_evolution_engine.py || true

echo
echo "COMPANYOS_SELF_EVOLUTION_GENERATION_FIX_V3=PASS"
echo "Next: scripts/companyos_evolutionctl once"
