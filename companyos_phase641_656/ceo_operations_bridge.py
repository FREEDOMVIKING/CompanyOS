from .operations_manager import OperationsManager
from .operations_audit import OperationsAudit

class CEOOperationsBridge:
    """655: CEO-facing operations and customer-success bridge."""

    def __init__(self, root=None):
        self.root=root

    def review_customer(self, customer):
        result=OperationsManager().review_customer(customer)
        if self.root:
            OperationsAudit(self.root).append("customer_review",result)
        return result

    def review_business(self, state):
        result=OperationsManager().review_business(state)
        if self.root:
            OperationsAudit(self.root).append("business_operations_review",result)
        return result
