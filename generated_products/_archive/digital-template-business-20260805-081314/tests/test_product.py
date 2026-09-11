import unittest
from pathlib import Path

class RevenueProductTests(unittest.TestCase):
    def test_required_files(self):
        root=Path(__file__).resolve().parents[1]
        required=[
            root/'website'/'index.html',
            root/'sales'/'product_description.md',
            root/'marketing'/'launch_copy.md',
            root/'product'/'docs'/'quick_start.md',
            root/'review'/'external_launch_checklist.md',
            root/'product_specification.json',
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))

if __name__=='__main__':
    unittest.main()
