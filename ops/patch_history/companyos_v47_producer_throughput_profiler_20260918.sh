#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
OUT="$R/v47_producer_throughput_$TS.json"
echo "===== COMPANYOS V47 PRODUCER + THROUGHPUT PROFILER ====="
echo "DURATION=180S SAMPLE=30S"
echo "MODE=READ_ONLY"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=0"

python - "$Q" "$OUT" <<'PY'
import json,sys,time,collections
from pathlib import Path
q,out=Path(sys.argv[1]),Path(sys.argv[2])

def snapshot():
 rows={}; states=collections.Counter(); types=collections.Counter()
 for p in q.glob("*.json"):
  try:x=json.loads(p.read_text())
  except: continue
  k=str(x.get("task_id") or p.stem); st=x.get("state","UNKNOWN"); ty=x.get("task_type") or "unknown"
  rows[k]=(st,ty,x.get("updated_at_unix",0))
  states[st]+=1; types[(ty,st)]+=1
 return rows,states,types

samples=[]; first=None; prev=None
for sec in range(0,181,30):
 rows,states,types=snapshot()
 if first is None: first=rows
 created=collections.Counter(); completed=collections.Counter(); failed=collections.Counter()
 if prev is not None:
  for k,(st,ty,u) in rows.items():
   if k not in prev: created[ty]+=1
   old=prev.get(k)
   if old and old[0]!="COMPLETED" and st=="COMPLETED": completed[ty]+=1
   if old and old[0]!="FAILED" and st=="FAILED": failed[ty]+=1
 print(f"T+{sec:03d} STATES={dict(states)} NEW={dict(created)} DONE={dict(completed)} FAIL={dict(failed)}",flush=True)
 samples.append({"t":sec,"states":dict(states),"new":dict(created),"done":dict(completed),"fail":dict(failed)})
 prev=rows
 if sec<180: time.sleep(30)

last=rows
created=collections.Counter(); done=collections.Counter(); fail=collections.Counter()
for k,(st,ty,u) in last.items():
 if k not in first: created[ty]+=1
 old=first.get(k)
 if old and old[0]!="COMPLETED" and st=="COMPLETED": done[ty]+=1
 if old and old[0]!="FAILED" and st=="FAILED": fail[ty]+=1

queued=collections.Counter(ty for st,ty,u in last.values() if st=="QUEUED")
print("===== 3-MINUTE TOTALS =====")
print("CREATED_BY_TYPE",dict(created))
print("COMPLETED_BY_TYPE",dict(done))
print("FAILED_BY_TYPE",dict(fail))
print("QUEUED_BY_TYPE",dict(queued))
print("CREATED_TOTAL",sum(created.values()))
print("COMPLETED_TRANSITIONS",sum(done.values()))
print("NET_CREATE_MINUS_COMPLETE",sum(created.values())-sum(done.values()))
print("CREATION_PER_MIN",round(sum(created.values())/3,2))
print("COMPLETION_PER_MIN",round(sum(done.values())/3,2))
if sum(done.values()):
 print("CREATE_TO_COMPLETE_RATIO",round(sum(created.values())/sum(done.values()),3))
else: print("CREATE_TO_COMPLETE_RATIO","INF")
bottleneck=max(queued,key=queued.get) if queued else "none"
print("LARGEST_QUEUED_TYPE",bottleneck,queued.get(bottleneck,0))
report={"samples":samples,"created_by_type":dict(created),"completed_by_type":dict(done),
"failed_by_type":dict(fail),"queued_by_type":dict(queued),
"creation_per_min":round(sum(created.values())/3,2),"completion_per_min":round(sum(done.values())/3,2),
"net_create_minus_complete":sum(created.values())-sum(done.values()),"largest_queued_type":bottleneck}
out.write_text(json.dumps(report,indent=2)+"\n")
print("REPORT",out)
PY
echo "V47_PROFILER=PASS"
echo "NEXT=send_bottom_output"
