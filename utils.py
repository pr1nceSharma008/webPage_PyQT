"""
utils.py — direct Python ports of your JS helper functions:
fmt(), totalOEE(), shiftOEE(), getShiftVisibility()

No PyQt-specific concepts here — this is just plain Python logic,
identical to your <script> block, so the "brains" of the app match exactly.
"""
from datetime import datetime


def fmt(total_seconds: int) -> str:
    """HH:MM:SS from a seconds count. Same as JS fmt()."""
    total_seconds = max(0, int(total_seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def total_oee(downtime_seconds: float) -> float:
    """Same formula as JS totalOEE(): 24h shift basis."""
    value = ((24 * 60 - downtime_seconds / 60) / (24 * 60)) * 100
    return min(100, max(0, value))


def shift_oee(downtime_seconds: float) -> float:
    """Same formula as JS shiftOEE(): 8h shift basis."""
    value = ((8 * 60 - downtime_seconds / 60) / (8 * 60)) * 100
    return min(100, max(0, value))


def get_shift_visibility(now: datetime | None = None) -> dict:
    """
    Same logic as JS getShiftVisibility().
    Shift 1: 07:30–15:30 | Shift 2: 15:30–23:30 | Shift 3: 23:30–07:30 (overnight)
    """
    now = now or datetime.now()
    t = now.hour * 60 + now.minute  # minutes since midnight

    s1_start = 7 * 60 + 30
    s2_start = 15 * 60 + 30
    s3_start = 23 * 60 + 30

    if s1_start <= t < s2_start:
        return {"s1": True, "s2": False, "s3": False}
    elif s2_start <= t < s3_start:
        return {"s1": True, "s2": True, "s3": False}
    else:
        return {"s1": True, "s2": True, "s3": True}
