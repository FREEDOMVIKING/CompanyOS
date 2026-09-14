import os, tempfile, unittest
from pathlib import Path
from companyos.runtime.runtime_control import _pid_is_alive, _read_pid_file

class RuntimeControlStalePidRecoveryV21Tests(unittest.TestCase):
    def test_current_pid_is_alive(self):
        self.assertTrue(_pid_is_alive(os.getpid()))

    def test_impossible_pid_is_dead(self):
        self.assertFalse(_pid_is_alive(999999))

    def test_read_pid_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "pid"
            p.write_text("123\n")
            self.assertEqual(_read_pid_file(p), 123)

if __name__ == "__main__":
    unittest.main()
