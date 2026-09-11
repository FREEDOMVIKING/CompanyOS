from __future__ import annotations
import json
from typing import Any

PROTECTED = (
    ".env", "wallet", "wallets", "secret", "credential", "private_key",
    "seed_phrase", "mnemonic", "financial", "payment", "approval",
)
ALLOWED_ACTIONS = {"create","update","replace","append","mkdir","delete"}

def _s(v: Any, default: str = "") -> str:
    if v is None:
        return default
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int,float,bool)):
        return str(v)
    return default

def _safe_path(v: Any) -> str:
    p = _s(v).replace("\\","/").lstrip("/")
    while p.startswith("./"):
        p = p[2:]
    parts = [x for x in p.split("/") if x not in ("",".")]
    if not parts or ".." in parts:
        return ""
    p = "/".join(parts)
    low = p.lower()
    if any(token in low for token in PROTECTED):
        return ""
    return p

def _as_list(v: Any) -> list[Any]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def _extract_changes(plan: dict[str, Any]) -> list[Any]:
    raw = None
    for key in ("changes","files","modifications","operations","edits"):
        if key in plan:
            raw = plan[key]
            break
    if isinstance(raw, dict):
        if any(k in raw for k in ("path","file","filename","target","content","code","body")):
            return [raw]
        out = []
        for path, value in raw.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("path", path)
            else:
                item = {"path": path, "content": value}
            out.append(item)
        return out
    return _as_list(raw)

def _normalize_change(item: Any, idx: int):
    if not isinstance(item, dict):
        return None
    path = _safe_path(item.get("path") or item.get("file") or item.get("filename") or item.get("target"))
    if not path:
        return None
    action = _s(item.get("action") or item.get("operation") or item.get("type"), "create").lower()
    aliases = {"write":"create","add":"create","modify":"update","edit":"update","patch":"update","overwrite":"replace","remove":"delete"}
    action = aliases.get(action, action)
    if action not in ALLOWED_ACTIONS:
        action = "create"
    content = item.get("content")
    if content is None:
        content = item.get("code") or item.get("body") or item.get("text") or ""
    if not isinstance(content, str):
        content = json.dumps(content, indent=2) if isinstance(content,(dict,list)) else _s(content)
    if action in {"create","update","replace","append"} and not content:
        return None
    return {
        "path": path,
        "action": action,
        "content": content,
        "reason": _s(item.get("reason") or item.get("description"), f"Normalized local-model change {idx+1}")
    }

def _normalize_tests(v: Any) -> list[str]:
    out = []
    for item in _as_list(v):
        cmd = item.strip() if isinstance(item,str) else _s(item.get("command") if isinstance(item,dict) else "")
        low = cmd.lower()
        if not cmd:
            continue
        if any(x in low for x in ("git push","npm publish","twine upload","solana transfer","send_transaction","buy domain","purchase")):
            continue
        out.append(cmd)
    return out[:12]

def normalize_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise ValueError("plan_not_object")
    for wrapper in ("plan","build_plan","result","proposal"):
        if isinstance(plan.get(wrapper), dict):
            plan = plan[wrapper]
            break
    changes = []
    for i, item in enumerate(_extract_changes(plan)):
        normalized = _normalize_change(item, i)
        if normalized:
            changes.append(normalized)
    return {
        "title": _s(plan.get("title") or plan.get("name") or plan.get("capability") or plan.get("feature"), "Local AI adaptive improvement"),
        "reason": _s(plan.get("reason") or plan.get("summary") or plan.get("description") or plan.get("goal"), "Locally generated CompanyOS improvement."),
        "changes": changes,
        "tests": _normalize_tests(plan.get("tests") or plan.get("validation") or plan.get("checks")),
        "integration": _s(plan.get("integration") or plan.get("integration_notes") or plan.get("handoff"), "Internal integration only; preserve external-action gates."),
    }
