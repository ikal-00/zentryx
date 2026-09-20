"""Interaction regressions with real Flet controls and the existing route service.

Run from app: python -m unittest discover -s tests -v
No browser/network required; Map.move_to is the only client RPC stubbed out.
"""

import unittest
from dataclasses import fields
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import flet as ft
import flet_map as ftm
import main
from components.passenger import AlertBanner, PassengerCard
from services import VehicleService


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
        self.page = PageStub()
        main.main(self.page)
        self.controls = list(descendants(self.page.root))
        self.map = next(c for c in self.controls if isinstance(c, ftm.Map))
        self.center = next(
            c
            for c in self.controls
            if isinstance(c, ft.IconButton)
            and c.tooltip == "Centrar y seguir la unidad"
        )
        self.badge = next(
            c
            for c in self.controls
            if isinstance(c, ft.Text) and c.value == "Siguiendo unidad"
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
        with patch.object(ftm.Map, "move_to", new_callable=AsyncMock):
            await markers[1].content.content.on_click(None)
            self.assertEqual(self.badge.value, "Exploración libre")
            selected = next(
                c
                for c in self.controls
                if isinstance(c, ft.Text) and c.value == "Bandera Tultitlán"
            )
            self.assertTrue(
                any(
                    isinstance(c, ft.Column)
                    and c.visible
                    and selected in list(descendants(c))
                    for c in self.controls
                )
            )
            await self.center.on_click(None)
            self.assertEqual(self.badge.value, "Siguiendo unidad")

    async def test_stream_updates_marker_heading_and_respects_free_map(self):
        _, coordinates, _, _ = main.load_geography()
        service = VehicleService(coordinates)
        snapshots = [service._snapshot(100 + i, 1, 8) for i in range(6)]

        async def finite_stream(_):
            for snapshot in snapshots:
                yield snapshot

        with (
            patch.object(VehicleService, "stream", finite_stream),
            patch.object(ftm.Map, "move_to", new_callable=AsyncMock) as move,
        ):
            await self.page.task()
            move.assert_awaited_once()
            marker = self.map.layers[2].markers[-1]
            self.assertEqual(marker.coordinates.latitude, snapshots[-1].lat)
            self.assertAlmostEqual(
                marker.content.content.rotate,
                main.math.radians(snapshots[-1].heading_deg),
            )
            await self.map.on_position_change(SimpleNamespace(has_gesture=True))
            move.reset_mock()
            await self.page.task()
            move.assert_not_awaited()
            await self.center.on_click(None)
            self.assertEqual(
                move.call_args.kwargs["destination"].latitude, snapshots[-1].lat
            )

    def test_eta_both_directions_stop_and_terminal(self):
        _, coordinates, _, stations = main.load_geography()
        service = VehicleService(coordinates)
        stations = sorted(
            [
                {**s, "progress_m": service.project_point_to_route(s["lat"], s["lon"])}
                for s in stations
            ],
            key=lambda s: s["progress_m"],
        )
        self.assertEqual(main.next_arrival(stations, 100, 1, 8)[0], "Bandera Tultitlán")
        self.assertEqual(main.next_arrival(stations, 100, -1, 8)[0], "Buenavista")
        self.assertIsNone(main.next_arrival(stations, 100, 1, 0)[1])
        self.assertEqual(
            main.next_arrival(stations, service.route_length_m, 1, 8),
            ("Terminal del tramo", 0),
        )
        self.assertEqual(main.format_eta(61), "2 min")
        self.assertEqual(main.format_eta(20), "<1 min")
        self.assertEqual(main.format_eta(None), "—")

    def test_unknown_data_and_alerts_do_not_invent_service_state(self):
        banner = AlertBanner(lambda e: None)
        self.assertFalse(banner.control.visible)
        banner.set_alert({"active": False, "message": "Inactive fixture"})
        self.assertFalse(banner.control.visible)
        banner.set_alert(
            {"active": True, "severity": "critical", "message": "Contract fixture"}
        )
        self.assertTrue(banner.control.visible)
        self.assertEqual(banner.message.value, "Contract fixture")
        banner.set_alert(None)
        self.assertFalse(banner.control.visible)
        _, coordinates, _, _ = main.load_geography()
        card = PassengerCard(lambda e: None)
        card.update_vehicle(VehicleService(coordinates)._snapshot(0, 1, 8), demo=True)
        self.assertFalse(card.occupancy.visible)
        self.assertEqual(card.status.value, "Datos de demostración")

    def test_geography_and_responsive_sizes(self):
        self.assertEqual(len(self.map.layers[2].markers), 4)
        self.assertTrue(
            self.map.layers[0].url_template.startswith(
                "https://tile.openstreetmap.org/"
            )
        )
        for width, height in [(320, 568), (390, 844), (844, 390), (1440, 900)]:
            self.page.width, self.page.height = width, height
            self.page.on_resize(None)
            body = self.page.root.content
            dock = body.controls[-1].content
            self.assertLessEqual(dock.width, min(width - 24, 460))
            self.assertEqual(dock.height, 150 if height < 560 else None)


if __name__ == "__main__":
    unittest.main()
