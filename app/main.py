import sys
from pathlib import Path
import flet as ft

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.router import launch_app
else:
    from .router import launch_app


if __name__ == "__main__":
    ft.run(launch_app)
