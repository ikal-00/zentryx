"""Backend environment and stable repository asset locations."""

import os
from pathlib import Path
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

ROOT = Path(__file__).resolve().parents[1]
ROUTES_DIR = ROOT / "app" / "assets" / "routes"
ROUTE_PATH = ROUTES_DIR / "l2_ordinary_route.geojson"
STATIONS_PATH = ROUTES_DIR / "l2_ordinary_stations.geojson"


def create_pool():
    load_dotenv(ROOT / ".env")
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise RuntimeError("POSTGRES_URL is required to start the Zentryx API")
    return ConnectionPool(
        conninfo=postgres_url,
        min_size=int(os.getenv("DB_POOL_MIN", "1")),
        max_size=int(os.getenv("DB_POOL_MAX", "30")),
        open=True,
    )
