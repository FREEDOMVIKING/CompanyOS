class CommandRouter:
    COMMANDS={"start","stop","status","health","cycle","checkpoint","recover","portfolio","ventures"}

    def route(self, command):
        return {"command":command,"valid":command in self.COMMANDS,
                "handler":f"handle_{command}" if command in self.COMMANDS else None}
