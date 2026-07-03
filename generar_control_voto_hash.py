# generar_control_voto_hash.py
# Crea la base de datos de control de unicidad de votantes.
# Autora Gadea Diez 

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
