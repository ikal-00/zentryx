import flet as ft
import flet_map as ftm


# =========================
# ZONA DE TRABAJO ZENTRYXS
# =========================

# Estación Bandera Tultitlán
STATION_LAT = 19.62211
STATION_LON = -99.16299

# Límites aproximados iniciales de trabajo
NORTH = 19.6311
SOUTH = 19.6131
WEST = -99.1726
EAST = -99.1534


def main(page: ft.Page):
    page.title = "Zentryxs"
    page.padding = 0

    # Posición simulada inicial del autobús
    bus_lat = 19.62170
    bus_lon = -99.16350

    # Zona operativa dibujada como polígono
    operational_zone = ftm.PolygonLayer(
        polygons=[
            ftm.PolygonMarker(
                coordinates=[
                    ftm.MapLatitudeLongitude(
                        latitude=NORTH,
                        longitude=WEST,
                    ),
                    ftm.MapLatitudeLongitude(
                        latitude=NORTH,
                        longitude=EAST,
                    ),
                    ftm.MapLatitudeLongitude(
                        latitude=SOUTH,
                        longitude=EAST,
                    ),
                    ftm.MapLatitudeLongitude(
                        latitude=SOUTH,
                        longitude=WEST,
                    ),
                ],
                color=ft.Colors.with_opacity(
                    0.10,
                    ft.Colors.BLUE,
                ),
                border_color=ft.Colors.BLUE,
                border_stroke_width=2,
                label="Zona de prueba Zentryxs",
            )
        ]
    )

    mapa = ftm.Map(
        expand=True,

        # El mapa abre centrado en Bandera Tultitlán
        initial_center=ftm.MapLatitudeLongitude(
            latitude=STATION_LAT,
            longitude=STATION_LON,
        ),

        initial_zoom=15,

        # Evita que el usuario aleje demasiado el mapa
        min_zoom=12,
        max_zoom=19,

        layers=[
            # Mapa base
            ftm.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                user_agent_package_name="zentryxs/1.0",
            ),

            # Zona operativa
            operational_zone,

            # Marcadores
            ftm.MarkerLayer(
                markers=[
                    # Estación Bandera Tultitlán
                    ftm.Marker(
                        coordinates=ftm.MapLatitudeLongitude(
                            latitude=STATION_LAT,
                            longitude=STATION_LON,
                        ),
                        width=50,
                        height=50,
                        content=ft.Icon(
                            ft.Icons.LOCATION_ON,
                            size=42,
                        ),
                    ),

                    # Autobús de prueba
                    ftm.Marker(
                        coordinates=ftm.MapLatitudeLongitude(
                            latitude=bus_lat,
                            longitude=bus_lon,
                        ),
                        width=50,
                        height=50,
                        content=ft.Icon(
                            ft.Icons.DIRECTIONS_BUS,
                            size=40,
                        ),
                    ),
                ]
            ),

            ftm.SimpleAttribution(
                text="OpenStreetMap contributors"
            ),
        ],
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                # Cabecera
                ft.Container(
                    padding=15,
                    content=ft.Text(
                        "ZENTRYXS",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),

                # Mapa
                ft.Container(
                    expand=True,
                    content=mapa,
                ),

                # Información
                ft.Container(
                    padding=15,
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Estación: Bandera Tultitlán",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Unidad: demo-unit-01"
                            ),
                            ft.Text(
                                f"Latitud: {bus_lat}"
                            ),
                            ft.Text(
                                f"Longitud: {bus_lon}"
                            ),
                            ft.Text(
                                "Llegada: --"
                            ),
                            ft.Text(
                                "Saturación: --"
                            ),
                            ft.Text(
                                "Estado: Simulación"
                            ),
                        ]
                    ),
                ),
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)