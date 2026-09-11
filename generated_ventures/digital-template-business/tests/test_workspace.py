import unittest
from pathlib import Path
class T(unittest.TestCase):
    def test_files(self):
        r=Path(__file__).resolve().parents[1]
        self.assertTrue((r/'website'/'index.html').exists())
        self.assertTrue((r/'api'/'server.py').exists())
        self.assertTrue((r/'specification.json').exists())
if __name__=='__main__': unittest.main()
