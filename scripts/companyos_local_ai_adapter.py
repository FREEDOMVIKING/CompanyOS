#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _balanced_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?[ \t\r\n]*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"[ \t\r\n]*```$", "", text)

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
        raise ValueError("Model response JSON was not an object")
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in model response")

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                value = json.loads(text[start:index + 1])
                if not isinstance(value, dict):
                    raise ValueError("Extracted JSON was not an object")
                return value

    raise ValueError("Model returned incomplete JSON")


def model_request(
    prompt: str,
    response_mode: str = "json",
) -> dict[str, Any]:
    configured_key = os.getenv("OPENAI_API_KEY", "").strip()
    configured_base = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
    configured_model = os.getenv("OPENAI_MODEL", "").strip()

    local_default = "http://127.0.0.1:8080/v1"
    localish = (
        not configured_base
        or configured_base.startswith("http://127.0.0.1:")
        or configured_base.startswith("http://localhost:")
        or configured_base.startswith("https://127.0.0.1:")
        or configured_base.startswith("https://localhost:")
    )
    has_cloud_key = bool(
        configured_key
        and configured_key != "companyos-local"
        and not configured_key.lower().startswith("replace")
    )

    max_tokens = _env_int("COMPANYOS_LOCAL_AI_MAX_TOKENS", 1200, 128, 4096)
    prompt_chars = _env_int("COMPANYOS_LOCAL_AI_PROMPT_CHARS", 5000, 800, 12000)
    timeout = _env_int("COMPANYOS_LOCAL_AI_TIMEOUT", 900, 60, 1800)

    full_prompt = prompt or ""
    if len(full_prompt) <= prompt_chars:
        compact_prompt = full_prompt
    else:
        head_chars = max(1800, int(prompt_chars * 0.65))
        tail_chars = max(900, prompt_chars - head_chars)
        compact_prompt = (
            full_prompt[:head_chars]
            + "\n\n[... middle runtime inventory omitted ...]\n\n"
            + full_prompt[-tail_chars:]
        )

    response_mode = str(
        response_mode or "json"
    ).strip().lower()

    if response_mode not in {"json", "text"}:
        response_mode = "json"

    if response_mode == "text":
        system_text = (
            "You are the CompanyOS adaptive code builder. "
            "Return only the requested raw source text. "
            "Do not use JSON, Markdown fences, headings, or commentary. "
            "Implement real code, not placeholders or TODO-only text. "
            "Never modify credentials, wallets, financial controls, approval gates, "
            "security controls, deployment gates, or secrets."
        )
    else:
        system_text = (
            "You are the CompanyOS adaptive build planner. "
            "Return one complete valid JSON object only. "
            "Do not use markdown fences or commentary. "
            "Implement real code, not placeholders or TODO-only text. "
            "Never modify credentials, wallets, financial controls, approval gates, "
            "security controls, deployment gates, or secrets."
        )

    if has_cloud_key and localish:
        model = os.getenv("COMPANYOS_OPENAI_MODEL", "").strip()
        if not model:
            model = configured_model if configured_model and configured_model != "companyos-local" else "gpt-5.6-luna"

        endpoint = "https://api.openai.com/v1/responses"
        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
                {"role": "user", "content": [{"type": "input_text", "text": compact_prompt}]},
            ],
            "max_output_tokens": max_tokens,
        }

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {configured_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return {
                "ok": False,
                "reason": f"HTTPError: HTTP {exc.code}",
                "body": body[:4000],
                "endpoint": endpoint,
                "model": model,
            }
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"{type(exc).__name__}: {exc}",
                "endpoint": endpoint,
                "model": model,
            }

        text = ""
        for item in data.get("output", []) if isinstance(data, dict) else []:
            if isinstance(item, dict):
                for content in item.get("content", []) or []:
                    if isinstance(content, dict) and content.get("type") == "output_text":
                        text += str(content.get("text") or "")

        if not text.strip():
            return {
                "ok": False,
                "reason": "unexpected_openai_responses_output",
                "raw_id": data.get("id") if isinstance(data, dict) else None,
                "endpoint": endpoint,
                "model": model,
            }

        return {
            "ok": True,
            "text": text.strip(),
            "raw_id": data.get("id"),
            "model": data.get("model", model),
            "endpoint": endpoint,
            "provider": "openai",
        }

    key = configured_key or "companyos-local"
    base_url = configured_base or local_default
    model = configured_model or "companyos-local"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": compact_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "stream": False,
    }

    if response_mode == "json":
        payload["response_format"] = {
            "type": "json_object"
        }

    endpoint = f"{base_url}/chat/completions"

    def perform(request_payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        try:
            data = perform(payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 400 and "response_format" in payload:
                fallback = dict(payload)
                fallback.pop("response_format", None)
                data = perform(fallback)
            else:
                return {
                    "ok": False,
                    "reason": f"HTTPError: HTTP {exc.code}",
                    "body": body[:4000],
                    "endpoint": endpoint,
                    "model": model,
                }
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "endpoint": endpoint,
            "model": model,
        }

    try:
        output = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "reason": "unexpected_local_model_response",
            "raw": data,
            "endpoint": endpoint,
            "model": model,
        }

    return {
        "ok": True,
        "text": str(output).strip(),
        "raw_id": data.get("id"),
        "model": data.get("model", model),
        "endpoint": endpoint,
        "provider": "openai_compatible",
    }


def extract_json(text: str) -> dict[str, Any]:
    return _balanced_json_object(text)
