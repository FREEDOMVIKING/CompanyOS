class DeploymentProviderAdapter:
    name="deployment_provider"
    capabilities=["deploy"]
    live_supported=False

    def execute(self, request, timeout=60, live=False):
        return {
            "success":True,
            "simulated":not live,
            "adapter":self.name,
            "environment":request.get("environment"),
            "artifact":request.get("artifact"),
            "status":"deployment_plan_executed_simulated" if not live else "adapter_specific_live_deploy_required"
        }
