import hashlib

class VentureIdentity:
    """577: stable venture identity across research, validation, build, and operations."""

    def make(self, name, theme=None):
        raw = f"{name or 'venture'}::{theme or ''}".strip().lower()
        return "venture_" + hashlib.sha256(raw.encode()).hexdigest()[:12]
