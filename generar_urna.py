
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    generar_urna.py
# =============================================================

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URNA_DB  = os.path.join(BASE_DIR, "database", "urna_burgos.db")

def crear_urna():
    if os.path.exists(URNA_DB):
        os.remove(URNA_DB)

    conn = sqlite3.connect(URNA_DB)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE votos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            token         TEXT NOT NULL UNIQUE,
            candidatura   TEXT NOT NULL,
            fecha_hora    TEXT NOT NULL,
            firma         TEXT NOT NULL,
            clave_publica TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"Urna electoral creada: {URNA_DB}")

if __name__ == "__main__":
    crear_urna()
