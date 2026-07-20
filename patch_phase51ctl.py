from pathlib import Path

p = Path("companyos/phase51ctl")
s = p.read_text()

old_import = '''from agents.phase51_execution_planner.task_executor import (
    status as executor_status,
    execute_next
)
'''

new_import = '''from agents.phase51_execution_planner.task_executor import (
    status as executor_status,
    execute_next
)

from agents.phase51_execution_planner.execution_loop import (
    run_loop
)
'''

if old_import not in s:
    raise SystemExit("executor import block not found")

s = s.replace(old_import, new_import, 1)

old_block = '''    if command == "executor-status":
        output(executor_status())
        return 0

    output({
'''

new_block = '''    if command == "executor-status":
        output(executor_status())
        return 0

    if command == "run-loop":
        output(run_loop())
        return 0

    output({
'''

if old_block not in s:
    raise SystemExit("executor-status block not found")

s = s.replace(old_block, new_block, 1)

old_list = '''            "execute-next",
            "executor-status"
'''

new_list = '''            "execute-next",
            "executor-status",
            "run-loop"
'''

if old_list not in s:
    raise SystemExit("command list block not found")

s = s.replace(old_list, new_list, 1)

p.write_text(s)

print("PHASE 51 CONTROLLER LOOP PATCHED")
