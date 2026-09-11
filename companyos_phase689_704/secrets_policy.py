class SecretsPolicy:
    """695: least-privilege secrets access."""

    def evaluate(self, request):
        requested = set(request.get("requested_secrets",[]))
        allowed = set(request.get("allowed_secrets",[]))
        denied = sorted(requested - allowed)
        return {
            "approved": not denied,
            "denied": denied,
            "principle": "least_privilege",
        }
