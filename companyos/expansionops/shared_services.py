class SharedServicesAllocator:
    def allocate(self, ventures, services):
        allocations=[]
        for v in ventures or []:
            for s in services or []:
                if s.get("enabled",True):
                    allocations.append({
                        "venture_id":v.get("venture_id"),
                        "service":s.get("name"),
                        "shared":True
                    })
        return allocations
