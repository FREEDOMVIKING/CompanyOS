class BoundedRoundPolicy:
    """881: cap autonomous revalidation execution rounds."""
    def evaluate(self,round_no,max_rounds=3):
        return {"allowed":int(round_no)<=int(max_rounds),
                "remaining":max(0,int(max_rounds)-int(round_no))}
