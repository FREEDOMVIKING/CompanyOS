class CommunicationOrchestrator:
    def draft(self, audience, objective, context=None):
        return {
            "audience":audience,
            "objective":objective,
            "context":context or {},
            "message":{
                "subject":f"Update: {objective}",
                "body":f"Prepared communication for {audience} regarding: {objective}"
            },
            "status":"draft_ready"
        }

    def delivery_action(self, draft):
        return {"kind":"send_external_email","draft":draft}
