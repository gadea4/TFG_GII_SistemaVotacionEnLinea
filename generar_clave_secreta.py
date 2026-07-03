
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    generar_clave_secreta.py
# =============================================================

import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_CLAVE = os.path.join(BASE_DIR, "clave_secreta.txt")

if os.path.exists(RUTA_CLAVE):
    print("Ya existe una clave secreta en:", RUTA_CLAVE)
    print("No se ha generado una nueva para no invalidar los hashes existentes.")
else:
    clave = secrets.token_hex(32)
    with open(RUTA_CLAVE, "w") as f:
        f.write(clave)
    print("Clave secreta generada correctamente en:", RUTA_CLAVE)
    print("Guárdala con cuidado y no la subas a ningún repositorio público.")
