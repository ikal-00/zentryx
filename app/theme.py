"""Zentryx visual tokens. No network or domain logic lives here."""

import flet as ft

INK = "#153C34"
ACCENT = "#D6F67A"
PAPER = "#F6F8F4"
WHITE = "#FFFFFF"
MUTED = "#64736D"
LINE = "#E2E9E2"
SOFT = "#EAF0E9"
WARNING = "#80520C"
CARD_WIDTH = 460


def shadow():
    return ft.BoxShadow(
        blur_radius=24,
        spread_radius=0,
        color="#18153C34",
        offset=ft.Offset(0, 6),
    )


def configure(page):
    page.title = "Zentryx · Mexibús"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = PAPER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=INK, use_material3=True)
