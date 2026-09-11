import importlib.util, json
from pathlib import Path
from .util import stable_id

BUILTINS=[
("strategy","Executive Strategy","5.0",["planning","prioritization","portfolio"]),
("research","Research Intelligence","5.0",["research","evidence","market_analysis"]),
("product","Product Intelligence","5.0",["product","packaging","pricing"]),
("marketing","Marketing Intelligence","5.0",["campaigns","positioning","acquisition"]),
("finance","Finance Intelligence","5.0",["budget","revenue","forecasting","cashflow"]),
("operations","Operations Intelligence","5.0",["workflow","health","capacity"]),
("customer","Customer Intelligence","5.0",["support","retention","feedback"]),
("launch","Launch Intelligence","5.0",["validation","launch","handoff"]),
("recovery","Recovery Intelligence","5.0",["diagnostics","retry","repair"]),
("memory","Executive Memory","5.0",["memory","lessons","decision_history"]),
]

class PluginManager:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.plugin_dir=self.home/"companyos_plugins"
        self.plugin_dir.mkdir(parents=True,exist_ok=True)

    def register_builtins(self):
        for pid,n,v,caps in BUILTINS:
            self.db.upsert_plugin(pid,n,v,"builtin",None,caps,True,"OK")

    def discover(self):
        self.register_builtins()
        found=0
        for manifest in self.plugin_dir.glob("*/plugin.json"):
            try:
                d=json.loads(manifest.read_text(encoding="utf-8"))
                pid=d.get("plugin_id") or stable_id("plugin",manifest.parent.name)
                self.db.upsert_plugin(pid,d.get("name",manifest.parent.name),d.get("version","1.0"),
                                      str(manifest.parent),d.get("entrypoint"),d.get("capabilities",[]),
                                      d.get("enabled",True),"OK")
                found+=1
            except Exception as e:
                self.db.event("plugin.discovery_error","plugin_manager",{"path":str(manifest),"error":str(e)})
        return found

    def capabilities(self):
        out={}
        for p in self.db.list_plugins():
            if not p.get("enabled"): continue
            for cap in p.get("capabilities",[]):
                out.setdefault(cap,[]).append(p["plugin_id"])
        return out
