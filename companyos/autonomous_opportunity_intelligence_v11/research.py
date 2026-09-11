import json, urllib.request, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from .util import sid, now, norm_text

class ResearchEngine:
    def __init__(self,db,source_registry):
        self.db=db; self.registry=source_registry

    def _fetch(self,url,timeout,user_agent):
        req=urllib.request.Request(url,headers={"User-Agent":user_agent,"Accept":"application/json, application/rss+xml, application/xml, text/xml, */*"})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.getcode(), r.headers.get("content-type",""), r.read(2_000_000)

    def _json_items(self,blob,source_cfg):
        data=json.loads(blob.decode("utf-8","replace"))
        items=[]
        if isinstance(data,dict) and isinstance(data.get("hits"),list):
            seq=data["hits"]
            for x in seq:
                items.append({
                    "title":x.get("title") or x.get("story_title"),
                    "url":x.get("url") or x.get("story_url"),
                    "summary":x.get("story_text") or "",
                    "published_at":x.get("created_at"),
                    "category":source_cfg.get("category","technology")
                })
        elif isinstance(data,list):
            for x in data:
                if not isinstance(x,dict): continue
                items.append({
                    "title":x.get("title") or x.get("name"),
                    "url":x.get("url") or x.get("link"),
                    "summary":x.get("summary") or x.get("description") or "",
                    "published_at":x.get("published_at") or x.get("date"),
                    "category":x.get("category") or source_cfg.get("category","general")
                })
        return items

    def _xml_items(self,blob,source_cfg):
        root=ET.fromstring(blob)
        items=[]
        nodes=root.findall(".//item")
        if not nodes:
            nodes=root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for n in nodes:
            def txt(tag):
                e=n.find(tag)
                return norm_text(e.text if e is not None else "")
            title=txt("title") or txt("{http://www.w3.org/2005/Atom}title")
            link=txt("link")
            if not link:
                le=n.find("{http://www.w3.org/2005/Atom}link")
                if le is not None: link=le.attrib.get("href","")
            summary=txt("description") or txt("{http://www.w3.org/2005/Atom}summary")
            pub=txt("pubDate") or txt("{http://www.w3.org/2005/Atom}updated")
            items.append({"title":title,"url":link,"summary":summary,"published_at":pub,
                          "category":source_cfg.get("category","general")})
        return items

    def cycle(self):
        cfg=self.registry.config()
        timeout=int(cfg.get("timeout_seconds",12))
        user_agent=cfg.get("user_agent","CompanyOS-OpportunityResearch/1.0")
        max_items=int(cfg.get("max_items_per_source",40))
        fetched=0; stored=0; failed=0

        sources=self.db.rows("SELECT * FROM research_sources WHERE enabled=1")
        for s in sources:
            source_cfg=json.loads(s["payload_json"] or "{}")
            try:
                code,ctype,blob=self._fetch(s["url"],timeout,user_agent)
                fetched+=1
                if s["source_type"]=="json" or "json" in ctype:
                    items=self._json_items(blob,source_cfg)
                else:
                    items=self._xml_items(blob,source_cfg)
                for x in items[:max_items]:
                    title=norm_text(x.get("title"))
                    if not title: continue
                    item_id=sid("item",s["source_id"],x.get("url") or title)
                    self.db.exec("""INSERT OR IGNORE INTO research_items
                    (item_id,source_id,title,url,published_at,summary,category,payload_json,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (item_id,s["source_id"],title,x.get("url"),x.get("published_at"),
                     norm_text(x.get("summary")),x.get("category","general"),json.dumps(x),now()))
                    stored+=1
                self.db.exec("""UPDATE research_sources SET status='OK',last_http_status=?,last_error=NULL,
                last_checked_at=?,updated_at=? WHERE source_id=?""",(code,now(),now(),s["source_id"]))
            except Exception as e:
                failed+=1
                self.db.exec("""UPDATE research_sources SET status='ERROR',last_error=?,last_checked_at=?,
                updated_at=? WHERE source_id=?""",(str(e)[:500],now(),now(),s["source_id"]))
        self.db.event("research.cycle","research_engine",{"sources_fetched":fetched,"items_seen":stored,"sources_failed":failed})
        return {"sources_fetched":fetched,"items_seen":stored,"sources_failed":failed}
