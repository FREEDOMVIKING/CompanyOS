from __future__ import annotations
import html,json
from pathlib import Path
def instrument(site_dir,venture_id,endpoint):
    p=Path(site_dir)/"index.html"
    if not p.exists():raise FileNotFoundError(p)
    marker="companyos-evidence-v1"
    s=p.read_text()
    if marker in s:return {"instrumented":False,"reason":"already_instrumented"}
    vid=json.dumps(str(venture_id));ep=json.dumps(str(endpoint).rstrip("/")+"/event")
    js=f"""<script id="{marker}">
(()=>{{const V={vid},E={ep};function send(kind){{const event_id=(crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2));fetch(E,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{venture_id:V,kind,event_id,timestamp:new Date().toISOString()}}),keepalive:true}}).catch(()=>{{}})}}send('page_view');document.addEventListener('submit',()=>send('lead'));document.addEventListener('click',e=>{{if(e.target.closest('[data-companyos-conversion]'))send('conversion')}})}})();
</script>"""
    s=s.replace("</body>",js+"</body>") if "</body>" in s else s+js
    p.write_text(s)
    return {"instrumented":True,"venture_id":venture_id,"endpoint":endpoint}
