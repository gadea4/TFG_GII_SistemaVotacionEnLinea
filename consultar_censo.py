
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    consultar_censo.py
# =============================================================

import sqlite3
import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "censo_burgos.db")


def consultar_censo(dni):
    try:
        if not os.path.exists(DB_PATH):
            return f"ERROR: No se encontró la base de datos en {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()

        cur.execute("""
            SELECT nombre, apellido1, apellido2, dni,
                   direccion, codigo_postal, ciudad,
                   distrito, seccion, mesa, local
            FROM censo
            WHERE UPPER(TRIM(dni)) = UPPER(TRIM(?))
        """, (dni,))

        fila = cur.fetchone()
        conn.close()

        if not fila:
            return f"ERROR: DNI {dni} no figura en el censo electoral"

        datos = {
            "nombre":        fila["nombre"],
            "apellido1":     fila["apellido1"],
            "apellido2":     fila["apellido2"],
            "dni":           fila["dni"],
            "direccion":     fila["direccion"],
            "codigo_postal": fila["codigo_postal"],
            "ciudad":        fila["ciudad"],
            "distrito":      fila["distrito"],
            "seccion":       fila["seccion"],
            "mesa":          fila["mesa"],
            "local":         fila["local"]
        }

        return f"CENSO OK: {json.dumps(datos, ensure_ascii=False)}"

    except Exception as e:
        return f"ERROR: {str(e)}"


if __name__ == "__main__":
    dni = sys.stdin.read().strip()
    if not dni:
        print("ERROR: DNI vacío")
    else:
        print(consultar_censo(dni))
