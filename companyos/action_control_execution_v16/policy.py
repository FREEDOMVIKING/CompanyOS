FINANCIAL_OR_PURCHASE={"PURCHASE_DOMAIN","WALLET_SIGN","FUND_TRANSFER","SPEND","PAYMENT","PURCHASE","PAY_INVOICE"}
SAFE_TYPES={"PUBLISH_STATIC_SITE","WRITE_ANALYTICS_EVENT","POST_WEBHOOK"}
class ActionPolicy:
    def classify(self,a):
        typ=(a.get("action_type") or "").upper()
        if typ in FINANCIAL_OR_PURCHASE or any(x in typ for x in ("WALLET","FUND_TRANSFER","PURCHASE","PAYMENT","SPEND")):
            return {"decision":"BLOCK_AUTOMATION","reason":"financial_or_purchase","auto_approve":False}
        if typ in SAFE_TYPES:
            return {"decision":"MANUAL_APPROVAL_REQUIRED","reason":"non_financial_external_side_effect","auto_approve":False}
        return {"decision":"MANUAL_APPROVAL_REQUIRED","reason":"default_review","auto_approve":False}
