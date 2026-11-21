"""Adapter for the approved MT-STATUS-001 V0.1 module.

The original source is preserved under canon/; this wrapper adds no new
status rules and keeps the battle integration separate from the canon file.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

SOURCE = Path(__file__).with_name("canon") / "MT-STATUS-001-V0.1.py"
spec = spec_from_file_location("monster_taimer_canon_status_v01", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("Canonical status source unavailable")
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

Status = module.Status
StatusState = module.StatusState
paralysis_speed = module.paralysis_speed

def state_from_string(value: str) -> StatusState:
    try:
        status = Status(value)
    except ValueError as exc:
        raise ValueError(f"Unknown canonical status: {value}") from exc
    if status == Status.SLEEP:
        raise ValueError("Sleep requires explicit duration; use StatusState.inflict")
    state = StatusState()
    if status != Status.NONE:
        state.inflict(status)
    return state
