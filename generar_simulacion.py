
# =============================================================
# Autor:      Gadea Díez Prieto
# Tutor:      Rubén Ruiz y Nuño Basurto
# Centro:     Universidad de Burgos — Escuela Politécnica Superior
# Titulación: Grado en Ingeniería Informática
# Proyecto:   TFG — Diseño de una plataforma para la
#             digitalización del proceso electoral
# Fecha:      Curso 2025-2026
# Archivo:    generar_simulacion.py
# =============================================================

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIMULACION_DB = os.path.join(BASE_DIR, "database", "simulacion_burgos.db")

def crear_simulacion():
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

    if os.path.exists(SIMULACION_DB):
        os.remove(SIMULACION_DB)

    conn = sqlite3.connect(SIMULACION_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE resultados_2023 (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            partido         TEXT NOT NULL,
            siglas          TEXT NOT NULL,
            votos           INTEGER NOT NULL,
            tipo            TEXT NOT NULL DEFAULT 'partido',
            escanos         INTEGER NOT NULL DEFAULT 0,
            dif_escanos     INTEGER NOT NULL DEFAULT 0,
            porc_anterior   REAL    NOT NULL DEFAULT 0,
            dif_votos       INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Resultados oficiales 
    resultados = [
        ("Partido Socialista Obrero Español",                "PSOE",       29626, "partido", 12,  1, 36.20,  -3468),
        ("Partido Popular",                                   "PP",         27555, "partido", 11,  4, 25.93,   3851),
        ("VOX",                                                "VOX",        10786, "partido",  4,  2,  7.17,   4228),
        ("Podemos - Izquierda Unida - Alianza Verde",         "POD-IU-AV",   4196, "partido",  0, -2,  6.63,  -1870),
        ("Demócratas de Castilla y de Burgos",                "DCD",         3364, "partido",  0,  0,  0.00,   3364),
        ("Vecinos por Burgos",                                "VB",          2393, "partido",  0,  0,  0.00,   2393),
        ("Ciudadanos",                                        "Cs",          1957, "partido",  0, -5, 16.87, -13473),
        ("Espacio Verde - Por Castilla - Tierra Comunera",    "EV-PCAS-TC",  1092, "partido",  0,  0,  0.00,   1092),
        ("Por un Burgos del Siglo XXI / Tercer Espacio",      "3E",          1063, "partido",  0,  0,  0.00,   1063),
        ("EQUO",                                               "EQUO",         576, "partido",  0,  0,  0.00,    576),
        ("Partido Comunista de los Trabajadores de España",  "PCTE",          239, "partido",  0,  0,  0.00,    239),
        ("Partido Socialista Liberal Federal",                "P.S.L.F.",      211, "partido",  0,  0,  0.00,     21),
        ("Voto en blanco",                                    "—",            1259, "voto_blanco", 0, 0, 0.00,   1259),
    ]

    for partido, siglas, votos, tipo, escanos, dif_escanos, porc_anterior, dif_votos in resultados:
        cur.execute(
            """INSERT INTO resultados_2023
               (partido, siglas, votos, tipo, escanos, dif_escanos, porc_anterior, dif_votos)
               VALUES (?,?,?,?,?,?,?,?)""",
            (partido, siglas, votos, tipo, escanos, dif_escanos, porc_anterior, dif_votos)
        )

    # Tabla de resumen 
    cur.execute("""
        CREATE TABLE resumen_2023 (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            censo_total     INTEGER NOT NULL,
            total_votantes  INTEGER NOT NULL,
            abstencion      INTEGER NOT NULL,
            nulos           INTEGER NOT NULL
        )
    """)
    cur.execute(
        "INSERT INTO resumen_2023 (censo_total, total_votantes, abstencion, nulos) VALUES (?,?,?,?)",
        (134826, 85904, 48922, 1587)
    )

    conn.commit()
    conn.close()
    print(f"Base de datos de simulación creada: {SIMULACION_DB}")
    print(f"{len(resultados)} registros insertados (12 partidos + voto en blanco)")
    print("Tabla resumen_2023 creada con censo, abstención y nulos.")

if __name__ == "__main__":
    crear_simulacion()
