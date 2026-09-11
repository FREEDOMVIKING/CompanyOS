from companyos_phase705_720 import RuntimeState

class StateProbe:
    """727: inspect unified runtime persistent state."""

    def __init__(self, root):
        self.state=RuntimeState(root)

    def inspect(self):
        return self.state.load()
