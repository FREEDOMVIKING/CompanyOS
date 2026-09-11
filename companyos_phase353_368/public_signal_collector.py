from __future__ import annotations
from .hackernews_source import HackerNewsSource
from .github_issues_source import GitHubIssuesSource
from .signal_query_plan import SignalQueryPlan
from .signal_provenance import SignalProvenance

class PublicSignalCollector:
    """363: collect from the initial no-key public signal network."""

    def __init__(self):
        self.hn = HackerNewsSource()
        self.gh = GitHubIssuesSource()
        self.plan = SignalQueryPlan()
        self.provenance = SignalProvenance()

    def collect(self, hn_limit=25, github_per_query=10):
        records, errors = [], []
        try:
            hn = self.hn.collect(limit=hn_limit)
            records.extend(self.provenance.attach(hn, "hackernews_topstories"))
        except Exception as exc:
            errors.append({"source":"Hacker News","error":f"{type(exc).__name__}:{exc}"})

        for query in self.plan.queries():
            try:
                gh = self.gh.collect(query, limit=github_per_query)
                records.extend(self.provenance.attach(gh, f"github:{query}"))
            except Exception as exc:
                errors.append({"source":"GitHub Issues","query":query,"error":f"{type(exc).__name__}:{exc}"})

        return {"records": records, "errors": errors}
