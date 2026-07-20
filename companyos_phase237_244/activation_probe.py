from __future__ import annotations
from companyos_phase229_236 import ConnectionProbe

class ActivationProbe:
    """241: run the real provider/coder contract probe."""

    def run(self, coder_command):
        return ConnectionProbe().probe(coder_command)
