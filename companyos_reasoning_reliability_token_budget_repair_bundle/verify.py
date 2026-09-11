from pathlib import Path
import py_compile

ROOT = Path.home()/"companyos"
files = [
    ROOT/"companyos/runtime/reasoning_reliability.py",
    ROOT/"scripts/companyos_reasoning_reliability_status.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.runtime.reasoning_reliability import install, status, _clamp_payload
if not install():
    raise SystemExit("VERIFY_FAIL: requests reliability shim not installed")

body, meta = _clamp_payload({"model":"x","messages":[],"max_tokens":65536})
if body["max_tokens"] != 8192:
    raise SystemExit("VERIFY_FAIL: token clamp failed")

st = status()
if not st.get("requests_wrapped"):
    raise SystemExit("VERIFY_FAIL: requests not wrapped")

print("TOKEN_CLAMP_65536_TO_8192: PASS")
print("REQUESTS_RELIABILITY_WRAPPER: PASS")
print("REASONING_RELIABILITY_TOKEN_BUDGET_REPAIR_VERIFY: PASS")
