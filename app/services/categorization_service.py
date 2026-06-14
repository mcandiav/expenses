from dataclasses import dataclass

from app.repositories import categoria_repository, regla_repository
from app.services.text_utils import normalizar_glosa


@dataclass
class ClasificacionResultado:
    categoria_id: int | None
    categoria_nombre: str | None
    regla_id: int | None
    patron: str | None
    metodo: str


def _especificidad(regla: dict) -> int:
    score = 0
    if regla.get("banco_opcional"):
        score += 4
    if regla.get("producto_opcional"):
        score += 2
    if regla.get("subtipo_fuente_opcional"):
        score += 1
    return score


def clasificar_glosa(
    glosa: str,
    banco: str | None = None,
    producto: str | None = None,
    subtipo_fuente: str | None = None,
) -> ClasificacionResultado:
    glosa_norm = normalizar_glosa(glosa)
    banco_norm = banco.strip().upper() if banco else None
    producto_norm = producto.strip().lower() if producto else None
    subtipo_norm = subtipo_fuente.strip().lower() if subtipo_fuente else None

    reglas = regla_repository.list_reglas(incluir_inactivas=False)
    candidatas: list[dict] = []

    for regla in reglas:
        patron = regla["patron"]
        if not patron or patron not in glosa_norm:
            continue
        if regla["banco_opcional"]:
            if not banco_norm or regla["banco_opcional"] != banco_norm:
                continue
        if regla["producto_opcional"] and producto_norm and regla["producto_opcional"] != producto_norm:
            continue
        if regla["subtipo_fuente_opcional"] and subtipo_norm and regla["subtipo_fuente_opcional"] != subtipo_norm:
            continue
        candidatas.append(regla)

    if not candidatas:
        por_revisar = categoria_repository.get_categoria_by_nombre("Por revisar")
        if por_revisar:
            return ClasificacionResultado(
                categoria_id=por_revisar["id"],
                categoria_nombre=por_revisar["nombre"],
                regla_id=None,
                patron=None,
                metodo="sin_regla",
            )
        return ClasificacionResultado(None, None, None, None, "sin_regla")

    candidatas.sort(
        key=lambda r: (_especificidad(r), r["prioridad"], r["id"]),
        reverse=True,
    )
    ganadora = candidatas[0]
    return ClasificacionResultado(
        categoria_id=ganadora["categoria_id"],
        categoria_nombre=ganadora["categoria_nombre"],
        regla_id=ganadora["id"],
        patron=ganadora["patron"],
        metodo="regla",
    )
