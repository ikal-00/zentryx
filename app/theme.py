"""Zentryx visual tokens (Tier-1 Crimson Palette). No network or domain logic lives here."""

import flet as ft

# Signature Mexibús Crimson & Executive Obsidian Neutrals (Strictly non-neon)
BRAND = "#D31034"
BRAND_STRONG = "#B50D2B"
BRAND_DARK = "#7A091D"
BRAND_SOFT = "#FDEBED"

INK = "#111217"
ACCENT = "#D31034"
ACCENT_SOFT = "#FDEBED"
PAPER = "#F8F9FA"
WHITE = "#FFFFFF"
MUTED = "#5F6368"
LINE = "#E5E7EB"
SOFT = "#F3F4F6"
WARNING = "#B45309"
SUCCESS = "#0F7644"
CARD_WIDTH = 460


def shadow():
    return ft.BoxShadow(
        blur_radius=20,
        spread_radius=-4,
        color="#18000000",
        offset=ft.Offset(0, 8),
    )


def configure(page):
    page.title = "Zentryx · Mexibús Línea 2"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = PAPER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=BRAND_STRONG, use_material3=True)
