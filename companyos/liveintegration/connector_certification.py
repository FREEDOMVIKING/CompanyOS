class ConnectorCertification:
    def certify(self, connector):
        checks={
            "enabled":bool(connector.get("enabled",False)),
            "capabilities":bool(connector.get("capabilities")),
            "health":float(connector.get("health_score",0))>=.7,
            "credentials":bool(connector.get("credentials_ready",False)),
            "fallback":bool(connector.get("fallback_ready",False)),
            "receipts":bool(connector.get("receipts_enabled",False)),
        }
        return {
            "name":connector.get("name"),
            "certified":all(checks.values()),
            "checks":checks
        }
