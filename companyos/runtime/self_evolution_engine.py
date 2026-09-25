from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"; EV=RT/"self_evolution"
WT=EV/"worktrees"; RC=EV/"receipts"; BK=EV/"promotion_backups"; STATE=EV/"state.json"; LEDGER=EV/"ledger.jsonl"
for p in (EV,WT,RC,BK): p.mkdir(parents=True,exist_ok=True)

SAFE_PREFIXES=("companyos/","companyos_modules/","scripts/","tests/","templates/")
EXACT_PROTECTED={
 "companyos/runtime/self_evolution_engine.py","companyos/runtime/self_evolution_runtime.py",
 "companyos/runtime/self_evolution_hypothesis.py",
 "companyos/runtime/self_evolution_backtest.py",
 "companyos/runtime/self_evolution_probe_contract.py",
 "companyos/runtime/service_supervisor.py","companyos/runtime/runtime_control.py",
 "scripts/companyos_evolutionctl","scripts/companyos_adaptive_self_build.py",
}

# COMPANYOS_V69_35I_HOST_OPTIMIZATION_ALLOWLIST
HOST_OPTIMIZATION_FILES={
 "companyos/runtime/authorized_local_migration_controller.py",
 "companyos/runtime/local_primary_registry.py",
 "companyos/runtime/local_lan_host_discovery.py",
 "companyos/runtime/local_host_capability_classifier.py",
 "companyos/runtime/remote_runtime_fabric.py",
 "companyos/runtime/hybrid_compute_mesh_controller.py",
 "companyos/runtime/distributed_compute_scheduler.py",
 "companyos/runtime/persistent_host_scout.py",
 "companyos/runtime/adaptive_offload_calibration_resumer.py",
}
PROTECTED_WORDS=("wallet","finance","banking","payment","credential","secret","security","auth","approval","governance","guardrail","policy_gate","deployment_gate","connector","solana","private_key")
PROTECTED_TERMS=("OPENAI_API_KEY","CLOUDFLARE_API_TOKEN","SOLANA_PRIVATE_KEY","SMTP_PASSWORD","SEED_PHRASE","MNEMONIC","COMPANYOS_DAILY_FINANCE_CAP_USD","COMPANYOS_SINGLE_FINANCE_CAP_USD","COMPANYOS_ENABLE_LIVE_FINANCE")
FORBIDDEN=("rm -rf","chmod 777","curl | sh","wget | sh","disable gate","bypass gate","remove approval","ignore approval","exfiltrate")
MAX_FILES=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_FILES","4")); MAX_LINES=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_LINES","600")); MAX_DAILY=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_DAILY_PROPOSALS","4"))

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); t.replace(p)

def ledger(event,**kw):
    with LEDGER.open("a") as f:f.write(json.dumps({"ts":time.time(),"iso":datetime.now(timezone.utc).isoformat(),"event":event,**kw},sort_keys=True)+"\n")

def run(a,cwd=ROOT,timeout=180,env=None):
    return subprocess.run(a,cwd=str(cwd),env=env or os.environ.copy(),text=True,capture_output=True,timeout=timeout)

def git(a,cwd=ROOT,timeout=120):return run(["git",*a],cwd,timeout)

def dirty(cwd=ROOT):
    out=set()
    for x in git(["status","--porcelain=v1"],cwd).stdout.splitlines():
        if len(x)>=4:
            p=x[3:].split(" -> ")[-1].strip(); out.add(p)
    return out

def path_allowed(rel):
    rel=str(rel).replace("\\","/").lstrip("./"); parts=Path(rel).parts; low=rel.lower()
    if not rel or rel.startswith("/") or ".." in parts:return False,"path_traversal"
    if rel.startswith((".git/",".github/","config/")):return False,"protected_top_level"
    if rel in EXACT_PROTECTED:return False,"exact_protected"
    if rel in HOST_OPTIMIZATION_FILES:return True,"authorized_host_optimization"
    if any(w in low for w in PROTECTED_WORDS):return False,"protected_path_word"
    if not rel.startswith(SAFE_PREFIXES):return False,"outside_safe_prefix"
    if rel.endswith((".pyc",".pyo",".so",".bin",".zip",".tar",".gz")):return False,"binary_or_archive"
    return True,"allowed"

def changed(cwd):
    a=[x.strip() for x in git(["diff","--name-only","HEAD"],cwd).stdout.splitlines() if x.strip()]
    a += [x.strip() for x in git(["ls-files","--others","--exclude-standard"],cwd).stdout.splitlines() if x.strip()]
    return sorted(set(a))

def guard(cwd,files):
    errors=[]
    if not files:errors.append("no_changes")
    if len(files)>MAX_FILES:errors.append(f"too_many_files:{len(files)}>{MAX_FILES}")
    for rel in files:
        ok,why=path_allowed(rel)
        if not ok:errors.append(f"path_rejected:{rel}:{why}")
    diff=git(["diff","--no-ext-diff","--unified=0","HEAD"],cwd).stdout
    for rel in files:
        if git(["ls-files","--error-unmatch",rel],cwd).returncode!=0:
            p=cwd/rel
            if p.is_file():
                try:diff += "\n+++ "+rel+"\n"+"\n".join("+"+x for x in p.read_text().splitlines())
                except:errors.append(f"unreadable:{rel}")
    lines=sum(1 for x in diff.splitlines() if x[:1] in "+-" and not x.startswith(("+++","---")))
    if lines>MAX_LINES:errors.append(f"too_many_changed_lines:{lines}>{MAX_LINES}")
    low=diff.lower()
    for x in FORBIDDEN:
        if x in low:errors.append("forbidden_fragment:"+x)
    for term in PROTECTED_TERMS:
        if any(x[:1] in "+-" and term in x for x in diff.splitlines()):errors.append("protected_control_touched:"+term)
    return {"ok":not errors,"errors":errors,"changed_files":files,"changed_lines":lines}

def diagnose():
    sup=load(
        RT/"service_supervisor_state.json",
        {},
    )
    profit=load(
        RT/"profit_opportunity_runtime_state.json",
        {},
    )

    services=sup.get("services") or {}
    issues=[]
    sh={}

    for name,row in services.items():
        sh[name]={
            "running":bool(row.get("running")),
            "restarts":int(row.get("restarts") or 0),
            "consecutive_failures":int(
                row.get("consecutive_failures") or 0
            ),
        }

        if not row.get("running"):
            issues.append(
                "service_not_running:"+name
            )

        if int(row.get("consecutive_failures") or 0):
            issues.append(
                "service_failures:"+name
            )

    host_objective=None

    try:
        from companyos.runtime.host_optimization_objective import (
            build_objective,
        )
        host_objective=build_objective()
    except Exception:
        host_objective=None

    protected=(
        " Preserve existing security, credential, approval, "
        "finance, wallet, deployment, connector, and "
        "self-evolution protections."
    )

    portfolio=[
        {
            "domain":"execution_throughput",
            "goal":(
                "Improve deterministic CompanyOS execution throughput. "
                "Reduce avoidable queue delay, stalled work, redundant work, "
                "or poor task handoff while preserving public contracts."
                + protected
            ),
        },
        {
            "domain":"opportunity_conversion",
            "goal":(
                "Improve the conversion of researched opportunities into "
                "concrete executable business work with measurable outcomes, "
                "clear completion state, and useful feedback."
                + protected
            ),
        },
        {
            "domain":"agent_coordination",
            "goal":(
                "Improve coordination between CompanyOS workers and agents. "
                "Reduce duplicate work, improve ownership, dependency handling, "
                "handoffs, retry behavior, and useful completion."
                + protected
            ),
        },
        {
            "domain":"recovery_resilience",
            "goal":(
                "Improve CompanyOS recovery, idempotency, failure handling, "
                "state consistency, restart resilience, and observability "
                "without hiding failures."
                + protected
            ),
        },
        {
            "domain":"research_evidence",
            "goal":(
                "Improve how CompanyOS turns research and evidence into "
                "higher-quality actionable decisions. Improve validation, "
                "ranking, evidence linkage, or decision closure."
                + protected
            ),
        },
        {
            "domain":"operational_efficiency",
            "goal":(
                "Improve useful work per unit of CPU, memory, storage, or "
                "worker capacity. Remove unnecessary repeated processing and "
                "improve bounded scheduling or state access."
                + protected
            ),
        },
    ]

    if (
        isinstance(host_objective,dict)
        and host_objective.get("recommended_goal")
    ):
        portfolio.append({
            "domain":"host_compute",
            "goal":host_objective[
                "recommended_goal"
            ],
        })

    if issues:
        domain="runtime_reliability"
        goal=(
            "Improve reliability around observed runtime issues: "
            + ", ".join(issues[:8])
            + ". Diagnose root causes, preserve existing contracts, "
              "and make failure handling measurable."
            + protected
        )
    else:
        # Rotate domains across proposals instead of optimizing the
        # same subsystem indefinitely.
        slot=today_count() % len(portfolio)
        selected=portfolio[slot]
        domain=selected["domain"]
        goal=selected["goal"]

    return {
        "generated_at":time.time(),
        "services":sh,
        "issues":issues,
        "profit_state_present":bool(profit),
        "host_optimization":host_objective,
        "adaptation_domain":domain,
        "adaptation_portfolio":[
            row["domain"]
            for row in portfolio
        ],
        "recommended_goal":goal,
        "dirty_files":len(dirty()),
    }

def today_count():
    day=datetime.now(timezone.utc).date().isoformat(); n=0
    if LEDGER.exists():
        for x in LEDGER.read_text(errors="replace").splitlines():
            try:r=json.loads(x); n += int(r.get("event")=="proposal_started" and str(r.get("iso","")).startswith(day))
            except:pass
    return n


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
    # Behavioral-impact gate.
    #
    # Reject candidates that only add labels, strings, statuses,
    # or declarative steps while leaving executable behavior
    # unchanged.
    # --------------------------------------------------------
    if baseline and old_tree is not None:

        def _behavior_profile(t):
            tracked=(
                _ast.Call,
                _ast.If,
                _ast.For,
                _ast.AsyncFor,
                _ast.While,
                _ast.Try,
                _ast.With,
                _ast.AsyncWith,
                _ast.Raise,
                _ast.Assert,
                _ast.Compare,
                _ast.BinOp,
                _ast.BoolOp,
                _ast.UnaryOp,
                _ast.Assign,
                _ast.AnnAssign,
                _ast.AugAssign,
                _ast.NamedExpr,
                _ast.Await,
                _ast.Yield,
                _ast.YieldFrom,
            )

            result={}

            for node in _ast.walk(t):
                if isinstance(node,tracked):
                    name=type(node).__name__
                    result[name]=result.get(name,0)+1

            return result

        def _strings(t):
            return {
                node.value
                for node in _ast.walk(t)
                if (
                    isinstance(node,_ast.Constant)
                    and isinstance(node.value,str)
                )
            }

        old_behavior=_behavior_profile(old_tree)
        new_behavior=_behavior_profile(tree)

        added_strings=_strings(tree)-_strings(old_tree)

        if (
            added_strings
            and old_behavior == new_behavior
        ):
            errors.append(
                "low_behavioral_impact:"
                "string_or_label_only_change"
            )

        # ----------------------------------------------------
        # Capability-novelty gate.
        #
        # Pure restructures of equivalent logic are not useful
        # autonomous improvements.
        # ----------------------------------------------------

        from collections import Counter as _Counter

        def _call_name(node):
            fn=node.func

            if isinstance(fn,_ast.Name):
                return fn.id

            if isinstance(fn,_ast.Attribute):
                parts=[fn.attr]
                cur=fn.value

                while isinstance(cur,_ast.Attribute):
                    parts.append(cur.attr)
                    cur=cur.value

                if isinstance(cur,_ast.Name):
                    parts.append(cur.id)

                return ".".join(reversed(parts))

            return type(fn).__name__

        def _capability_profile(t):
            calls=_Counter()
            comparisons=_Counter()

            state_writes=0
            raises=0
            try_blocks=0
            awaits=0
            yields=0
            assertions=0

            for node in _ast.walk(t):

                if isinstance(node,_ast.Call):
                    calls[_call_name(node)]+=1

                elif isinstance(
                    node,
                    (_ast.Attribute,_ast.Subscript),
                ):
                    if isinstance(
                        getattr(node,"ctx",None),
                        _ast.Store,
                    ):
                        state_writes+=1

                elif isinstance(node,_ast.Raise):
                    raises+=1

                elif isinstance(node,_ast.Try):
                    try_blocks+=1

                elif isinstance(node,_ast.Await):
                    awaits+=1

                elif isinstance(
                    node,
                    (_ast.Yield,_ast.YieldFrom),
                ):
                    yields+=1

                elif isinstance(node,_ast.Assert):
                    assertions+=1

                elif isinstance(node,_ast.Compare):
                    for op in node.ops:
                        comparisons[
                            type(op).__name__
                        ]+=1

            return {
                "calls":calls,
                "comparisons":comparisons,
                "state_writes":state_writes,
                "raises":raises,
                "try_blocks":try_blocks,
                "awaits":awaits,
                "yields":yields,
                "assertions":assertions,
            }

        old_cap=_capability_profile(old_tree)
        new_cap=_capability_profile(tree)

        capability_gain=False

        for name,count in new_cap["calls"].items():
            if count > old_cap["calls"].get(name,0):
                capability_gain=True

        for name,count in new_cap["comparisons"].items():
            if count > old_cap["comparisons"].get(name,0):
                capability_gain=True

        for key in (
            "state_writes",
            "raises",
            "try_blocks",
            "awaits",
            "yields",
            "assertions",
        ):
            if new_cap[key] > old_cap[key]:
                capability_gain=True

        if not capability_gain:
            errors.append(
                "low_capability_novelty:"
                "no_new_executable_effect_detected"
            )

 # --------------------------------------------------------
    # Preserve obvious command/status output contracts.
    #
    # If an existing script unconditionally emits JSON at
    # module level, an autonomous candidate may not move that
    # output behind a branch or replace it with plain text.
    # --------------------------------------------------------
    def _top_level_json_print(t):
        if t is None:
            return False

        for node in getattr(t, "body", []):
            if not isinstance(node, _ast.Expr):
                continue

            call=node.value

            if not (
                isinstance(call, _ast.Call)
                and isinstance(call.func, _ast.Name)
                and call.func.id == "print"
            ):
                continue

            for child in _ast.walk(call):
                if (
                    isinstance(child, _ast.Call)
                    and isinstance(
                        child.func,
                        _ast.Attribute,
                    )
                    and child.func.attr == "dumps"
                    and isinstance(
                        child.func.value,
                        _ast.Name,
                    )
                    and child.func.value.id == "json"
                ):
                    return True

        return False

    if (
        old_tree is not None
        and _top_level_json_print(old_tree)
        and not _top_level_json_print(tree)
    ):
        errors.append(
            "public_output_contract_changed:"
            "top_level_json_output_removed_or_guarded"
        )

 # --------------------------------------------------------
    # Runtime object-contract gate.
    #
    # Reject newly-read self attributes unless they existed
    # already, are assigned by the candidate, or are methods
    # defined by the candidate class.
    # --------------------------------------------------------
    if baseline and old_tree is not None:

        def _self_attributes(t):
            reads=set()
            writes=set()

            for node in _ast.walk(t):
                if not isinstance(
                    node,
                    _ast.Attribute,
                ):
                    continue

                if not (
                    isinstance(
                        node.value,
                        _ast.Name,
                    )
                    and node.value.id=="self"
                ):
                    continue

                if isinstance(
                    getattr(
                        node,
                        "ctx",
                        None,
                    ),
                    _ast.Store,
                ):
                    writes.add(
                        node.attr
                    )
                else:
                    reads.add(
                        node.attr
                    )

            return reads,writes

        def _methods(t):
            result=set()

            for node in getattr(
                t,
                "body",
                [],
            ):
                if not isinstance(
                    node,
                    _ast.ClassDef,
                ):
                    continue

                for child in node.body:
                    if isinstance(
                        child,
                        (
                            _ast.FunctionDef,
                            _ast.AsyncFunctionDef,
                        ),
                    ):
                        result.add(
                            child.name
                        )

            return result

        old_reads,old_writes=(
            _self_attributes(
                old_tree
            )
        )

        new_reads,new_writes=(
            _self_attributes(
                tree
            )
        )

        baseline_known=(
            old_reads
            | old_writes
            | _methods(old_tree)
        )

        candidate_defined=(
            new_writes
            | _methods(tree)
        )

        for attr in sorted(
            new_reads
            - baseline_known
            - candidate_defined
        ):
            errors.append(
                "introduced_unbound_self_attribute:"
                + attr
            )

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


def tests(cwd,files):
    rows=[]

    for rel in files:
        p=cwd/rel

        if not rel.endswith(".py") or not p.exists():
            continue

        content=p.read_text(errors="replace")

        baseline=""

        rbase=git(
            ["show",f"HEAD:{rel}"],
            cwd
        )

        if rbase.returncode==0:
            baseline=rbase.stdout or ""

        is_new=(
            git(
                ["ls-files","--error-unmatch",rel],
                cwd
            ).returncode != 0
        )

        quality_errors=_candidate_quality_errors(
            cwd,
            rel,
            content,
            baseline=baseline,
            planned_paths=set(files),
            is_new=is_new,
        )

        rows.append({
            "name":"runtime_quality:"+rel,
            "ok":not quality_errors,
            "stderr":"; ".join(quality_errors),
        })

        r=run(
            [sys.executable,"-m","py_compile",rel],
            cwd,
            60
        )

        rows.append({
            "name":"compile:"+rel,
            "ok":r.returncode==0,
            "stderr":(r.stderr or "")[-1200:],
        })

    if (cwd/"tests/test_self_evolution_guard.py").exists():
        r=run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_self_evolution_guard",
            ],
            cwd,
            90
        )

        rows.append({
            "name":"guard_tests",
            "ok":r.returncode==0,
            "stderr":(r.stderr or "")[-1800:],
        })

    if os.getenv(
        "COMPANYOS_SELF_EVOLUTION_FULL_TESTS",
        "1",
    )=="1":
        r=run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test*.py",
            ],
            cwd,
            int(
                os.getenv(
                    "COMPANYOS_SELF_EVOLUTION_TEST_TIMEOUT",
                    "240",
                )
            ),
        )

        rows.append({
            "name":"unittest_discovery",
            "ok":r.returncode==0,
            "stdout":(r.stdout or "")[-1200:],
            "stderr":(r.stderr or "")[-1800:],
        })

    return {
        "ok":all(x["ok"] for x in rows) if rows else True,
        "results":rows,
    }

def shadow(run_id):
    branch="companyos-evolution/"+run_id; parent=WT/run_id; wt=parent/"companyos"
    shutil.rmtree(parent,ignore_errors=True); parent.mkdir(parents=True,exist_ok=True)
    r=git(["worktree","add","-b",branch,str(wt),"HEAD"])
    if r.returncode:raise RuntimeError("worktree add failed: "+(r.stderr or r.stdout)[-1500:])
    return wt,branch

def cleanup(wt,branch,keep=False):
    git(["worktree","remove","--force",str(wt)])
    if not keep:git(["branch","-D",branch])


def _direct_generation_fallback(wt, goal):
    import ast as _ast
    import re as _re
    import subprocess as _subprocess
    import sys as _sys

    from companyos.runtime.self_evolution_hypothesis import (
        progress_event,
        propose_hypothesis,
    )

    scripts_dir=ROOT/"scripts"

    if str(scripts_dir) not in _sys.path:
        _sys.path.insert(
            0,
            str(scripts_dir),
        )

    try:
        from companyos_local_ai_adapter import (
            model_request,
        )
    except Exception as exc:
        return {
            "ok":False,
            "reason":"adapter_import_failed",
            "error":(
                f"{type(exc).__name__}: {exc}"
            ),
        }

    local_attempts=max(
        3,
        min(
            8,
            int(
                os.getenv(
                    "COMPANYOS_LOCAL_EVOLUTION_ATTEMPTS",
                    "5",
                )
            ),
        ),
    )

    target_budget=max(
        1,
        min(
            8,
            int(
                os.getenv(
                    "COMPANYOS_LOCAL_EVOLUTION_TARGETS_PER_CYCLE",
                    "4",
                )
            ),
        ),
    )

    max_source_bytes=max(
        750,
        min(
            8000,
            int(
                os.getenv(
                    "COMPANYOS_LOCAL_EVOLUTION_MAX_SOURCE_BYTES",
                    "3000",
                )
            ),
        ),
    )

    stop_words={
        "companyos",
        "improve",
        "improvement",
        "autonomously",
        "optimize",
        "optimization",
        "existing",
        "authorized",
        "every",
        "candidate",
        "modify",
        "modules",
        "tests",
        "preserve",
        "current",
        "system",
        "runtime",
    }

    goal_terms=[
        x
        for x in _re.findall(
            r"[a-z0-9_]{4,}",
            str(goal).lower(),
        )
        if x not in stop_words
    ]

    # --------------------------------------------------------
    # Learn from previous evolution receipts.
    # Repeatedly failing targets receive a temporary penalty.
    # Previously successful targets remain eligible.
    # --------------------------------------------------------

    history={}

    def _receipt_target(row):
        generation=(
            row.get("generation")
            if isinstance(row,dict)
            else None
        ) or {}

        possibilities=[]

        for key in ("targeted","fallback"):
            value=generation.get(key)

            if isinstance(value,dict):
                possibilities.append(value)

                nested=value.get("targeted")
                if isinstance(nested,dict):
                    possibilities.append(nested)

        for value in possibilities:
            target=(
                value.get("path")
                or value.get("target")
            )

            if target:
                return (
                    str(target),
                    value.get("last_error"),
                )

        return None,None

    try:
        receipt_files=sorted(
            RC.glob("*.json"),
            key=lambda x:x.stat().st_mtime,
            reverse=True,
        )[:80]
    except Exception:
        receipt_files=[]

    failure_statuses={
        "generation_failed",
        "candidate_tests_failed",
        "candidate_rejected_by_guard",
        "candidate_commit_failed",
        "exception",
    }

    success_statuses={
        "qualified_pending_promotion",
        "qualified_pending_overlap",
        "promoted",
        "promoted_push_pending",
    }

    for receipt_path in receipt_files:
        try:
            row=load(receipt_path,{})
            target,last_error=_receipt_target(row)

            if not target:
                continue

            h=history.setdefault(
                target,
                {
                    "failures":0,
                    "successes":0,
                    "last_ts":0.0,
                    "last_error":None,
                },
            )

            status=str(
                row.get("status") or ""
            )

            if status in failure_statuses:
                h["failures"]+=1

            if status in success_statuses:
                h["successes"]+=1

            ts=float(
                row.get("finished_at")
                or receipt_path.stat().st_mtime
            )

            if ts > h["last_ts"]:
                h["last_ts"]=ts
                h["last_error"]=last_error

        except Exception:
            continue

    # --------------------------------------------------------
    # Discover eligible real source targets.
    # --------------------------------------------------------

    candidates=[]

    for base in (
        "companyos",
        "companyos_modules",
        "scripts",
    ):
        root=wt/base

        if not root.exists():
            continue

        for fp in root.rglob("*.py"):
            try:
                rel=str(
                    fp.relative_to(wt)
                ).replace("\\","/")

                if rel.startswith("tests/"):
                    continue

                ok,_=path_allowed(rel)

                if not ok:
                    continue

                size=fp.stat().st_size

                if not (
                    250 <= size <= max_source_bytes
                ):
                    continue

                low=rel.lower()

                try:
                    source_text=fp.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )

                    source_tree=_ast.parse(
                        source_text,
                        filename=rel,
                    )

                    behavioral_nodes=(
                        _ast.Call,
                        _ast.If,
                        _ast.For,
                        _ast.AsyncFor,
                        _ast.While,
                        _ast.Try,
                        _ast.With,
                        _ast.AsyncWith,
                        _ast.Raise,
                        _ast.Assert,
                        _ast.Compare,
                        _ast.BinOp,
                        _ast.BoolOp,
                        _ast.Assign,
                        _ast.AugAssign,
                        _ast.Await,
                    )

                    behavior_score=sum(
                        1
                        for node in _ast.walk(
                            source_tree
                        )
                        if isinstance(
                            node,
                            behavioral_nodes,
                        )
                    )

                except Exception:
                    behavior_score=0

                score=sum(
                    3
                    for term in goal_terms
                    if term in low
                )

                for hint in (
                    "host",
                    "worker",
                    "compute",
                    "execution",
                    "performance",
                    "recovery",
                    "runtime",
                    "task",
                    "state",
                    "research",
                    "opportunity",
                    "agent",
                    "queue",
                    "outcome",
                    "evidence",
                ):
                    if (
                        hint in str(goal).lower()
                        and hint in low
                    ):
                        score+=2

                h=history.get(rel,{})
                failures=int(
                    h.get("failures") or 0
                )
                successes=int(
                    h.get("successes") or 0
                )

                effective=score

                # Prefer modules with actual executable behavior
                # over tiny declarative/static planners.
                effective+=min(
                    10,
                    behavior_score,
                )

                # Learn from repeated failures without permanently
                # banning a target.
                effective-=min(
                    12,
                    failures*3,
                )

                # A history of valid changes is a mild positive.
                effective+=min(
                    3,
                    successes,
                )

                last_ts=float(
                    h.get("last_ts") or 0
                )

                age=(
                    time.time()-last_ts
                    if last_ts
                    else None
                )

                # Encourage exploration after a recent attempt.
                if age is not None:
                    if age < 21600:
                        effective-=8
                    elif age < 86400:
                        effective-=4

                candidates.append({
                    "path":rel,
                    "size":size,
                    "score":score,
                    "effective_score":effective,
                    "behavior_score":behavior_score,
                    "history":h,
                })

            except Exception:
                continue

    if not candidates:
        return {
            "ok":False,
            "reason":"no_existing_safe_candidate",
        }

    candidates.sort(
        key=lambda x:(
            -x["effective_score"],
            -x["behavior_score"],
            x["size"],
            x["path"],
        )
    )

    # Rotate through a pool of strong candidates so identical
    # healthy cycles don't keep selecting the same smallest file.
    pool_size=min(
        len(candidates),
        max(
            target_budget*3,
            8,
        ),
    )

    pool=candidates[:pool_size]

    if pool:
        offset=today_count() % len(pool)
        pool=(
            pool[offset:]
            + pool[:offset]
        )

    selected_targets=pool[:target_budget]
    attempted_targets=[]

    def _clean_generated_python(text):
        text=str(text or "").strip()

        fenced=_re.search(
            r"```(?:python|py)?[ \t]*\r?\n"
            r"(.*?)```",
            text,
            flags=(
                _re.IGNORECASE
                | _re.DOTALL
            ),
        )

        if fenced:
            text=fenced.group(1).strip()

        low=text.lower()

        if low.startswith("python\n"):
            text=text.split(
                "\n",
                1,
            )[1].lstrip()

        elif low.startswith("python\r\n"):
            text=text.split(
                "\r\n",
                1,
            )[1].lstrip()

        return text

    for target_number,candidate in enumerate(
        selected_targets,
        1,
    ):
        target_rel=candidate["path"]
        target=wt/target_rel

        try:
            baseline=target.read_text(
                encoding="utf-8",
            )
        except Exception as exc:
            attempted_targets.append({
                "path":target_rel,
                "status":"read_failed",
                "last_error":(
                    f"{type(exc).__name__}: {exc}"
                ),
            })
            continue

        baseline_tokens=set(
            _re.findall(
                r"[A-Za-z_][A-Za-z0-9_]{2,}",
                baseline,
            )
        )

        related=[]

        for sibling in target.parent.glob(
            "*.py"
        ):
            if sibling == target:
                continue

            try:
                text=sibling.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception:
                continue

            if len(text) > 5000:
                continue

            tokens=set(
                _re.findall(
                    r"[A-Za-z_][A-Za-z0-9_]{2,}",
                    text,
                )
            )

            overlap=len(
                baseline_tokens & tokens
            )

            if overlap:
                related.append(
                    (
                        -overlap,
                        sibling.name,
                        text,
                    )
                )

        related.sort()

        related_context=""

        for _,name,text in related[:2]:
            related_context+=(
                "\n--- RELATED FILE: "
                + name
                + " ---\n"
                + text[:1800]
                + "\n"
            )

        h=candidate.get("history") or {}

        history_note=""

        if h:
            history_note=(
                "\nRECENT ADAPTATION HISTORY FOR "
                "THIS TARGET:\n"
                f"failures={int(h.get('failures') or 0)}, "
                f"successes={int(h.get('successes') or 0)}\n"
            )

            if h.get("last_error"):
                history_note+=(
                    "Last rejection: "
                    + str(
                        h.get("last_error")
                    )[:900]
                    + "\nAvoid repeating that failed approach.\n"
                )

        progress_event(
            "target_started",
            target_number=target_number,
            target_budget=len(selected_targets),
            target=target_rel,
            score=candidate.get(
                "effective_score"
            ),
            behavior_score=candidate.get(
                "behavior_score"
            ),
        )

        hypothesis_result=propose_hypothesis(
            ROOT,
            goal,
            target_rel,
            baseline,
            related_context,
            history_note,
            attempts=3,
        )

        if not hypothesis_result.get("ok"):
            attempted_targets.append({
                "path":target_rel,
                "status":"hypothesis_failed",
                "last_error":hypothesis_result.get(
                    "last_error"
                ),
                "score":candidate[
                    "effective_score"
                ],
            })

            progress_event(
                "target_rejected",
                target=target_rel,
                reason="hypothesis_failed",
                error=hypothesis_result.get(
                    "last_error"
                ),
            )

            continue

        hypothesis=hypothesis_result["plan"]

        feedback=""
        final_error=None

        for attempt in range(
            1,
            local_attempts+1,
        ):
            progress_event(
                "code_attempt",
                target=target_rel,
                attempt=attempt,
                max_attempts=local_attempts,
            )

            prompt=(
                "You are improving one existing CompanyOS "
                "Python file.\n\n"

                "SYSTEM IMPROVEMENT GOAL:\n"
                + str(goal)
                + "\n\n"

                "SELECTED CAPABILITY HYPOTHESIS:\n"
                + json.dumps(
                    hypothesis,
                    indent=2,
                    sort_keys=True,
                )
                + "\n\n"

                "Implement THIS hypothesis specifically. "
                "The resulting code must satisfy its acceptance "
                "condition. Do not replace it with a cosmetic "
                "or unrelated change.\n\n"

                "TARGET FILE:\n"
                + target_rel
                + "\n\n"

                "CURRENT COMPLETE SOURCE:\n"
                "----- BEGIN SOURCE -----\n"
                + baseline
                + "\n----- END SOURCE -----\n\n"

                "RELATED READ-ONLY IMPLEMENTATION "
                "CONTEXT:\n"
                + related_context
                + history_note
                + "\n"

                "Make ONE small but meaningful behavioral "
                "improvement to this exact file. Preserve "
                "its public contract and existing working "
                "behavior. Improve real reliability, "
                "execution quality, observability, "
                "validation, coordination, efficiency, "
                "recovery, or measurable capability. "

                "Do not create another file. Do not invent "
                "CompanyOS modules, functions, classes, "
                "scripts, APIs, or dependencies that do not "
                "already exist in the supplied source or "
                "related context. Do not return placeholders, "
                "fake work, simulated success, TODO-only "
                "changes, formatting-only changes, or comments "
                "as the improvement. "

                "Do not use shell=True. If launching Python, "
                "use sys.executable. Preserve ownership, queue, "
                "retry, state, dependency, and lifecycle "
                "invariants visible in the surrounding code. "

                "Return the COMPLETE replacement Python source. "
                "Return RAW PYTHON ONLY. Do not return JSON. "
                "Do not return Markdown fences. Do not return "
                "a filename, explanation, heading, or prose. "
                "The entire response must directly compile as "
                "the replacement file."
            )

            if feedback:
                prompt+=(
                    "\n\nYOUR PREVIOUS ATTEMPT WAS "
                    "REJECTED FOR:\n"
                    + feedback[:1800]
                    + "\nRepair those exact problems without "
                      "discarding correct existing behavior."
                )

            try:
                raw=model_request(
                    prompt,
                    response_mode="text",
                )

                if (
                    not isinstance(raw,dict)
                    or raw.get("ok") is False
                ):
                    feedback=str(
                        (raw or {}).get(
                            "reason",
                            "model_request_failed",
                        )
                    )
                    final_error=feedback
                    continue

                content=_clean_generated_python(
                    raw.get("text") or ""
                )

            except Exception as exc:
                feedback=(
                    "generation_failed:"
                    + type(exc).__name__
                    + ":"
                    + str(exc)
                )
                final_error=feedback
                continue

            if not content.strip():
                feedback="empty_content"
                final_error=feedback
                continue

            if (
                content.rstrip()
                == baseline.rstrip()
            ):
                feedback="no_actual_change"
                final_error=feedback
                continue

            if (
                len(
                    content.encode("utf-8")
                )
                > 50000
            ):
                feedback="content_too_large"
                final_error=feedback
                continue

            try:
                compile(
                    content,
                    target_rel,
                    "exec",
                )
            except Exception as exc:
                feedback=(
                    "invalid_python:"
                    + type(exc).__name__
                    + ":"
                    + str(exc)
                )
                final_error=feedback
                continue

            try:
                qerrors=_candidate_quality_errors(
                    wt,
                    target_rel,
                    content,
                    baseline=baseline,
                    planned_paths={
                        target_rel,
                    },
                    is_new=False,
                )
            except Exception as exc:
                feedback=(
                    "quality_gate_exception:"
                    + type(exc).__name__
                    + ":"
                    + str(exc)
                )
                final_error=feedback
                continue

            if qerrors:
                feedback="; ".join(qerrors)
                final_error=feedback

                progress_event(
                    "candidate_rejected",
                    target=target_rel,
                    attempt=attempt,
                    reason=feedback[:600],
                )

                continue

            target.write_text(
                content.rstrip()+"\n",
                encoding="utf-8",
            )

            cp=_subprocess.run(
                [
                    "git",
                    "status",
                    "--porcelain=v1",
                ],
                cwd=str(wt),
                text=True,
                capture_output=True,
                timeout=30,
            )

            changed_files=[
                line[3:].strip()
                for line in cp.stdout.splitlines()
                if len(line)>=4
            ]

            if (
                target_rel
                not in changed_files
            ):
                feedback=(
                    "write_produced_no_git_change"
                )
                final_error=feedback
                continue

            progress_event(
                "candidate_written",
                target=target_rel,
                attempt=attempt,
                hypothesis=hypothesis,
            )

            attempted_targets.append({
                "path":target_rel,
                "status":"candidate_written",
                "attempt":attempt,
                "score":candidate[
                    "effective_score"
                ],
            })

            return {
                "ok":True,
                "status":"targeted_candidate_written",
                "generator":"local_targeted_builder_v2",
                "attempt":attempt,
                "target_number":target_number,
                "path":target_rel,
                "action":"replace",
                "hypothesis":hypothesis,
                "changed_files":changed_files,
                "attempted_targets":attempted_targets,
                "targets_considered":[
                    x["path"]
                    for x in selected_targets
                ],
            }

        attempted_targets.append({
            "path":target_rel,
            "status":"generation_failed",
            "attempts":local_attempts,
            "last_error":final_error,
            "score":candidate[
                "effective_score"
            ],
        })

    return {
        "ok":False,
        "reason":"all_target_generation_attempts_failed",
        "attempts_per_target":local_attempts,
        "target_budget":target_budget,
        "attempted_targets":attempted_targets,
        "targets_considered":[
            x["path"]
            for x in selected_targets
        ],
        "last_error":(
            attempted_targets[-1].get(
                "last_error"
            )
            if attempted_targets
            else None
        ),
    }

def generate(wt, goal):
    import subprocess as _subprocess

    configured_base=os.getenv(
        "OPENAI_BASE_URL",""
    ).strip().lower()

    configured_key=os.getenv(
        "OPENAI_API_KEY",""
    ).strip().lower()

    local_mode=(
        configured_key=="companyos-local"
        or "127.0.0.1" in configured_base
        or "localhost" in configured_base
    )

    if local_mode:
        targeted=_direct_generation_fallback(
            wt,
            goal,
        )

        status=_subprocess.run(
            ["git","status","--porcelain=v1"],
            cwd=str(wt),
            text=True,
            capture_output=True,
            timeout=30,
        )

        changed_after=[
            line[3:].strip()
            for line in status.stdout.splitlines()
            if len(line)>=4
        ]

        return {
            "ok":bool(targeted.get("ok"))
                 and bool(changed_after),
            "generator":"local_targeted_builder",
            "targeted":targeted,
            "changed_files":changed_after,
        }

    script = ROOT / "scripts" / "companyos_adaptive_self_build.py"
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
                [sys.executable, str(script), "run"],
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

    legacy_receipt={}
    for line in reversed(
        (legacy.get("stdout_tail") or "").splitlines()
    ):
        try:
            parsed=json.loads(line)
            if isinstance(parsed,dict):
                legacy_receipt=parsed
                break
        except Exception:
            pass

    legacy_noop = (
        not changed
        or legacy_receipt.get("status")=="not_run"
        or legacy_receipt.get("no_changes") is True
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


def commit_candidate(wt,run_id,files):
    git(["add","--",*files],wt); r=git(["commit","-m",f"Self-evolution candidate {run_id}"],wt)
    return git(["rev-parse","HEAD"],wt).stdout.strip() if r.returncode==0 else None

def backup(run_id,files):
    b=BK/run_id; b.mkdir(parents=True,exist_ok=True); meta=[]
    for rel in files:
        src=ROOT/rel; meta.append({"path":rel,"existed":src.exists()})
        if src.is_file():dst=b/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    save(b/"manifest.json",{"files":meta}); return b

def restore(b):
    for x in load(b/"manifest.json",{"files":[]}).get("files",[]):
        rel=x["path"]; dst=ROOT/rel; src=b/rel
        if x.get("existed") and src.exists():dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        elif dst.is_file():dst.unlink()

def promote(run_id,wt,branch,files,csha):
    overlap=sorted(
        set(files) & dirty()
    )

    if overlap:
        return {
            "ok":False,
            "status":"promotion_pending_overlap",
            "overlap":overlap,
            "candidate_branch":branch,
            "candidate_sha":csha,
        }

    patch=git(
        [
            "diff",
            "HEAD^",
            "HEAD",
            "--binary",
        ],
        wt,
    ).stdout

    chk=subprocess.run(
        [
            "git",
            "apply",
            "--check",
            "-",
        ],
        cwd=str(ROOT),
        input=patch,
        text=True,
        capture_output=True,
    )

    if chk.returncode:
        return {
            "ok":False,
            "status":"patch_check_failed",
            "stderr":(
                chk.stderr or ""
            )[-1800:],
        }

    b=backup(
        run_id,
        files,
    )

    ap=subprocess.run(
        [
            "git",
            "apply",
            "-",
        ],
        cwd=str(ROOT),
        input=patch,
        text=True,
        capture_output=True,
    )

    if ap.returncode:
        restore(b)
        return {
            "ok":False,
            "status":"apply_failed",
        }

    t=tests(
        ROOT,
        files,
    )

    if not t["ok"]:
        restore(b)
        return {
            "ok":False,
            "status":"live_tests_failed_rolled_back",
            "tests":t,
        }

    git(
        [
            "add",
            "--",
            *files,
        ]
    )

    c=git([
        "commit",
        "-m",
        f"Promote self-evolution candidate {run_id}",
    ])

    if c.returncode:
        git(
            [
                "reset",
                "--",
                *files,
            ]
        )
        restore(b)

        return {
            "ok":False,
            "status":"commit_failed_rolled_back",
        }

    sha=git(
        [
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()

    br=git(
        [
            "branch",
            "--show-current",
        ]
    ).stdout.strip()

    push_ok=None
    remote_sha=None
    push_attempts=[]

    if (
        os.getenv(
            "COMPANYOS_SELF_EVOLUTION_PUSH",
            "1",
        )=="1"
        and br
    ):
        for attempt in range(1,4):
            pr=git(
                [
                    "push",
                    "origin",
                    br,
                ],
                timeout=180,
            )

            remote=git(
                [
                    "ls-remote",
                    "--heads",
                    "origin",
                    br,
                ],
                timeout=60,
            )

            remote_sha=None

            if remote.returncode==0:
                line=(
                    remote.stdout.strip()
                    .splitlines()
                )

                if line:
                    remote_sha=(
                        line[0]
                        .split()[0]
                    )

            verified=(
                pr.returncode==0
                and remote_sha==sha
            )

            push_attempts.append({
                "attempt":attempt,
                "returncode":pr.returncode,
                "verified":verified,
                "remote_sha":remote_sha,
                "stderr":(
                    pr.stderr or ""
                )[-700:],
            })

            if verified:
                push_ok=True
                break

            push_ok=False

            if attempt < 3:
                time.sleep(
                    2*attempt
                )

    return {
        "ok":True,
        "status":(
            "promoted"
            if push_ok is not False
            else "promoted_push_pending"
        ),
        "live_commit":sha,
        "branch":br,
        "backup":str(b),
        "tests":t,
        "push_ok":push_ok,
        "remote_sha":remote_sha,
        "push_attempts":push_attempts,
    }

def schedule_restart():
    ctl=ROOT/"scripts/companyosctl"
    if os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_RESTART","1")!="1" or not ctl.exists():return False
    subprocess.Popen(["bash","-lc",f"sleep 8; cd {str(ROOT)!r}; scripts/companyosctl restart >/dev/null 2>&1 || true"],cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True); return True

def state_update(**kw):
    s=load(STATE,{}); s.update(kw); s["updated_at"]=time.time(); save(STATE,s); return s

def health_guard():
    s=load(STATE,{}); p=s.get("last_promotion")
    if not isinstance(p,dict):return {"ok":True,"status":"no_recent_promotion"}
    age=time.time()-float(p.get("promoted_at") or 0); window=int(os.getenv("COMPANYOS_SELF_EVOLUTION_GUARD_SECONDS","900"))
    if age>window:
        if not p.get("guard_passed"):p["guard_passed"]=True; s["last_promotion"]=p; save(STATE,s); ledger("promotion_guard_passed",commit=p.get("live_commit"))
        return {"ok":True,"status":"guard_window_passed"}
    sup=load(RT/"service_supervisor_state.json",{}); bad=[n for n,r in (sup.get("services") or {}).items() if not r.get("running") or int(r.get("consecutive_failures") or 0)>=2]
    if not bad:return {"ok":True,"status":"guard_healthy","age_seconds":age}
    commit=p.get("live_commit"); r=git(["revert","--no-edit",commit]) if commit else None
    if not r or r.returncode:git(["revert","--abort"]); state_update(blocked=True,blocked_reason="rollback_conflict"); return {"ok":False,"status":"rollback_conflict_blocked","bad_services":bad}
    rev=git(["rev-parse","HEAD"]).stdout.strip(); ledger("automatic_rollback_complete",reverted_commit=commit,revert_commit=rev,bad_services=bad); state_update(blocked=False,last_rollback={"reverted_commit":commit,"revert_commit":rev,"bad_services":bad,"ts":time.time()},last_promotion=None); schedule_restart(); return {"ok":False,"status":"automatic_rollback_complete","revert_commit":rev,"bad_services":bad}

def cycle(force=False,proposal_only=False):
    if os.getenv("COMPANYOS_ENABLE_SELF_EVOLUTION","0")!="1" and not force:return {"ok":True,"status":"disabled"}
    if load(STATE,{}).get("blocked"):return {"ok":False,"status":"blocked","state":load(STATE,{})}
    hg=health_guard()
    if not hg.get("ok") and "rollback" not in hg.get("status",""):return {"ok":False,"status":"health_guard_blocked","guard":hg}
    if not force and today_count()>=MAX_DAILY:return {"ok":True,"status":"daily_budget_reached","limit":MAX_DAILY}
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); d=diagnose(); ledger("proposal_started",run_id=run_id,diagnosis=d); state_update(running=True,current_run=run_id,last_diagnosis=d,last_cycle_started=time.time())
    receipt={"run_id":run_id,"started_at":time.time(),"diagnosis":d}; wt=branch=None; keep=False
    try:
        wt,branch=shadow(run_id); receipt["candidate_branch"]=branch
        g=generate(wt,d["recommended_goal"]); receipt["generation"]=g
        if not g["ok"]:receipt["status"]="generation_failed"; return {"ok":False,**receipt}
        files=changed(wt); gd=guard(wt,files); receipt["guard"]=gd
        if not gd["ok"]:receipt["status"]="candidate_rejected_by_guard"; ledger("candidate_rejected",run_id=run_id,guard=gd); return {"ok":False,**receipt}
        t=tests(wt,files); receipt["candidate_tests"]=t
        if not t["ok"]:receipt["status"]="candidate_tests_failed"; return {"ok":False,**receipt}

        from companyos.runtime.self_evolution_backtest import behavioral_backtest

        bt=behavioral_backtest(
            ROOT,
            wt,
            files,
            g,
        )

        receipt["behavioral_backtest"]=bt

        if not bt.get("ok"):
            receipt["status"]="candidate_backtest_failed"
            ledger(
                "candidate_backtest_failed",
                run_id=run_id,
                changed_files=files,
                backtest=bt,
            )
            return {"ok":False,**receipt}

        ledger(
            "candidate_backtest_passed",
            run_id=run_id,
            changed_files=files,
            backtest=bt,
        )

        csha=commit_candidate(wt,run_id,files); receipt["candidate_sha"]=csha; receipt["changed_files"]=files
        if not csha:receipt["status"]="candidate_commit_failed"; return {"ok":False,**receipt}
        ledger("candidate_qualified",run_id=run_id,candidate_sha=csha,changed_files=files)
        if proposal_only or os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_PROMOTE","1")!="1":keep=True; receipt["status"]="qualified_pending_promotion"; state_update(pending_candidate={"run_id":run_id,"branch":branch,"sha":csha,"changed_files":files}); return {"ok":True,**receipt}
        pr=promote(run_id,wt,branch,files,csha); receipt["promotion"]=pr
        if pr.get("status")=="promotion_pending_overlap":keep=True; receipt["status"]="qualified_pending_overlap"; state_update(pending_candidate={"run_id":run_id,"branch":branch,"sha":csha,"changed_files":files,"overlap":pr.get("overlap")}); return {"ok":True,**receipt}
        if not pr.get("ok"):receipt["status"]=pr.get("status","promotion_failed"); return {"ok":False,**receipt}
        receipt["status"]=pr.get("status","promoted")
        state_update(
            pending_candidate=None,
            last_promotion={
                "run_id":run_id,
                "candidate_sha":csha,
                "live_commit":pr.get("live_commit"),
                "branch":pr.get("branch"),
                "changed_files":files,
                "backup":pr.get("backup"),
                "promoted_at":time.time(),
                "guard_passed":False,
                "push_ok":pr.get("push_ok"),
                "remote_sha":pr.get("remote_sha"),
            },
        )
        ledger(
            "promotion_complete",
            run_id=run_id,
            live_commit=pr.get("live_commit"),
            changed_files=files,
            push_ok=pr.get("push_ok"),
            remote_sha=pr.get("remote_sha"),
        )
        receipt["restart_scheduled"]=schedule_restart()
        return {"ok":True,**receipt}
    except Exception as e:receipt["status"]="exception"; receipt["error"]=f"{type(e).__name__}: {e}"; ledger("cycle_exception",run_id=run_id,error=receipt["error"]); return {"ok":False,**receipt}
    finally:
        receipt["finished_at"]=time.time(); save(RC/f"{run_id}.json",receipt); state_update(running=False,current_run=None,last_cycle_finished=time.time(),last_status=receipt.get("status"),last_receipt=str(RC/f"{run_id}.json"))
        if wt is not None and branch is not None:
            try:cleanup(wt,branch,keep)
            except Exception as e:ledger("worktree_cleanup_failed",run_id=run_id,error=str(e))

def status():
    return {"enabled":os.getenv("COMPANYOS_ENABLE_SELF_EVOLUTION","0")=="1","auto_promote":os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_PROMOTE","1")=="1","auto_restart":os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_RESTART","1")=="1","max_daily_proposals":MAX_DAILY,"proposals_today":today_count(),"state":load(STATE,{}),"diagnosis":diagnose(),"guard":health_guard()}
