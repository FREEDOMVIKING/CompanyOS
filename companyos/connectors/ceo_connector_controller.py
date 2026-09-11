from .registry import ConnectorRegistry
from .credential_refs import CredentialReferenceStore
from .health_router import ConnectorHealthRouter
from .capability_discovery import CapabilityDiscovery
from .fallback_engine import FallbackEngine
from .approval_router import ConnectorApprovalRouter
from .connector_state import ConnectorState
from .connector_audit import ConnectorAudit

class CEOConnectorController:
    def __init__(self, root):
        self.root=root
        self.registry=ConnectorRegistry(root)
        self.credentials=CredentialReferenceStore(root)
        self.state=ConnectorState(root)
        self.audit=ConnectorAudit(root)

    def run(self, health=None, requested_capabilities=None, actions=None):
        connectors=self.registry.list_enabled()
        ranked=ConnectorHealthRouter().rank(connectors,health or [])
        capabilities=CapabilityDiscovery().discover(connectors)
        routes={}
        for cap in requested_capabilities or []:
            candidates=[x for x in ranked if cap in x.get("capabilities",[])]
            routes[cap]=FallbackEngine().choose(candidates)
        credential_status={c["name"]:self.credentials.status(c["name"]) for c in connectors}
        authority=ConnectorApprovalRouter().route(actions or [])
        result={
            "success":True,
            "status":"real_world_connector_capability_cycle_complete",
            "connector_count":len(connectors),
            "capabilities":capabilities,
            "ranked_connectors":ranked,
            "capability_routes":routes,
            "credential_status":credential_status,
            **authority
        }
        self.state.save(result)
        self.audit.append("connector_cycle",result)
        return result
