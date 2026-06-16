PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rol (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES rol(id),
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL DEFAULT (datetime('now')),
    fecha_ultimo_login TEXT
);

CREATE TABLE IF NOT EXISTS sesion_usuario (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    expira_en TEXT NOT NULL,
    creada_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sesion_usuario_expira ON sesion_usuario(expira_en);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuario(id),
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id INTEGER,
    fecha TEXT NOT NULL DEFAULT (datetime('now')),
    antes_json TEXT,
    despues_json TEXT
);

CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
    uso TEXT,
    activa INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS regla_categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patron TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categoria(id),
    prioridad INTEGER NOT NULL DEFAULT 100,
    banco_opcional TEXT,
    producto_opcional TEXT,
    subtipo_fuente_opcional TEXT,
    activa INTEGER NOT NULL DEFAULT 1,
    comentario TEXT,
    creado_por_usuario_id INTEGER REFERENCES usuario(id),
    fecha_creacion TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS archivo_importado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_archivo TEXT NOT NULL,
    ruta_relativa TEXT NOT NULL,
    hash_archivo TEXT NOT NULL UNIQUE,
    banco_inferido TEXT,
    tipo_fuente_inferido TEXT,
    fecha_referencial TEXT,
    fecha_importacion TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_id INTEGER REFERENCES usuario(id),
    estado TEXT NOT NULL DEFAULT 'pendiente',
    mensaje_error TEXT,
    observacion TEXT,
    reporte_inspeccion_json TEXT,
    filas_leidas INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS movimiento_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archivo_id INTEGER NOT NULL REFERENCES archivo_importado(id),
    fila_origen INTEGER NOT NULL,
    hoja_origen TEXT,
    raw_json TEXT NOT NULL,
    fecha_carga TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS movimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archivo_id INTEGER REFERENCES archivo_importado(id),
    fila_origen INTEGER,
    banco TEXT,
    producto TEXT,
    subtipo_fuente TEXT,
    fecha_movimiento TEXT,
    fecha_facturacion TEXT,
    fecha_cargo TEXT,
    glosa_original TEXT,
    glosa_normalizada TEXT,
    glosa_corregida TEXT,
    monto REAL,
    monto_corregido REAL,
    moneda TEXT,
    monto_clp REAL,
    monto_moneda_origen REAL,
    tipo_movimiento TEXT,
    hash_movimiento TEXT UNIQUE,
    estado_normalizacion TEXT,
    estado_duplicado TEXT DEFAULT 'unico',
    movimiento_original_id INTEGER REFERENCES movimiento(id),
    score_duplicado REAL,
    motivo_duplicado TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS movimiento_categorizado (
    movimiento_id INTEGER PRIMARY KEY REFERENCES movimiento(id),
    categoria_id INTEGER REFERENCES categoria(id),
    metodo_clasificacion TEXT,
    regla_id INTEGER REFERENCES regla_categoria(id),
    confianza REAL,
    revisado INTEGER NOT NULL DEFAULT 0,
    categoria_manual_id INTEGER REFERENCES categoria(id),
    observacion TEXT,
    fecha_clasificacion TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_revision_id INTEGER REFERENCES usuario(id)
);

CREATE INDEX IF NOT EXISTS idx_regla_categoria_activa ON regla_categoria(activa);
CREATE INDEX IF NOT EXISTS idx_regla_categoria_banco ON regla_categoria(banco_opcional);
CREATE INDEX IF NOT EXISTS idx_movimiento_hash ON movimiento(hash_movimiento);
