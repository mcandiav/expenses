from app.repositories.movimiento_repository import (
    COLUMNAS_ORDENABLES,
    FiltrosMovimiento,
    actualizar_categorizacion,
    get_by_id,
    listar_movimientos,
    obtener_opciones_filtro,
)
from app.services.categorization_service import clasificar_glosa


class MovimientoService:
    COLUMNAS = list(COLUMNAS_ORDENABLES.keys())
    TAMANOS_PAGINA = (50, 100, 500)

    @staticmethod
    def sincronizar_desde_staging() -> int:
        from app.services.normalization_service import (
            normalizar_pendientes,
            reprocesar_archivos_multimoneda,
        )

        total = normalizar_pendientes()
        total += reprocesar_archivos_multimoneda()
        return total

    @staticmethod
    def listar(
        filtros: FiltrosMovimiento,
        orden_columna: str = "fecha",
        orden_desc: bool = True,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> tuple[list[dict], int]:
        if orden_columna not in COLUMNAS_ORDENABLES:
            orden_columna = "fecha"
        if por_pagina not in MovimientoService.TAMANOS_PAGINA:
            por_pagina = 50
        return listar_movimientos(filtros, orden_columna, orden_desc, pagina, por_pagina)

    @staticmethod
    def opciones_filtro() -> dict:
        return obtener_opciones_filtro()

    @staticmethod
    def reclasificar_movimiento(movimiento_id: int) -> dict | None:
        mov = get_by_id(movimiento_id)
        if not mov:
            return None

        resultado = clasificar_glosa(
            mov.get("glosa_original") or "",
            banco=mov.get("banco"),
            producto=mov.get("tipo_fuente"),
        )
        actualizar_categorizacion(
            movimiento_id=movimiento_id,
            categoria_id=resultado.categoria_id,
            metodo_clasificacion=resultado.metodo,
            regla_id=resultado.regla_id,
            revisado=False,
        )
        return get_by_id(movimiento_id)

    @staticmethod
    def movimiento_sin_categoria(mov: dict) -> bool:
        return (mov.get("categoria") or "").strip() == "Por revisar"
