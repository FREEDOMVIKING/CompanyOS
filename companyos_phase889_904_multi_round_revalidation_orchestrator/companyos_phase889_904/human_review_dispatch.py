class HumanReviewDispatch:
    """896: create bounded human-review request."""
    def dispatch(self,venture_id,history,reason):
        return {"review_required":True,"venture_id":venture_id,"reason":reason,"history":history}
