from __future__ import annotations

class SignalQueryPlan:
    """356: high-signal public issue-search queries."""

    def queries(self):
        return [
            '"manual" "workflow" is:issue is:open',
            '"too expensive" is:issue',
            '"difficult to use" is:issue',
            '"time consuming" is:issue',
            '"missing feature" is:issue is:open',
            '"integration" "pain" is:issue',
        ]
