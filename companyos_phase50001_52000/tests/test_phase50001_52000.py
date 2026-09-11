from pathlib import Path
import tempfile
from companyos.livegate import OneShotAuthorization

def test_one_shot_auth():
    root=Path(tempfile.mkdtemp())
    a=OneShotAuthorization(root)
    c=a.create(1,"D",ttl_seconds=60)
    assert a.validate(c["token"],0.5,"D")["allowed"] is True

def test_amount_cap():
    root=Path(tempfile.mkdtemp())
    a=OneShotAuthorization(root)
    c=a.create(1,"D",ttl_seconds=60)
    assert a.validate(c["token"],2,"D")["allowed"] is False
