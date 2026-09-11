import json, os, signal, sys, time
from dataclasses import asdict, is_dataclass
from pathlib import Path

ROOT=Path.home()/"companyos"
RUNTIME=ROOT/".companyos_runtime"
RUNTIME.mkdir(parents=True,exist_ok=True)
STATE_PATH=RUNTIME/"autonomous_ceo_runtime_service.json"
JOURNAL=RUNTIME/"full_autonomy_journal.jsonl"
OIDFILE=RUNTIME/"full_autonomy_current_oid.txt"

sys.path[:0]=[str(ROOT),str(ROOT/"companyos")]

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService, CEORuntimeServiceState

STOP=False
GOAL=os.environ.get("COMPANYOS_FULL_AUTONOMY_GOAL","").strip() or (
"Operate CompanyOS as a fully autonomous CEO. Continuously discover and rank business opportunities "
"and operational improvements; research them; create plans; delegate specialist agents; build and "
"evaluate products, services, campaigns, processes, and internal systems; create follow-up goals; "
"learn from outcomes; recover from failures; and improve the business portfolio. Route external and "
"financial actions through all existing CompanyOS authorization, signer, allowlist, live-limit, "
"reserve, reconciliation, and irreversible-action safeguards."
)

def log(event, **data):
    with JOURNAL.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"event":event,**data},default=str)+"\n")

def make_state():
    t=time.time()
    return CEORuntimeServiceState(
        running=True,ready=True,reason="full_autonomy_active",started_at_unix=t,last_cycle_unix=0.0,
        cycle_count=0,active_orchestrations=0,completed_orchestrations=0,failed_orchestrations=0,
        halted_orchestrations=0,cycles_dispatched_this_tick=0,last_orchestration_id=None,
        consecutive_failures=0,external_actions_performed=False,transaction_broadcasts=False
    )

def stop(*_):
    global STOP
    STOP=True

signal.signal(signal.SIGTERM,stop)
signal.signal(signal.SIGINT,stop)

ceo=AutonomousCEOOrchestrator()
rec=ceo.start(goal=GOAL,max_cycles=1000,max_follow_up_depth=8,priority_base=100)
oid=str(rec.orchestration_id)
OIDFILE.write_text(oid+"\n")
log("objective_created",orchestration_id=oid,state=getattr(rec,"state",None))

service=AutonomousCEORuntimeService(interval_seconds=10.0,max_consecutive_failures=5,state_path=STATE_PATH)
state=make_state()

print("COMPANYOS_FULL_AUTONOMY_STARTED")
print("ORCHESTRATION_ID:",oid)
print("PRIVATE_KEY: HIDDEN")
print("SAFETY_GATES: PRESERVED")
sys.stdout.flush()

while not STOP:
    try:
        state=service.cycle(state)
        d=asdict(state) if is_dataclass(state) else getattr(state,"__dict__",{})
        log("cycle",orchestration_id=oid,state=d)
        print(json.dumps({
            "ready":d.get("ready"),
            "reason":d.get("reason"),
            "cycle_count":d.get("cycle_count"),
            "active_orchestrations":d.get("active_orchestrations"),
            "completed_orchestrations":d.get("completed_orchestrations"),
            "failed_orchestrations":d.get("failed_orchestrations"),
            "halted_orchestrations":d.get("halted_orchestrations"),
            "cycles_dispatched_this_tick":d.get("cycles_dispatched_this_tick"),
            "last_orchestration_id":d.get("last_orchestration_id"),
            "external_actions_performed":d.get("external_actions_performed"),
            "transaction_broadcasts":d.get("transaction_broadcasts")
        },default=str),flush=True)
        time.sleep(10)
    except Exception as e:
        log("runtime_error",error_type=type(e).__name__,error=str(e)[:1000])
        print(json.dumps({"runtime_error":type(e).__name__,"message":str(e)[:1000]}),flush=True)
        time.sleep(10)

log("stopped",orchestration_id=oid)
print("COMPANYOS_FULL_AUTONOMY_STOPPED")
