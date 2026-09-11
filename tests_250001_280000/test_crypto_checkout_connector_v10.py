import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from companyos.crypto_checkout_connector_v10.app import render_page

class CryptoCheckoutConnectorV10Tests(unittest.TestCase):
    @patch("companyos.crypto_checkout_connector_v10.app.payment_status")
    @patch("companyos.crypto_checkout_connector_v10.app.catalog")
    def test_page_contains_crypto_checkout(self, mock_catalog, mock_payment):
        mock_catalog.return_value = {
            "products": [{
                "product_id": "test-product",
                "name": "Test Product",
                "pricing": {"recommended": 39},
                "quality_passed": True,
            }]
        }
        mock_payment.return_value = {
            "wallet_public_address_loaded": True,
            "wallet_public_address_masked": "5DRKX...TnCnQ",
        }
        page = render_page()
        self.assertIn("Pay with crypto", page)
        self.assertIn("Create payment invoice", page)
        self.assertIn("CompanyOS will verify", page)
        self.assertNotIn("private_key", page.lower())

if __name__ == "__main__":
    unittest.main()
