class ActionRateLimiter:
    def evaluate(self, recent_count, max_per_window=10):
        allowed=int(recent_count)<int(max_per_window)
        return {"allowed":allowed,"recent_count":int(recent_count),"limit":int(max_per_window)}
