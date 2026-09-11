class BackpressureController:
    def evaluate(self, queue_depth, soft_limit=50, hard_limit=100):
        q=int(queue_depth)
        if q>=int(hard_limit):
            return {"mode":"hard","accept_new_work":False,"worker_scale_factor":2.0}
        if q>=int(soft_limit):
            return {"mode":"soft","accept_new_work":True,"worker_scale_factor":1.5}
        return {"mode":"normal","accept_new_work":True,"worker_scale_factor":1.0}
