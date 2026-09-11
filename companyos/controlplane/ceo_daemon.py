from .event_bus import EventBus
from .daemon_state import DaemonState
from .department_loop import DepartmentLoop

class CEODaemon:
    def __init__(self,root):
        self.bus=EventBus(root)
        self.state=DaemonState(root)

    def run_once(self, departments=None, max_events=10):
        departments=departments or ["operations"]
        processed=[]
        for i in range(int(max_events)):
            event=self.bus.next()
            if not event:break
            dept=(event.get("payload") or {}).get("department") or departments[i % len(departments)]
            result=DepartmentLoop().run_once(dept,event)
            self.bus.ack(event["event_id"])
            processed.append(result)
        state={"running":True,"processed":len(processed),"events":self.bus.snapshot()}
        self.state.save(state)
        return {"processed":processed,"state":state}
