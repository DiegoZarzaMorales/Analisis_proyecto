# Sistema de Reporte y Seguimiento de Incidencias Urbanas

Proyecto escolar desarrollado en Python con Flask y SQLite.
Permite a los ciudadanos reportar incidencias urbanas (baches, luminarias danadas, basura, etc.)
y a los administradores dar seguimiento y actualizar el estado de cada reporte.

---

## Descripcion general

El sistema tiene dos roles:

| Rol | Funciones |
|---|---|
| **CIUDADANO** | Registrarse, iniciar sesion, crear reportes (descripcion + ubicacion + foto), ver estado de sus reportes |
| **ADMIN** | Iniciar sesion, ver todos los reportes, cambiar el estado (PENDIENTE / EN PROCESO / RESUELTO) |

### Estados de un reporte

- **PENDIENTE** - El reporte fue recibido pero aun no se atiende.
- **EN_PROCESO** - Se esta trabajando en solucionar la incidencia.
- **RESUELTO** - La incidencia fue atendida y resuelta.

---

## Requisitos

- Python 3.10 o superior
- pip (administrador de paquetes de Python)
- Visual Studio Code (recomendado)

---

## Instalacion de dependencias

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

Si prefieres usar un entorno virtual (recomendado):

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## Como ejecutar

```bash
python app.py
```

Para activar el modo de recarga automatica durante el desarrollo:

```bash
# Windows
set FLASK_DEBUG=1 && python app.py

# macOS / Linux
FLASK_DEBUG=1 python app.py
```

Luego abre tu navegador y entra a:

```
http://127.0.0.1:5000
```

La base de datos (`incidencias.db`) y la carpeta `uploads/` se crean automaticamente
la primera vez que ejecutas el sistema.

---

## Credenciales del administrador de prueba

Al ejecutar por primera vez se crea automaticamente un usuario administrador:

| Campo | Valor |
|---|---|
| Correo | `admin@demo.com` |
| Contrasena | `admin123` |

> Para crear un administrador adicional puedes registrarlo directamente
> en la base de datos con un cliente SQLite (por ejemplo DB Browser for SQLite)
> cambiando el campo `rol` a `'ADMIN'`.

---

## Estructura del proyecto

```
Analisis_proyecto/
    app.py              # Aplicacion Flask principal
    schema.sql          # Esquema de la base de datos
    requirements.txt    # Dependencias de Python
    README.md           # Este archivo
    uploads/            # Carpeta donde se guardan las fotos de evidencia
    incidencias.db      # Base de datos SQLite (se genera al ejecutar)
```

---

## Flujo de uso

### Ciudadano
1. Entra a `http://127.0.0.1:5000`
2. Haz clic en **Registrarme** y crea tu cuenta.
3. Inicia sesion con tu correo y contrasena.
4. Haz clic en **Nuevo reporte** para reportar una incidencia.
5. Llena la descripcion, latitud, longitud y sube una foto (opcional).
6. Consulta **Mis reportes** para ver el estado de tus reportes.

### Administrador
1. Inicia sesion con `admin@demo.com` / `admin123`.
2. Haz clic en **Panel admin** en la barra de navegacion.
3. Visualiza todos los reportes y usa el selector para cambiar el estado.
4. Haz clic en **Guardar** para confirmar el cambio.

---

## Notas tecnicas

- La contrasena se guarda con hash usando `werkzeug.security` (no en texto plano).
- La evidencia fotografica se guarda en la carpeta `uploads/` del servidor.
- Las fotos aceptadas son: PNG, JPG, JPEG, WEBP.
- La base de datos es un archivo SQLite local (`incidencias.db`).
- No se requiere instalar ningun servidor de base de datos adicional.
