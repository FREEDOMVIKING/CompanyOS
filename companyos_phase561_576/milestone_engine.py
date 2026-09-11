class MilestoneEngine:
    """570: derive next milestone from venture state."""

    ORDER = ["research","validation","build","launch","operations","scale"]

    def next(self, current):
        try:
            idx=self.ORDER.index(current)
        except ValueError:
            return "research"
        return self.ORDER[min(idx+1,len(self.ORDER)-1)]
