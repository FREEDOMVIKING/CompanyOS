from pathlib import Path
import py_compile, subprocess, os
ROOT=Path.home()/'companyos'
files=[ROOT/'companyos/governance/venture_identity_progression.py',ROOT/'dashboard/venture_identity_progression_server.py',ROOT/'dashboard/venture_identity_progression.html',ROOT/'dashboard/venture_identity_progression_start.sh',ROOT/'companyos/runtime/productive_autonomy_watchdog.py']
for p in files:
    print(p,'=>','PASS' if p.exists() else 'FAIL')
    if not p.exists(): raise SystemExit('VERIFY_FAIL')
py_compile.compile(str(ROOT/'companyos/governance/venture_identity_progression.py'),doraise=True)
py_compile.compile(str(ROOT/'dashboard/venture_identity_progression_server.py'),doraise=True)
py_compile.compile(str(ROOT/'companyos/runtime/productive_autonomy_watchdog.py'),doraise=True)
env=os.environ.copy();env['PYTHONPATH']=f"{ROOT}:{ROOT/'companyos'}"
p=subprocess.run(['python','scripts/companyos_progression_directive.py'],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(p.stdout[:12000])
if p.returncode!=0: raise SystemExit('DIRECTIVE_VERIFY_FAIL')
print('VENTURE_IDENTITY_PROGRESSION_VERIFY: PASS')
