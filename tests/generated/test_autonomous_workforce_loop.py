import inspect
from companyos.runtime import autonomous_workforce_loop as m
def test_canonical(): assert "f.active()" in inspect.getsource(m.workers)
def test_factory_cycle(): assert "f.cycle()" in inspect.getsource(m.cycle)
def test_no_fake_profit(): assert '"profit_attributed":0.0' in inspect.getsource(m.cycle)
def test_gates(): assert '"external_action_authorized":False' in inspect.getsource(m.cycle)
