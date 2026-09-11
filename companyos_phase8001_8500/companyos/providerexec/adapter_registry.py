class AdapterRegistry:
    def __init__(self):
        self._items={}

    def register(self, adapter):
        self._items[adapter.name]=adapter
        return adapter.name

    def get(self,name):
        return self._items.get(name)

    def for_capability(self,capability):
        return [a for a in self._items.values() if capability in getattr(a,"capabilities",[])]

    def inventory(self):
        return [{
            "name":a.name,
            "capabilities":list(getattr(a,"capabilities",[])),
            "live_supported":bool(getattr(a,"live_supported",False))
        } for a in self._items.values()]
