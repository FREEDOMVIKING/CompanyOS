from .sandbox_connector import SandboxPaymentConnector

class PaymentConnectorRegistry:
    def __init__(self):
        self._connectors = {
            "sandbox": SandboxPaymentConnector()
        }

    def register(self, name, connector):
        self._connectors[str(name)] = connector

    def get(self, name):
        return self._connectors.get(str(name))

    def names(self):
        return sorted(self._connectors)
