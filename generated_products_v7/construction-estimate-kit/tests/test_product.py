import unittest
from pathlib import Path
class ProductTest(unittest.TestCase):
    def test_required_assets(self):
        root=Path(__file__).resolve().parents[1]
        required=[
            root/'product_manifest.json',
            root/'website'/'index.html',
            root/'sales'/'product_page_copy.md',
            root/'marketing'/'email_campaign.md',
            root/'marketing'/'social_posts.md',
            root/'feedback'/'feedback_schema.json',
            root/'review'/'marketplace_publish_request.json',
        ]
        for p in required:self.assertTrue(p.exists(),str(p))
if __name__=='__main__':unittest.main()
