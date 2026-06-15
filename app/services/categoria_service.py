from dataclasses import dataclass

from app.repositories import categoria_repository, regla_repository


@dataclass
class ResultadoCrearRegla:
    regla: dict
    duplicada: bool
    movimientos_actualizados: int


class CategoriaService:
    @staticmethod
    def listar(incluir_inactivas: bool = True) -> list[dict]:
        return categoria_repository.list_categorias(incluir_inactivas)

    @staticmethod
    def crear(nombre: str, uso: str | None = None) -> dict:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de categoría es obligatorio.")
        if categoria_repository.get_categoria_by_nombre(nombre):
            raise ValueError(f"Ya existe una categoría llamada '{nombre}'.")
        return categoria_repository.create_categoria(nombre, uso)

    @staticmethod
    def actualizar(categoria_id: int, nombre: str, uso: str | None, activa: bool) -> None:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de categoría es obligatorio.")
        existente = categoria_repository.get_categoria_by_nombre(nombre)
        if existente and existente["id"] != categoria_id:
            raise ValueError(f"Ya existe otra categoría llamada '{nombre}'.")
        categoria_repository.update_categoria(categoria_id, nombre, uso, activa)

    @staticmethod
    def eliminar(categoria_id: int) -> None:
        categoria_repository.delete_categoria(categoria_id)


class ReglaService:
    @staticmethod
    def listar(incluir_inactivas: bool = True) -> list[dict]:
        return regla_repository.list_reglas(incluir_inactivas)

    @staticmethod
    def crear(
        patron: str,
        categoria_id: int,
        prioridad: int = 100,
        banco_opcional: str | None = None,
        producto_opcional: str | None = None,
        subtipo_fuente_opcional: str | None = None,
        comentario: str | None = None,
        usuario_id: int | None = None,
    ) -> dict:
        resultado = ReglaService.crear_y_aplicar(
            patron=patron,
            categoria_id=categoria_id,
            prioridad=prioridad,
            banco_opcional=banco_opcional,
            producto_opcional=producto_opcional,
            subtipo_fuente_opcional=subtipo_fuente_opcional,
            comentario=comentario,
            usuario_id=usuario_id,
            aplicar_pendientes=False,
        )
        return resultado.regla

    @staticmethod
    def crear_y_aplicar(
        patron: str,
        categoria_id: int,
        prioridad: int = 100,
        banco_opcional: str | None = None,
        producto_opcional: str | None = None,
        subtipo_fuente_opcional: str | None = None,
        comentario: str | None = None,
        usuario_id: int | None = None,
        aplicar_pendientes: bool = True,
    ) -> ResultadoCrearRegla:
        if not patron.strip():
            raise ValueError("El patrón de glosa es obligatorio.")
        if not categoria_repository.get_categoria_by_id(categoria_id):
            raise ValueError("La categoría seleccionada no existe.")

        existente = regla_repository.find_regla_duplicada(
            patron=patron,
            categoria_id=categoria_id,
            banco_opcional=banco_opcional,
        )
        if existente:
            regla = existente
            duplicada = True
        else:
            regla = regla_repository.create_regla(
                patron=patron,
                categoria_id=categoria_id,
                prioridad=prioridad,
                banco_opcional=banco_opcional,
                producto_opcional=producto_opcional,
                subtipo_fuente_opcional=subtipo_fuente_opcional,
                comentario=comentario,
                usuario_id=usuario_id,
            )
            duplicada = False

        movimientos_actualizados = 0
        if aplicar_pendientes:
            from app.services.movimiento_service import MovimientoService

            movimientos_actualizados = MovimientoService.reclasificar_pendientes()

        return ResultadoCrearRegla(
            regla=regla,
            duplicada=duplicada,
            movimientos_actualizados=movimientos_actualizados,
        )

    @staticmethod
    def actualizar(
        regla_id: int,
        patron: str,
        categoria_id: int,
        prioridad: int,
        banco_opcional: str | None,
        producto_opcional: str | None,
        subtipo_fuente_opcional: str | None,
        activa: bool,
        comentario: str | None,
    ) -> None:
        if not patron.strip():
            raise ValueError("El patrón de glosa es obligatorio.")
        regla_repository.update_regla(
            regla_id=regla_id,
            patron=patron,
            categoria_id=categoria_id,
            prioridad=prioridad,
            banco_opcional=banco_opcional,
            producto_opcional=producto_opcional,
            subtipo_fuente_opcional=subtipo_fuente_opcional,
            activa=activa,
            comentario=comentario,
        )

    @staticmethod
    def eliminar(regla_id: int) -> None:
        regla_repository.delete_regla(regla_id)
