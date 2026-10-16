import sys
from pathlib import Path
import flet as ft

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.router import launch_app
else:
    from .router import launch_app


import os

if __name__ == "__main__":
    is_web = "--web" in sys.argv or os.getenv("FLET_WEB", "0") in ("1", "true")
    view = ft.AppView.WEB_BROWSER if is_web else ft.AppView.FLET_APP
    port = int(os.getenv("PORT", "8550")) if is_web else 0
    host = "127.0.0.1" if is_web else None

    ft.run(
        launch_app,
        view=view,
        port=port,
        host=host,
    )
