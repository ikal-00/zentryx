"""Interaction and data regressions for the passenger frontend.

Run from root: python -m unittest discover -s app/tests -v
No browser/network required; Map.move_to is the only client RPC stubbed out.
"""

import math
import os
import unittest
from dataclasses import fields
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import flet as ft
import flet_map as ftm
from app.views import passenger as main
from app.components.passenger import AlertBanner, PassengerCard
from app.services import VehicleService, available_services, load_route


def descendants(control):
    yield control
    for field in fields(control):
        value = getattr(control, field.name)
        children = value if isinstance(value, list) else [value]
        for child in children:
            if isinstance(child, ft.Control):
                yield from descendants(child)


class PageStub:
    width, height = 390, 844

    def add(self, root):
        self.root = root

    def update(self):
        pass

    def run_task(self, task):
        self.task = task

    def show_dialog(self, dialog):
        self.dialog = dialog

    def pop_dialog(self):
        self.dialog = None


class FrontendTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"ZENTRYX_API_BASE_URL": ""})
        env.start()
        self.addCleanup(env.stop)
        self.page = PageStub()
        main.main(self.page)
        self.controls = list(descendants(self.page.root))
        self.map = next(c for c in self.controls if isinstance(c, ftm.Map))
        self.center = next(
            c
            for c in self.controls
            if isinstance(c, ft.IconButton) and c.tooltip == "Centrar y seguir la unidad"
        )
        self.badge = next(
            c for c in self.controls if isinstance(c, ft.Text) and c.value == "Siguiendo unidad"
        )
        self.map.on_init(None)

    async def test_gesture_releases_follow_and_center_restores_it(self):
        with patch.object(ftm.Map, "move_to", new_callable=AsyncMock) as move:
            await self.map.on_position_change(SimpleNamespace(has_gesture=False))
            self.assertEqual(self.badge.value, "Siguiendo unidad")

            await self.map.on_position_change(SimpleNamespace(has_gesture=True))
            self.assertEqual(self.badge.value, "Exploración libre")

            await self.center.on_click(None)
            self.assertEqual(self.badge.value, "Siguiendo unidad")
            move.assert_awaited_once()
            self.assertEqual(move.call_args.kwargs["zoom"], main.FOLLOW_ZOOM)

    async def test_station_selection_and_return_to_vehicle(self):
        markers = self.map.layers[2].markers
        bandera_marker = next(
            marker
            for marker in markers[:-1]
            if marker.content.content.tooltip == "Bandera Tultitlán"
        )

        with patch.object(ftm.Map, "move_to", new_callable=AsyncMock):
            await bandera_marker.content.content.on_click(None)
            self.assertEqual(self.badge.value, "Exploración libre")

            selected = next(
                c
                for c in self.controls
                if isinstance(c, ft.Text) and c.value == "Bandera Tultitlán"
            )
            self.assertTrue(
                any(
                    isinstance(c, ft.Column) and c.visible and selected in list(descendants(c))
                    for c in self.controls
                )
            )

            await self.center.on_click(None)
            self.assertEqual(self.badge.value, "Siguiendo unidad")

    async def test_stream_updates_marker_and_throttles_camera(self):
        route, coordinates, _, _ = main.load_geography()
        service = VehicleService(
            coordinates,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        snapshots = [service._snapshot(100 + i, 1, 8) for i in range(6)]

        async def finite_stream(_):
            for snapshot in snapshots:
                yield snapshot

        with (
            patch.object(VehicleService, "stream", finite_stream),
            patch.object(ftm.Map, "move_to", new_callable=AsyncMock) as move,
        ):
            await self.page.task()

            self.assertLessEqual(move.await_count, 1)
            marker = self.map.layers[2].markers[-1]
            self.assertEqual(marker.coordinates.latitude, snapshots[-1].lat)

            await self.map.on_position_change(SimpleNamespace(has_gesture=True))
            move.reset_mock()
            await self.page.task()
            move.assert_not_awaited()

            await self.center.on_click(None)
            self.assertEqual(
                move.call_args.kwargs["destination"].latitude,
                snapshots[-1].lat,
            )

    def test_heading_unwraps_across_north_by_shortest_path(self):
        previous = math.radians(359)
        next_rotation = main.unwrap_heading_radians(previous, 1)
        self.assertAlmostEqual(
            math.degrees(next_rotation - previous),
            2.0,
            places=6,
        )

        previous = math.radians(1)
        next_rotation = main.unwrap_heading_radians(previous, 359)
        self.assertAlmostEqual(
            math.degrees(next_rotation - previous),
            -2.0,
            places=6,
        )

    def test_eta_both_directions_stop_and_terminal(self):
        route, coordinates, _, stations = main.load_geography()
        service = VehicleService(
            coordinates,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        stations = [
            {
                **station,
                "progress_m": service.project_point_to_route(
                    station["lat"],
                    station["lon"],
                ),
            }
            for station in stations
        ]

        self.assertEqual(
            main.next_arrival(stations, 100, 1, 8)[0],
            "Lechería",
        )
        self.assertEqual(
            main.next_arrival(stations, 100, -1, 8)[0],
            "La Quebrada",
        )
        self.assertIsNone(main.next_arrival(stations, 100, 1, 0)[1])
        self.assertEqual(
            main.next_arrival(
                stations,
                service.route_length_m,
                1,
                8,
            ),
            ("Terminal del tramo", 0),
        )
        self.assertEqual(main.format_eta(61), "2 min")
        self.assertEqual(main.format_eta(20), "<1 min")
        self.assertEqual(main.format_eta(None), "—")

    def test_route_catalog_stop_order_and_geometry_alignment(self):
        self.assertIn("l2-ordinary", available_services())
        route = load_route("l2-ordinary")

        self.assertEqual(route.route_id, "route-l2")
        self.assertEqual(route.line_label, "L2")
        self.assertEqual(route.service_name, "Servicio ordinario")
        self.assertEqual(route.station_count, 43)
        self.assertEqual(route.stations[0].name, "La Quebrada")
        self.assertEqual(route.stations[-1].name, "Las Américas")
        self.assertEqual(
            [station.stop_order for station in route.stations],
            list(range(1, 44)),
        )
        self.assertEqual(
            len({station.name for station in route.stations}),
            43,
        )
        self.assertGreaterEqual(len(route.coordinates), 80)

        service = VehicleService(list(route.coordinates))
        progresses = []
        max_distance = 0.0
        for station in route.stations:
            progress = service.project_point_to_route(
                station.lat,
                station.lon,
            )
            progresses.append(progress)
            nearest = service.coordinate_at_progress(progress)
            max_distance = max(
                max_distance,
                service.haversine_m(
                    (station.lat, station.lon),
                    nearest,
                ),
            )

        self.assertEqual(progresses, sorted(progresses))
        self.assertLess(max_distance, 30.0)

    def test_vehicle_service_uses_injected_route_labels(self):
        route = load_route("l2-ordinary")
        service = VehicleService(
            list(route.coordinates),
            route_id="route-test",
            forward_direction_label="A → B",
            reverse_direction_label="B → A",
        )

        forward = service._snapshot(100, 1, 8)
        reverse = service._snapshot(100, -1, 8)
        self.assertEqual(forward.route_id, "route-test")
        self.assertEqual(forward.direction_label, "A → B")
        self.assertEqual(reverse.direction_label, "B → A")

    def test_unknown_data_and_alerts_do_not_invent_service_state(self):
        banner = AlertBanner(lambda e: None)
        self.assertFalse(banner.control.visible)
        banner.set_alert({"active": False, "message": "Inactive fixture"})
        self.assertFalse(banner.control.visible)
        banner.set_alert(
            {
                "active": True,
                "severity": "critical",
                "message": "Contract fixture",
            }
        )
        self.assertTrue(banner.control.visible)
        self.assertEqual(banner.message.value, "Contract fixture")
        banner.set_alert(None)
        self.assertFalse(banner.control.visible)

        route = load_route("l2-ordinary")
        card = PassengerCard(lambda e: None, line_label=route.line_label)
        card.update_vehicle(
            VehicleService(list(route.coordinates))._snapshot(0, 1, 8),
            demo=True,
        )
        self.assertFalse(card.occupancy.visible)
        self.assertEqual(card.status.value, "Datos de demostración")

    def test_geography_and_responsive_sizes(self):
        route, coordinates, _, stations = main.load_geography()
        self.assertEqual(route.service_id, "l2-ordinary")
        self.assertEqual(len(stations), 43)
        self.assertEqual(stations[0]["stop_order"], 1)
        self.assertEqual(stations[-1]["stop_order"], 43)
        self.assertEqual(len(self.map.layers[2].markers), 44)
        self.assertGreaterEqual(len(coordinates), 80)
        self.assertTrue(
            self.map.layers[0].url_template.startswith("https://tile.openstreetmap.org/")
        )

        for width, height in [
            (320, 568),
            (390, 844),
            (844, 390),
            (1440, 900),
        ]:
            self.page.width, self.page.height = width, height
            self.page.on_resize(None)
            body = self.page.root.content
            dock = body.controls[-1].content
            self.assertLessEqual(dock.width, min(width - 24, 460))
            self.assertEqual(
                dock.height,
                150 if height < 560 else None,
            )


if __name__ == "__main__":
    unittest.main()
