from __future__ import annotations

import copy
import json
import os
import random
import time
from typing import Any

_INSTALLED = False
_ORIGINAL_SESSION_REQUEST = None

DEFAULT_MAX_OUTPUT_TOKENS = int(os.getenv("COMPANYOS_REASONING_MAX_OUTPUT_TOKENS", "8192"))
MIN_RETRY_TOKENS = int(os.getenv("COMPANYOS_REASONING_MIN_RETRY_TOKENS", "1024"))
MAX_RETRIES = int(os.getenv("COMPANYOS_REASONING_HTTP_RETRIES", "2"))
BACKOFF_BASE_SECONDS = float(os.getenv("COMPANYOS_REASONING_RETRY_BACKOFF_SECONDS", "1.5"))

RETRYABLE_STATUS = {402, 408, 409, 425, 429, 500, 502, 503, 504}

def _looks_like_llm_request(url: str, payload: Any) -> bool:
    u = str(url or "").lower()
    if any(x in u for x in (
        "openrouter.ai", "/chat/completions", "/responses",
        "api.openai.com", "anthropic.com", "generativelanguage.googleapis.com",
    )):
        return isinstance(payload, dict)
    if isinstance(payload, dict):
        return any(k in payload for k in ("max_tokens", "max_output_tokens", "messages", "model"))
    return False

def _token_field(payload: dict) -> str | None:
    if "max_output_tokens" in payload:
        return "max_output_tokens"
    if "max_tokens" in payload:
        return "max_tokens"
    return None

def _clamp_payload(payload: dict, cap: int = DEFAULT_MAX_OUTPUT_TOKENS) -> tuple[dict, dict]:
    body = copy.deepcopy(payload)
    meta = {"changed": False, "field": None, "before": None, "after": None}
    field = _token_field(body)

    if field is None:
        # Add a sane ceiling only to clear chat-style LLM requests.
        if "messages" in body and "model" in body:
            field = "max_tokens"
            body[field] = cap
            meta.update(changed=True, field=field, before=None, after=cap)
        return body, meta

    try:
        before = int(body.get(field))
    except Exception:
        before = cap

    after = min(max(1, before), cap)
    body[field] = after
    if after != before:
        meta.update(changed=True, field=field, before=before, after=after)
    return body, meta

def _response_text(resp: Any) -> str:
    try:
        return str(resp.text or "")[:8000]
    except Exception:
        return ""

def _should_reduce(status: int, text: str) -> bool:
    t = text.lower()
    return (
        status in RETRYABLE_STATUS
        or "more credits" in t
        or "fewer max_tokens" in t
        or "max_tokens" in t and "credits" in t
        or "token" in t and "limit" in t
        or "provider" in t and "error" in t
    )

def _next_budget(current: int) -> int:
    if current <= MIN_RETRY_TOKENS:
        return current
    return max(MIN_RETRY_TOKENS, current // 2)

def install() -> bool:
    global _INSTALLED, _ORIGINAL_SESSION_REQUEST
    if _INSTALLED:
        return True

    try:
        import requests
    except Exception:
        return False

    original = requests.sessions.Session.request
    _ORIGINAL_SESSION_REQUEST = original

    def wrapped(self, method, url, **kwargs):
        payload = kwargs.get("json")
        if not _looks_like_llm_request(url, payload):
            return original(self, method, url, **kwargs)

        body, _ = _clamp_payload(payload or {})
        kwargs = dict(kwargs)
        kwargs["json"] = body

        field = _token_field(body)
        budget = int(body.get(field, DEFAULT_MAX_OUTPUT_TOKENS)) if field else DEFAULT_MAX_OUTPUT_TOKENS
        last_resp = None

        for attempt in range(MAX_RETRIES + 1):
            if field:
                kwargs["json"][field] = budget

            try:
                resp = original(self, method, url, **kwargs)
            except Exception:
                if attempt >= MAX_RETRIES:
                    raise
                sleep_for = BACKOFF_BASE_SECONDS * (2 ** attempt) + random.random() * 0.25
                time.sleep(sleep_for)
                budget = _next_budget(budget)
                continue

            last_resp = resp
            text = _response_text(resp)
            status = int(getattr(resp, "status_code", 0) or 0)

            if not _should_reduce(status, text) or attempt >= MAX_RETRIES:
                return resp

            next_budget = _next_budget(budget)
            if next_budget == budget and status not in {429, 500, 502, 503, 504}:
                return resp

            budget = next_budget
            sleep_for = BACKOFF_BASE_SECONDS * (2 ** attempt) + random.random() * 0.25
            time.sleep(sleep_for)

        return last_resp

    wrapped._companyos_reasoning_reliability_wrapped = True
    wrapped._companyos_reasoning_reliability_original = original
    requests.sessions.Session.request = wrapped
    _INSTALLED = True
    return True

def status() -> dict:
    out = {
        "installed": _INSTALLED,
        "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
        "min_retry_tokens": MIN_RETRY_TOKENS,
        "max_retries": MAX_RETRIES,
        "retryable_status": sorted(RETRYABLE_STATUS),
    }
    try:
        import requests
        out["requests_wrapped"] = bool(
            getattr(requests.sessions.Session.request, "_companyos_reasoning_reliability_wrapped", False)
        )
    except Exception:
        out["requests_wrapped"] = False
    return out
