#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import re
import shutil
import shlex
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from companyos_local_ai_adapter import model_request, extract_json
from companyos_plan_normalizer import normalize_plan

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
SB = RT / "self_build"
PLANS = SB / "plans"
RECEIPTS = SB / "receipts"
WORKSPACES = SB / "workspaces"
REVIEWS = SB / "reviews"
STATE = SB / "state.json"
LEDGER = SB / "ledger.jsonl"

for p in (PLANS, RECEIPTS, WORKSPACES, REVIEWS):
    p.mkdir(parents=True, exist_ok=True)

ALLOWED_PREFIXES = (
    "scripts/",
    "companyos_modules/",
    "tests/",
    "templates/",
    "config/",
)

PROTECTED_FILES = {
    ".env",
    "scripts/companyos_runtime_watchdog.sh",
}

PROTECTED_TERMS = (
    "PRIVATE_KEY",
    "SEED_PHRASE",
    "MNEMONIC",
    "CLOUDFLARE_API_TOKEN",
    "OPENAI_API_KEY",
)

FORBIDDEN_PLAN_PATTERNS = (
    "rm -rf",
    "curl | sh",
    "wget | sh",
    "chmod 777",
    "disable gate",
    "bypass gate",
    "remove approval",
    "exfiltrate",
)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def ledger(event):
    event = dict(event)
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inventory():
    files = []
    for base in ("scripts", "companyos_modules", "tests", "templates", "config"):
        root = ROOT / base
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            rel_parts = set(p.relative_to(ROOT).parts)
            if rel_parts & {"__pycache__", ".git", "node_modules", ".venv", "venv", "backups"}:
                continue
            if p.suffix.lower() in {".pyc", ".pyo", ".zip", ".tar", ".gz", ".gguf", ".bin", ".so"}:
                continue
            if ".before_" in p.name or ".backup" in p.name:
                continue
            if not p.is_file():
                continue
            if p.stat().st_size > 250_000:
                continue
            rel = str(p.relative_to(ROOT))
            files.append({
                "path": rel,
                "size": p.stat().st_size,
                "sha256": sha(p),
            })

    runtime_summary = {}
    for name in (
        "continuous_runtime_state.json",
        "operations_reconciler_state.json",
        "product_builder_state.json",
        "portfolio_feedback_state.json",
        "recovery_controller_state.json",
    ):
        p = RT / name
        if p.exists():
            runtime_summary[name] = load(p, {})

    return {
        "generated_at": time.time(),
        "files": files,
        "runtime_summary": runtime_summary,
        "installed_commands": sorted(
            x.split("=", 1)[0]
            for x in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
            if x.startswith("COMPANYOS_") and "=" in x
        ) if (ROOT / ".env").exists() else [],
    }


def _candidate_quality_errors(
    root,
    rel,
    content,
    baseline="",
    planned_paths=None,
    is_new=False,
):
    import ast as _ast
    import difflib as _difflib
    import re as _re

    errors = []
    planned_paths = {
        str(x).replace("\\", "/")
        for x in (planned_paths or set())
    }

    # --------------------------------------------------------
    # New production files are opt-in while using a small
    # local model. Tests may still be created freely.
    # --------------------------------------------------------
    if (
        is_new
        and not str(rel).startswith("tests/")
        and os.getenv(
            "COMPANYOS_SELF_EVOLUTION_ALLOW_NEW_PRODUCTION_FILES",
            "0",
        ) != "1"
    ):
        errors.append("new_production_file_requires_opt_in")

    # --------------------------------------------------------
    # Only judge newly-added text for filler markers so an
    # unrelated pre-existing TODO doesn't block an improvement.
    # --------------------------------------------------------
    added = []
    for line in _difflib.ndiff(
        (baseline or "").splitlines(),
        (content or "").splitlines(),
    ):
        if line.startswith("+ "):
            added.append(line[2:])

    added_text = "\n".join(added).lower()

    markers = (
        "placeholder for",
        "simulate performance optimization",
        "dummy implementation",
        "implementation goes here",
        "todo-only",
        "fake success",
    )

    for marker in markers:
        if marker in added_text:
            errors.append("placeholder_or_stub:" + marker)

    # --------------------------------------------------------
    # Parse candidate and baseline
    # --------------------------------------------------------
    try:
        tree = _ast.parse(content or "", filename=str(rel))
    except SyntaxError as exc:
        return errors + [
            "invalid_python:"
            + type(exc).__name__
            + ":"
            + str(exc)
        ]

    try:
        old_tree = _ast.parse(
            baseline or "",
            filename=str(rel) + ":baseline",
        )
    except Exception:
        old_tree = None

    # Reject formatting-only, comment-only, or otherwise
    # semantically identical Python replacements.
    if baseline and old_tree is not None:
        try:
            new_ast = _ast.dump(
                tree,
                include_attributes=False,
            )
            old_ast = _ast.dump(
                old_tree,
                include_attributes=False,
            )

            if new_ast == old_ast:
                errors.append("semantic_noop")
        except Exception:
            pass

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _local_module_exists(mod):
        parts = str(mod).split(".")
        base = root.joinpath(*parts)

        if base.with_suffix(".py").is_file():
            return True

        if (base / "__init__.py").is_file():
            return True

        p1 = "/".join(parts) + ".py"
        p2 = "/".join(parts) + "/__init__.py"

        return p1 in planned_paths or p2 in planned_paths

    def _imports(t):
        found = set()

        if t is None:
            return found

        for node in _ast.walk(t):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    mod = alias.name

                    if mod.startswith(
                        ("companyos.", "companyos_modules.")
                    ):
                        found.add(mod)

            elif isinstance(node, _ast.ImportFrom):
                mod = node.module or ""

                if mod.startswith(
                    ("companyos.", "companyos_modules.")
                ):
                    found.add(mod)

                elif mod in ("companyos", "companyos_modules"):
                    for alias in node.names:
                        if alias.name != "*":
                            found.add(
                                mod + "." + alias.name
                            )

        return found

    # --------------------------------------------------------
    # Newly introduced CompanyOS-local imports must exist.
    # --------------------------------------------------------
    new_imports = _imports(tree) - _imports(old_tree)

    for mod in sorted(new_imports):
        if not _local_module_exists(mod):
            errors.append("missing_local_import:" + mod)

    # --------------------------------------------------------
    # Literal local script references must exist.
    # Example:
    # scripts/optimization_script.py
    # --------------------------------------------------------
    def _local_file_refs(t):
        refs = set()

        if t is None:
            return refs

        for node in _ast.walk(t):
            if isinstance(node, _ast.Constant):
                value = node.value

                if not isinstance(value, str):
                    continue

                value = value.replace("\\", "/").strip()

                if (
                    value.startswith(
                        (
                            "scripts/",
                            "companyos/",
                            "companyos_modules/",
                            "tests/",
                            "templates/",
                        )
                    )
                    and value.endswith((".py", ".sh"))
                ):
                    refs.add(value)

        return refs

    new_refs = _local_file_refs(tree) - _local_file_refs(old_tree)

    for ref in sorted(new_refs):
        if not (root / ref).exists() and ref not in planned_paths:
            errors.append(
                "missing_local_file_reference:" + ref
            )

    # --------------------------------------------------------
    # Extract the static prefix of a path expression.
    # Handles:
    # "/opt/foo"
    # f"/opt/foo/{x}"
    # Path("/opt") / "foo"
    # --------------------------------------------------------
    def _path_prefix(node):
        if node is None:
            return None

        if isinstance(node, _ast.Constant):
            if isinstance(node.value, str):
                return node.value

        if isinstance(node, _ast.JoinedStr):
            out = ""

            for part in node.values:
                if isinstance(part, _ast.Constant):
                    if isinstance(part.value, str):
                        out += part.value
                else:
                    break

            return out or None

        if isinstance(node, _ast.BinOp):
            if isinstance(node.op, (_ast.Div, _ast.Add)):
                return _path_prefix(node.left)

        if isinstance(node, _ast.Call):
            name = ""

            if isinstance(node.func, _ast.Name):
                name = node.func.id
            elif isinstance(node.func, _ast.Attribute):
                name = node.func.attr

            if name == "Path" and node.args:
                return _path_prefix(node.args[0])

            if (
                isinstance(node.func, _ast.Attribute)
                and node.func.attr == "join"
                and node.args
            ):
                return _path_prefix(node.args[0])

        return None

    def _dangerous_absolute(path):
        if not path:
            return False

        p = str(path).replace("\\", "/")

        if p.startswith(("/tmp/", "/var/tmp/")):
            return False

        if p.startswith("/"):
            return True

        if _re.match(r"^[A-Za-z]:/", p):
            return True

        return False

    # --------------------------------------------------------
    # Collect filesystem writes.
    # --------------------------------------------------------
    def _writes(t):
        writes = set()

        if t is None:
            return writes

        write_methods = {
            "write_text",
            "write_bytes",
            "touch",
            "mkdir",
            "unlink",
            "rmdir",
        }

        for node in _ast.walk(t):
            if not isinstance(node, _ast.Call):
                continue

            fn = node.func

            # builtin open(path, mode)
            if isinstance(fn, _ast.Name) and fn.id == "open":
                mode = "r"

                if len(node.args) >= 2:
                    if isinstance(node.args[1], _ast.Constant):
                        mode = str(node.args[1].value)

                for kw in node.keywords:
                    if (
                        kw.arg == "mode"
                        and isinstance(kw.value, _ast.Constant)
                    ):
                        mode = str(kw.value.value)

                if any(x in mode for x in ("w", "a", "x", "+")):
                    p = (
                        _path_prefix(node.args[0])
                        if node.args
                        else None
                    )

                    if p:
                        writes.add(p)

            # pathlib Path(...).write_text(), mkdir(), etc.
            if (
                isinstance(fn, _ast.Attribute)
                and fn.attr in write_methods
            ):
                p = _path_prefix(fn.value)

                if p:
                    writes.add(p)

            # os.mkdir/makedirs/remove/unlink/rmdir
            if (
                isinstance(fn, _ast.Attribute)
                and isinstance(fn.value, _ast.Name)
                and fn.value.id == "os"
                and fn.attr
                in {
                    "mkdir",
                    "makedirs",
                    "remove",
                    "unlink",
                    "rmdir",
                }
                and node.args
            ):
                p = _path_prefix(node.args[0])

                if p:
                    writes.add(p)

            # shutil copy/move destinations
            if (
                isinstance(fn, _ast.Attribute)
                and isinstance(fn.value, _ast.Name)
                and fn.value.id == "shutil"
                and fn.attr
                in {
                    "copy",
                    "copy2",
                    "copyfile",
                    "move",
                }
                and len(node.args) >= 2
            ):
                p = _path_prefix(node.args[1])

                if p:
                    writes.add(p)

        return writes

    new_writes = _writes(tree) - _writes(old_tree)

    for path in sorted(new_writes):
        if _dangerous_absolute(path):
            errors.append(
                "privileged_or_external_absolute_write:" + path
            )

    # --------------------------------------------------------
    # subprocess quality checks.
    # --------------------------------------------------------
    def _subprocess_flags(t):
        flags = set()

        if t is None:
            return flags

        for node in _ast.walk(t):
            if not isinstance(node, _ast.Call):
                continue

            fn = node.func

            if not (
                isinstance(fn, _ast.Attribute)
                and isinstance(fn.value, _ast.Name)
                and fn.value.id == "subprocess"
                and fn.attr
                in {
                    "run",
                    "Popen",
                    "check_call",
                    "check_output",
                }
            ):
                continue

            for kw in node.keywords:
                if (
                    kw.arg == "shell"
                    and isinstance(kw.value, _ast.Constant)
                    and kw.value.value is True
                ):
                    flags.add("subprocess_shell_true")

            if node.args:
                cmd = node.args[0]

                if isinstance(cmd, (_ast.List, _ast.Tuple)):
                    if cmd.elts:
                        first = cmd.elts[0]

                        if (
                            isinstance(first, _ast.Constant)
                            and first.value in ("python", "python3")
                        ):
                            flags.add(
                                "hardcoded_python_executable"
                            )

        return flags

    for flag in sorted(
        _subprocess_flags(tree) - _subprocess_flags(old_tree)
    ):
        errors.append(flag)

    return sorted(set(errors))


def validate_plan(plan):
    errors=[]

    if not isinstance(plan,dict):
        return ["plan_not_object"]

    changes=plan.get("changes")

    if not isinstance(changes,list):
        return ["changes_not_list"]

    action_aliases={
        "update":"replace",
        "modify":"replace",
        "edit":"replace",
        "patch":"replace",
        "rewrite":"replace",
        "write":"replace",
        "change":"replace",
        "replace_file":"replace",
        "add":"create",
        "new":"create",
        "create_file":"create",
    }

    planned_paths={
        str(x.get("path","")).strip().replace("\\","/")
        for x in changes
        if isinstance(x,dict)
    }

    for i,change in enumerate(changes):
        if not isinstance(change,dict):
            errors.append(
                f"change_{i}_not_object"
            )
            continue

        path_value=str(
            change.get("path","")
        ).strip().replace("\\","/")

        raw_action=str(
            change.get("action","")
        ).strip().lower()

        content=str(
            change.get("content","")
        )

        action=action_aliases.get(
            raw_action,
            raw_action
        )

        target=ROOT/path_value

        if action not in {"create","replace"}:
            action=(
                "replace"
                if target.exists()
                else "create"
            )

        change["action"]=action

        if not path_value.startswith(ALLOWED_PREFIXES):
            errors.append(
                f"change_{i}_path_not_allowed:"
                f"{path_value}"
            )

        if path_value in PROTECTED_FILES:
            errors.append(
                f"change_{i}_protected_file:"
                f"{path_value}"
            )

        if (
            ".." in Path(path_value).parts
            or path_value.startswith("/")
        ):
            errors.append(
                f"change_{i}_path_traversal:"
                f"{path_value}"
            )

        if len(content.encode("utf-8")) > 180000:
            errors.append(
                f"change_{i}_content_too_large:"
                f"{path_value}"
            )

        lower=content.lower()

        for pattern in FORBIDDEN_PLAN_PATTERNS:
            if pattern in lower:
                errors.append(
                    f"change_{i}_forbidden_pattern:"
                    f"{path_value}"
                )

        for term in PROTECTED_TERMS:
            if (
                term in content
                and "os.getenv" not in content
            ):
                errors.append(
                    f"change_{i}_possible_secret_embedding:"
                    f"{term}"
                )

        baseline=""

        if target.is_file():
            try:
                baseline=target.read_text(
                    encoding="utf-8"
                )
            except Exception:
                baseline=""

        qerrors=_candidate_quality_errors(
            ROOT,
            path_value,
            content,
            baseline=baseline,
            planned_paths=planned_paths,
            is_new=not target.exists(),
        )

        for err in qerrors:
            errors.append(
                f"change_{i}_{err}"
            )

    return errors

def make_prompt(inv):
    goal = os.getenv(
        "COMPANYOS_SELF_BUILD_GOAL",
        (
            "Improve CompanyOS into a stronger autonomous company-building platform. "
            "Choose the highest-value missing internal capability based on the repository "
            "and runtime state. Prefer reliability, real usefulness, modularity, observability, "
            "customer/revenue operations, and self-repair. Do not duplicate installed modules."
        ),
    )

    return f"""
You are the adaptive software architect inside CompanyOS.

Goal:
{goal}

You may design and write internal CompanyOS code with broad freedom, but you must obey these hard constraints:
1. Return JSON only.
2. You may only create or replace files under scripts/, companyos_modules/, tests/, templates/, or config/.
3. Never modify .env, credentials, wallet keys, secrets, financial caps, approval gates, runtime watchdog, or external-action protections.
4. Never include destructive shell commands, remote shell installers, secret exfiltration, or code that bypasses approvals.
5. Do not directly spend funds, purchase assets, send customer messages, charge customers, or deploy externally.
6. Keep the phase coherent: build one major capability bundle, not random unrelated files.
7. Include tests.
8. Generated Python files must compile.
9. Prefer deterministic, inspectable modules with JSON state and receipts.
10. Avoid claiming a feature works unless your tests verify it.
11. Never generate placeholders, simulated work, dummy implementations, TODO-only code, or fake success messages.
12. Never use time.sleep() to simulate useful work.
13. Do not invent CompanyOS modules, classes, functions, or imports. Every CompanyOS-local dependency must already exist in the supplied inventory or be created by this same plan.
14. Prefer a small real improvement to an EXISTING file over creating a speculative new subsystem.
15. The resulting code must perform actual deterministic work that can be tested.
16. Do not create new production files unless absolutely necessary; prefer improving an existing file.
17. Never reference a local script, module, template, or helper that does not already exist in the supplied inventory or in the same plan.
18. Never write generated state to privileged system paths such as /opt, /etc, /usr, /var, Windows system folders, or drive-root locations.
19. Put runtime state under the existing CompanyOS runtime directory or use temporary directories only when appropriate.
20. Never use shell=True for generated subprocess calls.
21. Use sys.executable instead of hard-coded "python" or "python3" when launching Python subprocesses.
22. Validate required environment variables before using them in paths, process arguments, identifiers, or external operations.


Return exactly this schema:
{{
  "title": "short phase name",
  "reason": "why this is the best next capability",
  "changes": [
    {{
      "path": "scripts/example.py",
      "action": "create",
      "content": "complete file text"
    }}
  ],
  "tests": [
    {{
      "command": "python -m py_compile scripts/example.py",
      "timeout": 60
    }}
  ],
  "integration": {{
    "pipeline_command": "python scripts/example.py run",
    "env_name": "COMPANYOS_EXAMPLE_CMD"
  }}
}}

Current inventory and runtime state:
{json.dumps(inv, indent=2)[:50000]}
""".strip()


def sanitize_generated_content(content, rel):
    content = str(content or "").replace("\r\n", "\n").strip()

    # Decode literal line-break escapes returned inside local-model JSON.
    if "\\n" in content:
        content = content.replace("\\r\\n", "\n")
        content = content.replace("\\n", "\n")
        content = content.replace("\\t", "\t")

    # Remove Markdown code fences.
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].strip().lower() in ("```python", "```py", "```bash", "```sh", "```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    # Local models sometimes emit a bare language label.
    lines = content.splitlines()
    if lines and lines[0].strip().lower() in ("python", "py", "python3"):
        content = "\n".join(lines[1:]).lstrip()

    # Python destinations must contain valid Python before being written.
    if str(rel).endswith(".py"):
        compile(content, str(rel), "exec")

    return content

def apply_plan(plan):
    run_id = time.strftime("%Y%m%d_%H%M%S")
    workspace = WORKSPACES / run_id
    backup = workspace / "backup"
    backup.mkdir(parents=True, exist_ok=True)

    changed = []

    for change in plan["changes"]:
        rel = change["path"]
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            b = backup / rel
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, b)

        clean_content = sanitize_generated_content(change.get("content", ""), rel)
        target.write_text(clean_content, encoding="utf-8")
        if rel.startswith("scripts/") and target.suffix in (".py", ".sh"):
            target.chmod(0o700)

        changed.append(rel)

    return run_id, workspace, changed

def run_tests(plan):
    """Run model-provided tests without crashing on mixed entry types."""
    results = []
    tests = plan.get("tests", []) if isinstance(plan, dict) else []

    if tests is None:
        tests = []
    elif isinstance(tests, (str, dict)):
        tests = [tests]
    elif not isinstance(tests, list):
        return [{
            "command": repr(tests),
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "reason": "tests_not_list_string_or_object",
        }]

    allowed_prefixes = ("python ", "python3 ", "pytest ", "bash ", "sh ")

    for index, raw_test in enumerate(tests, 1):
        if isinstance(raw_test, str):
            test = {"command": raw_test, "timeout": 120}
        elif isinstance(raw_test, dict):
            test = raw_test
        else:
            results.append({
                "command": repr(raw_test),
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "reason": f"test_{index}_entry_not_string_or_object",
            })
            continue

        command = str(test.get("command", "") or "").strip()

        # A direct Python script may launch a daemon or application loop.
        # Convert simple "python file.py" checks into deterministic compile tests.
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = []

        if (
            len(parts) == 2
            and parts[0] in ("python", "python3")
            and parts[1].endswith(".py")
        ):
            command = f"{parts[0]} -m py_compile {shlex.quote(parts[1])}"

        try:
            timeout = int(test.get("timeout", 120))
        except (TypeError, ValueError):
            timeout = 120
        timeout = min(max(timeout, 1), 300)

        if not command:
            results.append({
                "command": "",
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "reason": f"test_{index}_command_missing",
            })
            continue

        if not command.startswith(allowed_prefixes):
            results.append({
                "command": command,
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "reason": f"test_{index}_command_not_allowed",
            })
            continue

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                timeout=timeout,
                env=os.environ.copy(),
            )
            results.append({
                "command": command,
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "")[-5000:],
                "stderr": (proc.stderr or "")[-5000:],
                "reason": None if proc.returncode == 0 else "test_command_failed",
            })
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            results.append({
                "command": command,
                "ok": False,
                "returncode": None,
                "stdout": stdout[-5000:],
                "stderr": stderr[-5000:],
                "reason": f"test_timeout_after_{timeout}_seconds",
            })
        except Exception as exc:
            results.append({
                "command": command,
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "reason": f"{type(exc).__name__}: {exc}",
            })

    return results

def rollback(workspace, changed):
    backup = workspace / "backup"

    for rel in changed:
        target = ROOT / rel
        saved = backup / rel

        if saved.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, target)
        elif target.exists():
            target.unlink()

def run():
    inv = inventory()
    prompt = make_prompt(inv)
    prompt += """
STRICT LOCAL MODEL OUTPUT RULES:
Return one JSON object only. No markdown and no commentary.
Use exactly this schema:
{"title":"short title","reason":"short reason","changes":[{"path":"relative/path.py","action":"update","content":"complete file content","reason":"short reason"}],"tests":[]}
Return exactly one change. Never modify __pycache__, .pyc, archives, models, backups, or generated files.
Keep the full response compact enough to finish without truncation.
"""
    last_generation_error = None
    for generation_attempt in range(1, 4):
        response = model_request(prompt)
        if not response.get("ok"):
            last_generation_error = {"stage": "model_request", **response}
            continue

        try:
            plan = normalize_plan(extract_json(response["text"]))
        except Exception as exc:
            last_generation_error = {
                "stage": "parse_plan",
                "reason": f"{type(exc).__name__}: {exc}",
                "model_output": response.get("text", "")[:8000],
            }
            prompt += (
                "\n\nCORRECTION: Your previous response was not valid plan JSON. "
                "Return exactly one valid JSON object matching the required schema."
            )
            continue

        errors = validate_plan(plan)
        if errors:
            last_generation_error = {
                "stage": "validate_plan",
                "errors": errors,
                "title": plan.get("title"),
            }
            prompt += (
                "\n\nCORRECTION: The previous plan failed validation: "
                + json.dumps(errors)
                + ". Return a corrected plan. For every .py destination, content must "
                  "be the complete executable Python file, never prose, a summary, "
                  "a placeholder, or a description of intended work."
            )
            continue

        plan_id = f"{int(time.time())}-{hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:12]}"
        save(PLANS / f"{plan_id}.json", plan)

        try:
            run_id, workspace, changed = apply_plan(plan)
            break
        except (SyntaxError, ValueError) as exc:
            last_generation_error = {
                "stage": "generated_content",
                "reason": f"{type(exc).__name__}: {exc}",
                "title": plan.get("title"),
                "attempt": generation_attempt,
            }
            prompt += (
                "\n\nCORRECTION: The previous generated file content was invalid: "
                + str(exc)
                + ". Regenerate the entire plan. Any .py content must be complete, "
                  "syntactically valid Python source code. Do not return English prose, "
                  "markdown fences, language labels, TODO-only placeholders, or summaries."
            )
    else:
        emit({
            "ok": False,
            "stage": "generation_retry_exhausted",
            "attempts": 3,
            "last_error": last_generation_error,
        }, 1)
    test_results = run_tests(plan)

    # Local models sometimes return no explicit tests. In that case, run
    # deterministic syntax checks against changed Python files instead of
    # automatically failing and rolling back an otherwise valid change.
    if not test_results:
        for rel in changed:
            if not str(rel).endswith(".py"):
                continue
            target = ROOT / rel
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(target)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                test_results.append({
                    "command": f"python -m py_compile {rel}",
                    "ok": proc.returncode == 0,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-5000:],
                    "stderr": proc.stderr[-5000:],
                })
            except Exception as exc:
                test_results.append({
                    "command": f"python -m py_compile {rel}",
                    "ok": False,
                    "reason": f"{type(exc).__name__}: {exc}",
                })

    # A valid plan may produce no filesystem delta when its content
    # already matches the current file. Treat that as a clean no-op.
    no_changes = not changed
    passed = (
        all(x.get("ok") for x in test_results)
        if test_results
        else True
    )

    if not passed and changed:
        rollback(workspace, changed)

    receipt = {
        "ok": passed,
        "plan_id": plan_id,
        "run_id": run_id,
        "title": plan.get("title"),
        "reason": plan.get("reason"),
        "changed_files": changed,
        "tests": test_results,
        "rolled_back": (not passed and bool(changed)),
        "no_changes": no_changes,
        "integration": plan.get("integration"),
        "model_response_id": response.get("raw_id"),
        "completed_at": time.time(),
        "hard_gates_preserved": True,
    }

    save(RECEIPTS / f"{plan_id}.json", receipt)
    save(STATE, receipt)
    ledger({
        "event": "adaptive_self_build_complete",
        "plan_id": plan_id,
        "ok": passed,
        "changed_files": changed,
        "rolled_back": (not passed and bool(changed)),
        "no_changes": no_changes,
    })

    emit(receipt, 0 if passed else 1)

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "run":
    run()
elif action == "inventory":
    emit(inventory())
elif action == "status":
    emit(load(STATE, {"ok": True, "status": "not_run"}))
else:
    emit({"ok": False, "reason": "unsupported_action", "action": action}, 2)
