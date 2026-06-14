from app.repositories import auditoria_repository, usuario_repository


MIN_PASSWORD_LENGTH = 6


class UsuarioService:
    @staticmethod
    def listar_usuarios(incluir_inactivos: bool = True) -> list[dict]:
        return usuario_repository.list_usuarios(incluir_inactivos)

    @staticmethod
    def listar_roles() -> list[dict]:
        return usuario_repository.list_roles()

    @staticmethod
    def crear(
        email: str,
        nombre: str,
        password: str,
        rol_nombre: str,
        actor_id: int,
    ) -> dict:
        email = email.strip()
        nombre = nombre.strip()
        UsuarioService._validar_password(password)
        if not email or not nombre:
            raise ValueError("Email y nombre son obligatorios.")
        if usuario_repository.get_by_email(email):
            raise ValueError(f"Ya existe un usuario con email '{email}'.")
        rol = usuario_repository.get_rol_by_nombre(rol_nombre)
        if not rol:
            raise ValueError(f"Rol '{rol_nombre}' no válido.")

        usuario = usuario_repository.create_usuario(email, nombre, password, rol["id"])
        auditoria_repository.registrar(
            usuario_id=actor_id,
            accion="crear",
            entidad="usuario",
            entidad_id=usuario["id"],
            despues=_snapshot_usuario(usuario),
        )
        return usuario

    @staticmethod
    def actualizar(
        usuario_id: int,
        email: str,
        nombre: str,
        rol_nombre: str,
        activo: bool,
        actor_id: int,
    ) -> dict:
        email = email.strip()
        nombre = nombre.strip()
        if not email or not nombre:
            raise ValueError("Email y nombre son obligatorios.")

        actual = usuario_repository.get_by_id(usuario_id)
        if not actual:
            raise ValueError("Usuario no encontrado.")

        otro = usuario_repository.get_by_email(email)
        if otro and otro["id"] != usuario_id:
            raise ValueError(f"Ya existe otro usuario con email '{email}'.")

        rol = usuario_repository.get_rol_by_nombre(rol_nombre)
        if not rol:
            raise ValueError(f"Rol '{rol_nombre}' no válido.")

        if usuario_id == actor_id:
            if not activo:
                raise ValueError("No puede desactivar su propio usuario.")
            if rol_nombre != "admin":
                raise ValueError("No puede quitarse el rol admin a usted mismo.")

        if actual["rol"] == "admin" and rol_nombre != "admin" and actual["activo"]:
            if usuario_repository.count_admins_activos(excluir_id=usuario_id) == 0:
                raise ValueError("Debe existir al menos un administrador activo.")

        if actual["rol"] == "admin" and not activo:
            if usuario_repository.count_admins_activos(excluir_id=usuario_id) == 0:
                raise ValueError("No puede desactivar al último administrador activo.")

        antes = _snapshot_usuario(actual)
        usuario_repository.update_usuario(usuario_id, email, nombre, rol["id"], activo)
        actualizado = usuario_repository.get_by_id(usuario_id)
        auditoria_repository.registrar(
            usuario_id=actor_id,
            accion="actualizar",
            entidad="usuario",
            entidad_id=usuario_id,
            antes=antes,
            despues=_snapshot_usuario(actualizado),
        )
        return actualizado

    @staticmethod
    def cambiar_password(
        usuario_id: int,
        password_nueva: str,
        actor_id: int,
    ) -> None:
        UsuarioService._validar_password(password_nueva)
        actual = usuario_repository.get_by_id(usuario_id)
        if not actual:
            raise ValueError("Usuario no encontrado.")

        usuario_repository.update_password(usuario_id, password_nueva)
        auditoria_repository.registrar(
            usuario_id=actor_id,
            accion="cambiar_password",
            entidad="usuario",
            entidad_id=usuario_id,
            despues={"email": actual["email"]},
        )

    @staticmethod
    def obtener_auditoria(usuario_id: int) -> list[dict]:
        return auditoria_repository.listar_por_entidad("usuario", usuario_id)

    @staticmethod
    def _validar_password(password: str) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")


def _snapshot_usuario(usuario: dict) -> dict:
    return {
        "id": usuario["id"],
        "email": usuario["email"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
        "activo": bool(usuario["activo"]),
    }
