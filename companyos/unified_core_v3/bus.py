class EventBus:
    def __init__(self, db):
        self.db=db

    def publish(self, event_type, source, payload, target=None):
        self.db.event(event_type,source,payload,target)

    def recent(self, limit=100):
        return self.db.list_events(limit)
