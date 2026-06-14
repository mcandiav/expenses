import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR, UPLOADS_DIR
from app.repositories import archivo_repository
from app.services.file_inspector import extraer_filas_raw, inspeccionar_archivo, reporte_a_json
from app.services.file_models import ReporteInspeccion
from app.services.format_detector import FormatoArchivo


@dataclass
class ResultadoImportacion:
    nombre_archivo: str
    exito: bool
    duplicado: bool
    mensaje: str
    archivo_id: int | None = None
    reporte: ReporteInspeccion | None = None
    filas_extraidas: int = 0


def calcular_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def inspeccionar_solo(content: bytes, nombre_archivo: str) -> ReporteInspeccion:
    return inspeccionar_archivo(content, nombre_archivo)


def importar_archivo(
    content: bytes,
    nombre_archivo: str,
    usuario_id: int,
    banco: str | None = None,
    tipo_fuente: str | None = None,
    observacion: str | None = None,
) -> ResultadoImportacion:
    nombre_archivo = Path(nombre_archivo).name
    hash_archivo = calcular_hash(content)

    existente = archivo_repository.get_by_hash(hash_archivo)
    if existente:
        return ResultadoImportacion(
            nombre_archivo=nombre_archivo,
            exito=False,
            duplicado=True,
            mensaje=f"Archivo duplicado. Ya fue importado el {existente['fecha_importacion']} (ID {existente['id']}).",
            archivo_id=existente["id"],
        )

    reporte = inspeccionar_archivo(content, nombre_archivo)
    if reporte.formato_detectado == FormatoArchivo.PDF.value:
        return ResultadoImportacion(
            nombre_archivo=nombre_archivo,
            exito=False,
            duplicado=False,
            mensaje="Formato PDF no soportado en V1.",
            reporte=reporte,
        )

    if reporte.errores_lectura and not reporte.hojas:
        return ResultadoImportacion(
            nombre_archivo=nombre_archivo,
            exito=False,
            duplicado=False,
            mensaje="; ".join(reporte.errores_lectura),
            reporte=reporte,
        )

    banco_final = (banco or reporte.banco_inferido or "").strip().upper() or None
    tipo_final = (tipo_fuente or reporte.tipo_fuente_inferido or "").strip() or None
    if reporte.subtipo_movimiento and tipo_final and reporte.subtipo_movimiento not in tipo_final:
        tipo_final = f"{tipo_final} — {reporte.subtipo_movimiento}"

    ruta_relativa = _guardar_archivo(content, nombre_archivo, hash_archivo)
    estado = "inspeccionado" if not reporte.errores_lectura else "error"

    archivo_id = archivo_repository.create(
        nombre_archivo=nombre_archivo,
        ruta_relativa=str(ruta_relativa).replace("\\", "/"),
        hash_archivo=hash_archivo,
        banco_inferido=banco_final,
        tipo_fuente_inferido=tipo_final,
        fecha_referencial=reporte.fecha_referencial,
        usuario_id=usuario_id,
        estado=estado,
        mensaje_error="; ".join(reporte.errores_lectura) if reporte.errores_lectura else None,
        observacion=observacion,
        reporte_inspeccion_json=reporte_a_json(reporte),
    )

    filas_raw = extraer_filas_raw(content, nombre_archivo, reporte)
    archivo_repository.insert_movimientos_raw(archivo_id, filas_raw)

    if filas_raw:
        archivo_repository.update_conteos(
            archivo_id,
            filas_leidas=len(filas_raw),
            estado="inspeccionado",
        )
    elif not reporte.errores_lectura:
        archivo_repository.update_conteos(archivo_id, filas_leidas=0, estado="sin_filas")

    return ResultadoImportacion(
        nombre_archivo=nombre_archivo,
        exito=True,
        duplicado=False,
        mensaje=f"Archivo importado e inspeccionado. {len(filas_raw)} filas en staging.",
        archivo_id=archivo_id,
        reporte=reporte,
        filas_extraidas=len(filas_raw),
    )


def _guardar_archivo(content: bytes, nombre_archivo: str, hash_archivo: str) -> Path:
    dest_dir = UPLOADS_DIR / datetime.now().strftime("%Y/%m")
    dest_dir.mkdir(parents=True, exist_ok=True)
    destino = dest_dir / f"{hash_archivo[:12]}_{nombre_archivo}"
    destino.write_bytes(content)
    return destino.relative_to(DATA_DIR)
