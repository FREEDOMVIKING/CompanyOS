#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import subprocess
import time

ROOT=Path.home()/"companyos"
MANIFEST=ROOT/"config/companyos_active_component_manifest.json"
OUT_JSON=ROOT/"audit/COMPANYOS_CONSOLIDATION_BASELINE.json"
OUT_MD=ROOT/"audit/COMPANYOS_CONSOLIDATION_BASELINE.md"


def git(*args: str) -> str:
    p=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True)
    return p.stdout.strip()


def is_historical(rel: str) -> bool:
    low=rel.lower()
    return (
        rel.startswith(("backups/","ops/patch_history/","companyos_phase"))
        or rel.startswith("install_phase")
        or "/backup" in low
        or "_backup_" in low
        or low.endswith((".backup",".bak",".bak2",".zip"))
    )


def file_size(rel: str) -> int:
    try:
        return (ROOT/rel).stat().st_size
    except Exception:
        return 0


def main() -> int:
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    tracked=git("ls-files").splitlines()

    historical=[x for x in tracked if is_historical(x)]
    current=[x for x in tracked if not is_historical(x)]

    ext_all=Counter((Path(x).suffix.lower() or "<none>") for x in tracked)
    ext_current=Counter((Path(x).suffix.lower() or "<none>") for x in current)
    ext_historical=Counter((Path(x).suffix.lower() or "<none>") for x in historical)

    historical_bytes=sum(file_size(x) for x in historical)
    current_bytes=sum(file_size(x) for x in current)

    # Current canonical service list. This only builds argv specs; it does not
    # start processes or perform external actions.
    service_names=[]
    try:
        from companyos.runtime.service_supervisor import ServiceSupervisor
        service_names=[x.name for x in ServiceSupervisor.default_services()]
    except Exception as exc:
        service_names=[f"ERROR:{type(exc).__name__}"]

    # Finance domains are deliberately separate. Do not compare USD treasury
    # values with SOL execution values as though they were one policy.
    finance={}
    try:
        from companyos.walletintegration.execution_policy import ExecutionPolicy
        p=ExecutionPolicy()
        finance["solana_live_execution_defaults"]={
            "unit":"SOL",
            "daily_cap":p.daily_cap_sol,
            "single_cap":p.single_cap_sol,
            "minimum_transfer":p.minimum_transfer_sol,
            "reserve":p.reserve_sol,
            "canonical_file":"companyos/walletintegration/execution_policy.py",
        }
    except Exception as exc:
        finance["solana_live_execution_error"]=type(exc).__name__

    try:
        from companyos.treasuryops.policy import TreasuryPolicy
        p=TreasuryPolicy()
        finance["treasury_budget_defaults"]={
            "unit":"USD/accounting",
            "daily_limit":p.autonomous_daily_limit,
            "single_tx_limit":p.autonomous_single_tx_limit,
            "reserve_floor":p.reserve_floor,
            "max_daily_loss":p.max_daily_loss,
            "allow_autonomous_transfers":p.allow_autonomous_transfers,
            "canonical_file":"companyos/treasuryops/policy.py",
        }
    except Exception as exc:
        finance["treasury_budget_error"]=type(exc).__name__

    # Show duplicate stems in the current/unclassified area. These are review
    # candidates only; no file is automatically deleted or moved.
    stems=defaultdict(list)
    for rel in current:
        p=Path(rel)
        if p.suffix.lower() in {".py",".sh"}:
            stems[p.stem].append(rel)
    duplicate_stems={
        k:v for k,v in stems.items()
        if len(v)>1
    }
    duplicate_stems=dict(
        sorted(duplicate_stems.items(), key=lambda kv:(-len(kv[1]),kv[0]))[:100]
    )

    missing=manifest.get("missing_canonical_paths",[])
    hosting_path="companyos/connectors/hosting_router.py"

    warnings=[]
    if missing:
        warnings.append("missing_canonical_component_paths")
    if not (ROOT/hosting_path).exists():
        warnings.append("canonical_hosting_router_missing")

    report={
        "schema":"companyos.consolidation_baseline.v1",
        "generated_at_unix":time.time(),
        "branch":git("branch","--show-current"),
        "head_sha":git("rev-parse","HEAD"),
        "status":"PASS_WITH_WARNINGS" if warnings else "PASS",
        "warnings":warnings,
        "canonical_manifest":{
            "path":"config/companyos_active_component_manifest.json",
            "component_count":len(manifest.get("component_status",{})),
            "missing":missing,
        },
        "repository_classification":{
            "tracked_total":len(tracked),
            "current_or_unclassified":len(current),
            "historical_or_archive":len(historical),
            "current_or_unclassified_bytes":current_bytes,
            "historical_or_archive_bytes":historical_bytes,
            "extensions_total":dict(ext_all.most_common()),
            "extensions_current":dict(ext_current.most_common()),
            "extensions_historical":dict(ext_historical.most_common()),
            "historical_examples":historical[:100],
        },
        "supervised_runtime_services":service_names,
        "hosting":{
            "canonical_router":hosting_path,
            "present":(ROOT/hosting_path).exists(),
            "connector_engine":"companyos/connectors_live/engine.py",
        },
        "finance_policy_domains":finance,
        "finance_policy_domains_distinct":True,
        "duplicate_current_stems":duplicate_stems,
        "deletion_performed":False,
        "financial_limits_changed":False,
        "external_actions_performed":False,
    }

    OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
    OUT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")

    lines=[
        "# CompanyOS V67.0 Consolidation Baseline",
        "",
        f"- Status: **{report['status']}**",
        f"- Tracked files: **{len(tracked)}**",
        f"- Current/unclassified files: **{len(current)}**",
        f"- Historical/archive files: **{len(historical)}**",
        f"- Canonical components: **{len(manifest.get('component_status',{}))}**",
        f"- Missing canonical paths: **{len(missing)}**",
        f"- Canonical hosting router present: **{report['hosting']['present']}**",
        f"- Supervised runtime services: **{len(service_names)}**",
        "",
        "## Finance policy domains",
        "",
        "SOL execution and USD/accounting treasury policy are intentionally separate domains. No limits were changed.",
        "",
        "## Consolidation rule",
        "",
        "Historical files are classified, not deleted. Future cleanup should move or remove files only after canonical replacements are verified by tests and runtime health checks.",
    ]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":report["status"],
        "tracked_total":len(tracked),
        "current_or_unclassified":len(current),
        "historical_or_archive":len(historical),
        "historical_megabytes":round(historical_bytes/1024/1024,2),
        "canonical_components":len(manifest.get("component_status",{})),
        "missing_canonical_paths":missing,
        "hosting_router_present":report["hosting"]["present"],
        "supervised_runtime_services":len(service_names),
        "duplicate_current_stems":len(duplicate_stems),
        "finance_policy_domains_distinct":True,
    },indent=2,sort_keys=True))
    return 0 if not warnings else 2


if __name__=="__main__":
    raise SystemExit(main())
