from app.repositories.movimiento_repository import (
    COLUMNAS_ORDENABLES,
    FiltrosMovimiento,
    listar_movimientos,
    obtener_opciones_filtro,
)
from app.services.normalization_service import normalizar_pendientes


class MovimientoService:
    COLUMNAS = list(COLUMNAS_ORDENABLES.keys())
    TAMANOS_PAGINA = (50, 100, 500)

    @staticmethod
    def sincronizar_desde_staging() -> int:
        return normalizar_pendientes()

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
