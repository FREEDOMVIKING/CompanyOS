from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


def progress_event(event, **fields):
    try:
        print(
            "[SELF-EVOLUTION] "
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


def _symbols(source):
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    result = []

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            result.append(node.name)

        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    result.append(
                        node.name + "." + child.name
                    )

    return result[:40]


def _normalize(value):
    return " ".join(
        str(value or "").split()
    ).strip()


def _source_facts(source):
    try:
        tree = ast.parse(source)
    except Exception:
        return {}

    names = set()
    calls = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)

        elif isinstance(node, ast.Attribute):
            names.add(node.attr)

        elif isinstance(node, ast.Call):
            fn = node.func

            if isinstance(fn, ast.Name):
                calls.add(fn.id)

            elif isinstance(fn, ast.Attribute):
                calls.add(fn.attr)

    return {
        "symbols": _symbols(source),
        "identifiers": sorted(names)[:80],
        "calls": sorted(calls)[:60],
        "has_branches": any(
            isinstance(x, ast.If)
            for x in ast.walk(tree)
        ),
        "has_loops": any(
            isinstance(x, (ast.For, ast.While))
            for x in ast.walk(tree)
        ),
        "has_exception_handling": any(
            isinstance(x, ast.Try)
            for x in ast.walk(tree)
        ),
    }



def novelty_errors(plan, baseline):
    """
    Reject hypotheses whose proposed capability already appears
    to be implemented in the target source.

    This is intentionally conservative: it does not block the
    target permanently. It only rejects the current hypothesis
    so another missing capability can be considered.
    """
    errors=[]

    source=str(baseline or "").lower()

    claim=(
        str(plan.get("problem") or "")
        + " "
        + str(plan.get("behavior_change") or "")
        + " "
        + str(plan.get("acceptance") or "")
    ).lower()

    # Duplicate / idempotency prevention already exists.
    if any(
        word in claim
        for word in (
            "duplicate",
            "dedup",
            "idempot",
            "already processed",
            "process only once",
        )
    ):
        identity_signal=any(
            word in source
            for word in (
                "seen",
                "completed",
                "processed",
                "sha256",
                "digest(",
                "idempot",
                "dedup",
            )
        )

        skip_signal=any(
            word in source
            for word in (
                "continue",
                "return",
                "if ",
            )
        )

        if identity_signal and skip_signal:
            errors.append(
                "capability_already_present:"
                "duplicate_prevention"
            )

    # Retry / bounded-attempt behavior already exists.
    if any(
        word in claim
        for word in (
            "retry",
            "retries",
            "backoff",
            "multiple attempts",
        )
    ):
        retry_signal=any(
            word in source
            for word in (
                "retry",
                "attempt",
                "backoff",
            )
        )

        loop_signal=any(
            word in source
            for word in (
                "for ",
                "while ",
            )
        )

        if retry_signal and loop_signal:
            errors.append(
                "capability_already_present:"
                "retry_handling"
            )

    # Validation already exists.
    if any(
        word in claim
        for word in (
            "validation",
            "validate",
            "invalid input",
            "input checking",
            "type check",
        )
    ):
        if any(
            word in source
            for word in (
                "isinstance(",
                "raise valueerror",
                "raise typeerror",
                "assert ",
            )
        ):
            errors.append(
                "capability_already_present:"
                "input_validation"
            )

    # Exception handling already exists.
    if any(
        word in claim
        for word in (
            "exception handling",
            "handle exceptions",
            "error handling",
            "catch errors",
        )
    ):
        if "try:" in source and "except" in source:
            errors.append(
                "capability_already_present:"
                "exception_handling"
            )

    # File-existence protection already exists.
    if any(
        word in claim
        for word in (
            "file existence",
            "missing file",
            "check if file exists",
            "ensure file exists",
        )
    ):
        if ".exists()" in source:
            errors.append(
                "capability_already_present:"
                "existence_check"
            )

    # Hash/digest integrity behavior already exists.
    if any(
        word in claim
        for word in (
            "hash",
            "sha256",
            "digest",
            "integrity hash",
        )
    ):
        if (
            "sha256" in source
            or "hashlib" in source
            or "digest(" in source
        ):
            errors.append(
                "capability_already_present:"
                "hash_integrity"
            )

    # Locking already exists.
    if any(
        word in claim
        for word in (
            "locking",
            "lock file",
            "concurrency lock",
            "prevent concurrent",
        )
    ):
        if any(
            word in source
            for word in (
                "flock",
                "lock_ex",
                "threading.lock",
                "filelock",
            )
        ):
            errors.append(
                "capability_already_present:"
                "locking"
            )

    # Atomic-write pattern already exists.
    if any(
        word in claim
        for word in (
            "atomic write",
            "atomic save",
            "safe write",
            "partial write",
        )
    ):
        if (
            ".replace(" in source
            or "with_suffix(\".tmp\")" in source
            or "with_suffix('.tmp')" in source
        ):
            errors.append(
                "capability_already_present:"
                "atomic_write"
            )

    return errors


def grounding_errors(
    plan,
    baseline,
    related_context="",
):
    errors = []

    symbols = _symbols(baseline)

    location = str(
        plan.get("location") or ""
    ).strip()

    evidence = str(
        plan.get("evidence") or ""
    ).strip()

    problem = str(
        plan.get("problem") or ""
    ).lower()

    behavior = str(
        plan.get("behavior_change") or ""
    ).lower()

    if location.lower() in {
        "",
        "existing function or method",
        "function or method",
        "existing function",
        "existing method",
        "function",
        "method",
    }:
        errors.append(
            "ungrounded_location:placeholder"
        )

    elif (
        location != "<module>"
        and location not in symbols
    ):
        errors.append(
            "ungrounded_location:"
            + location
        )

    normalized_source = _normalize(
        baseline
    )

    normalized_evidence = _normalize(
        evidence
    )

    if not normalized_evidence:
        errors.append(
            "missing_source_evidence"
        )

    elif normalized_evidence not in normalized_source:
        errors.append(
            "evidence_not_found_in_target"
        )

    claim = problem + " " + behavior

    source_low = baseline.lower()

    concept_support = {
        "duplicate": (
            "duplicate",
            "idempot",
            "dedup",
            "seen",
            "completed",
        ),
        "idempot": (
            "idempot",
            "duplicate",
            "seen",
            "completed",
        ),
        "retry": (
            "retry",
            "attempt",
            "backoff",
        ),
        "queue": (
            "queue",
            "enqueue",
            "dequeue",
            "task",
        ),
        "dependency": (
            "depend",
            "prerequisite",
            "stage",
        ),
        "state consistency": (
            "state",
            "save",
            "load",
            "persist",
        ),
    }

    for concept, support in concept_support.items():
        if (
            concept in claim
            and not any(
                token in source_low
                for token in support
            )
        ):
            errors.append(
                "unsupported_target_concept:"
                + concept
            )

    return errors


def propose_hypothesis(
    root,
    goal,
    target_rel,
    baseline,
    related_context="",
    history_note="",
    attempts=3,
):
    root = Path(root)

    scripts_dir = root / "scripts"

    if str(scripts_dir) not in sys.path:
        sys.path.insert(
            0,
            str(scripts_dir),
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
            "last_error":
                f"{type(exc).__name__}: {exc}",
        }

    facts = _source_facts(baseline)

    allowed_locations=[
        "<module>",
        *facts.get("symbols",[]),
    ]

    last_error = None
    correction = ""

    for attempt in range(
        1,
        max(1, int(attempts)) + 1,
    ):
        prompt = (
            "Plan ONE source-grounded behavioral improvement "
            "to this existing CompanyOS Python file.\n\n"

            "SYSTEM GOAL:\n"
            + str(goal)
            + "\n\n"

            "TARGET FILE:\n"
            + str(target_rel)
            + "\n\n"

            "DETECTED SOURCE FACTS:\n"
            + json.dumps(
                facts,
                indent=2,
                sort_keys=True,
            )
            + "\n\n"

            "LEGAL LOCATION VALUES:\n"
            + json.dumps(
                allowed_locations,
                indent=2,
            )
            + "\n"
            "The location field MUST exactly equal one value "
            "from LEGAL LOCATION VALUES. Do not return a call "
            "expression, variable name, source-text fragment, "
            "or a symbol from another file.\n\n"

            "CURRENT SOURCE:\n"
            "----- BEGIN SOURCE -----\n"
            + str(baseline)
            + "\n----- END SOURCE -----\n\n"

            "RELATED CONTEXT:\n"
            + str(related_context)
            + str(history_note)
            + "\n\n"

            "Rules:\n"
            "1. The weakness MUST be directly visible in the "
            "target source.\n"
            "2. evidence MUST be an exact quote copied from "
            "CURRENT SOURCE.\n"
            "3. location MUST be an exact detected function/"
            "method name, or <module> for top-level behavior.\n"
            "4. Do not claim the file performs work it only "
            "observes or reports.\n"
            "5. Do not invent duplicate prevention, retries, "
            "queue handling, state mutation, or execution "
            "semantics unless those concepts already exist in "
            "this target.\n"
            "6. Preserve the existing public/output contract.\n"
            "7. No formatting, renaming, labels, comments, "
            "or cosmetic refactors.\n\n"

            "Return JSON only:\n"
            "{"
            "\"problem\":\"specific visible weakness\","
            "\"location\":\"exact symbol or <module>\","
            "\"evidence\":\"exact source quote\","
            "\"behavior_change\":\"specific executable change\","
            "\"acceptance\":\"observable success condition\""
            "}"
            + correction
        )

        progress_event(
            "hypothesis_attempt",
            target=target_rel,
            attempt=attempt,
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

            plan = extract_json(
                response.get("text") or ""
            )

            required = (
                "problem",
                "location",
                "evidence",
                "behavior_change",
                "acceptance",
            )

            if not all(
                isinstance(plan.get(k), str)
                and plan[k].strip()
                for k in required
            ):
                last_error = (
                    "hypothesis_missing_fields"
                )
                continue

            errors = grounding_errors(
                plan,
                baseline,
                related_context,
            )

            errors.extend(
                novelty_errors(
                    plan,
                    baseline,
                )
            )

            if errors:
                last_error = "; ".join(errors)

                progress_event(
                    "hypothesis_rejected",
                    target=target_rel,
                    reason=last_error,
                )

                correction = (
                    "\n\nPREVIOUS PLAN WAS REJECTED:\n"
                    + last_error
                    + "\nLEGAL LOCATION VALUES ARE: "
                    + json.dumps(allowed_locations)
                    + "\nReturn a DIFFERENT plan grounded only "
                      "in the supplied source. The location must "
                      "exactly equal one legal location. If the "
                      "rejected capability is already implemented, "
                      "identify another genuinely missing behavior."
                )

                continue

            progress_event(
                "hypothesis_selected",
                target=target_rel,
                problem=plan["problem"][:180],
                location=plan["location"],
                evidence=plan["evidence"][:180],
                behavior_change=plan[
                    "behavior_change"
                ][:180],
            )

            return {
                "ok": True,
                "plan": plan,
                "attempt": attempt,
            }

        except Exception as exc:
            last_error = (
                f"{type(exc).__name__}: {exc}"
            )

    return {
        "ok": False,
        "reason":
            "grounded_hypothesis_generation_failed",
        "last_error": last_error,
    }
