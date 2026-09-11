class PolicyExceptionManager:
    def evaluate(self, exception):
        return {
            "exception":exception,
            "requires_owner":True,
            "requires_expiration":True,
            "requires_compensating_control":True,
            "auto_approve":False
        }
