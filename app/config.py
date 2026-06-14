import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("EXPENSAS_DATA_DIR", "./expensas-data"))
DB_DIR = DATA_DIR / "db"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"
BACKUPS_DIR = DATA_DIR / "backups"
DB_PATH = DB_DIR / "expensas.db"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def ensure_data_dirs() -> None:
    for path in (DB_DIR, UPLOADS_DIR, EXPORTS_DIR, LOGS_DIR, BACKUPS_DIR):
        path.mkdir(parents=True, exist_ok=True)
