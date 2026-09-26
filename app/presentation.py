"""Pure ETA formatting, demo arrivals and heading presentation."""

import math


def format_eta(seconds):
    if seconds is None:
        return "—"
    if seconds < 60:
        return "<1 min"
    return f"{math.ceil(seconds / 60)} min"


def next_arrival(stations, progress_m, direction, speed_mps):
    """Fallback usado únicamente por la fuente demo local."""
    ordered = stations if direction == 1 else reversed(stations)
    candidates = [
        station for station in ordered if (station["progress_m"] - progress_m) * direction > 15.0
    ]
    if not candidates:
        return "Terminal del tramo", 0

    target = candidates[0]
    seconds = abs(target["progress_m"] - progress_m) / speed_mps if speed_mps > 0 else None
    return target["name"], seconds


def unwrap_heading_radians(previous_rotation, heading_deg):
    previous_rotation = float(previous_rotation or 0.0)
    target = math.radians(heading_deg) % math.tau
    previous_normalized = previous_rotation % math.tau
    delta = (target - previous_normalized + math.pi) % math.tau - math.pi
    return previous_rotation + delta
