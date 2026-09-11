class DepartmentLoop:
    def run_once(self, department, event):
        return {
            "department":department,
            "event_id":event.get("event_id"),
            "topic":event.get("topic"),
            "status":"complete",
            "result":{"handled":True,"department":department}
        }
