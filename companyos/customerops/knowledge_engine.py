class CustomerKnowledgeEngine:
    def learn(self, resolved_tickets):
        articles=[]
        seen=set()
        for t in resolved_tickets or []:
            issue=t.get("issue")
            if issue and issue not in seen:
                seen.add(issue)
                articles.append({"title":"How to resolve: "+issue,"source_ticket":t.get("ticket_id"),"status":"draft_internal"})
        return articles
