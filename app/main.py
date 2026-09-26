"""Flet entrypoint: supports both `flet run app/main.py` and `python -m app.main`."""

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import flet as ft
from app.views.passenger import main

if __name__ == "__main__":
    ft.run(main)
