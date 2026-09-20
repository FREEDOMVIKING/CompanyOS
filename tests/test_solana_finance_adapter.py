from companyos.connectors_live.solana_finance_adapter import (
    b58decode,
    b58encode,
    ed25519_public_key,
    ed25519_sign,
    shortvec,
)

def test_base58_roundtrip():
    raw=b"\x00\x00hello-solana"
    assert b58decode(b58encode(raw))==raw

def test_shortvec():
    assert shortvec(0)==b"\x00"
    assert shortvec(127)==b"\x7f"
    assert shortvec(128)==b"\x80\x01"

def test_rfc8032_ed25519_vector_1():
    seed=bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    expected_pub=bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    expected_sig=bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    assert ed25519_public_key(seed)==expected_pub
    assert ed25519_sign(seed,b"")==expected_sig
