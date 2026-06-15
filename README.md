# Categorizacion de Expensas

## Bitácora de cambios

| Versión | Fecha | Cambio realizado | Motivo | Impacto | Sección afectada |
|---------|-------|------------------|--------|---------|------------------|
| V0.1 | 2026-06-12 | Creación del documento base inicial. | Inicio del proyecto y preparación de la fuente oficial de arquitectura. | Sin impacto funcional; solo estructura documental inicial. | Documento completo |
| V1.0 | 2026-06-12 | Definición de arquitectura inicial para categorización de movimientos bancarios y tarjetas. | Formalizar una solución pequeña, local, rápida y trazable para importar archivos bancarios heterogéneos y categorizarlos automáticamente. | Define ejecución local en Windows 11 con Docker, repositorio SQLite, normalización de fuentes, reglas determinísticas y salida Excel/CSV. | Documento completo |
| V1.1 | 2026-06-12 | Revisión inicial de archivos de muestra BCI en carpeta del proyecto. | Incorporar evidencia real de entrada para orientar el requerimiento al Programador. | Se confirma que existen archivos BCI de movimientos facturados nacionales e internacionales con extensión `.xls`, pero estructura interna tipo OOXML/ZIP. | Fuentes de datos / Requerimiento para Programador |
| V1.2 | 2026-06-12 | Definición de aplicación web monolítica dockerizada con pestañas, usuarios/roles, exportación filtrada y protección de duplicados. | Ajustar la solución a la operación real esperada: uso desde navegador, carga de archivos, revisión editable, control de duplicados y administración de usuarios. | Cambia el alcance V1 desde proceso local/CLI a app web en un solo Docker, desplegable inicialmente en servidor dev y portable a otros hosts Docker. | Arquitectura / Seguridad / Modelo de datos / Requerimiento para Programador |
| V1.3 | 2026-06-12 | Consolidación de documentación vigente en un único README.md. | Mantener la regla del proyecto: un solo documento oficial por proyecto. | El README.md queda como única fuente vigente e incluye el requerimiento para Programador dentro del mismo documento. | Documento completo / Requerimiento para Programador |
| V1.4 | 2026-06-14 | Unificación de Categorías y Reglas en una sola pestaña con subpestañas; inicio de implementación con Streamlit. | Decisión operativa de Miguel: catálogo maestro y reglas de matching en un mismo módulo UI. | La pestaña **Reglas y categorías** reemplaza la pestaña **Reglas** aislada; categorías se administran en subpestaña propia; stack web inicial: Python + Streamlit + SQLite. | Alcance funcional §2 / Interfaz §8.6 / Requerimiento §16 |
| V1.5 | 2026-06-14 | Inspector BCI/Excel/CSV e implementación de pestañas Subir archivos y Archivos importados. | Primer entregable técnico obligatorio del Programador: inspección con evidencia antes del mapeo definitivo BCI. | Detección de formato por contenido; reporte de hojas/columnas/ejemplos; carga con hash antiduplicado; staging `movimiento_raw`; historial en Archivos importados. | §8.2 / §8.3 / §16.7 / Implementación |
| V1.6 | 2026-06-14 | Política de persistencia de datos en actualizaciones y despliegues. | Miguel ingresa data real; rebuild/deploy no debe borrar SQLite, uploads ni clasificaciones. | Volumen host obligatorio; seed solo en BD vacía; migraciones idempotentes una sola vez; sin reproceso destructivo automático al abrir Movimientos. | §7 / §19 / §20 |

---

## Estado del documento

Fuente oficial de arquitectura vigente del proyecto **Categorizacion de Expensas**.

Versión arquitectónica vigente: **V1.6**.

Este README.md es el único documento vigente del proyecto. Gobierna el alcance, arquitectura, decisiones y requerimiento inicial para desarrollo. La configuración específica y el código deben ser tratados en hilos separados por los roles Configurador y Programador, pero no deben crear documentos vigentes paralelos salvo decisión explícita de Miguel.

---

## 1. Objetivo del proyecto

Construir una aplicación web dockerizada, liviana y trazable para importar movimientos financieros provenientes de bancos, tarjetas de crédito y cartolas, normalizarlos a un formato común, categorizarlos automáticamente mediante reglas configurables por glosa y permitir revisión/exportación desde navegador.

El objetivo funcional es transformar entradas heterogéneas como archivos CSV o Excel bancarios en un listado consolidado, categorizado, filtrable, editable de forma controlada y exportable a Excel.

Ejemplo esperado:

```text
Glosa original: JUMBO KENNEDY
Categoría sugerida: Supermercado / hogar
Método: regla por glosa
```

---

## 2. Alcance funcional V1

La V1 debe cubrir:

1. Aplicación web operable desde navegador.
2. Despliegue inicial en servidor dev usando un único contenedor Docker.
3. Portabilidad para ejecutar el mismo contenedor en PC local u otro host Docker.
4. Login de usuarios.
5. Usuario administrador inicial.
6. Pestaña para administración de usuarios y roles.
7. Roles iniciales: `admin` y `usuario`.
8. Pestañas funcionales: Dashboard, Subir archivos, Archivos importados, Movimientos, Por revisar, Reglas y categorías, Usuarios/Roles y Exportar.
9. Importar archivos `.xls`, `.xlsx` y `.csv` desde la interfaz web.
10. Soportar archivos Excel con extensión `.xls` cuyo contenido real sea OOXML/ZIP.
11. Registrar archivos importados y evitar reprocesamiento accidental.
12. Guardar una copia lógica del dato crudo.
13. Normalizar columnas heterogéneas a un modelo común.
14. Categorizar movimientos usando reglas determinísticas sobre glosa normalizada.
15. Marcar como `Por revisar` los movimientos no clasificados.
16. Permitir edición controlada de categorías, revisión, observaciones y estado.
17. Proteger contra duplicados a nivel de archivo y movimiento.
18. Permitir filtros por columna en el listado de movimientos.
19. Exportar a Excel el listado completo o la vista filtrada.
20. Mantener trazabilidad de fuente, archivo, fila original, categoría asignada, regla aplicada y usuario que realizó cambios.

Fuera de alcance V1:

1. Integración directa con NetSuite.
2. Automatización bancaria vía APIs.
3. Scraping bancario.
4. Uso obligatorio de IA para clasificar.
5. Separación frontend/backend en servicios distintos.
6. PDF como formato de entrada.
7. OCR.
8. Contabilidad formal o generación de asientos contables.

---

## 3. Contexto de negocio

Miguel recibe archivos desde distintas entidades financieras. Aunque los archivos representan movimientos similares, cada banco o producto financiero puede cambiar:

- nombre de columnas;
- orden de columnas;
- formato de fechas;
- formato de montos;
- signo de cargos/abonos;
- moneda;
- glosa o descripción;
- presencia de encabezados o textos antes de la tabla;
- extensión del archivo versus formato real del contenido.

La solución debe desacoplar el formato de origen del modelo de negocio. Por eso se requiere una capa de importación por fuente y una capa de normalización común.

---

## 4. Fuentes de datos revisadas

En la carpeta del proyecto existen los siguientes archivos de muestra:

```text
Categorizacion de Expensas/BCI_MovimientosFacturadosInternacionales_23-04-2026.xls
Categorizacion de Expensas/BCI_MovimientosFacturadosNacionales_25-03-2026.xls
```

Observaciones arquitectónicas:

1. Ambos archivos son muestras reales de BCI asociadas a movimientos facturados de tarjeta.
2. Hay al menos dos tipos de extracto BCI: movimientos nacionales y movimientos internacionales.
3. Aunque la extensión es `.xls`, el contenido detectado comienza como paquete ZIP/OOXML (`PK...`), propio de archivos Excel modernos tipo `.xlsx`.
4. El Programador no debe confiar solo en la extensión del archivo para decidir cómo leerlo.
5. El importador debe detectar formato por contenido, por ejemplo:
   - ZIP/OOXML aunque termine en `.xls`;
   - Excel binario real `.xls` si apareciera en el futuro;
   - CSV plano;
   - `.xlsx` explícito.
6. PDF queda explícitamente fuera de alcance V1.
7. El nombre del archivo debe usarse como metadata inicial cuando ayude a inferir banco, producto o tipo de cartola.

Metadata inferible desde los archivos actuales:

| Archivo | Banco | Tipo fuente | Tipo movimiento | Fecha referencial inferida |
|---------|-------|-------------|-----------------|----------------------------|
| `BCI_MovimientosFacturadosNacionales_25-03-2026.xls` | BCI | Tarjeta / movimientos facturados | Nacionales | 2026-03-25 |
| `BCI_MovimientosFacturadosInternacionales_23-04-2026.xls` | BCI | Tarjeta / movimientos facturados | Internacionales | 2026-04-23 |

Pendiente técnico para Programador:

- abrir ambos archivos con lector robusto de Excel OOXML aunque tengan extensión `.xls`;
- identificar nombre de hoja, rango usado, fila de encabezado real y columnas disponibles;
- generar un reporte de inspección inicial antes de cerrar el mapeo definitivo BCI.

---

## 5. Categorías iniciales

| Categoría | Uso |
|-----------|-----|
| Marketing / publicidad | Meta Ads, Google Ads, campañas |
| Proveedores / inventario | Compra de productos para vender |
| Despacho / logística | Starken, Chilexpress, correos |
| Software / tecnología | Shopify, Klaviyo, apps, dominios |
| Sueldos / honorarios | Equipo, comisiones, pagos de trabajo |
| Arriendo / oficina / bodega | Espacios físicos |
| Servicios básicos | Luz, agua, internet |
| Banco / intereses / impuestos | Comisiones, intereses, impuesto crédito |
| Supermercado / hogar | Gasto familiar |
| Comida / restaurantes | Restaurantes, delivery |
| Auto / combustible / ruta | Bencina, peajes, estacionamientos |
| Salud / farmacia | Farmacias, médicos |
| Educación / niños | Colegio, niños, actividades |
| Personal / familiar | Gasto no empresa |
| Por revisar | No se puede clasificar todavía |

---

## 6. Arquitectura propuesta

Arquitectura V1 vigente:

```text
Servidor dev / Host Docker
  └── Docker
      └── contenedor único categorizador-expensas
          ├── aplicación web monolítica
          ├── interfaz por pestañas
          ├── autenticación y roles
          ├── importador de archivos CSV/Excel
          ├── normalizador por fuente
          ├── detector de duplicados
          ├── SQLite como base persistente en volumen
          ├── motor de reglas determinísticas
          ├── editor controlado de movimientos
          └── exportador Excel/CSV
```

La V1 no separa frontend y backend en contenedores distintos. La separación debe ser lógica dentro del código, no operacional.

Flujo lógico:

```text
Usuario autenticado
   ↓
Sube archivo desde pestaña Subir archivos
   ↓
Sistema calcula hash de archivo
   ↓
Sistema valida duplicado de archivo
   ↓
Importador detecta formato real
   ↓
Sistema extrae filas tabulares
   ↓
Staging crudo
   ↓
Normalizador a modelo común
   ↓
Sistema calcula hash de movimiento
   ↓
Detector de duplicados
   ↓
Motor de reglas por glosa normalizada
   ↓
Movimientos categorizados / Por revisar
   ↓
Listado filtrable y editable de forma controlada
   ↓
Exportación Excel de vista completa o filtrada
```

Decisión central:

La clasificación V1 debe ser determinística, auditable y explicable. Se priorizan reglas por glosa antes de IA.

---

## 7. Despliegue y persistencia

La solución debe operar inicialmente en el servidor dev usando Docker.

Debe poder levantarse también en PC local u otro host Docker sin rediseño, siempre que se monten los volúmenes correspondientes.

Estructura persistente conceptual:

```text
/expensas-data
├── uploads
├── exports
├── db
│   └── expensas.db
├── logs
└── backups
```

El contenedor no debe ser el repositorio maestro de datos. La persistencia debe quedar en volúmenes o carpetas montadas desde el host.

---

## 8. Interfaz de aplicación

### 8.1 Dashboard

Debe mostrar:

- total de archivos subidos;
- archivos procesados correctamente;
- archivos con error;
- movimientos extraídos;
- movimientos categorizados;
- movimientos por revisar;
- movimientos duplicados detectados;
- monto total por categoría;
- monto total por banco;
- última importación.

### 8.2 Subir archivos

Debe permitir subir uno o varios archivos:

```text
.xls
.xlsx
.csv
```

Debe permitir registrar o inferir:

- banco;
- tipo de fuente;
- observación opcional.

Debe rechazar PDF en V1 con mensaje explícito de formato no soportado.

### 8.3 Archivos importados

Debe mostrar:

- fecha de carga;
- nombre de archivo;
- banco;
- tipo fuente;
- estado;
- cantidad de filas leídas;
- cantidad de movimientos importados;
- cantidad de duplicados detectados;
- cantidad de errores;
- hash del archivo;
- usuario que cargó el archivo.

Acciones:

- ver detalle;
- ver errores;
- reprocesar sin duplicar;
- marcar archivo como descartado si aplica.

### 8.4 Movimientos

Vista principal del sistema.

Columnas mínimas:

- fecha;
- banco;
- tipo fuente;
- archivo origen;
- glosa original;
- glosa normalizada;
- monto;
- moneda;
- categoría;
- estado;
- duplicado;
- revisado;
- regla aplicada;
- observación.

Filtros mínimos:

- fecha desde / hasta;
- banco;
- archivo;
- categoría;
- glosa contiene;
- monto mínimo / máximo;
- moneda;
- estado;
- duplicados sí/no;
- revisados sí/no;
- por revisar sí/no.

Edición permitida:

- categoría;
- estado de revisión;
- observación;
- marcar como duplicado manual;
- marcar como ignorado.

No deben editarse directamente:

- fecha original;
- monto original;
- glosa original;
- archivo origen;
- fila origen;
- hash del movimiento.

Si se requiere corregir datos de origen, usar campos corregidos separados:

- fecha_corregida;
- monto_corregido;
- glosa_corregida.

### 8.5 Por revisar

Debe mostrar solo movimientos no clasificados o con baja confianza.

Acciones:

- asignar categoría manual;
- crear regla sugerida desde glosa;
- marcar como revisado;
- marcar como ignorado.

### 8.6 Reglas y categorías

Pestaña única con **dos subpestañas**: **Categorías** y **Reglas**. Solo accesible por rol `admin` en V1.

#### Subpestaña Categorías

Catálogo maestro estandarizado de categorías de gasto. Las reglas y las clasificaciones de movimientos referencian categorías por `id`, nunca por texto libre duplicado.

Debe permitir:

- listar categorías activas e inactivas;
- agregar categoría (nombre único, case-insensitive);
- editar nombre y descripción/uso;
- desactivar categoría (no eliminar físicamente si tiene movimientos o reglas asociadas);
- eliminar solo categorías sin uso;
- mostrar contadores de reglas y movimientos asociados (solo lectura).

Campos mínimos:

- nombre;
- uso / descripción (opcional);
- activa.

#### Subpestaña Reglas

Debe permitir administrar reglas de categorización que apuntan a una categoría del catálogo.

Campos:

- patrón (texto a buscar en glosa normalizada; matching por contiene);
- categoría (selector desde catálogo);
- prioridad;
- banco opcional;
- producto opcional;
- subtipo fuente opcional;
- activa;
- comentario.

Comportamiento:

- banco vacío = regla global;
- a igual especificidad gana mayor prioridad numérica;
- regla más específica (con banco) gana sobre regla global;
- botón opcional **Probar regla**: ingresar glosa de ejemplo y ver categoría resultante;
- cambiar una regla no recategoriza movimientos históricos automáticamente; reaplicación manual queda para acción admin futura.

### 8.7 Usuarios/Roles

Debe permitir al administrador crear y administrar usuarios.

Roles iniciales:

| Rol | Permisos principales |
|-----|----------------------|
| admin | Acceso total: dashboard, subida de archivos, edición de movimientos, reglas, usuarios, exportación y administración. |
| usuario | Acceso operativo limitado: dashboard, consulta de movimientos, filtros y exportación. Puede editar categorías solo si el administrador lo permite en configuración futura. |

Requisitos:

1. Debe existir un usuario administrador inicial.
2. El administrador inicial debe poder crear otros usuarios.
3. Debe ser posible asignar rol `admin` o `usuario`.
4. Debe quedar auditoría básica de cambios relevantes por usuario.
5. Las contraseñas no deben almacenarse en texto plano.

### 8.8 Exportar

Debe permitir:

- exportar vista filtrada;
- exportar todo;
- exportar solo por revisar;
- exportar solo duplicados;
- exportar resumen por categoría;
- exportar resumen por banco;
- exportar resumen mensual.

El Excel exportado debe reflejar exactamente los filtros aplicados cuando el usuario elija exportar vista filtrada.

---

## 9. Componentes principales

### 9.1 Aplicación web monolítica

Responsabilidad:

- entregar la interfaz por pestañas;
- administrar navegación;
- validar sesión de usuario;
- invocar servicios internos de importación, normalización, categorización, duplicados y exportación.

### 9.2 Importador de archivos

Responsabilidad:

- recibir archivos desde la interfaz;
- detectar formato real del archivo;
- identificar fuente probable por nombre, carpeta o contenido;
- abrir CSV, XLSX/OOXML y eventualmente XLS binario;
- rechazar PDF en V1;
- registrar archivo importado;
- evitar duplicados usando hash de archivo;
- guardar datos originales en staging.

### 9.3 Normalizador

Responsabilidad:

- convertir diferentes layouts bancarios a un modelo común;
- limpiar glosa;
- normalizar fechas;
- normalizar montos;
- inferir moneda cuando exista;
- mantener referencia a archivo y fila original.

### 9.4 Detector de duplicados

Responsabilidad:

- detectar archivo repetido por hash de archivo;
- detectar movimiento exacto por hash de movimiento;
- marcar posible duplicado cuando existan coincidencias parciales;
- no borrar automáticamente registros financieros;
- permitir resolución manual.

### 9.5 Base SQLite

Responsabilidad:

- repositorio maestro local;
- trazabilidad de importaciones;
- almacenamiento de movimientos crudos y normalizados;
- almacenamiento de categorías y reglas;
- almacenamiento de usuarios, roles y auditoría básica;
- persistencia portable en un archivo `.db`.

### 9.6 Motor de reglas

Responsabilidad:

- aplicar reglas activas por prioridad;
- clasificar por coincidencia de texto en glosa normalizada;
- permitir reglas globales o específicas por banco/fuente;
- dejar como `Por revisar` si no hay coincidencia.

### 9.7 Exportador

Responsabilidad:

- generar archivo consolidado Excel/CSV;
- generar archivo separado de movimientos `Por revisar`;
- exportar resultados filtrados desde la UI;
- incluir columnas de auditoría: fuente, archivo, fila, regla aplicada, método de clasificación.

---

## 10. Modelo de datos conceptual

### 10.1 usuario

```text
id
email
nombre
password_hash
rol_id
activo
fecha_creacion
fecha_ultimo_login
```

### 10.2 rol

```text
id
nombre
descripcion
```

Roles iniciales:

```text
admin
usuario
```

### 10.3 auditoria

```text
id
usuario_id
accion
entidad
entidad_id
fecha
antes_json
despues_json
```

### 10.4 archivo_importado

```text
id
nombre_archivo
ruta_relativa
hash_archivo
banco_inferido
tipo_fuente_inferido
fecha_referencial
fecha_importacion
usuario_id
estado
mensaje_error
```

### 10.5 movimiento_raw

```text
id
archivo_id
fila_origen
hoja_origen
raw_json
fecha_carga
```

### 10.6 movimiento

```text
id
archivo_id
fila_origen
banco
producto
subtipo_fuente
fecha_movimiento
fecha_facturacion
fecha_cargo
glosa_original
glosa_normalizada
glosa_corregida
monto
monto_corregido
moneda
monto_clp
monto_moneda_origen
tipo_movimiento
hash_movimiento
estado_normalizacion
estado_duplicado
movimiento_original_id
score_duplicado
motivo_duplicado
activo
```

Valores sugeridos para `estado_duplicado`:

```text
unico
duplicado_exacto
posible_duplicado
no_duplicado_confirmado
```

### 10.7 categoria

```text
id
nombre
uso
activa
```

### 10.8 regla_categoria

```text
id
patron
categoria_id
prioridad
banco_opcional
producto_opcional
subtipo_fuente_opcional
activa
comentario
creado_por_usuario_id
```

### 10.9 movimiento_categorizado

```text
movimiento_id
categoria_id
metodo_clasificacion
regla_id
confianza
revisado
categoria_manual_id
observacion
fecha_clasificacion
usuario_revision_id
```

---

## 11. Reglas iniciales sugeridas

Ejemplos de reglas base:

| Patrón normalizado | Categoría |
|--------------------|-----------|
| jumbo | Supermercado / hogar |
| lider | Supermercado / hogar |
| unimarc | Supermercado / hogar |
| meta | Marketing / publicidad |
| facebook | Marketing / publicidad |
| google ads | Marketing / publicidad |
| shopify | Software / tecnología |
| klaviyo | Software / tecnología |
| starken | Despacho / logística |
| chilexpress | Despacho / logística |
| correos | Despacho / logística |
| copec | Auto / combustible / ruta |
| shell | Auto / combustible / ruta |
| estacionamiento | Auto / combustible / ruta |
| farmacia | Salud / farmacia |
| cruz verde | Salud / farmacia |
| salcobrand | Salud / farmacia |

Las reglas deben vivir en base SQLite y poder cargarse inicialmente desde un CSV editable.

---

## 12. Flujos de información

### 12.1 Flujo de login y usuarios

```text
1. Usuario accede a la aplicación web.
2. Sistema solicita login.
3. Sistema valida credenciales.
4. Sistema carga rol y permisos.
5. Sistema muestra pestañas disponibles según rol.
```

### 12.2 Flujo de importación

```text
1. Usuario autorizado sube archivo desde la pestaña Subir archivos.
2. Sistema calcula hash del archivo.
3. Sistema verifica si el archivo ya fue importado.
4. Sistema detecta formato real.
5. Sistema rechaza PDF si corresponde.
6. Sistema extrae filas tabulares.
7. Sistema guarda raw_json por fila.
8. Sistema normaliza a modelo común.
9. Sistema calcula hash de movimiento.
10. Sistema detecta duplicados exactos o posibles.
11. Sistema clasifica por reglas.
12. Sistema deja no clasificados como Por revisar.
13. Sistema actualiza dashboard y listados.
```

### 12.3 Flujo de revisión

```text
1. Usuario autorizado revisa movimientos Por revisar.
2. Asigna categoría correcta.
3. La corrección se registra como clasificación manual.
4. Si corresponde, se crea o propone una nueva regla.
5. En la siguiente importación, la regla clasifica automáticamente casos similares.
```

### 12.4 Flujo de exportación

```text
1. Usuario filtra movimientos en la pestaña Movimientos.
2. Usuario elige exportar vista filtrada.
3. Sistema genera Excel con los mismos criterios aplicados.
4. Sistema registra exportación si corresponde.
```

---

## 13. Seguridad y permisos

Criterios:

1. No guardar credenciales bancarias.
2. No conectarse a bancos.
3. No usar APIs bancarias.
4. No subir archivos a servicios externos.
5. No guardar secretos dentro del repositorio.
6. No versionar la base SQLite real con datos financieros si contiene información sensible.
7. No versionar archivos bancarios reales salvo decisión explícita de Miguel.
8. Exigir login para usar la aplicación.
9. Mantener contraseñas con hash seguro, nunca texto plano.
10. Crear usuario administrador inicial.
11. Permitir administración de usuarios desde pestaña Usuarios/Roles.
12. Restringir pestañas y acciones por rol.

Permisos V1 propuestos:

| Función | admin | usuario |
|---------|-------|---------|
| Ver dashboard | Sí | Sí |
| Subir archivos | Sí | No por defecto |
| Ver archivos importados | Sí | Sí |
| Ver movimientos | Sí | Sí |
| Filtrar movimientos | Sí | Sí |
| Exportar Excel | Sí | Sí |
| Editar categoría/observación | Sí | No por defecto |
| Administrar categorías y reglas | Sí | No |
| Administrar usuarios | Sí | No |
| Resolver duplicados | Sí | No por defecto |

---

## 14. Integraciones

### V1

Sin integraciones externas obligatorias.

### V1.5 opcional

NocoDB o interfaz web complementaria solo si la app monolítica no cubre operación.

### V2 opcional

Google Sheets como salida ejecutiva o colaboración.

### V3 opcional

IA para sugerir categorías solo sobre movimientos `Por revisar`, manteniendo auditoría de sugerencia versus decisión final.

### Futuro NetSuite

NetSuite queda fuera de alcance V1. Solo se evaluará si el proyecto evoluciona hacia registro contable, gastos, conciliación o asientos.

---

## 15. Decisiones arquitectónicas vigentes

| Decisión | Estado | Motivo |
|----------|--------|--------|
| Desplegar inicialmente en servidor dev | Vigente | Permite operar como app web real y acceder desde navegador sin depender de la PC local. |
| Mantener un único Docker en V1 | Vigente | Reduce complejidad operacional y permite mover la app a cualquier host Docker. |
| No separar frontend/backend en V1 | Vigente | El alcance no justifica dos servicios; la separación será interna por módulos. |
| Usar SQLite como base maestra local/persistente | Vigente | Liviano, portable, suficiente para V1. |
| Usar interfaz web por pestañas | Vigente | Calza con la operación esperada de carga, revisión, filtros y exportación. |
| Incorporar usuarios y roles en V1 | Vigente | Se requieren varios usuarios con perfiles admin y usuario. |
| Crear usuario administrador inicial | Vigente | Permite operar la app y crear usuarios adicionales desde la UI. |
| Clasificar primero por reglas determinísticas | Vigente | Más auditable, barato y controlable que IA inicial. |
| Exportar Excel/CSV desde vistas filtradas | Vigente | El usuario necesita extraer exactamente lo filtrado. |
| Proteger contra duplicados | Vigente | Evita reprocesamiento y registros repetidos. |
| No usar PDF en V1 | Vigente | Evita complejidad de extracción/OCR. |
| No integrar NetSuite en V1 | Vigente | El objetivo inicial es categorizar y revisar expensas. |
| Detectar formato por contenido y no solo por extensión | Vigente | Los archivos BCI tienen extensión `.xls` pero estructura interna OOXML/ZIP. |
| Unificar Categorías y Reglas en pestaña con subpestañas | Vigente | Reduce fricción operativa; catálogo y matching viven en un mismo módulo. |
| Stack web inicial Streamlit + SQLite | Vigente | App monolítica Python dockerizada; suficiente para V1 con pestañas. |

---

## 16. Requerimiento para Programador

### 16.1 Objetivo técnico

Construir una aplicación web monolítica dockerizada que permita autenticar usuarios, subir archivos financieros, normalizarlos a un modelo común, categorizarlos por reglas, proteger contra duplicados, revisar movimientos en grilla filtrable/editable y exportar resultados a Excel/CSV.

### 16.2 Plataforma esperada

```text
Despliegue inicial: servidor dev
Ejecución: Docker, un solo contenedor de aplicación
Aplicación: web monolítica Python (Streamlit)
Base: SQLite en volumen/carpeta montada
Entrada: .xls / .xlsx / .csv
Salida: Excel / CSV
PDF: fuera de alcance V1
```

### 16.3 Estructura lógica sugerida

```text
app/
├── ui/
│   ├── dashboard.py
│   ├── subir_archivos.py
│   ├── archivos.py
│   ├── movimientos.py
│   ├── por_revisar.py
│   ├── reglas_categorias.py
│   ├── usuarios.py
│   └── exportar.py
├── services/
│   ├── import_service.py
│   ├── normalization_service.py
│   ├── categorization_service.py
│   ├── duplicate_service.py
│   ├── export_service.py
│   └── auth_service.py
├── repositories/
│   ├── movimiento_repository.py
│   ├── archivo_repository.py
│   ├── categoria_repository.py
│   ├── regla_repository.py
│   ├── usuario_repository.py
│   └── auditoria_repository.py
└── db/
    └── schema.sql
```

### 16.4 Requerimientos funcionales

1. Crear aplicación web con login.
2. Crear usuario administrador inicial.
3. Permitir que el administrador cree otros usuarios.
4. Permitir roles `admin` y `usuario`.
5. Mostrar/permitir acciones según rol.
6. Crear interfaz por pestañas.
7. Crear pestaña Dashboard.
8. Crear pestaña Subir archivos.
9. Crear pestaña Archivos importados.
10. Crear pestaña Movimientos con filtros por columna.
11. Permitir exportar a Excel la vista filtrada.
12. Crear pestaña Por revisar.
13. Crear pestaña Reglas y categorías (subpestañas Categorías y Reglas).
14. Crear pestaña Usuarios/Roles.
15. Crear pestaña Exportar.
16. Soportar carga de archivos `.xls`, `.xlsx` y `.csv`.
17. Rechazar PDF con mensaje de formato no soportado en V1.
18. Detectar formato real del archivo:
   - CSV;
   - XLSX/OOXML aunque tenga extensión `.xls`;
   - XLS binario si aparece más adelante.
19. Calcular hash del archivo para evitar importaciones duplicadas.
20. Registrar metadata del archivo importado.
21. Extraer filas tabulares desde hojas Excel.
22. Guardar cada fila original como `raw_json`.
23. Implementar mapeos por fuente bancaria.
24. Crear mapeo inicial para archivos BCI:
   - movimientos facturados nacionales;
   - movimientos facturados internacionales.
25. Normalizar datos mínimos:
   - banco;
   - fecha;
   - glosa;
   - monto;
   - moneda si existe;
   - tipo de fuente;
   - archivo origen;
   - fila origen.
26. Calcular hash de movimiento.
27. Detectar duplicado exacto y posible duplicado.
28. Crear tabla de categorías iniciales.
29. Crear tabla de reglas de categorización.
30. Aplicar reglas por glosa normalizada.
31. Asignar `Por revisar` si no existe regla aplicable.
32. Permitir edición controlada de categoría, observación, estado de revisión y resolución de duplicado.
33. Registrar auditoría básica de cambios críticos.
34. Exportar archivo consolidado categorizado.
35. Exportar archivo de movimientos `Por revisar`.
36. Registrar errores de importación y normalización.

### 16.5 Requerimientos no funcionales

1. No requerir instalación de Python en el host.
2. No requerir instalación de base de datos externa.
3. Ejecutar en un solo contenedor Docker.
4. Persistir base, uploads, exports y logs fuera del contenedor.
5. No modificar archivos originales.
6. No subir datos a internet.
7. Ser reproducible por Docker.
8. Mantener logs legibles.
9. Permitir reejecución sin duplicar movimientos.
10. Mantener trazabilidad completa desde salida final hasta archivo/fila origen.
11. No almacenar contraseñas en texto plano.
12. Mantener código modular aunque la aplicación sea monolítica.

### 16.6 Entregables esperados del Programador

1. `Dockerfile`.
2. Archivo de orquestación local/dev si corresponde.
3. Aplicación web con pestañas.
4. Módulo de login y roles.
5. Módulo de usuarios y roles.
6. Módulo de inspección de archivos Excel/CSV.
7. Importador.
8. Normalizador.
9. Detector de duplicados.
10. Motor de reglas.
11. Exportador Excel/CSV.
12. Esquema SQLite inicial.
13. Semilla de usuario administrador inicial.
14. Semilla de roles `admin` y `usuario`.
15. Semilla de categorías.
16. Semilla de reglas.
17. README técnico de despliegue y operación para Miguel.
18. Prueba con los dos archivos BCI existentes en la carpeta del proyecto.

### 16.7 Primer entregable técnico obligatorio

Antes de implementar la categorización completa, el Programador debe entregar un **inspector de fuentes** que genere un reporte con:

```text
archivo
formato_detectado
hojas_detectadas
rango usado por hoja
fila probable de encabezado
columnas detectadas
primeras filas de ejemplo
errores de lectura
```

Este inspector es necesario para cerrar con evidencia el mapeo exacto de columnas BCI.

---

## 17. Impacto por rol

### Arquitecto

Define la arquitectura, alcance V1, modelo conceptual, decisiones vigentes, seguridad, roles y requerimiento para Programador.

### Configurador

Debe intervenir si se despliega en servidor dev para definir, junto con Miguel:

- host destino;
- puerto interno y externo;
- dominio o URL de acceso;
- reverse proxy si aplica;
- volumen persistente;
- backup del volumen y de SQLite;
- restricción de acceso si corresponde.

No debe configurar NetSuite en V1.

### Programador

Debe implementar la aplicación web monolítica dockerizada, login/roles, importador, normalizador, base SQLite, detector de duplicados, reglas, exportador, auditoría básica y pruebas con archivos BCI.

### Operación

Miguel debe operar desde navegador:

```text
1. Ingresar con usuario administrador inicial.
2. Crear usuarios adicionales si corresponde.
3. Subir archivos bancarios.
4. Revisar resultado de importación.
5. Filtrar movimientos.
6. Corregir categorías o duplicados según permisos.
7. Alimentar nuevas reglas.
8. Exportar Excel según filtros.
```

---

## 18. Pendientes de validación

1. ~~Confirmar stack definitivo de app web: Streamlit u otra alternativa Python.~~ **Resuelto V1.4:** Streamlit.
2. Confirmar URL/host del servidor dev.
3. Confirmar política de contraseñas inicial.
4. Confirmar si el rol `usuario` podrá editar categorías o solo consultar/exportar.
5. Confirmar volumen mensual aproximado de movimientos.
6. Confirmar si se procesarán solo tarjetas o también cuentas corrientes/cartolas.
7. Confirmar si la categoría final debe separar empresa versus personal/familiar.
8. Confirmar si los archivos reales deben permanecer dentro del proyecto o moverse a una carpeta local no versionada.
9. Confirmar reglas iniciales definitivas por comercio/glosa.
10. Confirmar el mapeo exacto de columnas BCI después del inspector del Programador. **Estado:** inspector implementado; pendiente validar con archivos BCI reales de Miguel.
11. Confirmar si movimientos internacionales deben convertirse a CLP o mantener moneda original y monto facturado.

---

## 19. Despliegue técnico (implementación V1.4)

```text
docker compose up --build
```

Acceso local: `http://localhost:8501`

Variables de entorno (`.env`):

| Variable | Descripción | Default |
|----------|-------------|---------|
| `EXPENSAS_DATA_DIR` | Carpeta persistente en host | `./expensas-data` |
| `ADMIN_EMAIL` | Email admin inicial | `admin@local` |
| `ADMIN_PASSWORD` | Contraseña admin inicial | `admin123` |

Estructura de datos en host:

```text
expensas-data/
├── db/expensas.db
├── uploads/
├── exports/
├── logs/
└── backups/
```

---

## 20. Persistencia de datos (actualizaciones y rebuild)

### Principio

Los datos de negocio viven **fuera del contenedor**, en el volumen montado `expensas-data/` del host. Un `docker compose up --build` **reemplaza solo la imagen de la app**, no la base ni los archivos subidos.

### Qué se conserva en cada actualización

| Dato | Ubicación | ¿Se conserva? |
|------|-----------|---------------|
| Base SQLite | `expensas-data/db/expensas.db` | Sí, si el volumen persiste |
| Archivos subidos | `expensas-data/uploads/` | Sí |
| Usuarios y contraseñas | SQLite | Sí (seed no sobrescribe) |
| Categorías y reglas creadas | SQLite | Sí |
| Movimientos y clasificaciones | SQLite | Sí |
| Exportaciones | `expensas-data/exports/` | Sí |

### Reglas de implementación vigentes

1. `CREATE TABLE IF NOT EXISTS` — nunca `DROP` ni `TRUNCATE` en arranque.
2. **Seed inicial** solo si tablas vacías (usuarios/categorías/reglas).
3. **Migraciones** registradas en `schema_migrations` — cada una corre **una sola vez**.
4. **Normalización** desde staging solo **agrega** filas nuevas; no borra movimientos existentes.
5. **Reproceso destructivo** (borrar y volver a importar un archivo) solo vía migración explícita o acción admin futura, nunca automático al abrir la UI.

### Deploy seguro (checklist)

```text
✓ Montar volumen: ./expensas-data:/expensas-data (o volumen nombrado equivalente)
✓ docker compose up --build
✗ NO usar: docker compose down -v  (el -v borra volúmenes nombrados)
✗ NO eliminar la carpeta expensas-data/ del host
✗ NO cambiar EXPENSAS_DATA_DIR sin migrar la carpeta manualmente
```

### Backup recomendado antes de actualizar

Copiar la carpeta completa:

```text
expensas-data/  →  expensas-data/backups/backup-AAAA-MM-DD/
```

Mínimo crítico: `expensas-data/db/expensas.db`.

### Coolify / servidor dev

En el panel de deploy, verificar que exista un **persistent storage** apuntando a `/expensas-data` (o la ruta configurada en `EXPENSAS_DATA_DIR`). Sin ese montaje, cada redeploy crea una base vacía.

### Diagnóstico en la app

El sidebar muestra conteo de movimientos y archivos. Si tras un deploy esos números vuelven a **0**, el volumen no está montado correctamente.
