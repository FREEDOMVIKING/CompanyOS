from typing import Dict, Any

class ConnectorRegistry:
    def __init__(self):
        self.connectors = {}

    def register(self, name: str, connector):
        self.connectors[name] = connector

    def status(self):
        return {
            name: {
                "configured": bool(getattr(connector, "configured", False)),
                "type": connector.__class__.__name__,
            }
            for name, connector in self.connectors.items()
        }

    def execute(self, name: str, action: str, payload: Dict[str, Any]):
        connector = self.connectors.get(name)
        if connector is None:
            return {"ok": False, "error": "connector_not_registered"}
        if not getattr(connector, "configured", False):
            return {"ok": False, "error": "connector_not_configured", "proposal": payload}
        return connector.execute(action, payload)

class ProposalConnector:
    configured = False

    def execute(self, action, payload):
        return {"ok": False, "error": "proposal_only", "action": action, "payload": payload}
