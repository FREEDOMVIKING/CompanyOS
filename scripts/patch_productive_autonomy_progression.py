from pathlib import Path
import shutil, time

p = Path.home()/'companyos'/'companyos'/'runtime'/'productive_autonomy_watchdog.py'
if not p.exists():
    raise SystemExit('FAIL: productive_autonomy_watchdog.py not found')

backup = p.with_name(p.name + '.bak.progression.' + str(int(time.time())))
shutil.copy2(p, backup)

s = p.read_text()

if 'from companyos.governance.venture_identity_progression import highest_priority_stalled' not in s:
    marker = 'from typing import Any'
    if marker in s:
        s = s.replace(marker, marker + '\nfrom companyos.governance.venture_identity_progression import highest_priority_stalled', 1)
    else:
        s = 'from companyos.governance.venture_identity_progression import highest_priority_stalled\n' + s

old = '''def start_internal_goal(goal: str) -> str:
    # Uses the existing orchestrator public API. This creates internal work only.
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    ceo = AutonomousCEOOrchestrator()
    rec = ceo.start(
        goal=goal,
        max_cycles=60,
        max_follow_up_depth=3,
        priority_base=150,
    )
'''

new = '''def start_internal_goal(goal: str) -> str:
    stalled = highest_priority_stalled()
    if stalled:
        goal = stalled["progression_directive"]

    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    ceo = AutonomousCEOOrchestrator()
    rec = ceo.start(
        goal=goal,
        max_cycles=60,
        max_follow_up_depth=3,
        priority_base=170 if stalled else 150,
    )
'''

if old not in s:
    raise SystemExit('FAIL: expected watchdog block not found; no changes made')

p.write_text(s.replace(old, new, 1))
print('BACKUP:', backup)
print('PRODUCTIVE_AUTONOMY_PROGRESSION_PATCH: PASS')
print('EXTERNAL_APPROVAL_GATES_BYPASSED: NO')
print('FINANCIAL_LIMITS_MODIFIED: NO')
