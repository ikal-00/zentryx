"""Frontend environment settings. Empty API URL selects the local demo."""

import os
from dataclasses import dataclass

ACTIVE_SERVICE_ID = "l2-ordinary"
FOLLOW_ZOOM = 16.5
FOLLOW_CAMERA_INTERVAL_SECONDS = 0.85
FOLLOW_MIN_DISTANCE_M = 4.0
FOLLOW_ANIMATION_MS = 420


@dataclass(frozen=True)
class AppSettings:
    api_base_url: str = ""
    service_id: str = ACTIVE_SERVICE_ID
    vehicle_id: str = "unit-01"

    @classmethod
    def from_env(cls):
        return cls(
            api_base_url=os.getenv("ZENTRYX_API_BASE_URL", "").strip(),
            service_id=os.getenv("ZENTRYX_SERVICE_ID", ACTIVE_SERVICE_ID).strip(),
            vehicle_id=os.getenv("ZENTRYX_VEHICLE_ID", "unit-01"),
        )
