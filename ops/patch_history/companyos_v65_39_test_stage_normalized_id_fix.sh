#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.39 TEST_STAGE NORMALIZED-ID FIX ====="

python - <<'PY'
from pathlib import Path
import shutil, time, re, py_compile

p=Path("companyos/runtime/capability_expansion.py")
src=p.read_text()
backup=p.with_name(p.name+f".v65_39_backup_{int(time.time())}")
shutil.copy2(p,backup)
print("BACKUP=",backup)

start=src.index("def test_stage(")
m=re.search(r"\ndef [A-Za-z_]\w*\(", src[start+1:])
end=(start+1+m.start()) if m else len(src)
old_block=src[start:end]
block=old_block

if "normalized_id = normalize_capability_id(cid)" not in block:
    first_nl=block.index("\n")
    block=block[:first_nl+1]+"    normalized_id = normalize_capability_id(cid)\n"+block[first_nl+1:]

block=block.replace("canonical_paths(cid)", "canonical_paths(normalized_id)")

if block != old_block:
    src=src[:start]+block+src[end:]
    p.write_text(src)
    print("PATCH_STATUS=patched")
else:
    print("PATCH_STATUS=already_patched")

py_compile.compile(str(p),doraise=True)
print("PY_COMPILE=PASS")
PY

echo "===== RECOVERY TEST ====="
python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py

echo "===== V65.39 END-TO-END RECHECK ====="
python - <<'PY'
import tempfile, os, subprocess
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.39"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old=(ce.ROOT,ce.STAGING,ce.PROMOTED)
with tempfile.TemporaryDirectory() as td:
    root=Path(td); ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    ce.PROMOTED=root/".companyos"/"capability_expansion"/"promoted"
    try:
        cid,staged,errors=ce.stage_plan(plan["gap"],plan)
        print("CID=",cid); print("STAGE_ERRORS=",errors)
        ok,steps=ce.test_stage(Path(staged),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok:
            print("TEST_STAGE_STEPS=",steps)
            raise SystemExit("V65_39_ABORT=test_stage_failed")
        ce.promote(Path(staged),plan["gap"]["id"],cid)
        normalized=ce.normalize_capability_id(cid)
        module_rel,test_rel=ce.canonical_paths(normalized)
        module=root/Path(module_rel); test=root/Path(test_rel)
        print("NORMALIZED_ID=",normalized)
        print("MODULE_EXISTS=",module.exists()); print("TEST_EXISTS=",test.exists())
        if not module.exists() or not test.exists():
            raise SystemExit("V65_39_ABORT=promotion_paths")
        env=os.environ.copy(); env["PYTHONPATH"]=str(root)+os.pathsep+env.get("PYTHONPATH","")
        for cmd in (["python","-m","py_compile",str(module),str(test)],
                    ["python","-m","pytest","-q",str(test)]):
            cp=subprocess.run(cmd,cwd=root,env=env,text=True,capture_output=True,timeout=90)
            print("COMMAND="," ".join(cmd)); print("RETURN_CODE=",cp.returncode)
            if cp.stdout: print(cp.stdout)
            if cp.stderr: print(cp.stderr)
            if cp.returncode: raise SystemExit("V65_39_ABORT=promoted_validation")
        print("V65_39_END_TO_END=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old
PY
echo "V65_39_COMPLETE"
