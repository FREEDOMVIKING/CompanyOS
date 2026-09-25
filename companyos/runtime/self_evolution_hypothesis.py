from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


def progress_event(event, **fields):
    try:
        print(
            "[SELF-EVOLUTION] "
            + json.dumps(
                {
                    "event": event,
                    **fields,
                },
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
        tree=ast.parse(source)
    except Exception:
        return []

    result=[]

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            result.append(node.name)

        elif isinstance(node,ast.ClassDef):
            for child in node.body:
                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    result.append(
                        node.name+"."+child.name
                    )

    return result[:30]


def propose_hypothesis(
    root,
    goal,
    target_rel,
    baseline,
    related_context="",
    history_note="",
    attempts=3,
):
    root=Path(root)

    scripts_dir=root/"scripts"

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
            "ok":False,
            "reason":"adapter_import_failed",
            "last_error":(
                f"{type(exc).__name__}: {exc}"
            ),
        }

    symbols=_symbols(baseline)

    prompt=(
        "Plan ONE concrete behavioral improvement to an "
        "existing CompanyOS Python file.\n\n"

        "SYSTEM GOAL:\n"
        + str(goal)
        + "\n\n"

        "TARGET FILE:\n"
        + str(target_rel)
        + "\n\n"

        "EXISTING FUNCTIONS/METHODS:\n"
        + json.dumps(symbols)
        + "\n\n"

        "CURRENT SOURCE:\n"
        "----- BEGIN SOURCE -----\n"
        + str(baseline)
        + "\n----- END SOURCE -----\n\n"

        "RELATED IMPLEMENTATION CONTEXT:\n"
        + str(related_context)
        + str(history_note)
        + "\n\n"

        "Find one specific weakness that can be corrected "
        "inside THIS EXISTING FILE without inventing modules, "
        "APIs, dependencies, or changing its public contract.\n\n"

        "Prefer real improvements such as input validation, "
        "duplicate-work prevention, retry correctness, queue "
        "correctness, dependency handling, deterministic "
        "fallbacks, state consistency, bounded failure "
        "handling, recovery behavior, useful error signaling, "
        "coordination, or execution efficiency.\n\n"

        "Do NOT propose formatting, renaming, comments, "
        "additional labels, status strings, list entries, "
        "fake logging, or cosmetic refactors.\n\n"

        "Return JSON only with exactly these fields:\n"
        "{"
        "\"problem\":\"specific existing weakness\","
        "\"location\":\"existing function or method\","
        "\"behavior_change\":\"specific executable change\","
        "\"acceptance\":\"observable proof the behavior changed\""
        "}"
    )

    last_error=None

    for attempt in range(
        1,
        max(1,int(attempts))+1,
    ):
        progress_event(
            "hypothesis_attempt",
            target=target_rel,
            attempt=attempt,
        )

        try:
            response=model_request(
                prompt,
                response_mode="json",
            )

            if (
                not isinstance(response,dict)
                or response.get("ok") is False
            ):
                last_error=str(
                    (response or {}).get(
                        "reason",
                        "model_request_failed",
                    )
                )
                continue

            plan=extract_json(
                response.get("text") or ""
            )

            required=(
                "problem",
                "location",
                "behavior_change",
                "acceptance",
            )

            if not all(
                isinstance(plan.get(k),str)
                and plan[k].strip()
                for k in required
            ):
                last_error=(
                    "hypothesis_missing_fields"
                )
                continue

            low=json.dumps(
                plan,
                sort_keys=True,
            ).lower()

            weak=(
                "formatting",
                "rename variable",
                "add comment",
                "add a label",
                "add status string",
                "add list entry",
                "whitespace",
            )

            if any(
                term in low
                for term in weak
            ):
                last_error="weak_hypothesis"
                continue

            progress_event(
                "hypothesis_selected",
                target=target_rel,
                problem=plan["problem"][:200],
                behavior_change=plan[
                    "behavior_change"
                ][:200],
                acceptance=plan[
                    "acceptance"
                ][:200],
            )

            return {
                "ok":True,
                "plan":plan,
                "attempt":attempt,
            }

        except Exception as exc:
            last_error=(
                f"{type(exc).__name__}: {exc}"
            )

    return {
        "ok":False,
        "reason":"hypothesis_generation_failed",
        "last_error":last_error,
    }
