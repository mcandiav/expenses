import csv
import json
from io import StringIO
from pathlib import Path

import bcrypt

from app.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.db.connection import get_connection

CATEGORIAS_INICIALES = [
    ("Marketing / publicidad", "Meta Ads, Google Ads, campañas"),
    ("Proveedores / inventario", "Compra de productos para vender"),
    ("Despacho / logística", "Starken, Chilexpress, correos"),
    ("Software / tecnología", "Shopify, Klaviyo, apps, dominios"),
    ("Sueldos / honorarios", "Equipo, comisiones, pagos de trabajo"),
    ("Arriendo / oficina / bodega", "Espacios físicos"),
    ("Servicios básicos", "Luz, agua, internet"),
    ("Banco / intereses / impuestos", "Comisiones, intereses, impuesto crédito"),
    ("Supermercado / hogar", "Gasto familiar"),
    ("Comida / restaurantes", "Restaurantes, delivery"),
    ("Auto / combustible / ruta", "Bencina, peajes, estacionamientos"),
    ("Salud / farmacia", "Farmacias, médicos"),
    ("Educación / niños", "Colegio, niños, actividades"),
    ("Personal / familiar", "Gasto no empresa"),
    ("Por revisar", "No se puede clasificar todavía"),
]

REGLAS_INICIALES = [
    ("jumbo", "Supermercado / hogar", 100, None),
    ("lider", "Supermercado / hogar", 100, None),
    ("unimarc", "Supermercado / hogar", 100, None),
    ("meta", "Marketing / publicidad", 100, None),
    ("facebook", "Marketing / publicidad", 100, None),
    ("google ads", "Marketing / publicidad", 100, None),
    ("shopify", "Software / tecnología", 100, None),
    ("klaviyo", "Software / tecnología", 100, None),
    ("starken", "Despacho / logística", 100, None),
    ("chilexpress", "Despacho / logística", 100, None),
    ("correos", "Despacho / logística", 100, None),
    ("copec", "Auto / combustible / ruta", 100, None),
    ("shell", "Auto / combustible / ruta", 100, None),
    ("estacionamiento", "Auto / combustible / ruta", 100, None),
    ("farmacia", "Salud / farmacia", 100, None),
    ("cruz verde", "Salud / farmacia", 100, None),
    ("salcobrand", "Salud / farmacia", 100, None),
]

ROLES = [
    ("admin", "Acceso total"),
    ("usuario", "Consulta y exportación"),
]


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_if_empty() -> None:
    """
    Semilla inicial solo en base vacía.
    Si ya hay usuarios, categorías o reglas, no modifica nada existente.
    """
    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM rol").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO rol (nombre, descripcion) VALUES (?, ?)", ROLES
            )

        if conn.execute("SELECT COUNT(*) FROM categoria").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO categoria (nombre, uso, activa) VALUES (?, ?, 1)",
                CATEGORIAS_INICIALES,
            )

        if conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] == 0:
            admin_rol_id = conn.execute(
                "SELECT id FROM rol WHERE nombre = 'admin'"
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO usuario (email, nombre, password_hash, rol_id, activo)
                VALUES (?, ?, ?, ?, 1)
                """,
                (ADMIN_EMAIL, "Administrador", _hash_password(ADMIN_PASSWORD), admin_rol_id),
            )

        if conn.execute("SELECT COUNT(*) FROM regla_categoria").fetchone()[0] == 0:
            categorias = {
                row["nombre"]: row["id"]
                for row in conn.execute("SELECT id, nombre FROM categoria").fetchall()
            }
            admin_id = conn.execute(
                "SELECT id FROM usuario WHERE email = ?", (ADMIN_EMAIL,)
            ).fetchone()[0]
            for patron, categoria_nombre, prioridad, banco in REGLAS_INICIALES:
                conn.execute(
                    """
                    INSERT INTO regla_categoria
                    (patron, categoria_id, prioridad, banco_opcional, activa, creado_por_usuario_id)
                    VALUES (?, ?, ?, ?, 1, ?)
                    """,
                    (patron, categorias[categoria_nombre], prioridad, banco, admin_id),
                )

        conn.commit()


def load_reglas_from_csv(csv_content: str, usuario_id: int | None = None) -> int:
    reader = csv.DictReader(StringIO(csv_content))
    inserted = 0
    with get_connection() as conn:
        categorias = {
            row["nombre"].lower(): row["id"]
            for row in conn.execute("SELECT id, nombre FROM categoria").fetchall()
        }
        for row in reader:
            patron = (row.get("patron") or row.get("Patrón") or "").strip().lower()
            categoria_nombre = (
                row.get("categoria") or row.get("Categoría") or ""
            ).strip()
            if not patron or not categoria_nombre:
                continue
            cat_id = categorias.get(categoria_nombre.lower())
            if cat_id is None:
                continue
            prioridad = int(row.get("prioridad") or row.get("Prioridad") or 100)
            banco = row.get("banco_opcional") or row.get("Banco") or None
            banco = banco.strip() if banco else None
            conn.execute(
                """
                INSERT INTO regla_categoria
                (patron, categoria_id, prioridad, banco_opcional, activa, creado_por_usuario_id)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (patron, cat_id, prioridad, banco, usuario_id),
            )
            inserted += 1
        conn.commit()
    return inserted
