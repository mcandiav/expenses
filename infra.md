# Infraestructura — Categorización de Expensas

Documento operativo vigente. Complementa el README (arquitectura) con el **entorno real de ejecución**.

---

## Entorno actual

| Ítem | Valor |
|------|--------|
| **Panel** | EasyPanel |
| **Proyecto** | `n8n` |
| **Servicio / App** | `expenses` |
| **Repositorio** | `https://github.com/mcandiav/expenses` |
| **Rama** | `main` |
| **Build** | Dockerfile en raíz del repo |
| **Acceso público** | Cloudflare (proxy al dominio configurado en EasyPanel → Domains) |
| **Puerto interno app** | `8501` (Streamlit) |

---

## Por qué se perdieron datos en un deploy (causa raíz)

EasyPanel construye y ejecuta el contenedor desde el **Dockerfile**, **no** desde `docker-compose.yml`.

El archivo `docker-compose.yml` del repo define:

```yaml
volumes:
  - ./expensas-data:/expensas-data
```

Ese montaje **no se aplica automáticamente** en EasyPanel si solo está en el repo. Sin volumen configurado en el panel:

1. Cada **redeploy** crea un contenedor nuevo.
2. `/expensas-data` queda **vacío dentro del contenedor**.
3. La app crea una SQLite nueva → parece que “borró todo” (usuarios, movimientos, reglas).

**No es el código el que borra en update:** es la **falta de almacenamiento persistente en EasyPanel**.

---

## Configuración obligatoria en EasyPanel (persistencia)

### 1. Volumen / Mount

En el servicio **n8n → expenses**, configurar un **mount persistente**:

| Campo | Valor |
|-------|--------|
| **Ruta en el contenedor** | `/expensas-data` |
| **Tipo** | Volumen persistente (named volume de EasyPanel) |

Debe existir **antes** del próximo redeploy con datos reales.

Contenido esperado tras operar la app:

```text
/expensas-data/
├── db/expensas.db
├── uploads/
├── exports/
├── logs/
└── backups/
```

### 2. Variables de entorno (pestaña Environment)

| Variable | Valor recomendado | Notas |
|----------|-------------------|--------|
| `EXPENSAS_DATA_DIR` | `/expensas-data` | Debe coincidir con el mount |
| `ADMIN_EMAIL` | email del admin | Solo afecta **primer arranque** con BD vacía |
| `ADMIN_PASSWORD` | contraseña segura | Solo afecta **primer arranque** con BD vacía |

No cambiar `ADMIN_*` esperando resetear usuarios: si la BD ya existe, el seed **no** sobrescribe.

### 3. Dominio (pestaña Domains + Cloudflare)

- EasyPanel expone el servicio en un dominio/subdominio.
- Cloudflare hace proxy SSL hacia ese host.
- Cloudflare **no** interviene en la persistencia de datos.

### 4. Deploy seguro

- Usar botón **Deploy** / redeploy desde Source.
- **No** eliminar el volumen persistente del servicio.
- Tras deploy, verificar en la app (sidebar): contador `📁 X mov. · Y archivos` > 0 si ya había datos.

---

## Recuperación si hubo pérdida de datos

1. En el servidor EasyPanel, buscar si quedó un volumen anterior del servicio `expenses` (a veces el panel conserva volúmenes huérfanos).
2. Si se encuentra un `expensas.db` con tamaño > 0, remontarlo en `/expensas-data` y redeploy.
3. Si no hay backup, los datos del deploy anterior **no son recuperables** desde la app; habría que reimportar archivos bancarios.

Backup manual recomendado (periódico): copiar `db/expensas.db` y `uploads/` fuera del servidor.

---

## Desarrollo local (referencia)

```text
docker compose up --build
```

En local **sí** aplica `docker-compose.yml` con `./expensas-data:/expensas-data`.

---

## Bitácora infra

| Fecha | Cambio |
|-------|--------|
| 2026-06-14 | Documento inicial. EasyPanel + Cloudflare. Causa pérdida datos: sin mount `/expensas-data`. |
