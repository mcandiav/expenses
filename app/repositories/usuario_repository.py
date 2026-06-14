import bcrypt

from app.db.connection import get_connection


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate(email: str, password: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.nombre, u.password_hash, u.activo, r.nombre AS rol
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.email = ? COLLATE NOCASE
            """,
            (email.strip(),),
        ).fetchone()
    if not row or not row["activo"]:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return None
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuario SET fecha_ultimo_login = datetime('now') WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
    return {
        "id": row["id"],
        "email": row["email"],
        "nombre": row["nombre"],
        "rol": row["rol"],
    }


def list_usuarios(incluir_inactivos: bool = True) -> list[dict]:
    query = """
        SELECT
            u.id,
            u.email,
            u.nombre,
            u.activo,
            u.fecha_creacion,
            u.fecha_ultimo_login,
            r.id AS rol_id,
            r.nombre AS rol,
            r.descripcion AS rol_descripcion
        FROM usuario u
        JOIN rol r ON r.id = u.rol_id
    """
    if not incluir_inactivos:
        query += " WHERE u.activo = 1"
    query += " ORDER BY u.email COLLATE NOCASE"
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def list_roles() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, nombre, descripcion FROM rol ORDER BY nombre"
        ).fetchall()
    return [dict(row) for row in rows]


def get_by_id(usuario_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.nombre, u.activo, u.fecha_creacion, u.fecha_ultimo_login,
                   r.id AS rol_id, r.nombre AS rol
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.id = ?
            """,
            (usuario_id,),
        ).fetchone()
    return dict(row) if row else None


def get_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.nombre, u.activo, r.id AS rol_id, r.nombre AS rol
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.email = ? COLLATE NOCASE
            """,
            (email.strip(),),
        ).fetchone()
    return dict(row) if row else None


def count_admins_activos(excluir_id: int | None = None) -> int:
    query = """
        SELECT COUNT(*) FROM usuario u
        JOIN rol r ON r.id = u.rol_id
        WHERE r.nombre = 'admin' AND u.activo = 1
    """
    params: list = []
    if excluir_id is not None:
        query += " AND u.id != ?"
        params.append(excluir_id)
    with get_connection() as conn:
        return conn.execute(query, params).fetchone()[0]


def create_usuario(
    email: str,
    nombre: str,
    password: str,
    rol_id: int,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO usuario (email, nombre, password_hash, rol_id, activo)
            VALUES (?, ?, ?, ?, 1)
            """,
            (email.strip(), nombre.strip(), _hash_password(password), rol_id),
        )
        conn.commit()
        usuario_id = cursor.lastrowid
    return get_by_id(usuario_id)


def update_usuario(
    usuario_id: int,
    email: str,
    nombre: str,
    rol_id: int,
    activo: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE usuario
            SET email = ?, nombre = ?, rol_id = ?, activo = ?
            WHERE id = ?
            """,
            (email.strip(), nombre.strip(), rol_id, int(activo), usuario_id),
        )
        conn.commit()


def update_password(usuario_id: int, password: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuario SET password_hash = ? WHERE id = ?",
            (_hash_password(password), usuario_id),
        )
        conn.commit()


def get_rol_by_nombre(nombre: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, nombre, descripcion FROM rol WHERE nombre = ?",
            (nombre,),
        ).fetchone()
    return dict(row) if row else None
