class BackpressureController:
    def evaluate(self, backlog, workers, max_backlog_per_worker=10):
        workers=max(1,int(workers))
        ratio=float(backlog)/workers
        if ratio>max_backlog_per_worker:
            return {"throttle":True,"action":"reduce_ingress","ratio":round(ratio,2)}
        return {"throttle":False,"action":"normal","ratio":round(ratio,2)}
