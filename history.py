import time
import json
import os

RUN_HISTORY = []

def record_run(variant_label: str, leading_suspect: str, net_position: int, confidence: int, audit_score: int, details: dict = None) -> dict:
    """
    Records an investigation run in lightweight memory and appends to local JSON log.
    """
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "variant": variant_label,
        "leading_suspect": leading_suspect or "Unknown",
        "net_position": net_position,
        "confidence": confidence,
        "audit_score": audit_score,
        "details": details or {}
    }
    RUN_HISTORY.append(entry)
    return entry

def get_run_history() -> list[dict]:
    """Returns all recorded investigation runs in the current session."""
    return list(RUN_HISTORY)

def clear_run_history():
    """Clears session history."""
    RUN_HISTORY.clear()
