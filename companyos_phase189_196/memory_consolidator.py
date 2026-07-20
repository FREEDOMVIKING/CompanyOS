class MemoryConsolidator:
    """194: consolidate repeated observations into durable operating lessons."""
    def consolidate(self,observations):
        groups={}
        for o in observations:
            topic=str(o.get("topic","general")); groups.setdefault(topic,[]).append(o)
        lessons=[]
        for topic,rows in groups.items():
            avg=sum(float(x.get("score",0)) for x in rows)/len(rows)
            lessons.append({"topic":topic,"samples":len(rows),"average_score":round(avg,4),
                            "durable":len(rows)>=3,"autonomous_reuse":len(rows)>=3})
        return lessons
