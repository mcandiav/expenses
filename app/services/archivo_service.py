from pathlib import Path

from app.config import DATA_DIR
from app.repositories import archivo_repository, auditoria_repository


class ArchivoService:
    @staticmethod
    def contar_movimientos(archivo_id: int) -> int:
        return archivo_repository.contar_movimientos(archivo_id)

    @staticmethod
    def eliminar_movimientos_de_archivo(archivo_id: int, usuario_id: int | None = None) -> int:
        archivo = archivo_repository.get_by_id(archivo_id)
        if not archivo:
            raise ValueError("Archivo no encontrado.")

        eliminados = archivo_repository.eliminar_movimientos_de_archivo(archivo_id)
        auditoria_repository.registrar(
            usuario_id=usuario_id,
            accion="eliminar_movimientos",
            entidad="archivo_importado",
            entidad_id=archivo_id,
            antes={"nombre_archivo": archivo["nombre_archivo"], "movimientos": eliminados},
        )
        return eliminados

    @staticmethod
    def eliminar_archivo_completo(archivo_id: int, usuario_id: int | None = None) -> dict:
        archivo = archivo_repository.get_by_id(archivo_id)
        if not archivo:
            raise ValueError("Archivo no encontrado.")

        resumen = archivo_repository.eliminar_archivo_completo(archivo_id)
        ruta = DATA_DIR / (archivo.get("ruta_relativa") or "")
        if ruta.is_file():
            try:
                ruta.unlink()
            except OSError:
                resumen["archivo_fisico_eliminado"] = False
            else:
                resumen["archivo_fisico_eliminado"] = True

        auditoria_repository.registrar(
            usuario_id=usuario_id,
            accion="eliminar_archivo",
            entidad="archivo_importado",
            entidad_id=archivo_id,
            antes={
                "nombre_archivo": archivo["nombre_archivo"],
                "hash_archivo": archivo["hash_archivo"],
                **resumen,
            },
        )
        return resumen
