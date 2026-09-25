from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from companyos.runtime.self_evolution_probe_contract import (
    callable_signatures,
    resolve_probe_sandbox,
    validate_call_signature,
    validate_probe_paths,
)


ALLOWED_ASSERTIONS = {
    "no_exception",
    "raises",
    "equals",
    "contains",
    "truthy",
    "falsy",
    "path_equals",
}

ALLOWED_EXCEPTIONS = {
    "Exception",
    "RuntimeError",
    "ValueError",
    "TypeError",
    "KeyError",
    "LookupError",
    "AssertionError",
    "IndexError",
    "AttributeError",
}


def _progress(event, **fields):
    try:
        print(
            "[BACKTEST] "
            + json.dumps(
                {"event": event, **fields},
                sort_keys=True,
                default=str,
            ),
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        pass


def _generation_hypothesis(generation):
    generation = generation or {}

    for key in ("targeted", "fallback"):
        value = generation.get(key)

        if not isinstance(value, dict):
            continue

        if isinstance(value.get("hypothesis"), dict):
            return value["hypothesis"], value.get("path")

        nested = value.get("targeted")

        if isinstance(nested, dict):
            if isinstance(nested.get("hypothesis"), dict):
                return (
                    nested["hypothesis"],
                    nested.get("path"),
                )

    return None, None


def _source_symbols(source):
    try:
        tree = ast.parse(source)
    except Exception:
        return {
            "functions": [],
            "classes": {},
        }

    functions = []
    classes = {}

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            methods = []

            for child in node.body:
                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    methods.append(child.name)

            classes[node.name] = methods

    return {
        "functions": functions,
        "classes": classes,
    }


def validate_probe(probe, candidate_source):
    errors = []

    if not isinstance(probe, dict):
        return ["probe_not_object"]

    mode = str(
        probe.get("mode") or ""
    ).strip()

    if mode not in {
        "function",
        "class_method",
    }:
        errors.append(
            "unsupported_probe_mode:" + mode
        )

    symbols = _source_symbols(
        candidate_source
    )

    identifier = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    if mode == "function":
        name = str(
            probe.get("function_name") or ""
        )

        if (
            not identifier.match(name)
            or name not in symbols["functions"]
        ):
            errors.append(
                "invalid_probe_function:" + name
            )

    elif mode == "class_method":
        cls = str(
            probe.get("class_name") or ""
        )

        method = str(
            probe.get("method_name") or ""
        )

        if (
            not identifier.match(cls)
            or cls not in symbols["classes"]
        ):
            errors.append(
                "invalid_probe_class:" + cls
            )

        elif (
            not identifier.match(method)
            or method not in symbols["classes"][cls]
        ):
            errors.append(
                "invalid_probe_method:"
                + cls
                + "."
                + method
            )

    for key in (
        "args",
        "constructor_args",
    ):
        if key in probe and not isinstance(
            probe.get(key),
            list,
        ):
            errors.append(
                "probe_" + key + "_not_list"
            )

    for key in (
        "kwargs",
        "constructor_kwargs",
    ):
        if key in probe and not isinstance(
            probe.get(key),
            dict,
        ):
            errors.append(
                "probe_" + key + "_not_dict"
            )

    errors.extend(
        validate_call_signature(
            probe,
            candidate_source,
        )
    )

    errors.extend(
        validate_probe_paths(
            probe
        )
    )

    assertion = probe.get("assertion")

    if not isinstance(assertion, dict):
        errors.append(
            "missing_probe_assertion"
        )
    else:
        kind = str(
            assertion.get("kind") or ""
        )

        if kind not in ALLOWED_ASSERTIONS:
            errors.append(
                "unsupported_assertion:" + kind
            )

        if kind == "raises":
            expected = str(
                assertion.get("value") or ""
            )

            if expected not in ALLOWED_EXCEPTIONS:
                errors.append(
                    "unsupported_exception:"
                    + expected
                )

        if kind == "path_equals":
            if not isinstance(
                assertion.get("path"),
                list,
            ):
                errors.append(
                    "path_equals_requires_path"
                )

    try:
        encoded = json.dumps(
            probe,
            sort_keys=True,
        )
    except Exception:
        errors.append(
            "probe_not_json_serializable"
        )
    else:
        if len(encoded) > 12000:
            errors.append(
                "probe_too_large"
            )

    return sorted(
        set(errors)
    )


def generate_probe(
    root,
    target_rel,
    baseline_source,
    candidate_source,
    hypothesis,
    attempts=3,
):
    root = Path(root)

    scripts = root / "scripts"

    if str(scripts) not in sys.path:
        sys.path.insert(
            0,
            str(scripts),
        )

    try:
        from companyos_local_ai_adapter import (
            model_request,
            extract_json,
        )
    except Exception as exc:
        return {
            "ok": False,
            "reason": "adapter_import_failed",
            "error":
                f"{type(exc).__name__}: {exc}",
        }

    symbols = _source_symbols(
        candidate_source
    )

    signatures = callable_signatures(
        candidate_source
    )

    last_error = None
    correction = ""

    for attempt in range(
        1,
        max(1, int(attempts)) + 1,
    ):
        _progress(
            "probe_design_attempt",
            target=target_rel,
            attempt=attempt,
        )

        prompt = (
            "Design ONE deterministic behavioral backtest "
            "for an autonomous CompanyOS code candidate.\n\n"

            "The SAME probe will run against ORIGINAL code "
            "and CANDIDATE code.\n"
            "The probe should fail its acceptance condition "
            "on the original behavior and pass on the "
            "candidate only if the stated improvement is real.\n\n"

            "TARGET FILE:\n"
            + target_rel
            + "\n\n"

            "HYPOTHESIS:\n"
            + json.dumps(
                hypothesis,
                indent=2,
                sort_keys=True,
            )
            + "\n\n"

            "AVAILABLE SYMBOLS:\n"
            + json.dumps(
                symbols,
                indent=2,
                sort_keys=True,
            )
            + "\n\n"

            "CALL SIGNATURE REQUIREMENTS:\n"
            + json.dumps(
                signatures,
                indent=2,
                sort_keys=True,
            )
            + "\n\n"

            "Supply every required constructor, function, "
            "and method argument. If an isolated filesystem "
            "home/root/path is required, use the literal "
            "string __SANDBOX__. Never invent an absolute "
            "filesystem path.\n\n"

            "ORIGINAL SOURCE:\n"
            "----- BEGIN ORIGINAL -----\n"
            + baseline_source
            + "\n----- END ORIGINAL -----\n\n"

            "CANDIDATE SOURCE:\n"
            "----- BEGIN CANDIDATE -----\n"
            + candidate_source
            + "\n----- END CANDIDATE -----\n\n"

            "Use JSON-compatible values only. "
            "Do not request shell commands, files, network, "
            "credentials, external services, sleeps, randomness, "
            "or environment mutation.\n\n"

            "Choose either mode=function or "
            "mode=class_method.\n\n"

            "Supported assertions:\n"
            "- no_exception\n"
            "- raises, with value equal to a built-in "
            "exception name\n"
            "- equals\n"
            "- contains\n"
            "- truthy\n"
            "- falsy\n"
            "- path_equals, with a JSON path list and value\n\n"

            "For a class method return:\n"
            "{"
            "\"mode\":\"class_method\","
            "\"class_name\":\"ExactClass\","
            "\"method_name\":\"exact_method\","
            "\"constructor_args\":[],"
            "\"constructor_kwargs\":{},"
            "\"args\":[],"
            "\"kwargs\":{},"
            "\"assertion\":{\"kind\":\"no_exception\"},"
            "\"why\":\"how this proves the hypothesis\""
            "}\n\n"

            "For a function return the same structure but use "
            "\"mode\":\"function\" and \"function_name\".\n\n"

            "Return JSON only."
            + correction
        )

        try:
            response = model_request(
                prompt,
                response_mode="json",
            )

            if (
                not isinstance(response, dict)
                or response.get("ok") is False
            ):
                last_error = str(
                    (response or {}).get(
                        "reason",
                        "model_request_failed",
                    )
                )
                continue

            probe = extract_json(
                response.get("text") or ""
            )

            errors = validate_probe(
                probe,
                candidate_source,
            )

            if errors:
                last_error = "; ".join(
                    errors
                )

                correction = (
                    "\n\nPREVIOUS PROBE WAS REJECTED:\n"
                    + last_error
                    + "\nReturn a corrected safe probe."
                )

                continue

            _progress(
                "probe_selected",
                target=target_rel,
                probe=probe,
            )

            return {
                "ok": True,
                "probe": probe,
                "attempt": attempt,
            }

        except Exception as exc:
            last_error = (
                f"{type(exc).__name__}: {exc}"
            )

    return {
        "ok": False,
        "reason": "probe_generation_failed",
        "last_error": last_error,
    }


_RUNNER = r'''
import importlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path


def blocked(*args, **kwargs):
    raise RuntimeError(
        "external action blocked during CompanyOS behavioral backtest"
    )


# Block external processes and network from the candidate probe.
socket.create_connection = blocked

try:
    socket.socket.connect = blocked
except Exception:
    pass

subprocess.Popen = blocked
subprocess.run = blocked
subprocess.check_call = blocked
subprocess.check_output = blocked
os.system = blocked

try:
    import urllib.request
    urllib.request.urlopen = blocked
except Exception:
    pass


probe = json.loads(
    os.environ["COMPANYOS_BACKTEST_PROBE"]
)

target_rel = os.environ[
    "COMPANYOS_BACKTEST_TARGET"
]

root = Path(
    os.environ["COMPANYOS_BACKTEST_ROOT"]
)

sys.path.insert(
    0,
    str(root),
)


def load_target():
    if target_rel.startswith(
        ("companyos/", "companyos_modules/")
    ):
        name = target_rel[:-3].replace("/", ".")
        return importlib.import_module(name)

    path = root / target_rel

    spec = importlib.util.spec_from_file_location(
        "companyos_backtest_target",
        path,
    )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    return module


def normalize(value):
    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, list):
        return [
            normalize(x)
            for x in value
        ]

    if isinstance(value, tuple):
        return [
            normalize(x)
            for x in value
        ]

    if isinstance(value, dict):
        return {
            str(k): normalize(v)
            for k, v in value.items()
        }

    return repr(value)


def path_value(value, path):
    cur = value

    for item in path:
        if isinstance(cur, dict):
            cur = cur[item]

        elif isinstance(cur, (list, tuple)):
            cur = cur[int(item)]

        else:
            cur = getattr(cur, str(item))

    return cur


result = None
exception = None

try:
    module = load_target()

    mode = probe["mode"]

    if mode == "function":
        fn = getattr(
            module,
            probe["function_name"],
        )

        result = fn(
            *(probe.get("args") or []),
            **(probe.get("kwargs") or {}),
        )

    else:
        cls = getattr(
            module,
            probe["class_name"],
        )

        obj = cls(
            *(probe.get("constructor_args") or []),
            **(probe.get("constructor_kwargs") or {}),
        )

        fn = getattr(
            obj,
            probe["method_name"],
        )

        result = fn(
            *(probe.get("args") or []),
            **(probe.get("kwargs") or {}),
        )

except BaseException as exc:
    exception = {
        "type": type(exc).__name__,
        "message": str(exc),
    }


assertion = probe["assertion"]
kind = assertion["kind"]

accepted = False

try:
    if kind == "no_exception":
        accepted = exception is None

    elif kind == "raises":
        accepted = (
            exception is not None
            and exception["type"]
            == str(assertion.get("value"))
        )

    elif exception is None:
        if kind == "equals":
            accepted = (
                result == assertion.get("value")
            )

        elif kind == "contains":
            accepted = (
                assertion.get("value")
                in result
            )

        elif kind == "truthy":
            accepted = bool(result)

        elif kind == "falsy":
            accepted = not bool(result)

        elif kind == "path_equals":
            actual = path_value(
                result,
                assertion.get("path") or [],
            )

            accepted = (
                actual
                == assertion.get("value")
            )

except BaseException as exc:
    accepted = False

    if exception is None:
        exception = {
            "type": type(exc).__name__,
            "message": str(exc),
        }


print(
    json.dumps(
        {
            "accepted": bool(accepted),
            "result": normalize(result),
            "exception": exception,
        },
        sort_keys=True,
        default=str,
    )
)
'''


def _parse_runner_output(proc):
    lines = [
        x.strip()
        for x in (
            proc.stdout or ""
        ).splitlines()
        if x.strip()
    ]

    for line in reversed(lines):
        try:
            value = json.loads(line)

            if (
                isinstance(value, dict)
                and "accepted" in value
            ):
                value["returncode"] = (
                    proc.returncode
                )

                value["stderr"] = (
                    proc.stderr or ""
                )[-1200:]

                return value

        except Exception:
            continue

    return {
        "accepted": False,
        "returncode": proc.returncode,
        "exception": {
            "type":
                "BacktestProtocolError",
            "message":
                "runner produced no result JSON",
        },
        "stdout": (
            proc.stdout or ""
        )[-1200:],
        "stderr": (
            proc.stderr or ""
        )[-1200:],
    }


def run_probe(
    worktree,
    target_rel,
    probe,
):
    worktree = Path(worktree)

    with tempfile.TemporaryDirectory(
        prefix="companyos_backtest_"
    ) as td:
        sandbox = Path(td)

        probe = resolve_probe_sandbox(
            probe,
            sandbox,
        )

        env = os.environ.copy()

        env.update({
            "HOME": str(sandbox),
            "TMPDIR": str(sandbox),
            "PYTHONDONTWRITEBYTECODE": "1",
            "COMPANYOS_BACKTEST": "1",

            # These apply only to the isolated test subprocess.
            "COMPANYOS_ENABLE_LIVE_FINANCE": "0",
            "COMPANYOS_ENABLE_EXTERNAL_ACTIONS": "0",
            "COMPANYOS_EXTERNAL_ACTIONS_ENABLED": "0",
            "COMPANYOS_LIVE_MODE": "0",

            "COMPANYOS_BACKTEST_ROOT":
                str(worktree),

            "COMPANYOS_BACKTEST_TARGET":
                target_rel,

            "COMPANYOS_BACKTEST_PROBE":
                json.dumps(probe),
        })

        pythonpath = env.get(
            "PYTHONPATH",
            "",
        )

        env["PYTHONPATH"] = (
            str(worktree)
            + (
                os.pathsep + pythonpath
                if pythonpath
                else ""
            )
        )

        proc = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                _RUNNER,
            ],
            cwd=str(sandbox),
            env=env,
            text=True,
            capture_output=True,
            timeout=45,
        )

        return _parse_runner_output(
            proc
        )


def run_probe_pair(
    worktree,
    target_rel,
    baseline_source,
    candidate_source,
    probe,
    candidate_runs=3,
):
    worktree = Path(worktree)
    target = worktree / target_rel

    original = target.read_text(
        encoding="utf-8",
    )

    try:
        target.write_text(
            baseline_source,
            encoding="utf-8",
        )

        baseline = run_probe(
            worktree,
            target_rel,
            probe,
        )

        target.write_text(
            candidate_source,
            encoding="utf-8",
        )

        candidate = []

        for index in range(
            max(1, int(candidate_runs))
        ):
            _progress(
                "candidate_canary_run",
                target=target_rel,
                run=index + 1,
            )

            candidate.append(
                run_probe(
                    worktree,
                    target_rel,
                    probe,
                )
            )

    finally:
        target.write_text(
            original,
            encoding="utf-8",
        )

    baseline_pass = bool(
        baseline.get("accepted")
    )

    candidate_pass = all(
        bool(x.get("accepted"))
        for x in candidate
    )

    improved = (
        not baseline_pass
        and candidate_pass
    )

    if baseline_pass:
        reason = (
            "baseline_already_satisfies_acceptance"
        )

    elif not candidate_pass:
        reason = (
            "candidate_failed_behavioral_canary"
        )

    else:
        reason = "behavioral_gain_proven"

    return {
        "ok": improved,
        "reason": reason,
        "baseline": baseline,
        "candidate_runs": candidate,
        "candidate_passes":
            sum(
                1
                for x in candidate
                if x.get("accepted")
            ),
        "candidate_run_count":
            len(candidate),
    }


def behavioral_backtest(
    root,
    worktree,
    files,
    generation,
):
    root = Path(root)
    worktree = Path(worktree)

    hypothesis, target_hint = (
        _generation_hypothesis(
            generation
        )
    )

    if not isinstance(
        hypothesis,
        dict,
    ):
        return {
            "ok": False,
            "reason":
                "missing_candidate_hypothesis",
        }

    python_files = [
        x
        for x in files
        if str(x).endswith(".py")
    ]

    if target_hint in python_files:
        target_rel = target_hint

    elif len(python_files) == 1:
        target_rel = python_files[0]

    else:
        return {
            "ok": False,
            "reason":
                "backtest_requires_single_target",
            "python_files": python_files,
        }

    target = worktree / target_rel

    if not target.exists():
        return {
            "ok": False,
            "reason":
                "backtest_target_missing",
            "target": target_rel,
        }

    baseline_proc = subprocess.run(
        [
            "git",
            "show",
            "HEAD:" + target_rel,
        ],
        cwd=str(worktree),
        text=True,
        capture_output=True,
        timeout=30,
    )

    if baseline_proc.returncode != 0:
        return {
            "ok": False,
            "reason":
                "no_baseline_for_behavioral_comparison",
            "target": target_rel,
        }

    baseline_source = (
        baseline_proc.stdout
    )

    candidate_source = (
        target.read_text(
            encoding="utf-8",
        )
    )

    designed = generate_probe(
        root,
        target_rel,
        baseline_source,
        candidate_source,
        hypothesis,
        attempts=3,
    )

    if not designed.get("ok"):
        return {
            "ok": False,
            "reason":
                "backtest_probe_design_failed",
            "target": target_rel,
            "probe_design": designed,
        }

    probe = designed["probe"]

    comparison = run_probe_pair(
        worktree,
        target_rel,
        baseline_source,
        candidate_source,
        probe,
        candidate_runs=3,
    )

    result = {
        "ok": bool(
            comparison.get("ok")
        ),
        "target": target_rel,
        "hypothesis": hypothesis,
        "probe": probe,
        "comparison": comparison,
    }

    _progress(
        "behavioral_backtest_complete",
        target=target_rel,
        ok=result["ok"],
        reason=comparison.get(
            "reason"
        ),
        candidate_passes=comparison.get(
            "candidate_passes"
        ),
        candidate_runs=comparison.get(
            "candidate_run_count"
        ),
    )

    return result
