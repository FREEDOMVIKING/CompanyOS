from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from urllib.parse import urlparse, parse_qs

from .aggregator import ConsoleAggregator
from .control import service_action

HOST = os.environ.get("COMPANYOS_DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMPANYOS_DASHBOARD_PORT", "8765"))

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS CEO Console</title>
<style>
:root{color-scheme:dark}
body{font-family:system-ui;margin:0;background:#0b0f14;color:#e6edf3}
header{position:sticky;top:0;background:#111821;border-bottom:1px solid #2b3440;padding:14px 16px;z-index:4}
h1{margin:0;font-size:22px}
small{color:#8b949e}
.wrap{padding:14px;max-width:1100px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.card{background:#141b23;border:1px solid #2b3440;border-radius:14px;padding:14px;overflow:auto}
.good{color:#3fb950}.bad{color:#f85149}.warn{color:#d29922}
button{border:0;border-radius:9px;padding:10px 14px;margin:4px;background:#238636;color:white;font-weight:700}
button.danger{background:#da3633}button.secondary{background:#30363d}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px;border-bottom:1px solid #2b3440;vertical-align:top}
pre{white-space:pre-wrap;word-break:break-word;font-size:12px}
input{width:100%;box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #30363d;background:#0d1117;color:white}
.badge{display:inline-block;padding:3px 7px;border-radius:999px;background:#30363d;font-size:12px}
.metric{font-size:24px;font-weight:800}
</style>
</head>
<body>
<header>
<h1>CompanyOS CEO Console</h1>
<small id="stamp">Loading...</small>
</header>
<div class="wrap">
<div class="card">
<button onclick="act('start')">Start</button>
<button class="secondary" onclick="act('restart')">Restart</button>
<button class="danger" onclick="act('stop')">Stop</button>
<span id="actionResult"></span>
</div>

<div class="grid">
<div class="card"><h2>System Health</h2><div id="health"></div></div>
<div class="card"><h2>Finance</h2><div id="finance"></div></div>
<div class="card"><h2>Audit</h2><div id="audit"></div></div>
</div>

<div class="card"><h2>Venture Pipeline</h2><div id="ventures"></div></div>
<div class="card"><h2>Agent and Task Activity</h2><div id="tasks"></div></div>
<div class="card"><h2>Worker Allocation</h2><div id="workers"></div></div>
<div class="card"><h2>Executive Decisions</h2><input id="search" placeholder="Search decisions or events..." oninput="renderFiltered()"><div id="decisions"></div></div>
<div class="card"><h2>Event Stream</h2><div id="events"></div></div>
<div class="card"><h2>CEO Memory</h2><pre id="memory"></pre></div>
</div>

<script>
let DATA={};

function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function money(v){return '$'+Number(v||0).toLocaleString(undefined,{maximumFractionDigits:2})}
function table(rows,cols){
 if(!rows.length)return '<small>No data yet.</small>';
 return '<table><thead><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join('')+'</tr></thead><tbody>'+
 rows.map(r=>'<tr>'+cols.map(c=>'<td>'+esc(typeof c[1]==='function'?c[1](r):r[c[1]])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
}

async function load(){
 const r=await fetch('/api/console',{cache:'no-store'}); DATA=await r.json();
 document.getElementById('stamp').textContent='Phase '+DATA.phase+' - '+DATA.generated_at;
 const h=DATA.health||{};
 document.getElementById('health').innerHTML='<div class="metric '+(h.overall_healthy?'good':'bad')+'">'+(h.overall_healthy?'HEALTHY':'ATTENTION')+'</div>'+
 '<p>'+esc(h.active_service_count||0)+' / '+esc(h.expected_service_count||0)+' services active</p>';
 const f=DATA.finance||{};
 document.getElementById('finance').innerHTML='<div class="metric">'+money(f.available_capital)+'</div>'+
 '<p>Deployable: '+money(f.deployable)+'<br>Reserve: '+money(f.reserve)+'<br>Proposed: '+money(f.proposed_total)+'<br>Mode: <span class="badge">'+esc(f.execution_mode)+'</span></p>';
 const a=DATA.audit||{};
 document.getElementById('audit').innerHTML='<div class="metric '+(a.passed?'good':'warn')+'">'+(a.passed?'PASSED':'REVIEW')+'</div>'+
 '<p>Issues: '+esc((a.issues||[]).length)+'</p>';

 document.getElementById('ventures').innerHTML=table(DATA.ventures||[],[
 ['Name','name'],['Stage','stage'],['Priority',r=>Number(r.priority_score||0).toFixed(3)],
 ['Progress',r=>Math.round(Number(r.progress||0)*100)+'%'],['Scale Action','scale_action'],
 ['Capital',r=>money(r.capital_proposed)]
 ]);
 document.getElementById('tasks').innerHTML=table(DATA.tasks||[],[
 ['Venture','venture_id'],['Action','action'],['Status','status'],['Approval','approval_required'],['Priority','priority_score']
 ]);
 document.getElementById('workers').innerHTML=table(DATA.workers||[],[
 ['Worker','worker_id'],['Specialty','specialty'],['Load',r=>String(r.current_load||0)+' / '+String(r.capacity||0)],
 ['Assigned',r=>(r.assigned_ventures||[]).join(', ')]
 ]);
 document.getElementById('memory').textContent=JSON.stringify(DATA.memory||{},null,2);
 renderFiltered();
}

function renderFiltered(){
 const q=(document.getElementById('search').value||'').toLowerCase();
 const ds=(DATA.decisions||[]).filter(x=>JSON.stringify(x).toLowerCase().includes(q));
 const es=(DATA.events||[]).filter(x=>JSON.stringify(x).toLowerCase().includes(q));
 document.getElementById('decisions').innerHTML=table(ds,[
 ['Venture','venture_id'],['Priority','priority_score'],['Scale','scale_action'],
 ['Capital',r=>money(r.capital_proposed)],['Approval','approval_required']
 ]);
 document.getElementById('events').innerHTML=table(es,[
 ['Time','timestamp'],['Type','type'],['Outcome','outcome'],['Lesson','lesson']
 ]);
}

async function act(action){
 document.getElementById('actionResult').textContent='Working...';
 const r=await fetch('/api/control?action='+encodeURIComponent(action),{method:'POST'});
 const d=await r.json();
 document.getElementById('actionResult').textContent=d.ok?'Done':'Failed';
 setTimeout(load,800);
}

load(); setInterval(load,5000);
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        body=json.dumps(data,indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/console":
            return self._send_json(200,ConsoleAggregator().snapshot())
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
            self.send_error(404); return
        action=parse_qs(parsed.query).get("action",[""])[0]
        try:
            result=service_action(action)
            self._send_json(200,{"ok":True,"action":action,"result":result})
        except Exception as exc:
            self._send_json(400,{"ok":False,"error":str(exc)})

    def log_message(self, format, *args):
        return

def main():
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    print(json.dumps({"console":"started","host":HOST,"port":PORT}),flush=True)
    server.serve_forever()

if __name__=="__main__":
    main()
