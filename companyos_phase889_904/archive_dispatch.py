class ArchiveDispatch:
    """895: archive venture outcome."""
    def dispatch(self,venture_id,reason):
        return {"archived":True,"venture_id":venture_id,"reason":reason}
