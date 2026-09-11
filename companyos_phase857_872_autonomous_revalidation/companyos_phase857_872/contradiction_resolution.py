class ContradictionResolutionTasks:
    def build(self,topics):
        return [{"dimension":"contradiction","topic":t,"query":f"verify conflicting claim with primary sources: {t}"} for t in (topics or [])]
