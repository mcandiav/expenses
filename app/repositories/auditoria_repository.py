import json

from app.db.connection import get_connection


def registrar(
    usuario_id: int | None,
    accion: str,
    entidad: str,
    entidad_id: int | None,
    antes: dict | None = None,
    despues: dict | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id, antes_json, despues_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                usuario_id,
                accion,
                entidad,
                entidad_id,
                json.dumps(antes, ensure_ascii=False) if antes else None,
                json.dumps(despues, ensure_ascii=False) if despues else None,
            ),
        )
        conn.commit()


def listar_por_entidad(entidad: str, entidad_id: int, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, u.email AS usuario_email
            FROM auditoria a
            LEFT JOIN usuario u ON u.id = a.usuario_id
            WHERE a.entidad = ? AND a.entidad_id = ?
            ORDER BY a.fecha DESC
            LIMIT ?
            """,
            (entidad, entidad_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
