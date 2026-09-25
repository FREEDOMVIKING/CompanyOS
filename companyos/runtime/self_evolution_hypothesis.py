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
                    + "\nReturn a new plan grounded only in "
                      "the supplied source."
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
