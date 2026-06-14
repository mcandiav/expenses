import sqlite3
from pathlib import Path

from app.config import DB_PATH, ensure_data_dirs


def get_connection() -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    ensure_data_dirs()
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()
    _run_migrations()


def _run_migrations() -> None:
    migrations = [
        "ALTER TABLE archivo_importado ADD COLUMN observacion TEXT",
        "ALTER TABLE archivo_importado ADD COLUMN reporte_inspeccion_json TEXT",
        "ALTER TABLE archivo_importado ADD COLUMN filas_leidas INTEGER DEFAULT 0",
    ]
    with get_connection() as conn:
        for sql in migrations:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()
