"""Migraciones de datos y esquema. Cada migración corre una sola vez y nunca borra datos de negocio salvo acción explícita documentada."""

from app.db.connection import get_connection


def _ensure_migration_table() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id TEXT PRIMARY KEY,
                descripcion TEXT,
                aplicada_en TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


def _migration_aplicada(migration_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE id = ?", (migration_id,)
        ).fetchone()
    return row is not None


def _marcar_migration(migration_id: str, descripcion: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO schema_migrations (id, descripcion) VALUES (?, ?)",
            (migration_id, descripcion),
        )
        conn.commit()


def run_data_migrations() -> None:
    """
    Ejecuta migraciones pendientes una sola vez.
    Las actualizaciones de código no deben repetir migraciones ya aplicadas.
    """
    _ensure_migration_table()

    _migration_20260614_fix_multimoneda_internacional()
    _migration_schema_columns()
    _migration_regla_patron_banco_unique()
    _migration_sesion_usuario_table()


def _migration_sesion_usuario_table() -> None:
    migration_id = "20260616_sesion_usuario_table"
    if _migration_aplicada(migration_id):
        return

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sesion_usuario (
                token TEXT PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
                expira_en TEXT NOT NULL,
                creada_en TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sesion_usuario_expira ON sesion_usuario(expira_en)"
        )
        conn.commit()

    _marcar_migration(migration_id, "Tabla sesion_usuario para login persistente.")


def _migration_regla_patron_banco_unique() -> None:
    migration_id = "20260614_regla_patron_banco_unique"
    if _migration_aplicada(migration_id):
        return

    with get_connection() as conn:
        desactivadas = _desactivar_reglas_duplicadas(conn)
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_regla_patron_banco_activa
            ON regla_categoria(patron, COALESCE(banco_opcional, ''))
            WHERE activa = 1
            """
        )
        conn.commit()

    detalle = "Índice único patrón+banco en reglas activas."
    if desactivadas:
        detalle += f" Se desactivaron {desactivadas} regla(s) duplicada(s) preexistente(s)."
    _marcar_migration(migration_id, detalle)


def _desactivar_reglas_duplicadas(conn) -> int:
    """Deja una sola regla activa por patrón+banco; desactiva el resto."""
    rows = conn.execute(
        """
        SELECT id, patron, banco_opcional, prioridad
        FROM regla_categoria
        WHERE activa = 1
        ORDER BY prioridad DESC, id ASC
        """
    ).fetchall()

    vistos: set[tuple[str, str]] = set()
    duplicadas: list[int] = []
    for row in rows:
        clave = (row["patron"], row["banco_opcional"] or "")
        if clave in vistos:
            duplicadas.append(int(row["id"]))
        else:
            vistos.add(clave)

    for regla_id in duplicadas:
        conn.execute("UPDATE regla_categoria SET activa = 0 WHERE id = ?", (regla_id,))
    return len(duplicadas)


def _migration_20260614_fix_multimoneda_internacional() -> None:
    migration_id = "20260614_fix_multimoneda_internacional"
    if _migration_aplicada(migration_id):
        return

    from app.services.normalization_service import reprocesar_archivos_multimoneda

    reprocesar_archivos_multimoneda()
    _marcar_migration(
        migration_id,
        "Corrección única: archivos internacionales BCI con moneda CLP errónea.",
    )


def _migration_schema_columns() -> None:
    """Columnas añadidas en versiones anteriores (idempotente)."""
    migration_id = "20260614_schema_archivo_columns"
    if _migration_aplicada(migration_id):
        return

    import sqlite3

    alters = [
        "ALTER TABLE archivo_importado ADD COLUMN observacion TEXT",
        "ALTER TABLE archivo_importado ADD COLUMN reporte_inspeccion_json TEXT",
        "ALTER TABLE archivo_importado ADD COLUMN filas_leidas INTEGER DEFAULT 0",
    ]
    with get_connection() as conn:
        for sql in alters:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()

    _marcar_migration(migration_id, "Columnas extra en archivo_importado (V1.5).")
