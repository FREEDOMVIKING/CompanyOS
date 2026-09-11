from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material


@dataclass(frozen=True)
class OfflineSigningProof:
    backend: str
    signature_verified: bool
    public_address: str | None
    message_sha256: str
    transaction_created: bool = False
    transaction_broadcast: bool = False


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        check=False,
        timeout=30,
    )


def prove_ed25519_signing(secret: str, encoding: str = "auto") -> OfflineSigningProof:
    """
    Produce and verify an OFFLINE Ed25519 signature over a harmless fixed challenge.

    No Solana transaction is created.
    No RPC call is made.
    Nothing is broadcast.
    The private key is never printed.
    """
    material = load_signer_material(secret, encoding)

    if material.key_length not in (32, 64):
        raise ValueError("unsupported_key_length")

    openssl = shutil.which("openssl")
    if not openssl:
        raise RuntimeError("openssl_not_found")

    # Solana/Ed25519 64-byte exported secret is seed(32) + public key(32).
    seed = material.secret_bytes[:32]
    pub = material.secret_bytes[32:64] if material.key_length == 64 else None

    if pub is None:
        raise RuntimeError(
            "offline_public_key_unavailable_for_32_byte_seed_without_crypto_backend"
        )

    # Minimal DER wrappers for Ed25519 raw seed/public key.
    # PKCS#8 PrivateKeyInfo:
    # 30 2e 02 01 00 30 05 06 03 2b 65 70 04 22 04 20 <32-byte-seed>
    priv_der = bytes.fromhex("302e020100300506032b657004220420") + seed

    # SubjectPublicKeyInfo:
    # 30 2a 30 05 06 03 2b 65 70 03 21 00 <32-byte-public>
    pub_der = bytes.fromhex("302a300506032b6570032100") + pub

    challenge = (
        b"CompanyOS Phase73 offline signing proof v1\n"
        b"Purpose: verify local Ed25519 signing capability only.\n"
        b"No transaction. No RPC. No broadcast.\n"
    )
    digest = hashlib.sha256(challenge).hexdigest()

    with tempfile.TemporaryDirectory(prefix="companyos_phase73_") as td:
        td = os.path.abspath(td)
        priv_path = os.path.join(td, "ed25519_private.der")
        pub_path = os.path.join(td, "ed25519_public.der")
        msg_path = os.path.join(td, "challenge.bin")
        sig_path = os.path.join(td, "challenge.sig")

        # Restrictive file mode for private key material.
        fd = os.open(priv_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, priv_der)
        finally:
            os.close(fd)

        with open(pub_path, "wb") as f:
            f.write(pub_der)
        with open(msg_path, "wb") as f:
            f.write(challenge)

        sign = _run([
            openssl, "pkeyutl",
            "-sign",
            "-rawin",
            "-inkey", priv_path,
            "-keyform", "DER",
            "-in", msg_path,
            "-out", sig_path,
        ])
        if sign.returncode != 0:
            raise RuntimeError(
                "openssl_sign_failed:" +
                sign.stderr.decode(errors="ignore")[:240]
            )

        verify = _run([
            openssl, "pkeyutl",
            "-verify",
            "-rawin",
            "-pubin",
            "-inkey", pub_path,
            "-keyform", "DER",
            "-in", msg_path,
            "-sigfile", sig_path,
        ])

        verified = verify.returncode == 0

    return OfflineSigningProof(
        backend="openssl_ed25519",
        signature_verified=verified,
        public_address=material.public_address,
        message_sha256=digest,
    )
