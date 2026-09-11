class QueueHandoff:
    """898: normalize terminal handoff payloads."""
    def build(self,terminal,build=None,archive=None,review=None):
        return {"terminal":terminal,"build":build,"archive":archive,"review":review}
