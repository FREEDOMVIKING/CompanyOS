from companyos_phase577_592 import LifecycleStore

class LifecycleProbe:
    """724: confirm venture lifecycle persistence."""

    def __init__(self, root):
        self.store=LifecycleStore(root)

    def inspect(self, venture_id):
        record=self.store.get(venture_id)
        return {
            "present":record is not None,
            "venture_id":venture_id,
            "record":record,
            "stage":None if record is None else record.get("stage"),
        }
