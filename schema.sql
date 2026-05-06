-- ============================================================
-- Esquema de base de datos para el sistema de incidencias urbanas
-- Proyecto escolar - SQLite
-- ============================================================

-- Eliminar tablas si ya existen (para poder reinicializar)
DROP TABLE IF EXISTS reportes;
DROP TABLE IF EXISTS usuarios;

-- Tabla de usuarios
-- Almacena tanto ciudadanos como administradores
CREATE TABLE usuarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT    NOT NULL,
    correo           TEXT    NOT NULL UNIQUE,
    contrasena_hash  TEXT    NOT NULL,
    rol              TEXT    NOT NULL CHECK (rol IN ('CIUDADANO', 'ADMIN'))
);

-- Tabla de reportes de incidencias
-- Cada reporte pertenece a un ciudadano
CREATE TABLE reportes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario      INTEGER NOT NULL,
    descripcion     TEXT    NOT NULL,
    latitud         REAL    NOT NULL,
    longitud        REAL    NOT NULL,
    ruta_foto       TEXT,                        -- Nombre del archivo en uploads/ (puede ser NULL)
    estado          TEXT    NOT NULL DEFAULT 'PENDIENTE'
                    CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'RESUELTO')),
    fecha_creacion  TEXT    NOT NULL,            -- ISO 8601 (ej. 2025-01-15T10:30:00)
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
