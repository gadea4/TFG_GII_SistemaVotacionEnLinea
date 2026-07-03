
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    generar_control_voto_hash.py
# =============================================================
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTROL_VOTO_HASH_DB = os.path.join(BASE_DIR, "database", "control_voto_hash.db")

def crear_control_voto_hash():
    if os.path.exists(CONTROL_VOTO_HASH_DB):
        os.remove(CONTROL_VOTO_HASH_DB)

    conn = sqlite3.connect(CONTROL_VOTO_HASH_DB)
    conn.execute("""
        CREATE TABLE control_voto_hash (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_dni    TEXT NOT NULL UNIQUE,
            fecha_hora  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Base de datos de control creada: {CONTROL_VOTO_HASH_DB}")

if __name__ == "__main__":
    crear_control_voto_hash()
