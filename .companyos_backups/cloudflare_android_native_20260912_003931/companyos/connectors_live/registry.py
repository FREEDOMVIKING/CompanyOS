import os
from .adapters import SMTPConnector, RESTConnector, HostingConnector as VercelHostingConnector, DomainConnector, CRMConnector, AccountingConnector, BankingConnector, CryptoConnector
from .cloudflare_adapter import CloudflareHostingConnector

def build_registry(config):
    g=config.get("global",{})
    def merged(name): return {**g,**config.get(name,{})}
    hc=merged("hosting")
    provider=str(os.environ.get("COMPANYOS_HOSTING_PROVIDER",hc.get("provider","cloudflare"))).lower().strip()
    hosting=VercelHostingConnector(hc) if provider=="vercel" else CloudflareHostingConnector(hc)
    return {
        "smtp":SMTPConnector(merged("smtp")),"rest_api":RESTConnector(merged("rest_api")),
        "hosting":hosting,"domains":DomainConnector(merged("domains")),"crm":CRMConnector(merged("crm")),
        "accounting":AccountingConnector(merged("accounting")),"banking":BankingConnector(merged("banking")),
        "crypto":CryptoConnector(merged("crypto")),
    }
