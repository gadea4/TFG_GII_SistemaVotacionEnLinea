# -*- coding: utf-8 -*-
# Genera candidaturas_burgos.db con 6 candidaturas (A-F)
# 23 candidatos

import sqlite3
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CENSO_DB = os.path.join(BASE_DIR, "database", "censo_burgos.db")
CAND_DB  = os.path.join(BASE_DIR, "database", "candidaturas_burgos.db")

# Nombres masculinos y femeninos típicos españoles para clasificar
NOMBRES_FEMENINOS = {
    'ANA','MARÍA','LAURA','CARMEN','ISABEL','SARA','LUCÍA','PAULA','ELENA',
    'MARTA','PILAR','ROSA','PATRICIA','CRISTINA','BEATRIZ','SILVIA','NURIA',
    'RAQUEL','MÓNICA','VIRGINIA','EVA','JULIA','TERESA','MERCEDES','AMPARO',
    'REMEDIOS','VICTORIA','ESTHER','BLANCA','YOLANDA','SONIA','REBECA',
    'NATALIA','LETICIA','ANDREA','MIRIAM','ALBA','IRENE','VERÓNICA','SUSANA',
    'ROCÍO','CONCEPCIÓN','DOLORES','MANUELA','JOSEFA','FRANCISCA','ANTONIA',
    'ENCARNACIÓN','MARGARITA','INMACULADA','MONTSERRAT','LORENA','CLAUDIA',
    'DANIELA','SOFÍA','EMMA','VERA','ALICIA','CAROLINA','GLORIA','ANGELINES',
    'ÁNGELA','PENÉLOPE','PALOMA','SOLEDAD','MARINA','RUTH','LOURDES',
    'ESPERANZA','CONSUELO','ALEJANDRA','LAIA','ARIADNA','NAIA','AITANA'
}

def es_mujer(nombre):
    return nombre.upper().split()[0] in NOMBRES_FEMENINOS

# Leer censo
censo_conn = sqlite3.connect(CENSO_DB)
censo_conn.row_factory = sqlite3.Row
cur_censo = censo_conn.cursor()

cur_censo.execute("SELECT nombre, apellido1, apellido2 FROM censo ORDER BY RANDOM()")
todos = cur_censo.fetchall()
censo_conn.close()

# Separar por sexo
hombres = [(r['nombre'], r['apellido1'], r['apellido2']) for r in todos if not es_mujer(r['nombre'])]
mujeres = [(r['nombre'], r['apellido1'], r['apellido2']) for r in todos if es_mujer(r['nombre'])]

print(f"Hombres disponibles: {len(hombres)}")
print(f"Mujeres disponibles: {len(mujeres)}")

# Crear BD de candidaturas
if os.path.exists(CAND_DB):
    os.remove(CAND_DB)

cand_conn = sqlite3.connect(CAND_DB)
cur_cand = cand_conn.cursor()

cur_cand.execute("""
    CREATE TABLE candidatos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        candidatura TEXT NOT NULL,
        posicion    INTEGER NOT NULL,
        tipo        TEXT NOT NULL CHECK(tipo IN ('titular','suplente')),
        nombre      TEXT NOT NULL,
        apellido1   TEXT NOT NULL,
        apellido2   TEXT NOT NULL
    )
""")

candidaturas = ['A', 'B', 'C', 'D', 'E', 'F']
h_idx = 0
m_idx = 0

for cand in candidaturas:
    print(f"\nCandidatura {cand}:")
    # 20 titulares con paridad: H, M, H, M, ...
    for pos in range(1, 21):
        if pos % 2 == 1:  # posición impar → hombre
            nombre, ap1, ap2 = hombres[h_idx]
            h_idx += 1
        else:             # posición par → mujer
            nombre, ap1, ap2 = mujeres[m_idx]
            m_idx += 1

        cur_cand.execute(
            "INSERT INTO candidatos (candidatura, posicion, tipo, nombre, apellido1, apellido2) VALUES (?,?,?,?,?,?)",
            (cand, pos, 'titular', nombre, ap1, ap2)
        )
        print(f"  {pos:2d}. {'H' if pos%2==1 else 'M'} {nombre} {ap1} {ap2}")

    # 3 suplentes con paridad: H, M, H
    for pos, sexo in enumerate(['H', 'M', 'H'], start=1):
        if sexo == 'H':
            nombre, ap1, ap2 = hombres[h_idx]
            h_idx += 1
        else:
            nombre, ap1, ap2 = mujeres[m_idx]
            m_idx += 1

        cur_cand.execute(
            "INSERT INTO candidatos (candidatura, posicion, tipo, nombre, apellido1, apellido2) VALUES (?,?,?,?,?,?)",
            (cand, pos, 'suplente', nombre, ap1, ap2)
        )
        print(f"  S{pos}. {sexo} {nombre} {ap1} {ap2}")

cand_conn.commit()

# Verificar
cur_cand.execute("SELECT candidatura, COUNT(*) as total FROM candidatos GROUP BY candidatura")
for row in cur_cand.fetchall():
    print(f"\nCandidatura {row[0]}: {row[1]} candidatos")

cand_conn.close()
print("\n✔ Base de datos candidaturas_burgos.db creada correctamente")

