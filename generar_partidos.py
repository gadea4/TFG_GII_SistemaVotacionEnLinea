
# generar_partidos.py
# Crea la base de datos de partidos: letra, nombre, siglas, color y logo.
# Es una tabla independiente de candidaturas_burgos.db

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARTIDOS_DB = os.path.join(BASE_DIR, "database", "partidos_burgos.db")

def crear_partidos():
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

    if os.path.exists(PARTIDOS_DB):
        os.remove(PARTIDOS_DB)

    conn = sqlite3.connect(PARTIDOS_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE partidos (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            letra  TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            siglas TEXT NOT NULL,
            color  TEXT NOT NULL,
            logo   BLOB
        )
    """)

    partidos_iniciales = [
        ("A", "Partido A", "PA", "#3a7abf"),
        ("B", "Partido B", "PB", "#c0392b"),
        ("C", "Partido C", "PC", "#2e8b57"),
        ("D", "Partido D", "PD", "#e67e22"),
        ("E", "Partido E", "PE", "#8e44ad"),
        ("F", "Partido F", "PF", "#16a085"),
    ]

    for letra, nombre, siglas, color in partidos_iniciales:
        cur.execute(
            "INSERT INTO partidos (letra, nombre, siglas, color, logo) VALUES (?,?,?,?,NULL)",
            (letra, nombre, siglas, color)
        )

    conn.commit()
    conn.close()
    print(f"Base de datos de partidos creada: {PARTIDOS_DB}")
    print(f"{len(partidos_iniciales)} partidos insertados (A-F)")

if __name__ == "__main__":
    crear_partidos()

