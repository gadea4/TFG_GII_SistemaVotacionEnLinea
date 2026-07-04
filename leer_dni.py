
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    leer_dni.py
# =============================================================


import time
from smartcard.System import readers
from smartcard.scard import SCardEstablishContext, SCardReleaseContext, SCARD_SCOPE_USER

LECTOR_OBJETIVO = "ACS ACR3901 ICC Reader 0"


def detectar_dni():
    hcontext = None
    conexion = None

    try:
        lista = readers()

        if not lista:
            return "ERROR: No hay lectores disponibles"

        lector_objetivo = None
        for lector in lista:
            if str(lector).strip() == LECTOR_OBJETIVO:
                lector_objetivo = lector
                break

        if lector_objetivo is None:
            return f"ERROR: Lector no disponible -> {LECTOR_OBJETIVO}"

        conexion = lector_objetivo.createConnection()

        try:
            conexion.connect()
            resultado = f"DNI OK: Tarjeta detectada en {LECTOR_OBJETIVO}"
        except Exception:
            resultado = f"ERROR: No hay DNI insertado en {LECTOR_OBJETIVO}"
        finally:
            # Desconectar siempre
            try:
                conexion.disconnect()
            except Exception:
                pass
            # Pequeño retardo para que PC/SC libere el lector
            # antes de que PKCS#11 intente acceder
            time.sleep(0.8)

        return resultado

    except Exception as e:
        return f"ERROR: {str(e)}"

    finally:
        # Liberar contexto PC/SC explícitamente
        try:
            hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
            if hcontext:
                SCardReleaseContext(hcontext)
        except Exception:
            pass


if __name__ == "__main__":
    print(detectar_dni())
