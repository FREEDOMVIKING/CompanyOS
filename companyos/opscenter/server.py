from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from urllib.parse import urlparse, parse_qs

from .engine import OperationsEngine
from .control import service_action
from .storage import read_json

HOST = os.environ.get("COMPANYOS_DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMPANYOS_DASHBOARD_PORT", "8765"))

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Executive Operations Center</title>
<style>
:root{color-scheme:dark}
body{font-family:system-ui;margin:0;background:#090d12;color:#e6edf3}
header{position:sticky;top:0;background:#111821;border-bottom:1px solid #2b3440;padding:14px 16px;z-index:5}
h1{font-size:21px;margin:0}.muted{color:#8b949e}
.wrap{padding:13px;max-width:1200px;margin:auto}
.nav{display:flex;gap:7px;overflow:auto;padding-bottom:8px}
.nav button,.controls button{border:0;border-radius:9px;padding:10px 13px;background:#30363d;color:white;font-weight:700;white-space:nowrap}
.controls button.start{background:#238636}.controls button.stop{background:#da3633}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}
.card{background:#141b23;border:1px solid #2b3440;border-radius:14px;padding:14px;margin-bottom:12px;overflow:auto}
.metric{font-size:25px;font-weight:800}.good{color:#3fb950}.warn{color:#d29922}.bad{color:#f85149}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px;border-bottom:1px solid #2b3440;vertical-align:top}
.badge{display:inline-block;padding:3px 7px;border-radius:999px;background:#30363d;font-size:11px}
.bar{height:9px;background:#30363d;border-radius:9px;overflow:hidden}.bar span{display:block;height:100%;background:#3fb950}
input{width:100%;box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #30363d;background:#0d1117;color:white}
pre{white-space:pre-wrap;word-break:break-word;font-size:12px}
section{scroll-margin-top:90px}
</style>
</head>
<body>
<header><h1>CompanyOS Executive Operations Center</h1><div class="muted" id="stamp">Loading...</div></header>
<div class="wrap">
<div class="nav">
<button onclick="go('overview')">Overview</button><button onclick="go('ventures')">Ventures</button>
<button onclick="go('agents')">Agents</button><button onclick="go('roadmap')">Roadmap</button>
<button onclick="go('alerts')">Alerts</button><button onclick="go('events')">Events</button>
</div>
<div class="card controls">
<button class="start" onclick="act('start')">Start</button>
<button onclick="act('restart')">Restart</button>
<button class="stop" onclick="act('stop')">Stop</button>
<span id="actionResult"></span>
</div>

<section id="overview">
<div class="grid">
<div class="card"><h2>System</h2><div id="system"></div></div>
<div class="card"><h2>Portfolio KPIs</h2><div id="kpis"></div></div>
<div class="card"><h2>Finance</h2><div id="finance"></div></div>
<div class="card"><h2>Audit</h2><div id="audit"></div></div>
</div>
</section>

<section id="ventures" class="card"><h2>Venture Portfolio</h2><div id="ventureTable"></div></section>
<section id="agents" class="card"><h2>Specialist Agents and Routed Tasks</h2><div id="agentTable"></div><br><div id="taskTable"></div></section>
<section id="roadmap" class="card"><h2>Multi-Week Roadmap</h2><div id="roadmapTable"></div></section>
<section id="alerts" class="card"><h2>Notification Center</h2><div id="notificationTable"></div><h3>Predicted Bottlenecks</h3><div id="bottleneckTable"></div></section>
<section id="events" class="card"><h2>Searchable Activity</h2><input id="search" placeholder="Search events, ventures, tasks, alerts..." oninput="renderSearch()"><div id="searchResults"></div></section>
</div>
<script>
let D={};
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function money(v){return '$'+Number(v||0).toLocaleString(undefined,{maximumFractionDigits:2})}
function table(rows,cols){
 if(!rows||!rows.length)return '<span class="muted">No data yet.</span>';
 return '<table><thead><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join('')+'</tr></thead><tbody>'+
 rows.map(r=>'<tr>'+cols.map(c=>'<td>'+esc(typeof c[1]==='function'?c[1](r):r[c[1]])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
}
function go(id){document.getElementById(id).scrollIntoView({behavior:'smooth'})}
async function load(){
 const r=await fetch('/api/ops',{cache:'no-store'});D=await r.json();
 document.getElementById('stamp').textContent='Phase '+D.phase+' - '+D.generated_at;
 const h=D.health||{},k=D.kpis||{},f=D.finance_state||{},c=D.capital||{},a=D.audit||{};
 document.getElementById('system').innerHTML='<div class="metric '+(h.overall_healthy?'good':'bad')+'">'+(h.overall_healthy?'HEALTHY':'ATTENTION')+'</div><p>'+
 esc(h.active_service_count||0)+' / '+esc(h.expected_service_count||0)+' services active</p>';
 document.getElementById('kpis').innerHTML='<div class="metric">'+esc(k.venture_count||0)+' ventures</div><p>Average health: '+Math.round(Number(k.average_venture_health||0)*100)+'%<br>Task assignment: '+Math.round(Number(k.task_assignment_rate||0)*100)+'%<br>Milestones: '+esc(k.planned_milestone_count||0)+'<br>Blocked: '+esc(k.blocked_venture_count||0)+'</p>';
 document.getElementById('finance').innerHTML='<div class="metric">'+money(f.available_capital)+'</div><p>Deployable: '+money(c.deployable)+'<br>Reserve: '+money(c.reserve)+'<br>Proposed: '+money(k.capital_proposed_total)+'</p>';
 document.getElementById('audit').innerHTML='<div class="metric '+(a.passed?'good':'warn')+'">'+(a.passed?'PASSED':'REVIEW')+'</div><p>Issues: '+esc((a.issues||[]).length)+'</p>';

 document.getElementById('ventureTable').innerHTML=table(D.ventures,[
 ['Venture','name'],['Stage','stage'],['Health',r=>Math.round(Number(r.health_score||0)*100)+'%'],
 ['Priority',r=>Number(r.priority_score||0).toFixed(3)],['Progress',r=>Math.round(Number(r.progress||0)*100)+'%'],
 ['Next Action','scale_action'],['Capital',r=>money(r.capital_proposed)]
 ]);
 const agents=Object.values(D.agent_registry||{});
 document.getElementById('agentTable').innerHTML=table(agents,[
 ['Agent','worker_id'],['Pool','pool'],['Specialty','specialty'],['Reliability','reliability'],
 ['Free Capacity',r=>Number(r.available_capacity||0).toFixed(2)]
 ]);
 document.getElementById('taskTable').innerHTML=table(D.routed_tasks,[
 ['Task','task_id'],['Venture','venture_id'],['Action','action'],['Pool','desired_pool'],
 ['Assigned Agent','assigned_agent'],['Status','routing_status']
 ]);
 document.getElementById('roadmapTable').innerHTML=table(D.roadmap,[
 ['Week','week'],['Venture','venture_name'],['Milestone','milestone'],['Due','due_at'],['Status','status']
 ]);
 document.getElementById('notificationTable').innerHTML=table(D.notifications,[
 ['Time','timestamp'],['Severity','severity'],['Category','category'],['Message','message']
 ]);
 document.getElementById('bottleneckTable').innerHTML=table(D.bottlenecks,[
 ['Venture','venture_name'],['Severity','severity'],['Reasons',r=>(r.reasons||[]).join(', ')],['Action','recommended_action']
 ]);
 renderSearch();
}
function renderSearch(){
 const q=(document.getElementById('search').value||'').toLowerCase();
 const all=[
 ...(D.events||[]).map(x=>({type:'event',text:JSON.stringify(x),data:x})),
 ...(D.ventures||[]).map(x=>({type:'venture',text:JSON.stringify(x),data:x})),
 ...(D.routed_tasks||[]).map(x=>({type:'task',text:JSON.stringify(x),data:x})),
 ...(D.notifications||[]).map(x=>({type:'notification',text:JSON.stringify(x),data:x}))
 ].filter(x=>x.text.toLowerCase().includes(q)).slice(0,100);
 document.getElementById('searchResults').innerHTML=table(all,[['Type','type'],['Record',r=>JSON.stringify(r.data)]]);
}
async function act(action){
 document.getElementById('actionResult').textContent='Working...';
 const r=await fetch('/api/control?action='+encodeURIComponent(action),{method:'POST'});
 const d=await r.json();document.getElementById('actionResult').textContent=d.ok?'Done':'Failed';
 setTimeout(load,900);
}
load();setInterval(load,5000);
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        body=json.dumps(data,indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/ops":
            return self._json(200,OperationsEngine().run_cycle())
        if path=="/api/orchestration":
            from companyos.orchestrator.engine import OrchestratorEngine
            return self._json(200,OrchestratorEngine().run_cycle())
        if path=="/api/intelligence":
            from companyos.intelligence.engine import ExecutiveIntelligenceEngine
            return self._json(200,ExecutiveIntelligenceEngine().run_cycle())
        if path=="/api/expansion":
            from companyos.expansion.engine import ExpansionEngine
            return self._json(200,ExpansionEngine().run_cycle())
        if path=="/api/expansion/capabilities":
            from companyos.expansion.capabilities import capability_manifest
            return self._json(200,{"capabilities":capability_manifest()})
        if path=="/api/expansion/actions":
            from companyos.expansion.storage import read_json
            from pathlib import Path
            p=Path.home()/"companyos"/"companyos_runtime"/"expansion21"/"actions.json"
            return self._json(200,{"actions":read_json(p,[])})
        if path=="/api/connectors" or path=="/api/connectors/health":
            from companyos.connectors_live.engine import ConnectorEngine
            return self._json(200,ConnectorEngine().health())
        if path=="/api/connectors/actions":
            from companyos.connectors_live.storage import read_json
            from pathlib import Path
            p=Path.home()/"companyos"/"companyos_runtime"/"connectors"/"actions.json"
            return self._json(200,{"actions":read_json(p,[])})
        if path=="/api/backbone" or path=="/api/backbone/profiles":
            from companyos.api_backbone.engine import APIBackboneEngine
            return self._json(200,APIBackboneEngine().health())
        if path in {"/","/index.html"}:
            body=HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):
        parsed=urlparse(self.path)
        if parsed.path!="/api/control":
            self.send_error(404);return
        action=parse_qs(parsed.query).get("action",[""])[0]
        try:
            result=service_action(action)
            self._json(200,{"ok":True,"action":action,"result":result})
        except Exception as exc:
            self._json(400,{"ok":False,"error":str(exc)})

    def log_message(self, format, *args):
        return

def main():
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    print(json.dumps({"opscenter":"started","host":HOST,"port":PORT}),flush=True)
    server.serve_forever()

if __name__=="__main__":
    main()
