"""
Sistema de Reporte y Seguimiento de Incidencias Urbanas
=======================================================
Proyecto escolar - Python + Flask + SQLite

Roles:
  CIUDADANO - se registra, inicia sesion, crea reportes y consulta sus estados.
  ADMIN     - inicia sesion, ve todos los reportes y cambia su estado.

Ejecutar:
  python app.py
  Luego abrir http://127.0.0.1:5000 en el navegador.

Admin de prueba creado automaticamente:
  Correo    : admin@demo.com
  Contrasena: admin123
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    abort,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


# ---------------------------------------------------------------
# Configuracion de la aplicacion
# ---------------------------------------------------------------

# Directorio donde vive este archivo
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))

# Ruta al archivo de base de datos SQLite
RUTA_BD = os.path.join(RUTA_BASE, "incidencias.db")

# Carpeta donde se guardan las fotos subidas
RUTA_UPLOADS = os.path.join(RUTA_BASE, "uploads")

# Extensiones de imagen aceptadas para la evidencia fotografica
EXTENSIONES_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp"}

app = Flask(__name__)

# Clave secreta para firmar la cookie de sesion.
# En produccion usa una cadena larga y aleatoria y guardala en variable de entorno.
app.secret_key = "cambia_esta_clave_secreta_en_produccion"


# ---------------------------------------------------------------
# Funciones de base de datos
# ---------------------------------------------------------------

def obtener_conexion() -> sqlite3.Connection:
    """Devuelve una conexion SQLite con Row factory para acceder columnas por nombre."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd() -> None:
    """
    Crea la carpeta uploads/ si no existe.
    Si la base de datos no existe todavia, la crea leyendo schema.sql
    e inserta un usuario administrador de prueba.
    """
    # Crear la carpeta de evidencias si no existe
    os.makedirs(RUTA_UPLOADS, exist_ok=True)

    # Si ya existe la base de datos, no hacer nada mas
    if os.path.exists(RUTA_BD):
        return

    # Leer el esquema SQL
    ruta_schema = os.path.join(RUTA_BASE, "schema.sql")
    with open(ruta_schema, "r", encoding="utf-8") as archivo:
        script_sql = archivo.read()

    conexion = obtener_conexion()
    try:
        # Crear las tablas
        conexion.executescript(script_sql)

        # Insertar administrador de prueba
        hash_admin = generate_password_hash("admin123")
        conexion.execute(
            """
            INSERT INTO usuarios (nombre, correo, contrasena_hash, rol)
            VALUES (?, ?, ?, 'ADMIN')
            """,
            ("Administrador", "admin@demo.com", hash_admin),
        )
        conexion.commit()
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Decoradores de acceso
# ---------------------------------------------------------------

def login_requerido(funcion):
    """Redirige al login si el usuario no ha iniciado sesion."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "id_usuario" not in session:
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return envoltura


def admin_requerido(funcion):
    """Redirige al login si no hay sesion; devuelve 403 si no es ADMIN."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "id_usuario" not in session:
            return redirect(url_for("login"))
        if session.get("rol") != "ADMIN":
            abort(403)
        return funcion(*args, **kwargs)
    return envoltura


# ---------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------

def extension_valida(nombre_archivo: str) -> bool:
    """Comprueba que el archivo tenga una extension de imagen permitida."""
    _, ext = os.path.splitext(nombre_archivo.lower())
    return ext in EXTENSIONES_PERMITIDAS


def html_layout(titulo: str, contenido: str, mensaje_error: str = "", mensaje_ok: str = "") -> str:
    """
    Devuelve una pagina HTML completa con barra de navegacion.
    Mantiene el proyecto simple (sin archivos de plantilla separados).
    """
    usuario = session.get("nombre", "")
    rol = session.get("rol", "")

    # Barra de navegacion segun si hay sesion iniciada o no
    if usuario:
        enlace_sesion = (
            f'Sesion: <b>{usuario}</b> ({rol}) '
            f'| <a href="{url_for("logout")}">Salir</a>'
        )
        enlaces_nav = (
            f'<a href="{url_for("inicio")}">Inicio</a> | '
            f'<a href="{url_for("mis_reportes")}">Mis reportes</a> | '
            f'<a href="{url_for("nuevo_reporte_form")}">Nuevo reporte</a>'
        )
        if rol == "ADMIN":
            enlaces_nav += f' | <a href="{url_for("panel_admin")}">Panel admin</a>'
    else:
        enlace_sesion = (
            f'<a href="{url_for("login")}">Iniciar sesion</a> | '
            f'<a href="{url_for("registro_form")}">Registrarse</a>'
        )
        enlaces_nav = f'<a href="{url_for("inicio")}">Inicio</a>'

    alerta_error = f'<p style="color:red; font-weight:bold;">{mensaje_error}</p>' if mensaje_error else ""
    alerta_ok = f'<p style="color:green; font-weight:bold;">{mensaje_ok}</p>' if mensaje_ok else ""

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titulo} - Incidencias Urbanas</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f9f9f9; color: #222; }}
    .barra-nav {{ background: #1a73e8; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }}
    .barra-nav a {{ color: #fff; text-decoration: none; margin-right: 10px; }}
    .barra-nav a:hover {{ text-decoration: underline; }}
    .contenedor {{ max-width: 960px; margin: 30px auto; background: #fff; padding: 24px 32px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    h2 {{ color: #1a73e8; margin-top: 0; }}
    label {{ font-weight: bold; }}
    input[type=text], input[type=email], input[type=password], input[type=number], textarea, select {{
      width: 100%; padding: 8px; margin: 6px 0 14px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
    }}
    button[type=submit] {{ background: #1a73e8; color: #fff; border: none; padding: 10px 22px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
    button[type=submit]:hover {{ background: #1558b0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #1a73e8; color: #fff; padding: 8px; text-align: left; }}
    td {{ padding: 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
    tr:nth-child(even) {{ background: #f4f8ff; }}
    .etiqueta-estado {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
    .estado-PENDIENTE {{ background: #fff3cd; color: #856404; }}
    .estado-EN_PROCESO {{ background: #cfe2ff; color: #0a3f8e; }}
    .estado-RESUELTO {{ background: #d1e7dd; color: #0a4a2e; }}
  </style>
</head>
<body>
  <div class="barra-nav">
    <div>{enlaces_nav}</div>
    <div>{enlace_sesion}</div>
  </div>
  <div class="contenedor">
    <h2>{titulo}</h2>
    {alerta_error}
    {alerta_ok}
    {contenido}
  </div>
</body>
</html>"""


# ---------------------------------------------------------------
# Rutas publicas
# ---------------------------------------------------------------

@app.get("/")
def inicio():
    contenido = """
    <p>Bienvenido al sistema de reporte y seguimiento de incidencias urbanas.</p>
    <ul>
      <li><b>Ciudadanos:</b> registrate, inicia sesion, crea reportes (con descripcion, ubicacion y foto) y consulta su estado.</li>
      <li><b>Administradores:</b> inicia sesion y gestiona todos los reportes cambiando su estado.</li>
    </ul>
    <h3>Estados posibles de un reporte</h3>
    <ul>
      <li><span class="etiqueta-estado estado-PENDIENTE">PENDIENTE</span> - El reporte fue recibido pero aun no se atiende.</li>
      <li><span class="etiqueta-estado estado-EN_PROCESO">EN PROCESO</span> - Se esta trabajando en solucionar la incidencia.</li>
      <li><span class="etiqueta-estado estado-RESUELTO">RESUELTO</span> - La incidencia fue atendida y resuelta.</li>
    </ul>
    <p>
      <a href="/registro"><button type="button" style="background:#1a73e8;color:#fff;border:none;padding:10px 18px;border-radius:4px;cursor:pointer;margin-right:8px;">Registrarme</button></a>
      <a href="/login"><button type="button" style="background:#555;color:#fff;border:none;padding:10px 18px;border-radius:4px;cursor:pointer;">Iniciar sesion</button></a>
    </p>
    <hr>
    <p style="color:#555;font-size:13px;">
      <b>Admin de prueba:</b> correo <code>admin@demo.com</code> / contrasena <code>admin123</code>
    </p>
    """
    return html_layout("Sistema de Incidencias Urbanas", contenido)


@app.get("/registro")
def registro_form():
    contenido = """
    <form method="post" action="/registro">
      <label>Nombre completo:</label>
      <input name="nombre" type="text" required maxlength="120" placeholder="Ej. Juan Perez">

      <label>Correo electronico:</label>
      <input name="correo" type="email" required maxlength="200" placeholder="correo@ejemplo.com">

      <label>Contrasena:</label>
      <input name="contrasena" type="password" required minlength="6" placeholder="Minimo 6 caracteres">

      <button type="submit">Crear cuenta</button>
    </form>
    <p style="margin-top:14px;">Ya tienes cuenta? <a href="/login">Inicia sesion aqui</a>.</p>
    """
    return html_layout("Registro de ciudadano", contenido)


@app.post("/registro")
def registro_post():
    nombre = (request.form.get("nombre") or "").strip()
    correo = (request.form.get("correo") or "").strip().lower()
    contrasena = request.form.get("contrasena") or ""

    if not nombre or not correo or not contrasena:
        return html_layout("Registro", "", mensaje_error="Todos los campos son obligatorios."), 400

    if len(contrasena) < 6:
        return html_layout("Registro", "", mensaje_error="La contrasena debe tener al menos 6 caracteres."), 400

    hash_contrasena = generate_password_hash(contrasena)

    conexion = obtener_conexion()
    try:
        try:
            conexion.execute(
                "INSERT INTO usuarios (nombre, correo, contrasena_hash, rol) VALUES (?, ?, ?, 'CIUDADANO')",
                (nombre, correo, hash_contrasena),
            )
            conexion.commit()
        except sqlite3.IntegrityError:
            return html_layout("Registro", "", mensaje_error="Ese correo ya esta registrado."), 400
    finally:
        conexion.close()

    return redirect(url_for("login") + "?ok=registro")


@app.get("/login")
def login():
    mensaje_ok = "Cuenta creada. Ahora inicia sesion." if request.args.get("ok") == "registro" else ""
    contenido = """
    <form method="post" action="/login">
      <label>Correo electronico:</label>
      <input name="correo" type="email" required placeholder="correo@ejemplo.com">

      <label>Contrasena:</label>
      <input name="contrasena" type="password" required placeholder="Tu contrasena">

      <button type="submit">Entrar</button>
    </form>
    <p style="margin-top:14px;">No tienes cuenta? <a href="/registro">Registrate aqui</a>.</p>
    """
    return html_layout("Inicio de sesion", contenido, mensaje_ok=mensaje_ok)


@app.post("/login")
def login_post():
    correo = (request.form.get("correo") or "").strip().lower()
    contrasena = request.form.get("contrasena") or ""

    conexion = obtener_conexion()
    try:
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE correo = ?", (correo,)
        ).fetchone()
    finally:
        conexion.close()

    if not usuario or not check_password_hash(usuario["contrasena_hash"], contrasena):
        return html_layout(
            "Inicio de sesion",
            """
            <form method="post" action="/login">
              <label>Correo electronico:</label>
              <input name="correo" type="email" required>
              <label>Contrasena:</label>
              <input name="contrasena" type="password" required>
              <button type="submit">Entrar</button>
            </form>
            """,
            mensaje_error="Correo o contrasena incorrectos.",
        ), 401

    # Guardar datos minimos en la sesion del navegador
    session["id_usuario"] = usuario["id"]
    session["nombre"] = usuario["nombre"]
    session["rol"] = usuario["rol"]

    return redirect(url_for("inicio"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


# ---------------------------------------------------------------
# Rutas de ciudadano (reportes)
# ---------------------------------------------------------------

@app.get("/reporte/nuevo")
@login_requerido
def nuevo_reporte_form():
    contenido = """
    <p>Completa el formulario para crear un nuevo reporte de incidencia.</p>
    <form method="post" action="/reporte/nuevo" enctype="multipart/form-data">
      <label>Descripcion del problema:</label>
      <textarea name="descripcion" required rows="4" placeholder="Describe la incidencia con detalle..."></textarea>

      <label>Latitud (grados decimales):</label>
      <input name="latitud" type="number" step="any" required placeholder="Ej. 19.432608">

      <label>Longitud (grados decimales):</label>
      <input name="longitud" type="number" step="any" required placeholder="Ej. -99.133209">

      <label>Evidencia fotografica (opcional, PNG/JPG/JPEG/WEBP):</label>
      <input name="foto" type="file" accept=".png,.jpg,.jpeg,.webp">

      <button type="submit">Enviar reporte</button>
    </form>
    <p style="color:#777;font-size:13px;">
      La foto se guarda en la carpeta <b>uploads/</b> del servidor.
    </p>
    """
    return html_layout("Nuevo reporte", contenido)


@app.post("/reporte/nuevo")
@login_requerido
def nuevo_reporte_post():
    descripcion = (request.form.get("descripcion") or "").strip()
    latitud_str = (request.form.get("latitud") or "").strip()
    longitud_str = (request.form.get("longitud") or "").strip()
    archivo_foto = request.files.get("foto")

    # Validacion de campos obligatorios
    if not descripcion or not latitud_str or not longitud_str:
        return html_layout("Nuevo reporte", "", mensaje_error="Descripcion, latitud y longitud son obligatorios."), 400

    # Convertir coordenadas a numeros
    try:
        latitud = float(latitud_str)
        longitud = float(longitud_str)
    except ValueError:
        return html_layout("Nuevo reporte", "", mensaje_error="Latitud y longitud deben ser numeros validos."), 400

    # Guardar foto si se adjunto una
    nombre_foto = None
    if archivo_foto and archivo_foto.filename:
        nombre_seguro = secure_filename(archivo_foto.filename)
        if not extension_valida(nombre_seguro):
            return html_layout(
                "Nuevo reporte", "",
                mensaje_error="Formato de imagen no permitido. Usa PNG, JPG, JPEG o WEBP.",
            ), 400

        # Generar nombre unico usando id de usuario, fecha y hora actual
        marca_tiempo = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        _, ext = os.path.splitext(nombre_seguro)
        nombre_foto = f"reporte_{session['id_usuario']}_{marca_tiempo}{ext.lower()}"
        ruta_destino = os.path.join(RUTA_UPLOADS, nombre_foto)
        archivo_foto.save(ruta_destino)

    fecha_creacion = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conexion = obtener_conexion()
    try:
        conexion.execute(
            """
            INSERT INTO reportes (id_usuario, descripcion, latitud, longitud, ruta_foto, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, 'PENDIENTE', ?)
            """,
            (session["id_usuario"], descripcion, latitud, longitud, nombre_foto, fecha_creacion),
        )
        conexion.commit()
    finally:
        conexion.close()

    return redirect(url_for("mis_reportes") + "?ok=creado")


@app.get("/reportes")
@login_requerido
def mis_reportes():
    mensaje_ok = "Reporte creado correctamente." if request.args.get("ok") == "creado" else ""

    conexion = obtener_conexion()
    try:
        reportes = conexion.execute(
            "SELECT * FROM reportes WHERE id_usuario = ? ORDER BY id DESC",
            (session["id_usuario"],),
        ).fetchall()
    finally:
        conexion.close()

    # Construir filas de la tabla
    filas_html = ""
    for reporte in reportes:
        estado = reporte["estado"]
        etiqueta_estado = f'<span class="etiqueta-estado estado-{estado}">{estado.replace("_", " ")}</span>'

        if reporte["ruta_foto"]:
            celda_foto = f'<a href="/uploads/{reporte["ruta_foto"]}" target="_blank">Ver foto</a>'
        else:
            celda_foto = "Sin foto"

        filas_html += f"""
        <tr>
          <td>{reporte["id"]}</td>
          <td>{reporte["descripcion"]}</td>
          <td>{reporte["latitud"]},<br>{reporte["longitud"]}</td>
          <td>{etiqueta_estado}</td>
          <td>{reporte["fecha_creacion"]}</td>
          <td>{celda_foto}</td>
        </tr>"""

    if not filas_html:
        filas_html = "<tr><td colspan='6' style='text-align:center;'>Aun no tienes reportes. <a href='/reporte/nuevo'>Crea uno aqui</a>.</td></tr>"

    contenido = f"""
    <p>Aqui puedes ver todos tus reportes y su estado actual.</p>
    <a href="/reporte/nuevo">
      <button type="button" style="background:#1a73e8;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;margin-bottom:14px;">
        Nuevo reporte
      </button>
    </a>
    <table>
      <tr>
        <th>ID</th>
        <th>Descripcion</th>
        <th>Ubicacion (lat/lon)</th>
        <th>Estado</th>
        <th>Fecha</th>
        <th>Foto</th>
      </tr>
      {filas_html}
    </table>
    """
    return html_layout("Mis reportes", contenido, mensaje_ok=mensaje_ok)


@app.get("/uploads/<nombre_archivo>")
@login_requerido
def ver_upload(nombre_archivo: str):
    """
    Sirve los archivos de evidencia fotografica.
    Solo permite el acceso si el archivo pertenece a un reporte del usuario
    que hizo la solicitud, o si el usuario es ADMIN.
    """
    # Los administradores pueden ver todas las fotos
    if session.get("rol") == "ADMIN":
        return send_from_directory(RUTA_UPLOADS, nombre_archivo)

    # Los ciudadanos solo pueden ver fotos de sus propios reportes
    conexion = obtener_conexion()
    try:
        reporte = conexion.execute(
            "SELECT id FROM reportes WHERE ruta_foto = ? AND id_usuario = ?",
            (nombre_archivo, session["id_usuario"]),
        ).fetchone()
    finally:
        conexion.close()

    if reporte is None:
        abort(403)

    return send_from_directory(RUTA_UPLOADS, nombre_archivo)


# ---------------------------------------------------------------
# Rutas del panel administrativo
# ---------------------------------------------------------------

@app.get("/admin")
@admin_requerido
def panel_admin():
    mensaje_ok = "Estado actualizado correctamente." if request.args.get("ok") == "actualizado" else ""

    conexion = obtener_conexion()
    try:
        reportes = conexion.execute(
            """
            SELECT r.*, u.nombre AS nombre_usuario, u.correo AS correo_usuario
            FROM reportes r
            JOIN usuarios u ON u.id = r.id_usuario
            ORDER BY r.id DESC
            """
        ).fetchall()
    finally:
        conexion.close()

    filas_html = ""
    for reporte in reportes:
        estado = reporte["estado"]
        opciones_estado = ""
        for opcion in ("PENDIENTE", "EN_PROCESO", "RESUELTO"):
            seleccionado = 'selected' if estado == opcion else ''
            opciones_estado += f'<option value="{opcion}" {seleccionado}>{opcion.replace("_", " ")}</option>'

        if reporte["ruta_foto"]:
            celda_foto = f'<a href="/uploads/{reporte["ruta_foto"]}" target="_blank">Ver foto</a>'
        else:
            celda_foto = "Sin foto"

        etiqueta_estado = f'<span class="etiqueta-estado estado-{estado}">{estado.replace("_", " ")}</span>'

        filas_html += f"""
        <tr>
          <td>{reporte["id"]}</td>
          <td>{reporte["nombre_usuario"]}<br><small style="color:#777;">{reporte["correo_usuario"]}</small></td>
          <td>{reporte["descripcion"]}</td>
          <td>{reporte["latitud"]},<br>{reporte["longitud"]}</td>
          <td>{etiqueta_estado}</td>
          <td>{reporte["fecha_creacion"]}</td>
          <td>{celda_foto}</td>
          <td>
            <form method="post" action="/admin/actualizar_estado" style="margin:0;">
              <input type="hidden" name="id_reporte" value="{reporte["id"]}">
              <select name="estado" style="width:auto;padding:4px;margin:0 0 6px 0;">
                {opciones_estado}
              </select><br>
              <button type="submit" style="padding:4px 10px;font-size:12px;">Guardar</button>
            </form>
          </td>
        </tr>"""

    if not filas_html:
        filas_html = "<tr><td colspan='8' style='text-align:center;'>No hay reportes registrados.</td></tr>"

    contenido = f"""
    <p>Panel de administracion: gestiona todos los reportes y actualiza su estado.</p>
    <table>
      <tr>
        <th>ID</th>
        <th>Ciudadano</th>
        <th>Descripcion</th>
        <th>Ubicacion (lat/lon)</th>
        <th>Estado actual</th>
        <th>Fecha</th>
        <th>Foto</th>
        <th>Cambiar estado</th>
      </tr>
      {filas_html}
    </table>
    """
    return html_layout("Panel de administracion", contenido, mensaje_ok=mensaje_ok)


@app.post("/admin/actualizar_estado")
@admin_requerido
def admin_actualizar_estado():
    id_reporte = request.form.get("id_reporte")
    nuevo_estado = request.form.get("estado")

    estados_validos = {"PENDIENTE", "EN_PROCESO", "RESUELTO"}
    if not id_reporte or nuevo_estado not in estados_validos:
        return html_layout("Error", "", mensaje_error="Datos invalidos para actualizar el estado."), 400

    conexion = obtener_conexion()
    try:
        conexion.execute(
            "UPDATE reportes SET estado = ? WHERE id = ?",
            (nuevo_estado, int(id_reporte)),
        )
        conexion.commit()
    finally:
        conexion.close()

    return redirect(url_for("panel_admin") + "?ok=actualizado")


# ---------------------------------------------------------------
# Manejo de errores
# ---------------------------------------------------------------

@app.errorhandler(403)
def error_403(e):
    return html_layout("Acceso denegado", "<p>No tienes permiso para acceder a esta pagina.</p>"), 403


@app.errorhandler(404)
def error_404(e):
    return html_layout("Pagina no encontrada", "<p>La pagina que buscas no existe.</p>"), 404


# ---------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------

if __name__ == "__main__":
    inicializar_bd()
    # Modo debug: activo solo si la variable de entorno FLASK_DEBUG=1
    # En produccion asegurate de que FLASK_DEBUG no este definida.
    modo_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=modo_debug)
