from .adapters import SMTPConnector, RESTConnector, HostingConnector, DomainConnector, CRMConnector, AccountingConnector, BankingConnector, CryptoConnector

def build_registry(config):
    g=config.get('global',{})
    def merged(name):
        return {**g,**config.get(name,{})}
    return {
        'smtp':SMTPConnector(merged('smtp')),
        'rest_api':RESTConnector(merged('rest_api')),
        'hosting':HostingConnector(merged('hosting')),
        'domains':DomainConnector(merged('domains')),
        'crm':CRMConnector(merged('crm')),
        'accounting':AccountingConnector(merged('accounting')),
        'banking':BankingConnector(merged('banking')),
        'crypto':CryptoConnector(merged('crypto')),
    }
