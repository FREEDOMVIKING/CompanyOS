import json
from pathlib import Path
from .util import sid, now, read_json

DEFAULTS={
  "user_agent":"CompanyOS-OpportunityResearch/1.0",
  "timeout_seconds":12,
  "max_items_per_source":40,
  "sources":[
    {
      "name":"Hacker News Front Page",
      "type":"json",
      "url":"https://hn.algolia.com/api/v1/search?tags=front_page",
      "enabled":False,
      "category":"technology"
    }
  ]
}

class SourceRegistry:
    def __init__(self,home,db):
        self.home=Path(home); self.db=db
        self.path=self.home/"config"/"opportunity_sources.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps(DEFAULTS,indent=2),encoding="utf-8")

    def config(self):
        return read_json(self.path,DEFAULTS)

    def sync(self):
        cfg=self.config(); n=0
        for s in cfg.get("sources",[]) or []:
            name=s.get("name"); url=s.get("url")
            if not name or not url: continue
            source_id=s.get("source_id") or sid("source",name,url)
            self.db.exec("""INSERT INTO research_sources
            (source_id,name,source_type,url,enabled,status,last_http_status,last_error,last_checked_at,payload_json,updated_at)
            VALUES(?,?,?,?,?,'CONFIGURED',NULL,NULL,NULL,?,?)
            ON CONFLICT(source_id) DO UPDATE SET name=excluded.name,source_type=excluded.source_type,
            url=excluded.url,enabled=excluded.enabled,payload_json=excluded.payload_json,updated_at=excluded.updated_at""",
            (source_id,name,s.get("type","rss"),url,1 if s.get("enabled",False) else 0,json.dumps(s),now()))
            n+=1
        return n
