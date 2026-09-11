#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.public_research_connectors import collect_public_research

topic, rows, errors = collect_public_research()
print("=== COMPANYOS PUBLIC RESEARCH CONNECTORS ===")
print("TOPIC:", topic)
print("RESULTS:", len(rows))
print("ERRORS:", len(errors))
for e in errors:
    print("ERROR:", e)
for r in rows[:9]:
    print(f"{r['source']} | {r['title'][:100]}")
print("EXTERNAL WRITE ACTIONS: DISABLED")
print("FINANCIAL ACTIONS: DISABLED")
