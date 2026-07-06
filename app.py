# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    app.py
# =============================================================

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import subprocess
import os
import threading
import hashlib
import pkcs11
from pkcs11 import ObjectClass, Attribute, Mechanism
from cryptography import x509
from cryptography.hazmat.backends import default_backend

try:
    import pyttsx3
    TTS_DISPONIBLE = True
except Exception:
    TTS_DISPONIBLE = False
    print("[TTS] pyttsx3 no disponible — instala con: py -3.11 -m pip install pyttsx3")
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora  # Clave para cifrar la sesión

BASE_DIR = r"C:\Users\cvetu\Desktop\TFG1"
# Nota: tts.js debe estar en TFG1/static/tts.js
CERT_DB = os.path.join(BASE_DIR, "database", "censo_burgos.db")

ADMIN_USER = "admin"
ADMIN_PASS = "gade1500"

SCRIPT_TEST_LECTOR      = os.path.join(BASE_DIR, "test_lector.py")
SCRIPT_LEER_DNI         = os.path.join(BASE_DIR, "leer_dni.py")
SCRIPT_LEER_CERTIFICADO = os.path.join(BASE_DIR, "leer_certificado.py")
SCRIPT_CONSULTAR_CENSO  = os.path.join(BASE_DIR, "consultar_censo.py")
CANDIDATURAS_DB = os.path.join(BASE_DIR, "database", "candidaturas_burgos.db")
URNA_DB         = os.path.join(BASE_DIR, "database", "urna_burgos.db")
CENSO_DB        = os.path.join(BASE_DIR, "database", "censo_burgos.db")
PARTIDOS_DB     = os.path.join(BASE_DIR, "database", "partidos_burgos.db")
SIMULACION_DB   = os.path.join(BASE_DIR, "database", "simulacion_burgos.db")
CONTROL_VOTO_HASH_DB = os.path.join(BASE_DIR, "database", "control_voto_hash.db")

# Clave secreta del servidor para calcular el hash de control de unicidad.
RUTA_CLAVE_SECRETA = os.path.join(BASE_DIR, "clave_secreta.txt")
try:
    with open(RUTA_CLAVE_SECRETA) as f:
        CLAVE_SECRETA_SERVIDOR = f.read().strip()
except FileNotFoundError:
    print("[AVISO] No se encontró clave_secreta.txt. Ejecuta generar_clave_secreta.py")
    CLAVE_SECRETA_SERVIDOR = ""


# ── CONFIGURACIÓN DE ENVÍO DE EMAIL

RUTA_EMAIL_CONFIG = os.path.join(BASE_DIR, "email_config.txt")
try:
    with open(RUTA_EMAIL_CONFIG, encoding="utf-8") as f:
        lineas = [l.strip() for l in f.readlines() if l.strip()]
        EMAIL_REMITENTE = lineas[0]
        EMAIL_CONTRASENA_APP = lineas[1]
except (FileNotFoundError, IndexError):
    print("[AVISO] No se encontró email_config.txt o está incompleto. "
          "El envío de certificados por correo no funcionará.")
    EMAIL_REMITENTE = ""
    EMAIL_CONTRASENA_APP = ""


def enviar_certificado_por_email(destinatario, pdf_bytes, codigo):
    """
    Envía el certificado PDF de voto al correo del votante mediante Gmail
    (SMTP con contraseña de aplicación). El correo del destinatario no se
    guarda en ningún sitio: solo se usa para este envío puntual.
    """
    import smtplib
    from email.message import EmailMessage

    if not EMAIL_REMITENTE or not EMAIL_CONTRASENA_APP:
        raise RuntimeError("El sistema de envío de correo no está configurado (email_config.txt)")

    msg = EmailMessage()
    msg["Subject"] = "Justificante de voto — Sistema de Votación Electrónica"
    msg["From"] = EMAIL_REMITENTE
    msg["To"] = destinatario
    msg.set_content(
        "Adjunto encontrará el justificante de su voto emitido en el "
        "Sistema de Votación Electrónica de la Universidad de Burgos.\n\n"
        f"Número de justificante: {codigo}\n\n"
        "Recuerde que su voto es secreto: este justificante no contiene "
        "ninguna información sobre la candidatura votada.\n\n"
        "Este es un correo automático, por favor no responda a este mensaje."
    )
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"certificado_voto_{codigo}.pdf"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(EMAIL_REMITENTE, EMAIL_CONTRASENA_APP)
        servidor.send_message(msg)


# ── SESIÓN PKCS#11 PERSISTENTE 
RUTA_LIB_PKCS11 = r'C:\Program Files\OpenSC Project\OpenSC\pkcs11\opensc-pkcs11.dll'

_pkcs11_token_ctx = None    # context manager de token.open(), para poder cerrarlo
_pkcs11_session   = None    # sesión PKCS#11 abierta (con login ya hecho)
_pkcs11_clave_priv = None   # objeto de clave privada para firmar


def pkcs11_cerrar_sesion():
    """Cierra la sesión PKCS#11 si hay alguna abierta. Permite retirar el DNIe."""
    global _pkcs11_token_ctx, _pkcs11_session, _pkcs11_clave_priv
    if _pkcs11_token_ctx is not None:
        try:
            _pkcs11_token_ctx.__exit__(None, None, None)
        except Exception as e:
            print(f"[PKCS11] Error cerrando sesión: {e}")
    _pkcs11_token_ctx  = None
    _pkcs11_session    = None
    _pkcs11_clave_priv = None


def pkcs11_abrir_y_leer_certificado(pin):
    """
    Abre una sesión PKCS#11 con el PIN dado y la deja ABIERTA (no se cierra
    al terminar la función), guardándola en las variables globales para
    poder firmar más adelante sin pedir el PIN otra vez.

    Devuelve un diccionario con el resultado, igual que hacía el antiguo
    leer_certificado.py por subprocess, pero ejecutado dentro del propio
    proceso de Flask.
    """
    global _pkcs11_token_ctx, _pkcs11_session, _pkcs11_clave_priv

    # Por si quedara una sesión anterior sin cerrar (ej. proceso cancelado)
    pkcs11_cerrar_sesion()

    try:
        lib = pkcs11.lib(RUTA_LIB_PKCS11)
    except Exception as e:
        return {"ok": False, "error": f"No se pudo cargar la librería PKCS#11: {e}"}

    token = None
    for slot in lib.get_slots():
        try:
            token = slot.get_token()
            break
        except Exception:
            pass

    if token is None:
        return {"ok": False, "error": "No hay DNI insertado en el lector"}

    try:
        token_ctx = token.open(user_pin=pin)
        session_pkcs = token_ctx.__enter__()

        certs = list(session_pkcs.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))

        datos_certificado = None
        for cert in certs:
            cert_der = cert[Attribute.VALUE]
            x509_cert = x509.load_der_x509_certificate(cert_der, default_backend())
            subject = x509_cert.subject

            datos = {}
            for attr in subject:
                datos[attr.oid._name] = attr.value

            if "serialNumber" in datos:
                dni = datos.get("serialNumber", "")
                common_name = datos.get("commonName", "")

                apellido1 = apellido2 = nombre = ""
                try:
                    base = common_name.split("(")[0].strip()
                    partes = base.split(",")
                    if len(partes) == 2:
                        apellidos = partes[0].strip()
                        nombre = partes[1].strip()
                        apellidos_split = apellidos.split()
                        if len(apellidos_split) >= 2:
                            apellido1 = apellidos_split[0]
                            apellido2 = apellidos_split[1]
                        elif len(apellidos_split) == 1:
                            apellido1 = apellidos_split[0]
                except Exception:
                    pass

                # Extraer la clave pública del certificado en formato PEM
                from cryptography.hazmat.primitives import serialization
                clave_publica_pem = x509_cert.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode("utf-8")

                datos_certificado = {
                    "dni": dni, "nombre": nombre,
                    "apellido1": apellido1, "apellido2": apellido2,
                    "clave_publica_pem": clave_publica_pem
                }
                break

        if datos_certificado is None:
            token_ctx.__exit__(None, None, None)
            return {"ok": False, "error": "No se encontró certificado válido en el DNIe"}

        # Buscar la clave privada de autenticación/firma para usarla después
        claves_priv = list(session_pkcs.get_objects({Attribute.CLASS: ObjectClass.PRIVATE_KEY}))
        clave_priv = claves_priv[0] if claves_priv else None

        # Guardar la sesión ABIERTA en las variables globales (no se cierra aquí)
        _pkcs11_token_ctx  = token_ctx
        _pkcs11_session    = session_pkcs
        _pkcs11_clave_priv = clave_priv

        return {"ok": True, "datos": datos_certificado}

    except Exception as e:
        pkcs11_cerrar_sesion()
        if "CKR_PIN" in str(e) or "pin" in str(e).lower():
            return {"ok": False, "error": "PIN incorrecto"}
        return {"ok": False, "error": str(e)}


def pkcs11_firmar(mensaje):
    """
    Firma el mensaje dado usando la sesión PKCS#11 ya abierta (con login
    hecho previamente). No vuelve a pedir el PIN porque la sesión sigue viva.
    Devuelve la firma en hexadecimal, o None si no hay sesión disponible.
    """
    global _pkcs11_clave_priv
    if _pkcs11_clave_priv is None:
        return None
    try:
        firma_bytes = _pkcs11_clave_priv.sign(
            mensaje.encode("utf-8"),
            mechanism=Mechanism.SHA256_RSA_PKCS
        )
        return firma_bytes.hex()
    except Exception as e:
        print(f"[PKCS11] Error al firmar: {e}")
        return None


def calcular_hash_dni(dni):
    """
    Calcula el hash de control de unicidad a partir del DNI y la clave
    secreta del servidor. Este hash se guarda en control_voto_hash.db y permite
    comprobar si una persona ya ha votado sin almacenar su DNI en claro.
    """
    texto = dni + CLAVE_SECRETA_SERVIDOR
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def ejecutar_script(script_path, input_text=None, args=None):
    try:
        comando = ["python", script_path] + (args or [])
        resultado = subprocess.run(
            comando,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=BASE_DIR
        )

        salida_stdout = (resultado.stdout or "").strip()
        salida_stderr = (resultado.stderr or "").strip()

        salida = salida_stdout
        if salida_stderr:
            salida = salida + "\n" + salida_stderr if salida else salida_stderr

        return {
            "returncode": resultado.returncode,
            "salida": salida
        }

    except Exception as e:
        return {
            "returncode": -1,
            "salida": f"ERROR: {str(e)}"
        }


# ── RUTAS DE PANTALLAS ──

@app.route("/")
def raiz():
    session.clear()  # Limpiar sesión al volver al inicio
    pkcs11_cerrar_sesion()  # Por si el proceso se abandonó con el DNIe insertado
    return render_template("1.Inicio.html")

@app.route("/inicio")
def inicio():
    session.clear()
    pkcs11_cerrar_sesion()
    return render_template("1.Inicio.html")

@app.route("/login")
def login():
    session.clear()
    pkcs11_cerrar_sesion()
    return render_template("1.Inicio.html")

@app.route("/pasos")
def pasos():
    return render_template("2.pasos.html")

@app.route("/dni")
def dni():
    return render_template("3.dni.html")

@app.route("/validacion")
def validacion():
    # Pasar datos del votante a la plantilla
    nombre    = session.get("nombre", "")
    apellidos = session.get("apellidos", "")
    dni_num   = session.get("dni", "")
    return render_template("4.validacion_censo.html",
                           nombre=nombre,
                           apellidos=apellidos,
                           dni=dni_num)

@app.route("/votacion")
def votacion():
    # Verificar que el votante pasó la validación
    if not session.get("validado"):
        return redirect(url_for("raiz"))
    nombre = session.get("nombre", "")
    return render_template("seleccion_partidos.html", nombre=nombre)

@app.route("/confirmacion")
def confirmacion():
    if not session.get("voto_emitido"):
        return redirect(url_for("raiz"))
    return render_template("confirmacion.html")


@app.route("/api/confirmacion")
def api_confirmacion():
    if not session.get("voto_emitido"):
        return jsonify({"ok": False})
    import re
    dni = session.get("dni", "")
    dni_oculto = re.sub(r"(?<=.{4}).(?=.)", "*", dni[:-1]) + dni[-1] if len(dni) > 1 else dni
    return jsonify({
        "ok":        True,
        "nombre":    session.get("nombre", ""),
        "apellidos": session.get("apellidos", ""),
        "dni_oculto": dni_oculto,
        "distrito":  session.get("distrito", ""),
        "seccion":   session.get("seccion", ""),
        "mesa":      session.get("mesa", ""),
        "local":     session.get("local", ""),
        "codigo":    session.get("codigo_voto", ""),
        "fecha_hora": session.get("fecha_voto", "")
    })


@app.route("/api/enviar_certificado", methods=["POST"])
def api_enviar_certificado():
    """
    Genera el certificado PDF de voto y lo envía por correo electrónico al
    votante. El PDF se genera en memoria y nunca se guarda en disco. El
    email introducido tampoco se almacena en ninguna base de datos: se usa
    exclusivamente para este envío puntual y se descarta inmediatamente
    después, preservando el anonimato del sistema de votación.
    """
    if not session.get("voto_emitido"):
        return jsonify({"ok": False, "error": "No hay un voto emitido en esta sesión"})

    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip()
        email_confirmacion = (data.get("email_confirmacion") or "").strip()

        if not email or not email_confirmacion:
            return jsonify({"ok": False, "error": "Debe rellenar ambos campos de correo electrónico"})
        if email.lower() != email_confirmacion.lower():
            return jsonify({"ok": False, "error": "Los dos correos electrónicos introducidos no coinciden"})

        import re as re_mod
        if not re_mod.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return jsonify({"ok": False, "error": "El correo electrónico introducido no es válido"})

        import sys
        sys.path.insert(0, BASE_DIR)
        from generar_certificado import generar_pdf_certificado

        codigo = session.get("codigo_voto", "")
        pdf_bytes = generar_pdf_certificado(
            codigo   = codigo,
            nombre   = session.get("nombre", ""),
            apellidos= session.get("apellidos", ""),
            dni      = session.get("dni", ""),
            distrito = session.get("distrito", ""),
            seccion  = session.get("seccion", ""),
            mesa     = session.get("mesa", ""),
            local    = session.get("local", ""),
            fecha_hora = session.get("fecha_voto", "")
        )

        enviar_certificado_por_email(email, pdf_bytes, codigo)

        print(f"[EMAIL] Certificado enviado correctamente (destinatario no registrado en BD)")
        return jsonify({"ok": True, "mensaje": "Certificado enviado correctamente. Revise su bandeja de entrada."})

    except Exception as e:
        print(f"[ERROR enviar_certificado]: {e}")
        return jsonify({"ok": False, "error": f"No se pudo enviar el correo: {str(e)}"})


# ── RUTAS DE API ──

@app.route("/test_dni")
def test_dni():
    resultado = ejecutar_script(SCRIPT_TEST_LECTOR)
    salida = resultado["salida"]
    return jsonify({
        "ok": "LECTOR OK:" in salida,
        "salida": salida
    })

@app.route("/leer_dni")
def leer_dni():
    resultado = ejecutar_script(SCRIPT_LEER_DNI)
    salida = resultado["salida"]
    return jsonify({
        "ok": "DNI OK:" in salida,
        "salida": salida
    })

@app.route("/api/leer_dni", methods=["POST"])
def api_leer_dni():
    try:
        data = request.get_json(silent=True) or {}
        pin = (data.get("pin") or "").strip()

        if not pin:
            return jsonify({"ok": False, "error": "PIN vacío"})

        resultado = pkcs11_abrir_y_leer_certificado(pin)
        print(f"[DEBUG leer_certificado] resultado={resultado}")

        if resultado["ok"]:
            datos = resultado["datos"]

            # Guardar datos en sesión
            session["nombre"]    = datos.get("nombre", "")
            session["apellidos"] = f"{datos.get('apellido1', '')} {datos.get('apellido2', '')}".strip()
            session["dni"]       = datos.get("dni", "")
            session["dni_ok"]    = True
            session["clave_publica_pem"] = datos.get("clave_publica_pem", "")

            return jsonify({
                "ok": True,
                "nombre":    session["nombre"],
                "apellidos": session["apellidos"],
                "dni":       session["dni"]
            })
        else:
            error_txt = resultado.get("error", "Error al leer el certificado.")
            if "PIN" in error_txt.upper():
                error = "PIN incorrecto. Inténtelo de nuevo."
            elif "lector" in error_txt.lower() or "tarjeta" in error_txt.lower() or "dni" in error_txt.lower():
                error = "No se detectó el DNI en el lector."
            else:
                error = error_txt
            return jsonify({"ok": False, "error": error})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/candidatos/<candidatura>")
def api_candidatos(candidatura):
    try:
        import sqlite3 as sq
        conn = sq.connect(CANDIDATURAS_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT posicion, tipo, nombre, apellido1, apellido2
            FROM candidatos
            WHERE candidatura = ?
            ORDER BY tipo DESC, posicion ASC
        """, (candidatura.upper(),))
        rows = cur.fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "titulares": [
                {"pos": r["posicion"], "nombre": r["nombre"],
                 "apellido1": r["apellido1"], "apellido2": r["apellido2"]}
                for r in rows if r["tipo"] == "titular"
            ],
            "suplentes": [
                {"pos": r["posicion"], "nombre": r["nombre"],
                 "apellido1": r["apellido1"], "apellido2": r["apellido2"]}
                for r in rows if r["tipo"] == "suplente"
            ]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/partidos")
def api_partidos():
    """
    Lista los partidos disponibles para la pantalla de votación. Es un
    endpoint público (no requiere sesión de admin) porque lo consume el
    propio votante al cargar seleccion_partidos.html, igual que ya hace
    /api/candidatos/<letra>.
    """
    try:
        import sqlite3 as sq
        conn = sq.connect(PARTIDOS_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("SELECT letra, nombre FROM partidos ORDER BY letra")
        filas = [{"letra": r["letra"], "nombre": r["nombre"]} for r in cur.fetchall()]
        conn.close()
        return jsonify({"ok": True, "partidos": filas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


import queue

_tts_queue = queue.Queue()
_tts_motor = None

def _tts_worker():
    """Hilo único que procesa las locuciones en orden, una a una,
    evitando que pyttsx3 se pise con llamadas concurrentes."""
    global _tts_motor
    while True:
        texto = _tts_queue.get()
        if not texto:
            continue
        try:
            _tts_motor = pyttsx3.init()
            _tts_motor.setProperty('rate', 150)
            _tts_motor.setProperty('volume', 1.0)
            for voz in _tts_motor.getProperty('voices'):
                if 'spanish' in voz.name.lower() or 'es' in voz.id.lower():
                    _tts_motor.setProperty('voice', voz.id)
                    break
            _tts_motor.say(texto)
            _tts_motor.runAndWait()
            try:
                _tts_motor.stop()
            except Exception:
                pass
        except Exception as e:
            print(f"[TTS] Error: {e}")
        finally:
            _tts_motor = None

if TTS_DISPONIBLE:
    threading.Thread(target=_tts_worker, daemon=True).start()


def _hablar(texto):
    """Encola el texto para que se reproduzca en orden, sin pisarse con otras locuciones."""
    if not TTS_DISPONIBLE:
        return
    _tts_queue.put(texto)


@app.route("/api/tts/cancelar", methods=["POST"])
def api_tts_cancelar():
    """Vacía la cola pendiente y detiene la locución actual."""
    try:
        while not _tts_queue.empty():
            _tts_queue.get_nowait()
    except Exception:
        pass
    try:
        if TTS_DISPONIBLE and _tts_motor is not None:
            _tts_motor.stop()
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.get_json(silent=True) or {}
    texto = data.get("texto", "").strip()
    if texto:
        _hablar(texto)
    return jsonify({"ok": True})


@app.route("/login_admin")
def login_admin():
    return render_template("0.login_admin.html")

@app.route("/admin_panel")
def admin_panel():
    if not session.get("admin_ok"):
        return redirect(url_for("login_admin"))
    return render_template("0.admin_panel.html")

@app.route("/votacion_admin")
def votacion_admin():
    if not session.get("admin_ok"):
        return redirect(url_for("login_admin"))
    return render_template("0.votacion.html")

@app.route("/auditoria")
def auditoria():
    if not session.get("admin_ok"):
        return redirect(url_for("login_admin"))
    return render_template("0.auditoria.html")

@app.route("/bbdd")
def bbdd():
    if not session.get("admin_ok"):
        return redirect(url_for("login_admin"))
    return render_template("0.bbdd.html")

@app.route("/simulacion")
def simulacion():
    if not session.get("admin_ok"):
        return redirect(url_for("login_admin"))
    return render_template("0.simulacion.html")

@app.route("/api/login_admin", methods=["POST"])
def api_login_admin():
    data = request.get_json(silent=True) or {}
    if data.get("usuario") == ADMIN_USER and data.get("password") == ADMIN_PASS:
        session["admin_ok"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/api/logout_admin", methods=["POST"])
def api_logout_admin():
    session.pop("admin_ok", None)
    return jsonify({"ok": True})


@app.route("/api/admin/auditar_votos")
def api_admin_auditar_votos():
    """
    Verifica criptográficamente cada voto de la urna: comprueba que la
    firma guardada es válida para el mensaje (token|candidatura|fecha_hora)
    usando la clave pública guardada junto a él. No necesita el DNIe físico
    del votante, solo la clave pública que ya quedó registrada al votar.
    """
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        import sqlite3 as sq
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature

        conn = sq.connect(URNA_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("SELECT token, candidatura, fecha_hora, firma, clave_publica FROM votos ORDER BY id")
        filas = cur.fetchall()
        conn.close()

        resultados = []
        for fila in filas:
            mensaje = f"{fila['token']}|{fila['candidatura']}|{fila['fecha_hora']}".encode("utf-8")
            try:
                firma_bytes = bytes.fromhex(fila["firma"])
                clave_publica = serialization.load_pem_public_key(
                    fila["clave_publica"].encode("utf-8")
                )
                clave_publica.verify(
                    firma_bytes,
                    mensaje,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                valido = True
                error_txt = ""
            except InvalidSignature:
                valido = False
                error_txt = "Firma no válida para este mensaje"
            except Exception as e:
                valido = False
                error_txt = str(e)

            resultados.append({
                "token": fila["token"][:16] + "...",
                "candidatura": fila["candidatura"],
                "fecha_hora": fila["fecha_hora"],
                "valido": valido,
                "error": error_txt
            })

        total = len(resultados)
        validos = sum(1 for r in resultados if r["valido"])

        return jsonify({
            "ok": True,
            "total": total,
            "validos": validos,
            "invalidos": total - validos,
            "resultados": resultados
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/admin/estadisticas")
def api_admin_estadisticas():
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        import sqlite3 as sq
        conn = sq.connect(os.path.join(BASE_DIR, "database", "censo_burgos.db"))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM censo")
        total = cur.fetchone()[0]
        conn.close()

        conn_control = sq.connect(CONTROL_VOTO_HASH_DB)
        cur_control  = conn_control.cursor()
        cur_control.execute("SELECT COUNT(*) FROM control_voto_hash")
        votados = cur_control.fetchone()[0]
        conn_control.close()

        participacion = round(votados / total * 100, 2) if total > 0 else 0

        # Resultados por candidatura desde la urna (BD separada)
        resultados = []
        try:
            conn_urna = sq.connect(URNA_DB)
            cur_urna  = conn_urna.cursor()
            cur_urna.execute("SELECT candidatura, COUNT(*) as votos FROM votos GROUP BY candidatura ORDER BY votos DESC")
            filas = cur_urna.fetchall()
            conn_urna.close()
            total_votos = sum(f[1] for f in filas)
            resultados = [
                {
                    "candidatura": f[0],
                    "votos": f[1],
                    "porcentaje": round(f[1] / total_votos * 100, 1) if total_votos > 0 else 0
                }
                for f in filas
            ]
        except Exception as e:
            print(f"[ERROR estadisticas urna]: {e}")
        return jsonify({
            "ok": True,
            "total": total,
            "votados": votados,
            "participacion": participacion,
            "resultados": resultados
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/admin/resetear_votos", methods=["POST"])
def api_admin_resetear_votos():
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        import sqlite3 as sq

        # Vaciar la tabla de control de unicidad (ya no existe el campo vota)
        conn_control = sq.connect(CONTROL_VOTO_HASH_DB)
        cur_control  = conn_control.cursor()
        cur_control.execute("DELETE FROM control_voto_hash")
        filas = cur_control.rowcount
        conn_control.commit()
        conn_control.close()

        # Vaciar la urna electoral
        conn_urna = sq.connect(URNA_DB)
        conn_urna.execute("DELETE FROM votos")
        conn_urna.commit()
        conn_urna.close()

        return jsonify({"ok": True, "mensaje": f"Votos reseteados. {filas} registros de control eliminados y urna vaciada."})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)})


@app.route("/api/admin/regenerar_censo", methods=["POST"])
def api_admin_regenerar_censo():
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        data = request.get_json(silent=True) or {}
        try:
            num_votantes = int(data.get("num_votantes", 134800))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "mensaje": "El número de votantes debe ser un valor numérico"})
        if num_votantes < 1:
            return jsonify({"ok": False, "mensaje": "El número de votantes debe ser mayor que 0"})

        resultado = ejecutar_script(
            os.path.join(BASE_DIR, "generar_censo.py"),
            args=[str(num_votantes)]
        )
        ok = resultado["returncode"] == 0
        return jsonify({"ok": ok, "mensaje": f"Censo regenerado correctamente con {num_votantes} votantes." if ok else resultado["salida"]})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)})


@app.route("/api/admin/regenerar_candidaturas", methods=["POST"])
def api_admin_regenerar_candidaturas():
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        data = request.get_json(silent=True) or {}
        letra = (data.get("letra") or "").strip().upper()

        args = []
        if letra:
            if letra not in ("A", "B", "C", "D", "E", "F"):
                return jsonify({"ok": False, "mensaje": "Letra de candidatura no válida (debe ser A-F)"})
            args = [letra]

        resultado = ejecutar_script(os.path.join(BASE_DIR, "generar_candidaturas.py"), args=args)
        ok = resultado["returncode"] == 0
        if ok:
            mensaje = f"Candidatura {letra} regenerada correctamente." if letra else "Candidaturas regeneradas correctamente."
        else:
            mensaje = resultado["salida"]
        return jsonify({"ok": ok, "mensaje": mensaje})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)})


@app.route("/api/identificar", methods=["POST"])
def api_identificar():
    try:
        data = request.get_json(silent=True) or {}
        session["dni"]       = data.get("dni", "").strip()
        session["nombre"]    = data.get("nombre", "").strip()
        session["apellidos"] = data.get("apellidos", "").strip()
        session["dni_ok"]    = True
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/validar_censo", methods=["POST"])
def api_validar_censo():
    try:
        # Verificar sesión activa
        if not session.get("dni_ok"):
            return jsonify({"ok": False, "error": "Sesión no válida"})

        data = request.get_json(silent=True) or {}
        dni = session.get("dni", "").strip()
        # Fallback: usar DNI enviado en el body si no está en sesión
        if not dni:
            dni = data.get("dni_fallback", "").strip()
            if dni:
                session["dni"] = dni
                session["dni_ok"] = True
        print(f"[DEBUG censo] DNI en sesión: {repr(dni)}")
        if not dni:
            return jsonify({"ok": False, "error": "DNI no disponible en sesión"})

        # Consultar el censo real
        resultado = ejecutar_script(SCRIPT_CONSULTAR_CENSO, input_text=dni + "\n")
        salida = resultado["salida"]
        print(f"[DEBUG consultar_censo] salida={repr(salida[:200])}")

        if not salida.startswith("CENSO OK:"):
            return jsonify({"ok": False, "error": salida.replace("ERROR:", "").strip()})

        # Extraer datos del censo
        import json as json_mod
        json_str = salida[len("CENSO OK:"):].strip()
        datos = json_mod.loads(json_str)

        # Guardar datos del censo en sesión
        session["validado"]      = True
        session["direccion"]     = datos.get("direccion", "")
        session["codigo_postal"] = datos.get("codigo_postal", "")
        session["ciudad"]        = datos.get("ciudad", "")
        session["distrito"]      = datos.get("distrito", "")
        session["seccion"]       = datos.get("seccion", "")
        session["mesa"]          = datos.get("mesa", "")
        session["local"]         = datos.get("local", "")

        print(f"[DEBUG censo datos] dir={datos.get('direccion')} dist={datos.get('distrito')} sec={datos.get('seccion')} mesa={datos.get('mesa')}")

        # Comprobar voto previo consultando control_voto_hash.db (ya no existe
        # el campo vota en censo_burgos.db; el control de unicidad vive
        # ahora en una tabla separada, sin datos personales en claro).
        import sqlite3 as sq
        hash_dni = calcular_hash_dni(dni)
        conn_control = sq.connect(CONTROL_VOTO_HASH_DB)
        cur_control  = conn_control.cursor()
        cur_control.execute("SELECT 1 FROM control_voto_hash WHERE hash_dni=?", (hash_dni,))
        ya_voto = cur_control.fetchone() is not None
        conn_control.close()

        return jsonify({
            "ok":           True,
            "direccion":    datos.get("direccion", ""),
            "codigo_postal":datos.get("codigo_postal", ""),
            "ciudad":       datos.get("ciudad", ""),
            "distrito":     str(datos.get("distrito", "")),
            "seccion":      str(datos.get("seccion", "")),
            "mesa":         str(datos.get("mesa", "")),
            "local":        datos.get("local", ""),
            "vota":         "1" if ya_voto else "0"
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/emitir_voto", methods=["POST"])
def api_emitir_voto():
    try:
        # Verificar que el votante está validado
        if not session.get("validado"):
            return jsonify({"ok": False, "error": "Votante no validado"})

        # Verificar que no ha votado ya en esta sesión
        if session.get("voto_emitido"):
            return jsonify({"ok": False, "error": "Ya ha emitido su voto en esta sesión"})

        data = request.get_json(silent=True) or {}
        candidatura = data.get("candidatura", "")
        if not candidatura:
            return jsonify({"ok": False, "error": "Candidatura no especificada"})

        import secrets, sqlite3 as sq
        from datetime import datetime

        # Generar el token de la urna 
        # El justificante tiene un token aleatorio sin nada que ver con el de la urnaa 
        token        = secrets.token_hex(16).upper()
        justificante = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
        fecha_hora   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        dni = session.get("dni", "")
        if not dni:
            return jsonify({"ok": False, "error": "DNI no disponible en sesión"})

        # ── Paso 1: comprobar que el votante existe en el censo ──
        # El censo solo certifica el derecho a voto; ya NO guarda si ha votado.
        conn_censo = sq.connect(CENSO_DB)
        cur_censo  = conn_censo.cursor()
        cur_censo.execute("SELECT dni FROM censo WHERE dni=?", (dni,))
        existe = cur_censo.fetchone()
        conn_censo.close()
        if not existe:
            return jsonify({"ok": False, "error": "Votante no encontrado en el censo"})

        # ── Paso 2: comprobar unicidad mediante el hash de control ──
        # El hash depende del DNI + una clave secreta que solo conoce el servidor
        hash_dni = calcular_hash_dni(dni)

        conn_control = sq.connect(CONTROL_VOTO_HASH_DB)
        cur_control  = conn_control.cursor()
        cur_control.execute("SELECT 1 FROM control_voto_hash WHERE hash_dni=?", (hash_dni,))
        if cur_control.fetchone():
            conn_control.close()
            pkcs11_cerrar_sesion()
            return jsonify({"ok": False, "error": "Este votante ya ha ejercido su derecho al voto"})

        # ── Paso 2.5: firmar el voto con la sesión PKCS#11 ya abierta 
        mensaje_a_firmar = f"{token}|{candidatura}|{fecha_hora}"
        firma = pkcs11_firmar(mensaje_a_firmar)
        if firma is None:
            conn_control.close()
            pkcs11_cerrar_sesion()
            return jsonify({"ok": False, "error": "No se pudo firmar el voto con el DNIe. Vuelva a intentarlo."})

        
        clave_publica_pem = session.get("clave_publica_pem", "")

        # ── Paso 3 : registrar el voto 
        conn_urna = sq.connect(URNA_DB)
        conn_urna.execute(
            "INSERT INTO votos (token, candidatura, fecha_hora, firma, clave_publica) VALUES (?,?,?,?,?)",
            (token, candidatura, fecha_hora, firma, clave_publica_pem)
        )
        conn_urna.commit()
        conn_urna.close()

        # ── Paso 4 : registrar el hash en la tabla de control 
        
        try:
            cur_control.execute(
                "INSERT INTO control_voto_hash (hash_dni, fecha_hora) VALUES (?,?)",
                (hash_dni, fecha_hora)
            )
            conn_control.commit()
        finally:
            conn_control.close()

        # Cerrar sesión
        pkcs11_cerrar_sesion()

        # Guardar en sesión el JUSTIFICANTE (no el token de la urna) 
        session["voto_emitido"] = True
        session["codigo_voto"]  = justificante
        session["fecha_voto"]   = fecha_hora
        session["candidatura"]  = candidatura

        print(f"[VOTO] Token={token} Justificante={justificante} Candidatura={candidatura} Fecha={fecha_hora} Firma={firma[:16]}...")
        return jsonify({"ok": True})

    except Exception as e:
        print(f"[ERROR api_emitir_voto]: {e}")
        pkcs11_cerrar_sesion()
        return jsonify({"ok": False, "error": str(e)})


# ── GESTIÓN DE BASES DE DATOS (panel de administración) ──


def _admin_requerido():
    """Devuelve una respuesta de error si no hay sesión de admin activa, o None si todo OK."""
    if not session.get("admin_ok"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    return None


# ── CENSO 

@app.route("/api/bbdd/censo/buscar")
def api_bbdd_censo_buscar():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq

        dni       = request.args.get("dni", "").strip()
        nombre    = request.args.get("nombre", "").strip()
        apellido1 = request.args.get("apellido1", "").strip()
        apellido2 = request.args.get("apellido2", "").strip()

        condiciones = []
        valores = []
        if dni:
            condiciones.append("UPPER(dni) LIKE UPPER(?)")
            valores.append(f"%{dni}%")
        if nombre:
            condiciones.append("UPPER(nombre) LIKE UPPER(?)")
            valores.append(f"%{nombre}%")
        if apellido1:
            condiciones.append("UPPER(apellido1) LIKE UPPER(?)")
            valores.append(f"%{apellido1}%")
        if apellido2:
            condiciones.append("UPPER(apellido2) LIKE UPPER(?)")
            valores.append(f"%{apellido2}%")

        if not condiciones:
            return jsonify({"ok": False, "error": "Introduzca al menos un criterio de búsqueda"})

        where = " AND ".join(condiciones)
        conn = sq.connect(CENSO_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, nombre, apellido1, apellido2, dni, direccion, codigo_postal,
                   ciudad, distrito, seccion, mesa, local
            FROM censo
            WHERE {where}
            ORDER BY apellido1, apellido2
            LIMIT 200
        """, valores)
        filas = [dict(f) for f in cur.fetchall()]
        cur.execute(f"SELECT COUNT(*) FROM censo WHERE {where}", valores)
        total = cur.fetchone()[0]
        conn.close()

        return jsonify({
            "ok": True,
            "filas": filas,
            "total": total,
            "truncado": total > 200
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/censo/<int:registro_id>", methods=["PUT"])
def api_bbdd_censo_editar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["nombre", "apellido1", "apellido2", "dni", "direccion",
                  "codigo_postal", "ciudad", "distrito", "seccion", "mesa", "local"]
        sets = ", ".join(f"{c}=?" for c in campos)
        valores = [data.get(c, "") for c in campos]
        valores.append(registro_id)

        conn = sq.connect(CENSO_DB)
        conn.execute(f"UPDATE censo SET {sets} WHERE id=?", valores)
        conn.commit()
        filas_afectadas = conn.total_changes
        conn.close()

        if filas_afectadas == 0:
            return jsonify({"ok": False, "error": "Registro no encontrado"})
        return jsonify({"ok": True, "mensaje": "Registro actualizado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/censo/<int:registro_id>", methods=["DELETE"])
def api_bbdd_censo_eliminar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(CENSO_DB)
        conn.execute("DELETE FROM censo WHERE id=?", (registro_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro eliminado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/censo", methods=["POST"])
def api_bbdd_censo_crear():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["nombre", "apellido1", "apellido2", "dni", "direccion",
                  "codigo_postal", "ciudad", "distrito", "seccion", "mesa", "local"]
        valores = [data.get(c, "") for c in campos]
        placeholders = ",".join("?" * len(campos))

        conn = sq.connect(CENSO_DB)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO censo ({','.join(campos)}) VALUES ({placeholders})", valores)
        nuevo_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro creado correctamente", "id": nuevo_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── CANDIDATURAS 

@app.route("/api/bbdd/candidaturas")
def api_bbdd_candidaturas_listar():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(CANDIDATURAS_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, candidatura, posicion, tipo, nombre, apellido1, apellido2
            FROM candidatos
            ORDER BY candidatura, tipo DESC, posicion
        """)
        filas = [dict(f) for f in cur.fetchall()]
        conn.close()
        return jsonify({"ok": True, "filas": filas, "total": len(filas)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/candidaturas/<int:registro_id>", methods=["PUT"])
def api_bbdd_candidaturas_editar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["candidatura", "posicion", "tipo", "nombre", "apellido1", "apellido2"]
        sets = ", ".join(f"{c}=?" for c in campos)
        valores = [data.get(c, "") for c in campos]
        valores.append(registro_id)

        conn = sq.connect(CANDIDATURAS_DB)
        conn.execute(f"UPDATE candidatos SET {sets} WHERE id=?", valores)
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro actualizado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/candidaturas/<int:registro_id>", methods=["DELETE"])
def api_bbdd_candidaturas_eliminar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(CANDIDATURAS_DB)
        conn.execute("DELETE FROM candidatos WHERE id=?", (registro_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro eliminado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/candidaturas", methods=["POST"])
def api_bbdd_candidaturas_crear():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["candidatura", "posicion", "tipo", "nombre", "apellido1", "apellido2"]
        valores = [data.get(c, "") for c in campos]
        placeholders = ",".join("?" * len(campos))

        conn = sq.connect(CANDIDATURAS_DB)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO candidatos ({','.join(campos)}) VALUES ({placeholders})", valores)
        nuevo_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro creado correctamente", "id": nuevo_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── PARTIDOS 

@app.route("/api/bbdd/partidos")
def api_bbdd_partidos_listar():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(PARTIDOS_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("SELECT id, letra, nombre, siglas, color FROM partidos ORDER BY letra")
        filas = [dict(f) for f in cur.fetchall()]
        conn.close()
        return jsonify({"ok": True, "filas": filas, "total": len(filas)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/partidos/<int:registro_id>", methods=["PUT"])
def api_bbdd_partidos_editar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["letra", "nombre", "siglas", "color"]
        sets = ", ".join(f"{c}=?" for c in campos)
        valores = [data.get(c, "") for c in campos]
        valores.append(registro_id)

        conn = sq.connect(PARTIDOS_DB)
        conn.execute(f"UPDATE partidos SET {sets} WHERE id=?", valores)
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro actualizado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/partidos/<int:registro_id>", methods=["DELETE"])
def api_bbdd_partidos_eliminar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(PARTIDOS_DB)
        conn.execute("DELETE FROM partidos WHERE id=?", (registro_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro eliminado correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/partidos", methods=["POST"])
def api_bbdd_partidos_crear():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        campos = ["letra", "nombre", "siglas", "color"]
        valores = [data.get(c, "") for c in campos]
        placeholders = ",".join("?" * len(campos))

        conn = sq.connect(PARTIDOS_DB)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO partidos ({','.join(campos)}, logo) VALUES ({placeholders}, NULL)", valores)
        nuevo_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Registro creado correctamente", "id": nuevo_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── SIMULACIÓN ELECTORAL 

@app.route("/api/bbdd/simulacion")
def api_bbdd_simulacion_listar():
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(SIMULACION_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, partido, siglas, votos, tipo,
                   escanos, dif_escanos, porc_anterior, dif_votos
            FROM resultados_2023 ORDER BY votos DESC
        """)
        filas = [dict(f) for f in cur.fetchall()]
        conn.close()
        return jsonify({"ok": True, "filas": filas, "total": len(filas)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/admin/estadisticas_2023")
def api_admin_estadisticas_2023():
    """
    Devuelve las estadísticas reales de las elecciones municipales de
    Burgos del 28/05/2023, calculadas a partir de resumen_2023 y la suma
    de resultados_2023, para mostrarlas junto a las estadísticas en vivo
    del sistema de votación (panel de administración → Votación).
    """
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        conn = sq.connect(SIMULACION_DB)
        conn.row_factory = sq.Row
        cur = conn.cursor()

        cur.execute("SELECT censo_total, total_votantes, abstencion, nulos FROM resumen_2023")
        resumen = cur.fetchone()

        cur.execute("SELECT SUM(votos) AS total FROM resultados_2023")
        votos_validos = cur.fetchone()["total"] or 0

        cur.execute("SELECT votos FROM resultados_2023 WHERE tipo = 'voto_blanco'")
        fila_blanco = cur.fetchone()
        votos_blanco = fila_blanco["votos"] if fila_blanco else 0

        conn.close()

        if not resumen:
            return jsonify({"ok": False, "error": "No hay datos de resumen_2023"})

        censo_total = resumen["censo_total"]
        total_votantes = resumen["total_votantes"]
        abstencion = resumen["abstencion"]
        nulos = resumen["nulos"]
        participacion = round(total_votantes / censo_total * 100, 2) if censo_total > 0 else 0

        return jsonify({
            "ok": True,
            "censo_total": censo_total,
            "votos_validos": votos_validos,
            "votos_blanco": votos_blanco,
            "total_votantes": total_votantes,
            "abstencion": abstencion,
            "nulos": nulos,
            "participacion": participacion
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/bbdd/simulacion/<int:registro_id>", methods=["PUT"])
def api_bbdd_simulacion_editar(registro_id):
    error = _admin_requerido()
    if error: return error
    try:
        import sqlite3 as sq
        data = request.get_json(silent=True) or {}

        try:
            votos = int(data.get("votos", 0))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "El número de votos debe ser un valor numérico"})
        if votos < 0:
            return jsonify({"ok": False, "error": "El número de votos no puede ser negativo"})

        conn = sq.connect(SIMULACION_DB)
        conn.execute("UPDATE resultados_2023 SET votos=? WHERE id=?", (votos, registro_id))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": "Votos actualizados correctamente"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host="0.0.0.0", port=5000, debug=True)
