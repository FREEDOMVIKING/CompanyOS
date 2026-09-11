from __future__ import annotations
import json
import urllib.parse
import urllib.request

class GitHubIssuesSource:
    """354: search public GitHub issues for repeated software/workflow pain."""

    ENDPOINT = "https://api.github.com/search/issues"

    def __init__(self, timeout=20):
        self.timeout = int(timeout)

    def collect(self, query, limit=30):
        params = urllib.parse.urlencode({
            "q": query,
            "per_page": max(1, min(100, int(limit))),
            "sort": "updated",
            "order": "desc",
        })
        req = urllib.request.Request(
            f"{self.ENDPOINT}?{params}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "CompanyOS-Research/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        records = []
        for item in data.get("items", []):
            title = item.get("title") or ""
            body = item.get("body") or ""
            records.append({
                "source": "GitHub Issues",
                "title": title or "Untitled",
                "text": body or title,
                "url": item.get("html_url"),
                "published_at": item.get("updated_at"),
                "metadata": {
                    "format": "github_issue_search",
                    "state": item.get("state"),
                    "comments": item.get("comments"),
                    "repository_url": item.get("repository_url"),
                },
            })
        return records
