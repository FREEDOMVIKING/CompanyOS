class CrossDepartmentWorkflowEngine:
    def build(self, objective):
        return [
            {"name":"research","department":"research","capability":"research"},
            {"name":"validate","department":"research","capability":"research"},
            {"name":"build","department":"product","capability":"build"},
            {"name":"deploy","department":"operations","capability":"deploy"},
            {"name":"operate","department":"operations","capability":"operations"},
            {"name":"optimize","department":"growth","capability":"growth"},
        ]
