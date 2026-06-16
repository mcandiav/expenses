import re
from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class HojaInspeccion:
    nombre: str
    filas_totales: int
    columnas_totales: int
    rango_usado: str
    fila_encabezado_probable: int | None
    columnas_detectadas: list[str]
    filas_ejemplo: list[dict] = field(default_factory=list)


@dataclass
class ReporteInspeccion:
    archivo: str
    formato_detectado: str
    hojas_detectadas: list[str]
    hojas: list[HojaInspeccion]
    errores_lectura: list[str] = field(default_factory=list)
    banco_inferido: str | None = None
    tipo_fuente_inferido: str | None = None
    subtipo_movimiento: str | None = None
    fecha_referencial: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def inferir_metadata_desde_nombre(nombre_archivo: str) -> dict[str, str | None]:
    nombre = nombre_archivo.lower()
    metadata: dict[str, str | None] = {
        "banco_inferido": None,
        "tipo_fuente_inferido": None,
        "subtipo_movimiento": None,
        "fecha_referencial": None,
    }

    if "bci" in nombre:
        metadata["banco_inferido"] = "BCI"
    elif "itau" in nombre:
        metadata["banco_inferido"] = "ITAU"
    elif "santander" in nombre:
        metadata["banco_inferido"] = "SANTANDER"
    elif "chile" in nombre or "banco de chile" in nombre:
        metadata["banco_inferido"] = "BANCO DE CHILE"
    elif "scotiabank" in nombre or "scotia" in nombre:
        metadata["banco_inferido"] = "SCOTIABANK"

    if "movimientosfacturados" in nombre.replace("_", "").replace(" ", ""):
        metadata["tipo_fuente_inferido"] = "Tarjeta / movimientos facturados"
        if "nacionales" in nombre:
            metadata["subtipo_movimiento"] = "Nacionales"
        elif "internacionales" in nombre:
            metadata["subtipo_movimiento"] = "Internacionales"
    elif "scotiabank" in nombre or "scotia" in nombre:
        metadata["tipo_fuente_inferido"] = "Tarjeta de crédito"
        if "nacional" in nombre:
            metadata["subtipo_movimiento"] = "Nacionales"
        elif "internacional" in nombre or " inter" in nombre:
            metadata["subtipo_movimiento"] = "Internacionales"
    elif "cartola" in nombre:
        metadata["tipo_fuente_inferido"] = "Cartola"
    elif "tarjeta" in nombre:
        metadata["tipo_fuente_inferido"] = "Tarjeta"

    match = re.search(r"(\d{2})[-_](\d{2})[-_](\d{4})", nombre_archivo)
    if match:
        dd, mm, yyyy = match.groups()
        try:
            datetime(int(yyyy), int(mm), int(dd))
            metadata["fecha_referencial"] = f"{yyyy}-{mm}-{dd}"
        except ValueError:
            pass

    return metadata
