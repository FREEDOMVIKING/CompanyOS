import json,tempfile
from pathlib import Path
from companyos.runtime.backlog_truth_probe import probe
def test_classification():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)
        rows=[
          {"task_id":"c","goal_id":"g","task_type":"research","stage":"research","state":"COMPLETED"},
          {"task_id":"a","goal_id":"g","task_type":"planning","state":"QUEUED","depends_on_stage":"research"},
          {"task_id":"b","goal_id":"x","task_type":"planning","state":"QUEUED","depends_on_stage":"research"},
          {"task_id":"z","goal_id":"g","task_type":"weird","state":"QUEUED"}]
        for i,r in enumerate(rows):(p/f"{i}.json").write_text(json.dumps(r))
        x=probe(p)
        assert x["reasons"]["execution_ready"]==1
        assert x["reasons"]["dependency_blocked"]==1
        assert x["reasons"]["unsupported_type"]==1
