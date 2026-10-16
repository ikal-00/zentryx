import base64
from datetime import datetime
import re
from typing import Dict, Optional, Tuple

from app.models_driver import AssignedVehicle, EmergencyAlertPayload, OperatorSession


# Registry of official mock Mexibús Línea 2 operators and units for instant validation
OFFICIAL_OPERATORS: Dict[str, Tuple[str, str]] = {
    "84021": ("Carlos Eduardo Mendoza Rojas", "EDOMEX-op-2026-84021"),
    "10492": ("Roberto Hernández Villaseñor", "EDOMEX-op-2026-10492"),
    "55210": ("Miguel Ángel Vargas Gómez", "EDOMEX-op-2026-55210"),
    "99001": ("Alejandro Torres Ramírez", "EDOMEX-op-2026-99001"),
}

OFFICIAL_VEHICLES: Dict[str, AssignedVehicle] = {
    "MEX-1234": AssignedVehicle(
        plate="MEX-1234",
        economic_number="U-042",
        route_name="Línea 2 · Las Américas ⇄ La Quebrada",
        service_type="Expreso Rosa / Articulado BRT",
        terminal_origin="Las Américas",
        terminal_destination="La Quebrada",
    ),
    "MEX-2048": AssignedVehicle(
        plate="MEX-2048",
        economic_number="U-108",
        route_name="Línea 2 · Las Américas ⇄ La Quebrada",
        service_type="Ordinario Articulado",
        terminal_origin="Las Américas",
        terminal_destination="La Quebrada",
    ),
    "MEX-0912": AssignedVehicle(
        plate="MEX-0912",
        economic_number="U-019",
        route_name="Línea 2 · Las Américas ⇄ Río de los Remedios",
        service_type="Expreso",
        terminal_origin="Las Américas",
        terminal_destination="Río de los Remedios",
    ),
}

FOLIO_PATTERN = re.compile(r"^\d{4,8}$")
PLATE_PATTERN = re.compile(r"^[A-Z]{3}-\d{3,4}[A-Z]?$")


def normalize_plate(raw: str) -> str:
    cleaned = raw.strip().upper().replace(" ", "")
    if re.match(r"^[A-Z]{3}\d{3,4}[A-Z]?$", cleaned):
        return f"{cleaned[:3]}-{cleaned[3:]}"
    return cleaned


def validate_operator_credentials(
    folio: str, raw_plate: str
) -> Tuple[bool, str, Optional[str], Optional[AssignedVehicle]]:
    """
    Validates operator folio (4-8 digits) and vehicle plate (e.g. MEX-1234).
    Returns (is_valid, status_message, operator_name, assigned_vehicle).
    """
    clean_folio = folio.strip()
    plate = normalize_plate(raw_plate)

    if not clean_folio and not plate:
        return (
            False,
            "Ingresa tu Folio Único de Operador y Matrícula de la Unidad.",
            None,
            None,
        )

    if not FOLIO_PATTERN.match(clean_folio):
        return (
            False,
            "El Folio Único debe contener entre 4 y 8 dígitos numéricos.",
            None,
            None,
        )

    if not PLATE_PATTERN.match(plate):
        return (
            False,
            "Formato de matrícula inválido (ejemplo válido: MEX-1234).",
            None,
            None,
        )

    operator_info = OFFICIAL_OPERATORS.get(
        clean_folio,
        (f"Operador Cert. #{clean_folio}", f"EDOMEX-OP-2026-{clean_folio}"),
    )
    vehicle_info = OFFICIAL_VEHICLES.get(
        plate,
        AssignedVehicle(
            plate=plate,
            economic_number=f"U-{clean_folio[-3:]}",
            route_name="Línea 2 · Las Américas ⇄ La Quebrada",
            service_type="Ordinario BRT",
            terminal_origin="Las Américas",
            terminal_destination="La Quebrada",
        ),
    )

    return (
        True,
        "Operador Vigente y Asignado · SITRAMYTEM / Mexibús L2",
        operator_info[0],
        vehicle_info,
    )


def apply_credentials_to_session(
    session: OperatorSession, folio: str, raw_plate: str, auth_method: str = "manual"
) -> bool:
    valid, status_msg, op_name, vehicle = validate_operator_credentials(folio, raw_plate)
    session.folio = folio.strip()
    session.unit_plate = normalize_plate(raw_plate)
    session.status_label = status_msg
    session.is_valid_assignment = valid
    if valid and op_name and vehicle:
        session.operator_name = op_name
        session.license_Code = f"SITRAMYTEM-{session.folio}"
        session.vehicle = vehicle
        session.auth_method = auth_method
    else:
        session.operator_name = ""
        session.vehicle = None
    return valid


def simulate_qr_scan_payload(preset_index: int = 0) -> Tuple[str, str, str]:
    """
    Returns (folio, plate, qr_token) simulating an official Mexiquense transit QR credential.
    """
    presets = [
        ("84021", "MEX-1234", "SITRAMYTEM://OP-84021/UNIT-MEX-1234/VIGENTE-2026"),
        ("10492", "MEX-2048", "SITRAMYTEM://OP-10492/UNIT-MEX-2048/VIGENTE-2026"),
        ("55210", "MEX-0912", "SITRAMYTEM://OP-55210/UNIT-MEX-0912/VIGENTE-2026"),
    ]
    return presets[preset_index % len(presets)]


def generate_ine_preview_data_uri(side: str, operator_name: str, folio: str, source: str) -> str:
    """
    Generates a clean, high-contrast SVG encoded as a base64 data URI so Flet's ft.Image
    renders an immediate realistic INE preview whether captured from the camera or gallery.
    """
    side_title = "INSTITUTO NACIONAL ELECTORAL · ANVERSO" if side == "front" else "INSTITUTO NACIONAL ELECTORAL · REVERSO (MRZ)"
    badge_text = "CAPTURA CÁMARA HD" if source == "camera" else "ARCHIVO GALERÍA"
    name_display = (operator_name or "OPERADOR MEXIBÚS L2").upper()[:28]
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if side == "front":
        detail_lines = f"""
        <rect x="28" y="68" width="82" height="98" rx="8" fill="#1F2430" stroke="#D31034" stroke-width="2"/>
        <circle cx="69" cy="102" r="18" fill="#374151"/>
        <path d="M45 152 C45 130, 93 130, 93 152" fill="#374151"/>
        <text x="128" y="84" fill="#9CA3AF" font-family="sans-serif" font-size="10" font-weight="bold">NOMBRE DEL TITULAR</text>
        <text x="128" y="102" fill="#FFFFFF" font-family="sans-serif" font-size="13" font-weight="bold">{name_display}</text>
        <text x="128" y="124" fill="#9CA3AF" font-family="sans-serif" font-size="10" font-weight="bold">CLAVE DE ELECTOR / CURP</text>
        <text x="128" y="140" fill="#E5E7EB" font-family="monospace" font-size="11">MNRJCR88041215H200 · FOLIO {folio or '84021'}</text>
        <text x="128" y="162" fill="#10B981" font-family="sans-serif" font-size="11" font-weight="bold">✓ HOLOGRAMA Y BIOMETRÍA DETECTADOS</text>
        """
    else:
        detail_lines = f"""
        <rect x="28" y="66" width="364" height="38" rx="6" fill="#090A0F" stroke="#374151" stroke-width="1"/>
        <text x="40" y="90" fill="#E5E7EB" font-family="monospace" font-size="12" letter-spacing="2">I&lt;MEX2491083746&lt;&lt;088041215H3012319</text>
        <text x="28" y="126" fill="#9CA3AF" font-family="monospace" font-size="11">8804127M3112315MEX&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;06</text>
        <text x="28" y="146" fill="#9CA3AF" font-family="monospace" font-size="11">MENDOZA&lt;ROJAS&lt;&lt;CARLOS&lt;EDUARDO&lt;&lt;</text>
        <text x="28" y="168" fill="#10B981" font-family="sans-serif" font-size="11" font-weight="bold">✓ CÓDIGO QR E INE-CIC VALIDADOS</text>
        """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="210" viewBox="0 0 420 210">
      <rect width="420" height="210" rx="14" fill="#111217"/>
      <rect x="2" y="2" width="416" height="206" rx="12" fill="none" stroke="#D31034" stroke-width="2" stroke-dasharray="6,4"/>
      <rect x="0" y="0" width="420" height="46" rx="14" fill="#1A1D26"/>
      <text x="20" y="28" fill="#FFFFFF" font-family="sans-serif" font-size="11" font-weight="bold">{side_title}</text>
      <rect x="286" y="12" width="118" height="22" rx="11" fill="#D31034"/>
      <text x="345" y="27" text-anchor="middle" fill="#FFFFFF" font-family="sans-serif" font-size="9" font-weight="bold">{badge_text}</text>
      {detail_lines}
      <text x="28" y="194" fill="#6B7280" font-family="monospace" font-size="9">ZENTRYX SECURE CAPTURE · {timestamp}</text>
    </svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_emergency_alert(
    session: OperatorSession,
    latitude: float,
    longitude: float,
    station_context: str,
    trigger_method: str,
) -> EmergencyAlertPayload:
    now = datetime.now()
    alert = EmergencyAlertPayload(
        alert_id=f"SOS-{now.strftime('%H%M%S')}-{session.folio or '84021'}",
        operator_folio=session.folio or "84021",
        operator_name=session.operator_name or "Carlos Eduardo Mendoza Rojas",
        unit_plate=session.unit_plate or "MEX-1234",
        economic_number=session.vehicle.economic_number if session.vehicle else "U-042",
        latitude=round(latitude, 6),
        longitude=round(longitude, 6),
        station_context=station_context or "Ecatepec",
        trigger_method=trigger_method,
        timestamp_iso=now.strftime("%Y-%m-%d %H:%M:%S"),
    )
    session.last_alert = alert
    return alert
