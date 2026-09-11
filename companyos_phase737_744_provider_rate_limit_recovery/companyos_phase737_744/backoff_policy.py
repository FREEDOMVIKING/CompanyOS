class BackoffPolicy:
    def delay_seconds(self,attempts,base=30,maximum=1800):
        return min(int(maximum),int(base)*(2**max(0,int(attempts))))
