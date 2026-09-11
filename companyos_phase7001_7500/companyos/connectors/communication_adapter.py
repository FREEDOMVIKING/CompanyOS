class CommunicationAdapter:
    def draft(self, channel, recipient, subject, body):
        return {
            "capability":"communication",
            "channel":channel,
            "recipient":recipient,
            "subject":subject,
            "body":body,
            "status":"draft_ready"
        }

    def send_action(self, draft):
        return {"kind":"send_external_message","draft":draft}
