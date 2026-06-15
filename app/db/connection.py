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
    """Crea tablas si no existen. Nunca elimina ni trunca datos existentes."""
    ensure_data_dirs()
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()


def bootstrap_database() -> dict:
    """
    Arranque seguro: esquema + migraciones + seed solo si vacío.
    Retorna metadatos para diagnóstico en UI.
    """
    from app.db.migrations import run_data_migrations
    from app.db.seed import seed_if_empty

    db_existia = DB_PATH.exists()
    init_db()
    run_data_migrations()
    seed_if_empty()

    with get_connection() as conn:
        total_mov = conn.execute("SELECT COUNT(*) FROM movimiento").fetchone()[0]
        total_arch = conn.execute("SELECT COUNT(*) FROM archivo_importado").fetchone()[0]

    return {
        "db_path": str(DB_PATH),
        "db_existia": db_existia,
        "total_movimientos": total_mov,
        "total_archivos": total_arch,
    }
