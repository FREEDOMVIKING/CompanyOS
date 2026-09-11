class ParallelDispatcher:
    def dispatch(self, jobs, max_parallel=4):
        jobs=list(jobs or [])
        batches=[]
        for i in range(0,len(jobs),max(1,int(max_parallel))):
            batches.append(jobs[i:i+max(1,int(max_parallel))])
        return {"batches":batches,"batch_count":len(batches),"max_parallel":max_parallel}
