from companyos.runtime import autonomous_workforce_loop as m
class F:
    def __init__(self):
        self.reg={"workers":[
          {"worker_id":"a","status":"probation"},
          {"worker_id":"b","status":"permanent"},
          {"worker_id":"c","status":"retired"}]}
    def active(self,t):
        raise AssertionError("Factory.active must not receive worker dict")
def test_registry_status():
    assert [x["worker_id"] for x in m._active(F())]==["a","b"]
