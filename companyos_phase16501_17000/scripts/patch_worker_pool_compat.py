#!/usr/bin/env python3
from pathlib import Path

p = Path.home() / "companyos/companyos/workerops/worker_pool.py"
if not p.exists():
    print("WORKER_POOL_COMPAT_SKIPPED:not_found")
    raise SystemExit(0)

s = p.read_text()
if "claim_updates.pop" in s:
    print("WORKER_POOL_COMPAT_ALREADY_FIXED")
    raise SystemExit(0)

lines = s.splitlines()
for i, line in enumerate(lines):
    if "queue.update" in line and "**claimed" in line:
        indent = line[:len(line)-len(line.lstrip())]
        lines[i:i+1] = [
            indent + "claim_updates = dict(claimed)",
            indent + "claim_updates.pop('job_id', None)",
            indent + "queue.update(job['job_id'], **claim_updates)"
        ]
        p.with_suffix(".py.phase17000.bak").write_text(s)
        p.write_text("\n".join(lines) + "\n")
        print("WORKER_POOL_COMPAT_PATCHED")
        raise SystemExit(0)

print("WORKER_POOL_COMPAT_NO_TARGET")
