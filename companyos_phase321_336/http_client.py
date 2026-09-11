from __future__ import annotations
import urllib.request

class ResearchHttpClient:
    """322: bounded HTTP GET client for configured research sources."""

    def __init__(self, timeout=20, user_agent="CompanyOS-Research/1.0"):
        self.timeout = int(timeout)
        self.user_agent = user_agent

    def get(self, url, headers=None):
        hdrs = {"User-Agent": self.user_agent, "Accept": "*/*"}
        hdrs.update(headers or {})
        req = urllib.request.Request(url, headers=hdrs, method="GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read()
            return {
                "status": getattr(resp, "status", 200),
                "content_type": resp.headers.get("Content-Type", ""),
                "body": body,
                "url": resp.geturl(),
            }
