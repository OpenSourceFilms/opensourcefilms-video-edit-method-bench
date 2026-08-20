#!/bin/bash
# Syntax and structural self-check. Does not require a live Runpod pod, any
# real credentials, or any of the six upstream tools installed — it only
# verifies the scripts parse correctly, the workflow JSON is valid JSON, and
# no secret material or Ditto-graph content has been accidentally committed.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

echo "=== python syntax check ==="
for f in \
  "$ROOT/env/scan_runpod_envs.py" \
  "$ROOT/env/stage_inputs.py" \
  "$ROOT/env/write_runtime_leftovers.py" \
  "$ROOT/materialize/materialize_upstream_workflows.py" \
  "$ROOT/validation/validate_comfy_workflows.py" \
  "$ROOT/cli/kiwi_edit/run_orbit_turn.py"
do
  if python3 -m py_compile "$f" 2>/dev/null; then
    echo "OK   $f"
  else
    echo "FAIL $f"
    FAIL=1
  fi
done

echo
echo "=== bash syntax check ==="
for f in \
  "$ROOT/cli/ditto_high_quality/run_orbit_turn.sh" \
  "$ROOT/cli/sync_lora/run_orbit_turn.sh"
do
  if bash -n "$f"; then
    echo "OK   $f"
  else
    echo "FAIL $f"
    FAIL=1
  fi
done

echo
echo "=== workflow JSON validity ==="
for f in "$ROOT"/workflows/*.json "$ROOT"/workflows/generated/*.json; do
  [ -f "$f" ] || continue
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    echo "OK   $f"
  else
    echo "FAIL $f"
    FAIL=1
  fi
done

echo
echo "=== no committed secret material ==="
if grep -rlE '\-\-\-\-\-BEGIN (OPENSSH|RSA|EC) PRIVATE KEY\-\-\-\-\-|hf_[A-Za-z0-9]{20,}' "$ROOT" \
    --include='*' 2>/dev/null | grep -v '^Binary'; then
  echo "FAIL: possible private key or HF token found committed in this repo"
  FAIL=1
else
  echo "OK   no private key headers or HF token patterns found"
fi

echo
echo "=== no Ditto-derived workflow graph committed ==="
if find "$ROOT/workflows" -iname '*ditto*' 2>/dev/null | grep -q .; then
  echo "FAIL: a Ditto-named workflow file was found — Ditto's graph is CC-BY-NC-SA-4.0 and must not be redistributed here"
  FAIL=1
else
  echo "OK   no Ditto workflow files present"
fi

echo
if [ "$FAIL" = "0" ]; then
  echo "selfcheck: PASS"
else
  echo "selfcheck: FAIL"
fi
exit "$FAIL"
