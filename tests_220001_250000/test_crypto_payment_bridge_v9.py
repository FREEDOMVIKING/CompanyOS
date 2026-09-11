import os
import tempfile
import unittest
from pathlib import Path
from companyos.crypto_payment_bridge_v9.bridge import CryptoPaymentBridgeV9, write_json

TEST_WALLET = "5DRKXC4SD4TfSTPG8aQej7kBbZrtX8Tgpn4PgRbTnCnQ"

class CryptoPaymentBridgeV9Tests(unittest.TestCase):
    def seed(self, home):
        runtime = home / "companyos_runtime" / "storefront_sales_v8_190001_220000"
        runtime.mkdir(parents=True, exist_ok=True)
        product = home / "generated_products_v7" / "test-product"
        (product / "product").mkdir(parents=True, exist_ok=True)
        package = home / "storefront_v8_fulfillment" / "test-product.zip"
        package.parent.mkdir(parents=True, exist_ok=True)
        package.write_bytes(b"zip")
        write_json(runtime / "catalog.json", {
            "products": [{
                "product_id": "test-product",
                "name": "Test Product",
                "pricing": {"recommended": 39},
                "fulfillment_package": str(package),
            }]
        })
        write_json(runtime / "orders.json", {"orders": []})

    def test_invoice_is_review_safe(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.environ.get("COMPANYOS_WALLET_ADDRESS")
            os.environ["COMPANYOS_WALLET_ADDRESS"] = TEST_WALLET
            try:
                home = Path(td)
                self.seed(home)
                engine = CryptoPaymentBridgeV9(home)
                result, code = engine.create_invoice("test-product", "buyer@example.com")
                self.assertEqual(code, 201)
                invoice = result["invoice"]
                self.assertEqual(invoice["status"], "AWAITING_VERIFIED_PAYMENT")
                self.assertEqual(invoice["wallet_address"], TEST_WALLET)
                self.assertNotIn("private_key", json_text(result))
                state = engine.status()
                self.assertTrue(state["wallet_public_address_loaded"])
                self.assertFalse(state["private_key_displayed"])
            finally:
                if old is None:
                    os.environ.pop("COMPANYOS_WALLET_ADDRESS", None)
                else:
                    os.environ["COMPANYOS_WALLET_ADDRESS"] = old

def json_text(value):
    import json
    return json.dumps(value).lower()

if __name__ == "__main__":
    unittest.main()
