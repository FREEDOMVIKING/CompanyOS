#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.3 FIX STALE BRIDGE TEST ====="
T="tests/generated/test_adaptive_workforce_execution_bridge.py"
cp "$T" "$T.v64_3_backup_$(date +%Y%m%d_%H%M%S)"

cat > "$T" <<'PY'
import inspect
from companyos.runtime import adaptive_workforce_execution_bridge as bridge

def test_current_bridge_contract():
    assert callable(bridge.cycle)
    assert callable(bridge.run)
    assert callable(bridge._invoke_cycle)
    assert bridge.RESULTS.name == "adaptive_workforce_verified_results.jsonl"
    assert bridge.EMITTED.name == "adaptive_workforce_emitted_jobs.json"

def test_factory_cycle_adapter_has_no_invented_required_args():
    class F:
        def cycle(self):
            return {"ok": True}
    assert bridge._invoke_cycle(F()) == {"ok": True}

def test_items_are_bounded_to_supported_collections():
    assert list(bridge._items({"queue":[{"id":"x"}]})) == [{"id":"x"}]
    assert list(bridge._items({"unknown":[{"id":"x"}]})) == []

def test_source_preserves_financial_evidence_guard():
    src=inspect.getsource(bridge.cycle)
    assert '"financial_metrics_invented": False' in src
    assert 'attributed_profit' in src
    assert 'isinstance' in src
PY

python -m pytest -q "$T" --disable-warnings --maxfail=1
git diff --check
echo "===== TEST DIFF ====="
git diff -- "$T" | sed -n '1,180p'
echo "V64_3_STALE_BRIDGE_TEST_FIX=PASS"
