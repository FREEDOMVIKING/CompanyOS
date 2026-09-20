#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PKG="$ROOT/companyos/outreach_orchestrator_v24"
BACKUP="$ROOT/backups/v24_outreach_orchestrator_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " CompanyOS V24 - Autonomous Outreach Orchestrator"
echo "============================================================"

test -d "$ROOT/companyos" || { echo "FAIL: CompanyOS missing"; exit 1; }
test -f "$ROOT/companyos_v23ctl" || { echo "FAIL: V23 missing"; exit 1; }

mkdir -p "$PKG" "$ROOT/ceo_memory" "$ROOT/config" "$ROOT/.companyos_outreach" "$BACKUP"

for f in "$ROOT/companyos_v23ctl" \
         "$ROOT/config/outreach_policy_v23.json" \
         "$ROOT/.companyos_outreach/queue.json" \
         "$ROOT/.companyos_outreach/receipts.json"; do
    [ -e "$f" ] && cp -a "$f" "$BACKUP/" || true
done

cat > "$PKG/__init__.py" <<'PY'
from .orchestrator import OutreachOrchestratorV24
PY

cat > "$PKG/orchestrator.py" <<'PY'
from __future__ import annotations
import json, hashlib, re
from pathlib import Path
from datetime import datetime, timezone
from companyos.outreach_execution_v23.engine import OutreachExecutionV23

ROOT=Path.home()/"companyos"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, obj):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

class OutreachOrchestratorV24:
    def __init__(self, root=ROOT):
        self.root=Path(root)
        self.v23=OutreachExecutionV23(root)
        self.prospects=self.root/"ceo_memory/outreach_prospects_v24.json"
        self.history=self.root/"ceo_memory/outreach_contact_history_v24.json"
        self.metrics=self.root/"ceo_memory/outreach_metrics_v24.json"
        self.policy=self.root/"config/outreach_orchestrator_v24.json"
        if not self.policy.exists():
            save(self.policy,{
                "version":24,
                "autonomous_drafting":True,
                "autonomous_queueing":True,
                "autonomous_external_sending":False,
                "minimum_prospect_score":60,
                "max_queue_per_cycle":5,
                "duplicate_contact_window_days":14,
                "require_valid_email":True
            })

    def status(self):
        policy=load(self.policy,{})
        prospects=load(self.prospects,[])
        history=load(self.history,[])
        return {
            "status":"companyos_v24_autonomous_outreach_orchestrator_ready",
            "autonomous_drafting":policy.get("autonomous_drafting",False),
            "autonomous_queueing":policy.get("autonomous_queueing",False),
            "autonomous_external_sending":policy.get("autonomous_external_sending",False),
            "prospects_total":len(prospects),
            "contact_history_total":len(history),
            "v23_queue":self.v23.queue_status(),
            "financial_actions_enabled":False
        }

    def add_prospect(self, email, company, opportunity, score=60):
        email=(email or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email):
            return {"status":"REJECTED_INVALID_EMAIL"}
        score=max(0,min(100,int(score)))
        pid=hashlib.sha256(f"{email}|{company}".encode()).hexdigest()[:20]
        data=load(self.prospects,[])
        existing=next((x for x in data if x.get("prospect_id")==pid),None)
        item={
            "prospect_id":pid,
            "email":email,
            "company":company.strip(),
            "opportunity":opportunity.strip(),
            "score":score,
            "state":"DISCOVERED",
            "created_at": existing.get("created_at") if existing else now(),
            "updated_at":now()
        }
        if existing:
            data[data.index(existing)]=item
        else:
            data.append(item)
        save(self.prospects,data)
        return {"status":"PROSPECT_STORED","prospect_id":pid,"score":score}

    def _already_contacted(self,email):
        return any(
            x.get("email","").lower()==email.lower()
            and x.get("state") in ("QUEUED","SENT")
            for x in load(self.history,[])
        )

    def draft(self, prospect):
        company=prospect.get("company") or "your team"
        opportunity=prospect.get("opportunity") or "a potential business opportunity"
        subject=f"Potential collaboration with {company}"
        body=(
            f"Hello,\n\n"
            f"I'm reaching out regarding {opportunity}. "
            f"We'd like to explore whether there may be a useful fit with {company}.\n\n"
            f"If this is relevant, we'd be happy to continue the conversation.\n\n"
            f"Regards,\nCompanyOS"
        )
        return subject,body

    def cycle(self):
        policy=load(self.policy,{})
        minimum=int(policy.get("minimum_prospect_score",60))
        maximum=int(policy.get("max_queue_per_cycle",5))
        prospects=load(self.prospects,[])
        history=load(self.history,[])
        queued=[]
        skipped=[]

        candidates=sorted(
            [p for p in prospects if int(p.get("score",0))>=minimum],
            key=lambda x:int(x.get("score",0)),
            reverse=True
        )

        for p in candidates:
            if len(queued)>=maximum:
                break
            if self._already_contacted(p["email"]):
                skipped.append({"prospect_id":p["prospect_id"],"reason":"DUPLICATE_CONTACT"})
                continue

            subject,body=self.draft(p)
            result=self.v23.create(p["email"],subject,body)

            if result.get("status")=="REVIEW_REQUIRED":
                p["state"]="QUEUED_FOR_REVIEW"
                p["updated_at"]=now()
                h={
                    "prospect_id":p["prospect_id"],
                    "message_id":result["message_id"],
                    "email":p["email"],
                    "state":"QUEUED",
                    "created_at":now()
                }
                history.append(h)
                queued.append({
                    "prospect_id":p["prospect_id"],
                    "message_id":result["message_id"],
                    "score":p["score"],
                    "status":"REVIEW_REQUIRED"
                })
            else:
                skipped.append({
                    "prospect_id":p["prospect_id"],
                    "reason":result.get("status")
                })

        save(self.prospects,prospects)
        save(self.history,history)

        result={
            "status":"companyos_v24_cycle_complete",
            "eligible_candidates":len(candidates),
            "queued_for_review":len(queued),
            "queued":queued,
            "skipped":skipped,
            "external_messages_sent":0,
            "autonomous_external_sending":False
        }
        save(self.metrics,result)
        return result

    def review(self):
        q=load(self.root/".companyos_outreach/queue.json",[])
        rows=[]
        for x in q:
            if x.get("status")=="REVIEW_REQUIRED":
                rows.append({
                    "message_id":x.get("message_id"),
                    "to":x.get("to"),
                    "subject":x.get("subject"),
                    "status":x.get("status")
                })
        return {
            "status":"companyos_v24_review_queue",
            "review_required":len(rows),
            "messages":rows
        }
PY

cat > "$ROOT/companyos_v24ctl" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/"companyos"))
from companyos.outreach_orchestrator_v24.orchestrator import OutreachOrchestratorV24

x=OutreachOrchestratorV24()
cmd=sys.argv[1] if len(sys.argv)>1 else "status"

if cmd=="status":
    out=x.status()
elif cmd=="cycle":
    out=x.cycle()
elif cmd=="review":
    out=x.review()
elif cmd=="add-prospect":
    if len(sys.argv)<6:
        raise SystemExit(
            'usage: companyos_v24ctl add-prospect EMAIL COMPANY OPPORTUNITY SCORE'
        )
    out=x.add_prospect(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
else:
    raise SystemExit(
        "usage: companyos_v24ctl {status|cycle|review|add-prospect}"
    )
print(json.dumps(out,indent=2))
PY
chmod +x "$ROOT/companyos_v24ctl"

cat > "$ROOT/config/outreach_orchestrator_v24.json" <<'JSON'
{
  "version": 24,
  "autonomous_drafting": true,
  "autonomous_queueing": true,
  "autonomous_external_sending": false,
  "minimum_prospect_score": 60,
  "max_queue_per_cycle": 5,
  "duplicate_contact_window_days": 14,
  "require_valid_email": true
}
JSON

echo "[1/5] Compile"
python -m py_compile "$PKG"/*.py "$ROOT/companyos_v24ctl"
echo "PASS compile"

echo "[2/5] V23 dependency"
python "$ROOT/companyos_v23ctl" status

echo "[3/5] V24 status"
python "$ROOT/companyos_v24ctl" status

echo "[4/5] Empty orchestration cycle"
python "$ROOT/companyos_v24ctl" cycle

echo "[5/5] Runtime preservation"
cd "$ROOT"
bash companyosctl status || true

echo
echo "============================================================"
echo " V24 AUTONOMOUS OUTREACH ORCHESTRATOR INSTALLED"
echo "============================================================"
echo "Backup: $BACKUP"
echo
echo "Commands:"
echo "  cd ~/companyos"
echo "  python companyos_v24ctl status"
echo "  python companyos_v24ctl review"
echo "  python companyos_v24ctl cycle"
echo
echo "Autonomous drafting and queueing are enabled."
echo "External sending remains disabled."
echo "V23 approval controls remain in force."
echo "No wallet/private/seed credentials are scanned."
echo "No financial actions are performed."
