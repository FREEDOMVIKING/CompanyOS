class UnifiedControlAPI:
    def snapshot(self, daemon, events, health, ventures, portfolio):
        return {"daemon":daemon,"events":events,"health":health,
                "ventures":ventures,"portfolio":portfolio}

    def action_result(self, command, result):
        return {"command":command,"success":True,"result":result}
