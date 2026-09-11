import json, os, re
from pathlib import Path
from companyos.runtime.reasoning_reliability import install, status

ROOT = Path.home() / "companyos"
install()

hits = []
patterns = [
    re.compile(r"max_tokens\s*[:=]\s*[\"']?(\d+)", re.I),
    re.compile(r"max_output_tokens\s*[:=]\s*[\"']?(\d+)", re.I),
]
for p in (ROOT / "companyos").rglob("*.py"):
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat in patterns:
        for m in pat.finditer(txt):
            try:
                n = int(m.group(1))
            except Exception:
                continue
            if n > 8192:
                hits.append({
                    "file": str(p.relative_to(ROOT)),
                    "value": n,
                    "snippet": txt[max(0,m.start()-80):m.end()+80].replace("\n"," ")[:300]
                })

print(json.dumps({
    "runtime_shim": status(),
    "high_static_token_values_found": hits[:100],
    "environment": {
        "COMPANYOS_REASONING_MAX_OUTPUT_TOKENS": os.getenv("COMPANYOS_REASONING_MAX_OUTPUT_TOKENS", "8192(default)"),
        "COMPANYOS_REASONING_MIN_RETRY_TOKENS": os.getenv("COMPANYOS_REASONING_MIN_RETRY_TOKENS", "1024(default)"),
        "COMPANYOS_REASONING_HTTP_RETRIES": os.getenv("COMPANYOS_REASONING_HTTP_RETRIES", "2(default)"),
    }
}, indent=2))
