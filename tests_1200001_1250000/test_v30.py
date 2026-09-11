
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_finance_treasury_v30.engine import FinanceV30, wj
class T(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); (h/".companyos_runtime").mkdir()
            (h/"storefront_sales_records_v29").mkdir()
            wj(h/"storefront_sales_records_v29/orders.json",{"orders":[{"order_id":"o1","product_id":"p1","amount_usd":49,"payment_status":"PAID_VERIFIED"}]})
            wj(h/".companyos_runtime/finance_expenses_v30.json",{"expenses":[{"reference":"e1","product_id":"p1","amount_usd":10,"verified":True}]})
            wj(h/".companyos_runtime/autonomous_revenue_expansion_v26_live.json",{"portfolio":[{"venture_id":"v1","name":"Test","portfolio_score":85}]})
            s=FinanceV30(h).run_cycle()
            self.assertEqual(s["status"],"autonomous_finance_treasury_ready")
            self.assertEqual(s["pnl"]["net_profit_usd"],39.0)
            self.assertFalse(s["automatic_transfers_enabled"])
if __name__=="__main__": unittest.main()
