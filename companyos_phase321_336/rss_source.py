from __future__ import annotations
import xml.etree.ElementTree as ET

class RSSSource:
    """323: RSS/Atom feed parser."""

    def parse(self, body, source_name, source_url):
        root = ET.fromstring(body)
        records = []

        # RSS
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()
            link = (item.findtext("link") or source_url).strip()
            pub = (item.findtext("pubDate") or "").strip()
            if title or desc:
                records.append({
                    "source": source_name,
                    "title": title or "Untitled",
                    "text": desc,
                    "url": link,
                    "published_at": pub or None,
                    "metadata": {"format": "rss"},
                })

        # Atom
        ns = "{http://www.w3.org/2005/Atom}"
        for entry in root.findall(f".//{ns}entry"):
            title = (entry.findtext(f"{ns}title") or "").strip()
            summary = (
                entry.findtext(f"{ns}summary")
                or entry.findtext(f"{ns}content")
                or ""
            ).strip()
            link_el = entry.find(f"{ns}link")
            link = link_el.attrib.get("href") if link_el is not None else source_url
            published = (
                entry.findtext(f"{ns}published")
                or entry.findtext(f"{ns}updated")
                or ""
            ).strip()
            if title or summary:
                records.append({
                    "source": source_name,
                    "title": title or "Untitled",
                    "text": summary,
                    "url": link,
                    "published_at": published or None,
                    "metadata": {"format": "atom"},
                })
        return records
