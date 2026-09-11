from pathlib import Path
import shutil, time, os, subprocess, stat

ROOT = Path.home() / "companyos"
stamp = str(int(time.time()))

identity = 'import re\n\nINTERNAL = {\n    "accounting","runtime","logs","backups","backup","tmp","temp","quotes",\n    "projects","invoices","artifacts","exports","dashboard","ceo_memory",\n    "companyos_runtime"\n}\n\ndef slugify(name):\n    s = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())\n    return re.sub(r"_+", "_", s).strip("_")\n\ndef canonical_id(name):\n    s = slugify(name)\n    patterns = [\n        r"_?v\\d+(?:_\\d+){0,2}$",\n        r"_?version_?\\d+$",\n        r"_?release_?\\d+$",\n        r"_?build_?\\d+$",\n    ]\n    changed = True\n    while changed:\n        changed = False\n        for pat in patterns:\n            n = re.sub(pat, "", s, flags=re.I).strip("_")\n            if n != s:\n                s = n\n                changed = True\n    return s\n\ndef is_internal(name):\n    return canonical_id(name) in {canonical_id(x) for x in INTERNAL}\n\ndef display_name(cid):\n    return "_".join(x.capitalize() for x in cid.split("_") if x)\n'
controller = 'from __future__ import annotations\nimport json\nimport time\nfrom pathlib import Path\nfrom companyos.governance.venture_identity_resolver import canonical_id, display_name, is_internal\n\nROOT = Path.home() / "companyos"\nIDENTITY = ROOT / ".companyos_runtime" / "venture_identity_progression.json"\nSTATE = ROOT / ".companyos_runtime" / "stalled_stage_progression_state.json"\n\nSTAGE_TASKS = {\n    "CUSTOMER_ACQUISITION": [\n        "define one measurable acquisition experiment with channel, audience, offer, and success metric",\n        "create internal campaign assets, messaging, landing copy, outreach templates, and a tracking plan",\n        "prepare a lead/prospect list or channel plan using permitted research sources",\n        "separate internally authorized work from external actions that still require approval",\n        "after approved execution, record conversion, fulfillment status, customer feedback, and the next iteration",\n    ],\n    "LAUNCH_READY": [\n        "prepare the launch checklist and authorized deployment path",\n        "prepare customer-facing launch assets",\n        "identify consequential external actions that still require approval",\n    ],\n    "BUILD": [\n        "identify the smallest missing sellable feature",\n        "implement or delegate that feature",\n        "run an internal acceptance check and record results",\n    ],\n    "TEST": [\n        "define explicit acceptance criteria",\n        "run internal tests",\n        "record failures and create only the fixes required to pass",\n    ],\n    "DISCOVER": [\n        "define the customer problem and target segment",\n        "collect evidence of demand",\n        "produce a measurable opportunity brief",\n    ],\n}\n\ndef load(path, default):\n    try:\n        return json.loads(path.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\ndef save(path, obj):\n    path.parent.mkdir(parents=True, exist_ok=True)\n    path.write_text(json.dumps(obj, indent=2, default=str) + "\\n", encoding="utf-8")\n\ndef canonical_ventures():\n    src = load(IDENTITY, {"ventures": {}})\n    merged = {}\n    order = {\n        "DISCOVER":0,"VALIDATE":1,"BUILD":2,"TEST":3,"PACKAGE":4,\n        "LAUNCH_READY":5,"LAUNCH":6,"CUSTOMER_ACQUISITION":7,\n        "OPERATE":8,"SCALE":9\n    }\n\n    for key, rec in (src.get("ventures") or {}).items():\n        if not isinstance(rec, dict):\n            continue\n        cid = canonical_id(rec.get("canonical_id") or key)\n        if not cid or is_internal(cid):\n            continue\n\n        cur = merged.setdefault(cid, {\n            "canonical_id": cid,\n            "display_name": display_name(cid),\n            "aliases": set(),\n            "artifact_count": 0,\n            "stage": "DISCOVER",\n            "unchanged_observations": 0,\n        })\n\n        for alias in rec.get("aliases", []) or []:\n            cur["aliases"].add(alias)\n        cur["aliases"].add(key)\n        cur["artifact_count"] += int(rec.get("artifact_count", 0) or 0)\n        cur["unchanged_observations"] = max(\n            cur["unchanged_observations"],\n            int(rec.get("unchanged_observations", 0) or 0)\n        )\n\n        stage = rec.get("stage", "DISCOVER")\n        if order.get(stage, 0) > order.get(cur["stage"], 0):\n            cur["stage"] = stage\n\n    for row in merged.values():\n        row["aliases"] = sorted(row["aliases"])\n    return merged\n\ndef stalled_ventures(min_unchanged=3):\n    rows = [\n        row for row in canonical_ventures().values()\n        if row["unchanged_observations"] >= min_unchanged\n    ]\n    rows.sort(key=lambda x: x["unchanged_observations"], reverse=True)\n    return rows\n\ndef goal_for(row):\n    stage = row.get("stage", "DISCOVER")\n    tasks = STAGE_TASKS.get(\n        stage,\n        ["advance the venture to its next measurable lifecycle milestone"]\n    )\n    numbered = "\\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))\n    return (\n        f"Advance existing canonical CompanyOS venture \'{row[\'canonical_id\']}\'.\\n"\n        f"Current stage: {stage}\\n"\n        f"Unchanged observations: {row[\'unchanged_observations\']}\\n"\n        "Do not create a duplicate or version-suffixed venture. Reuse existing artifacts.\\n"\n        "Execute this INTERNAL and REVERSIBLE progression chain:\\n"\n        f"{numbered}\\n"\n        "Produce measurable state change. Keep consequential external actions, financial "\n        "transactions, credential changes, destructive actions, and irreversible commitments "\n        "behind existing approval and safety gates."\n    )\n\ndef maybe_start(min_unchanged=3, cooldown_seconds=300):\n    state = load(STATE, {"starts": [], "last_started_by_venture": {}})\n    now = time.time()\n\n    for row in stalled_ventures(min_unchanged):\n        last = float(state["last_started_by_venture"].get(row["canonical_id"], 0) or 0)\n        if now - last < cooldown_seconds:\n            continue\n\n        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator\n        rec = AutonomousCEOOrchestrator().start(\n            goal=goal_for(row),\n            max_cycles=80,\n            max_follow_up_depth=4,\n            priority_base=190,\n        )\n        entry = {\n            "ts": now,\n            "canonical_id": row["canonical_id"],\n            "stage": row["stage"],\n            "orchestration_id": getattr(rec, "orchestration_id", None),\n        }\n        state["starts"].append(entry)\n        state["starts"] = state["starts"][-200:]\n        state["last_started_by_venture"][row["canonical_id"]] = now\n        save(STATE, state)\n        return {"started": True, "entry": entry}\n\n    return {"started": False, "reason": "no_eligible_stalled_venture"}\n'

files = {
    ROOT / "companyos/governance/venture_identity_resolver.py": identity,
    ROOT / "companyos/runtime/stalled_stage_progression_controller.py": controller,
}

for path, content in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + ".bak." + stamp)
        shutil.copy2(path, backup)
        print("BACKUP:", backup)
    path.write_text(content, encoding="utf-8")
    print("INSTALLED:", path)

watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
if not watchdog.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = watchdog.with_name(watchdog.name + ".bak.stalled_stage." + stamp)
shutil.copy2(watchdog, backup)
s = watchdog.read_text(encoding="utf-8")

imp = "from companyos.runtime.stalled_stage_progression_controller import maybe_start as maybe_start_stalled_stage"
if imp not in s:
    if "from typing import Any" in s:
        s = s.replace("from typing import Any", "from typing import Any\n" + imp, 1)
    else:
        s = imp + "\n" + s

needle = 'if should_start:\n        idx = int(ws.get("goal_index", 0)) % len(GOALS)'
replacement = '''if should_start:
        stalled = maybe_start_stalled_stage(
            min_unchanged=int(os.getenv("COMPANYOS_STALLED_STAGE_MIN_OBSERVATIONS", "3")),
            cooldown_seconds=int(os.getenv("COMPANYOS_STALLED_STAGE_COOLDOWN_SECONDS", "300")),
        )
        if stalled.get("started"):
            entry = stalled.get("entry") or {}
            action = "autostart_stalled_stage_progression"
            new_orchestration_id = entry.get("orchestration_id")
            ws["autostarts"].append(now)
            ws["total_autostarts"] = int(ws.get("total_autostarts", 0)) + 1
            ws["last_progress_unix"] = now
            ws["last_cycle_count"] = cycles
            log("STALLED_STAGE_AUTOSTART " + json.dumps(entry, default=str, sort_keys=True))
            should_start = False

    if should_start:
        idx = int(ws.get("goal_index", 0)) % len(GOALS)'''

if needle not in s:
    raise SystemExit("FAIL: expected watchdog trigger block not found; no changes made")

watchdog.write_text(s.replace(needle, replacement, 1), encoding="utf-8")
print("WATCHDOG_PATCH: PASS")
print("BACKUP:", backup)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(
    ["python", "-m", "py_compile",
     "companyos/governance/venture_identity_resolver.py",
     "companyos/runtime/stalled_stage_progression_controller.py",
     "companyos/runtime/productive_autonomy_watchdog.py"],
    cwd=ROOT, env=env, check=True
)

print("STALLED_STAGE_PROGRESSION_INSTALL: PASS")
print("VERSION_SUFFIX_CANONICALIZATION: ENABLED")
print("STALLED_STAGE_AUTODISPATCH: ENABLED_FOR_INTERNAL_REVERSIBLE_WORK")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
