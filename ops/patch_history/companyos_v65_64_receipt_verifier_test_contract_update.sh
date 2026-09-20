#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.64 RECEIPT VERIFIER TEST CONTRACT UPDATE ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys

ROOT = Path.home() / "companyos"
TEST = ROOT / "tests/test_phase38001_40000.py"

if not TEST.exists():
    raise SystemExit("V65_64_ABORT=test_file_missing")

text = TEST.read_text()
tree = ast.parse(text)

target = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "test_receipt_verification"),
    None,
)
if target is None:
    raise SystemExit("V65_64_ABORT=test_receipt_verification_not_found")

BACKUP = TEST.with_name(f"{TEST.name}.v65_64_backup_{int(time.time())}")
shutil.copy2(TEST, BACKUP)
print("BACKUP=", BACKUP)

marker = "V65.64 confirmed-RPC receipt verification contract"

if marker not in text:
    lines = text.splitlines(keepends=True)
    start = target.lineno - 1
    end = target.end_lineno

    replacement = [
        "def test_receipt_verification():\n",
        "    # V65.64 confirmed-RPC receipt verification contract\n",
        "    class ConfirmedRpc:\n",
        "        def signature_status(self, tx_id):\n",
        "            assert tx_id == \"abc\"\n",
        "            return {\n",
        "                \"success\": True,\n",
        "                \"result\": {\n",
        "                    \"value\": [\n",
        "                        {\n",
        "                            \"confirmationStatus\": \"confirmed\",\n",
        "                            \"err\": None,\n",
        "                        }\n",
        "                    ]\n",
        "                },\n",
        "            }\n",
        "\n",
        "    v = OnChainReceiptVerifier(rpc=ConfirmedRpc()).verify(\n",
        "        {\"success\": True, \"signature\": \"abc\"}\n",
        "    )\n",
        "    assert v[\"passed\"] is True\n",
        "    assert v[\"rpc_checked\"] is True\n",
        "    assert v[\"confirmation_status\"] == \"confirmed\"\n",
    ]

    lines[start:end] = replacement
    TEST.write_text("".join(lines))
    print("PATCH_STATUS=updated_legacy_test_to_confirmed_rpc_contract")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(TEST), doraise=True)
    print("TEST_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, TEST)
    print("TEST_COMPILE=FAIL")
    print("TEST_RESTORED=TRUE")
    raise

print("PATCHED_TEST_BEGIN")
patched = TEST.read_text().splitlines()
for i, line in enumerate(patched, 1):
    if marker in line:
        lo = max(1, i-2)
        hi = min(len(patched), i+28)
        for j in range(lo, hi+1):
            print(f"{j:04d}: {patched[j-1]}")
        break
print("PATCHED_TEST_END")

def run(label, args, timeout=180):
    cp = subprocess.run(
        args,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Run exact phase file.
rc = run(
    "PHASE38001_40000_TEST_FILE",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    180,
)
if rc != 0:
    shutil.copy2(BACKUP, TEST)
    py_compile.compile(str(TEST), doraise=True)
    print("PHASE_TEST=FAIL")
    print("TEST_RESTORED=TRUE")
    raise SystemExit(rc)

print("PHASE_TEST=PASS")

# Continue to the next full-suite failure.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_64_fullsuite_{int(time.time())}.out"
OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w") as fh:
    cp = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x"],
        cwd=str(ROOT),
        text=True,
        stdout=fh,
        stderr=subprocess.STDOUT,
        timeout=900,
    )

print("FULL_SUITE_RETURN_CODE=", cp.returncode)
tail = OUT.read_text(errors="ignore").splitlines()[-200:]
print("FULL_SUITE_TAIL_BEGIN")
print("\n".join(tail))
print("FULL_SUITE_TAIL_END")
print("FULL_SUITE_OUTPUT=", OUT)

if cp.returncode == 0:
    print("FULL_SUITE=PASS")
    print("V65_64_READY_FOR_CHECKPOINT=TRUE")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")
    print("V65_64_READY_FOR_CHECKPOINT=RECEIPT_TEST_ONLY")

print("V65_64_COMPLETE")
PY
