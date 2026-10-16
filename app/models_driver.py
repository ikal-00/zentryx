from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AssignedVehicle:
    plate: str
    economic_number: str
    route_name: str
    service_type: str
    terminal_origin: str
    terminal_destination: str


@dataclass
class IneDocumentState:
    front_captured: bool = False
    back_captured: bool = False
    front_source: Optional[str] = None  # "camera" | "gallery"
    back_source: Optional[str] = None   # "camera" | "gallery"
    front_preview_uri: Optional[str] = None
    back_preview_uri: Optional[str] = None
    front_filename: Optional[str] = None
    back_filename: Optional[str] = None
    verifying: bool = False
    verification_progress: float = 0.0
    verification_step_label: str = "Esperando captura de documento..."
    verified: bool = False
    verified_at: Optional[str] = None
    curp_masked: str = "MAVG880412HMC***09"
    ine_cic: str = "IDMEX2491083746<<0880412"

    @property
    def ready_for_verification(self) -> bool:
        return self.front_captured and self.back_captured


@dataclass
class EmergencyAlertPayload:
    alert_id: str
    operator_folio: str
    operator_name: str
    unit_plate: str
    economic_number: str
    latitude: float
    longitude: float
    station_context: str
    trigger_method: str  # "hold_3s" | "slide_confirm"
    timestamp_iso: str
    status: str = "ENVIADA A CENTRAL C5 / MEXIBÚS"


@dataclass
class OperatorSession:
    folio: str = ""
    unit_plate: str = ""
    operator_name: str = ""
    license_Code: str = ""
    status_label: str = ""
    is_valid_assignment: bool = False
    auth_method: str = "manual"  # "manual" | "qr"
    vehicle: Optional[AssignedVehicle] = None
    ine: IneDocumentState = field(default_factory=IneDocumentState)
    authenticated_at: Optional[str] = None
    active_shift: bool = False
    last_alert: Optional[EmergencyAlertPayload] = None

    def mark_authenticated(self, auth_method: str = "manual") -> None:
        self.auth_method = auth_method
        self.authenticated_at = datetime.now().strftime("%H:%M:%S")
