#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.companyos_backups/openai_selfbuild_adapter_v5_$STAMP"

cd "$ROOT"
mkdir -p "$BACKUP"
cp -a scripts/companyos_local_ai_adapter.py "$BACKUP/companyos_local_ai_adapter.py"
cp -a companyos/runtime/self_evolution_engine.py "$BACKUP/self_evolution_engine.py"

echo "CompanyOS OpenAI Self-Build Adapter Fix V5"

python - <<'PY'
from pathlib import Path
import re

p = Path("scripts/companyos_local_ai_adapter.py")
s = p.read_text()

m = re.search(r'(?m)^def\s+model_request\s*\([^)]*\)\s*->\s*dict\[[^\n]+\]\s*:\s*\n', s)
if not m:
    raise SystemExit("ERROR: model_request not found")
start = m.start()
n = re.search(r'(?m)^def\s+extract_json\s*\(', s[m.end():])
if not n:
    raise SystemExit("ERROR: extract_json boundary not found")
end = m.end() + n.start()

replacement = r'''def model_request(prompt: str) -> dict[str, Any]:
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
        "response_format": {"type": "json_object"},
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


'''

p.write_text(s[:start] + replacement + s[end:])
print("AI_ADAPTER_CLOUD_ROUTING_PATCHED=YES")
PY

python - <<'PY'
from pathlib import Path
p = Path("companyos/runtime/self_evolution_engine.py")
s = p.read_text()
old = '''        if isinstance(raw, dict):
            if isinstance(raw.get("response"), dict):
                plan = raw["response"]
            elif isinstance(raw.get("result"), dict):
                plan = raw["result"]
            elif isinstance(raw.get("data"), dict):
                plan = raw["data"]
            else:
                plan = raw
        elif isinstance(raw, str):
            plan = extract_json(raw)
        else:
            plan = extract_json(str(raw))
'''
new = '''        if isinstance(raw, dict):
            if raw.get("ok") is False:
                return {
                    "ok": False,
                    "reason": "model_generation_failed",
                    "adapter_reason": raw.get("reason"),
                    "endpoint": raw.get("endpoint"),
                    "model": raw.get("model"),
                }
            if isinstance(raw.get("text"), str):
                plan = extract_json(raw["text"])
            elif isinstance(raw.get("response"), dict):
                plan = raw["response"]
            elif isinstance(raw.get("result"), dict):
                plan = raw["result"]
            elif isinstance(raw.get("data"), dict):
                plan = raw["data"]
            else:
                plan = raw
        elif isinstance(raw, str):
            plan = extract_json(raw)
        else:
            plan = extract_json(str(raw))
'''
if old not in s:
    raise SystemExit("ERROR: V4 response block not found")
p.write_text(s.replace(old, new, 1))
print("SELF_EVOLUTION_TEXT_UNWRAP_PATCHED=YES")
PY

python -m py_compile scripts/companyos_local_ai_adapter.py companyos/runtime/self_evolution_engine.py
python -m unittest tests.test_self_evolution_guard

source "$HOME/.companyos_launch_env"

python - <<'PY'
import sys
sys.path.insert(0, "scripts")
from companyos_local_ai_adapter import model_request, extract_json
r = model_request('Return exactly one JSON object: {"test":"ok"}')
print("MODEL_OK=", bool(r.get("ok")))
print("MODEL_PROVIDER=", r.get("provider"))
print("MODEL_ENDPOINT=", r.get("endpoint"))
print("MODEL_NAME=", r.get("model"))
if not r.get("ok"):
    print("MODEL_REASON=", r.get("reason"))
    raise SystemExit(1)
obj = extract_json(r.get("text", ""))
print("JSON_PARSE_OK=", obj.get("test") == "ok")
if obj.get("test") != "ok":
    raise SystemExit(2)
PY

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

git add -- scripts/companyos_local_ai_adapter.py companyos/runtime/self_evolution_engine.py
if ! git diff --cached --quiet; then
  git commit -m "Route self-build generation through OpenAI cloud"
fi

BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

if [ -x scripts/companyosctl ]; then
  scripts/companyosctl restart || true
fi
sleep 5

echo
echo "COMPANYOS_OPENAI_SELFBUILD_ADAPTER_FIX_V5=PASS"
echo "Next: scripts/companyos_evolutionctl once"
