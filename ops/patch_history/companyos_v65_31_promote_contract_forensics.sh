#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"

echo "===== COMPANYOS V65.31 PROMOTE CONTRACT FORENSICS ====="

python - <<'PY'
import inspect, tempfile, traceback, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

print("PROMOTE_SIGNATURE=", inspect.signature(ce.promote))
print("PROMOTE_SOURCE_BEGIN")
print(inspect.getsource(ce.promote))
print("PROMOTE_SOURCE_END")

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.31 promote contract proof"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        run_cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        staged_root=Path(staged_root)
        cid=ce.normalize_capability_id(plan["gap"]["id"])
        print("RUN_CID=",run_cid)
        print("NORMALIZED_ID=",cid)
        print("STAGED_ROOT=",staged_root)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_31_ABORT=stage_errors")

        ok,steps=ce.test_stage(staged_root,cid)
        print("TEST_STAGE_OK=",ok)
        print("TEST_STAGE_STEPS=",json.dumps(steps,default=str)[:12000])
        if not ok: raise SystemExit("V65_31_ABORT=test_stage_failed")

        sig=inspect.signature(ce.promote)
        names=list(sig.parameters)
        print("PROMOTE_PARAMS=",names)

        # Bind by semantic parameter names rather than guessing position.
        values={}
        for name in names:
            low=name.lower()
            if low in ("root","repo_root","destination_root","dest_root"):
                values[name]=root
            elif low in ("staged_root","stage_root","staging_root","src_root","source_root"):
                values[name]=staged_root
            elif low in ("cid","capability_id","id"):
                values[name]=cid
            elif sig.parameters[name].default is inspect._empty:
                raise SystemExit("V65_31_ABORT=unknown_required_promote_param:"+name)

        print("PROMOTE_BOUND_ARGS=", {k:str(v) for k,v in values.items()})
        bound=sig.bind(**values)
        receipt=ce.promote(*bound.args,**bound.kwargs)
        print("PROMOTE_RECEIPT=",json.dumps(receipt,indent=2,default=str))

        module_rel,test_rel=ce.canonical_paths(cid)
        final_module=root/module_rel
        final_test=root/test_rel
        print("FINAL_MODULE=",final_module)
        print("FINAL_TEST=",final_test)
        print("FINAL_MODULE_EXISTS=",final_module.exists())
        print("FINAL_TEST_EXISTS=",final_test.exists())

        if not final_module.exists() or not final_test.exists():
            print("FINAL_TREE_BEGIN")
            for f in sorted(x for x in root.rglob("*") if x.is_file()):
                print("FINAL_FILE=",f.relative_to(root))
            print("FINAL_TREE_END")
            raise SystemExit("V65_31_ABORT=promotion_destination_mismatch")

        print("V65_31_PROMOTE_CONTRACT=PASS")
    except Exception:
        print("V65_31_EXCEPTION")
        traceback.print_exc()
        raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging

print("V65_31_COMPLETE")
PY
