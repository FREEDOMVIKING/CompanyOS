import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from companyos.controlplane.storage import atomic_write_json, read_json
from companyos.controlplane.processes import pid_alive
from companyos.controlplane.health import collect_health

class ControlPlaneTests(unittest.TestCase):
    def test_atomic_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            atomic_write_json(path, {"ok": True, "count": 3})
            self.assertEqual(read_json(path, {}), {"ok": True, "count": 3})

    def test_read_json_default_for_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_json(Path(tmp) / "missing.json", {"x": 1}), {"x": 1})

    def test_current_process_alive(self):
        self.assertTrue(pid_alive(os.getpid()))

    def test_invalid_pid_not_alive(self):
        self.assertFalse(pid_alive(-1))

    def test_health_snapshot_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            runtime = home / "companyos_runtime" / "controlplane"
            runtime.mkdir(parents=True)
            atomic_write_json(runtime / "services.json", {"services": {}})
            with patch("companyos.controlplane.health.companyos_home", return_value=home),                  patch("companyos.controlplane.health.runtime_dir", return_value=runtime):
                health = collect_health()
                self.assertEqual(health["phase"], "18301-18400")
                self.assertIn("services", health)
                self.assertIn("legacy_tests", health)

if __name__ == "__main__":
    unittest.main()
