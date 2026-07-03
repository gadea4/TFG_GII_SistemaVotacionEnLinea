# Autora Gadea Díez 

import sqlite3
import random
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "censo_burgos.db")
os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

# Número de votantes a generar: se puede indicar como argumento de
# línea de comandos (py -3.11 generar_censo.py 50000). Si no se indica
# nada, se usa el valor por defecto de 134.800 (tamaño real aproximado
# del censo de Burgos capital).
NUM_VOTANTES = 134800
if len(sys.argv) > 1:
    try:
        NUM_VOTANTES = int(sys.argv[1])
        if NUM_VOTANTES < 1:
            print("El número de votantes debe ser mayor que 0. Usando 1.")
            NUM_VOTANTES = 1
    except ValueError:
        print(f"Argumento '{sys.argv[1]}' no es un número válido. Usando el valor por defecto (134800).")
        NUM_VOTANTES = 134800

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Elimina la tabla si ya existe para recrearla con la estructura actualizada
cursor.execute("DROP TABLE IF EXISTS censo")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS censo (
id INTEGER PRIMARY KEY,
nombre TEXT,
apellido1 TEXT,
apellido2 TEXT,
dni TEXT UNIQUE,
direccion TEXT,
codigo_postal TEXT,
ciudad TEXT,
distrito INTEGER,
seccion INTEGER,
mesa TEXT,
local TEXT
)
""")

# 100 Nombres propios frecuentes en Burgos 
nombres = [
    # Masculinos
    "Antonio", "Manuel", "José", "Francisco", "David", "Juan", "Javier", "Daniel", "Carlos", "Miguel",
    "Ángel", "Jesús", "Luis", "Rafael", "Pedro", "Alejandro", "Sergio", "Fernando", "Jorge", "Alberto",
    "Rodrigo", "Pablo", "Ignacio", "Andrés", "Diego", "Álvaro", "Rubén", "Iván", "Marcos", "Adrián",
    "Gonzalo", "Tomás", "Emilio", "Enrique", "Roberto", "Víctor", "Raúl", "Héctor", "Félix", "Agustín",
    "Julián", "Gregorio", "Valentín", "Isidro", "Hilario", "Saturio", "Primitivo", "Feliciano", "Esteban", "Bonifacio",
    # Femeninos
    "María", "Carmen", "Ana", "Isabel", "Laura", "Marta", "Sara", "Elena", "Lucía", "Paula",
    "Raquel", "Cristina", "Patricia", "Silvia", "Beatriz", "Noelia", "Nuria", "Eva", "Claudia", "Teresa",
    "Adriana", "Rosa", "Julia", "Pilar", "Dolores", "Inés", "Alicia", "Victoria", "Sandra", "Irene",
    "Rebeca", "Natalia", "Mónica", "Verónica","Esther", "Amparo", "Consuelo", "Encarnación", "Remedios", "Concepción",
    "Guadalupe", "Ascensión", "Visitación", "Purificación", "Asunción", "Esperanza", "Rosario", "Milagros", "Inmaculada", "Presentación"
]

# 100 Primeros apellidos frecuentes en Burgos 
apellidos1 = [
    "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
    "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
    "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Suárez",
    "Molina", "Morales", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias",
    "Núñez", "Medina", "Cortés", "Castillo", "Lozano", "Guerrero", "Cano", "Prieto", "Méndez", "Calvo",
    "Herrero", "Peña", "Flores", "Pascual", "Fuentes", "Vicente", "Vega", "Santamaría", "Crespo", "Ibáñez",
    "Pardo", "Velasco", "Arroyo", "Nieto", "Benito", "Montero", "Aguilar", "Moro", "Burgos", "Lastra",
    "Antón", "Sedano", "Merino", "Bravo", "Vara", "Saiz", "Salas", "Ceballos", "Barrio", "Nebreda",
    "Escudero", "Quintana", "Olmos", "Maté", "Angulo", "Barriocanal", "Revilla", "Díez", "Sastre", "Gallo",
    "Olmedo", "Marcos", "Aparicio", "Madrigal", "Cabezón", "Espinosa", "Aranda", "Cardeña", "Lerma", "Covarrubias"
]

# 100 Segundos apellidos frecuentes en Burgos 
apellidos2 = [
    "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
    "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
    "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Suárez",
    "Molina", "Morales", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias",
    "Núñez", "Medina", "Cortés", "Castillo", "Lozano", "Guerrero", "Cano", "Prieto", "Méndez", "Calvo",
    "Herrero", "Peña", "Flores", "Pascual", "Fuentes", "Vicente", "Vega", "Santamaría", "Crespo", "Ibáñez",
    "Pardo", "Velasco", "Arroyo", "Nieto", "Benito", "Montero", "Aguilar", "Moro", "Burgos", "Lastra",
    "Antón", "Sedano", "Merino", "Bravo", "Vara", "Saiz", "Salas", "Ceballos", "Barrio", "Nebreda",
    "Escudero", "Quintana", "Olmos", "Maté", "Angulo", "Barriocanal", "Revilla", "Díez", "Sastre", "Gallo",
    "Olmedo", "Marcos", "Aparicio", "Madrigal", "Cabezón", "Espinosa", "Aranda", "Cardeña", "Lerma", "Covarrubias"
]

# Calles + código postal asociado 
calles_cp = {
    # 09001 — Zona oeste, Huelgas, Villalonquejar
    "Calle Madrid":                      "09001",
    "Avenida Monasterio de Huelgas":     "09001",
    "Paseo de Comendadores":             "09001",
    "Calle Alfonso VIII":                "09001",
    "Calle Cervantes":                   "09001",
    "Paseo de Fuentecillas":             "09001",
    "Calle Calderon de la Barca":        "09001",
    "Calle Benito Pérez Galdós":         "09001",
    # 09002 — Zona sur, Gamonal sur, San Pedro
    "Calle San Pablo":                   "09002",
    "Calle Miranda":                     "09002",
    "Calle Santa Clara":                 "09002",
    "Calle San Cosme":                   "09002",
    "Calle Arlanzon":                    "09002",
    "Paseo de la Sierra de Atapuerca":   "09002",
    "Calle Ramon y Cajal":               "09002",
    "Calle Tizona":                      "09002",
    "Calle Pisuerga":                    "09002",
    "Calle San Lucas":                   "09002",
    # 09003 — Centro histórico, casco antiguo
    "Calle Laín Calvo":                  "09003",
    "Calle Paloma":                      "09003",
    "Calle Avellanos":                   "09003",
    "Calle Fernán González":             "09003",
    "Calle San Lorenzo":                 "09003",
    "Calle San Juan":                    "09003",
    "Paseo de la Isla":                  "09003",
    "Calle Huerto del Rey":              "09003",
    "Calle Lain Calvo":                  "09003",
    "Calle Santander":                   "09003",
    # 09004 — Norte, Gamonal norte, San Lesmes
    "Calle Vitoria":                     "09004",
    "Calle San Lesmes":                  "09004",
    "Avenida del Arlanzón":              "09004",
    "Calle Burgense":                    "09004",
    "Calle Anselmo Salvá":               "09004",
    "Calle Timoteo Arnaiz":              "09004",
    "Calle Menéndez Pidal":              "09004",
    # 09005 — Este, Capiscol, Fuentes Blancas
    "Avenida del Cid":                   "09005",
    "Avenida Reyes Católicos":           "09005",
    "Calle Antonio Machado":             "09005",
    "Calle Gonzalo de Berceo":           "09005",
    "Calle Juan de Valladolid":          "09005",
    "Calle Duque de Frías":              "09005",
    # 09006 — Sureste, Villímar, Gamonal
    "Calle Severo Ochoa":                "09006",
    "Avenida Cantabria":                 "09006",
    "Calle Juan Ramón Jiménez":          "09006",
    "Calle Francisco de Vitoria":        "09006",
    "Avenida Islas Canarias":            "09006",
    "Calle Enrique Granados":            "09006",
    "Calle Dos de Mayo":                 "09006",
    # 09007 — Noroeste, Cortes, Parque Fuentes
    "Calle Doctor Fleming":              "09007",
    "Calle Francisco Grandmontagne":     "09007",
    "Calle Juan de la Encina":           "09007",
}

calles = list(calles_cp.keys())


# Locales electorales reales por distrito (extraídos del BOPBUR)
locales_por_distrito = {
    1: [
        "C.P. RIO ARLANZON — CALLE VITORIA 33",
        "C.P. VENERABLES — PQUE DOCTOR VARA 2",
    ],
    2: [
        "C.P. RIO ARLANZON — CALLE VITORIA 33",
        "C.P. VENERABLES — PQUE DOCTOR VARA 2",
    ],
    3: [
        "I.E.S. CARDENAL LOPEZ DE MENDOZA — PLAZA LUIS MARTIN SANTOS 1",
        "C.P. SOLAR DEL CID — CALLE ENRIQUE III 10",
        "COLEGIO AURELIO GOMEZ ESCOLAR — AVDA COSTA RICA S/N",
    ],
    4: [
        "COLEGIO LA SALLE — AVDA DEL CID CAMPEADOR 23",
        "C.P. VENERABLES — PQUE DOCTOR VARA 2",
    ],
    5: [
        "C.P. LOS VADILLOS — CALLE PETRONILA CASADO 2",
        "C.P. ANTONIO MACHADO — CALLE SORIA S/N",
        "COLEGIO VIRGEN DE LA ROSA — AVDA CANTABRIA 33",
        "C.E.E. FRAY PEDRO PONCE DE LEON — CALLE LAS CALZADAS 6",
        "COLEGIO SAGRADA FAMILIA — PLAZA DOS DE MAYO 23",
        "C.P. MIGUEL DELIBES — CALLE VICTORIA BALFE 25",
        "I.E.S. COMUNEROS DE CASTILLA — CALLE BATALLA DE VILLALAR S/N",
        "CENTRO CULTURAL SAN CRISTOBAL — CALLE ALCALDE MARTIN COBOS S/N",
        "CENTRO CIVICO VISTA ALEGRE — CALLE VICTORIA BALFE 32",
        "ESCUELA DE ARQUITECTOS TECNICOS — AVDA CANTABRIA 57",
        "C.E.I.P. ISABEL DE BASILEA — CALLE ROSA CHACEL 4",
        "CENTRO CIVICO GAMONAL NORTE — CALLE JOSE MARIA CODON 2",
        "CENTRO CULTURAL VILLIMAR — CALLE POZA (VILLIMAR) 3",
    ],
    6: [
        "COLEGIO JESUS MARIA — CALLE DOCTOR FLEMING 1",
        "I.E.S. CARDENAL LOPEZ DE MENDOZA — PLAZA LUIS MARTIN SANTOS 1",
        "CENTRO CIVICO SAN AGUSTIN — CALLE SAN AGUSTIN 2",
        "C.P. PADRE MANJON — CALLE SALAS 9",
    ],
    7: [
        "COLEGIO JESUS MARIA — CALLE DOCTOR FLEMING 1",
        "COLEGIO LA MERCED — CALLE PADRE DIEGO LUIS SAN VITORES 1",
        "C.P. PADRE MANJON — CALLE SALAS 9",
        "CENTRO CIVICO SAN AGUSTIN — CALLE SAN AGUSTIN 2",
    ],
    8: [
        "CENTRO CIVICO SAN AGUSTIN — CALLE SAN AGUSTIN 2",
        "COLEGIO SIERRA DE ATAPUERCA — CALLE ALICANTE 3",
        "ESCUELAS PADRE ARAMBURU — CALLE QUINTANAR DE LA SIERRA 11",
        "EDIF. SERV. CENTRALES UNIVERSIDAD DE BURGOS — CALLE DON JUAN DE AUSTRIA 1",
        "I.E.S. CARDENAL LOPEZ DE MENDOZA — PLAZA LUIS MARTIN SANTOS 1",
    ],
    9: [
        "C.P. JUAN DE VALLEJO — CALLE TRAVESIA ESCUELAS 1",
        "C.P. LAS CANDELAS — CALLE LAS ESCUELAS 1",
        "C.P. MARCELIANO SANTAMARIA — PLAZA MARIE CURIE 16",
        "C.P. CLAUDIO SANCHEZ ALBORNOZ — CALLE VILLAFRANCA S/N",
        "CENTRO CIVICO CAPISCOL — CALLE FUNDACION SONSOLES BALLVE 1",
        "C.P. FERNANDO DE ROJAS — PASAJE FERNANDO DE ROJAS S/N",
        "COLEGIO APOSTOL SAN PABLO — PLAZA ROMA 2",
        "I.E.S. DIEGO MARIN AGUILERA — CTRA POZA S/N",
        "C.E.I.P. ISABEL DE BASILEA — CALLE ROSA CHACEL 4",
        "CENTRO CIVICO GAMONAL NORTE — CALLE JOSE MARIA CODON 2",
    ],
}

# Rangos de numeración real por calle de Burgos
rangos_portal = {
    "Calle Vitoria":                      (1,  120),
    "Avenida del Cid":                    (1,   80),
    "Calle Santander":                    (1,   60),
    "Calle San Pablo":                    (1,   50),
    "Avenida Reyes Católicos":            (1,  100),
    "Calle Miranda":                      (1,   70),
    "Calle Madrid":                       (1,   90),
    "Calle San Juan":                     (1,   40),
    "Paseo de la Isla":                   (1,   30),
    "Avenida Cantabria":                  (1,  120),
    "Calle San Lesmes":                   (1,   50),
    "Calle Laín Calvo":                   (1,   30),
    "Calle Paloma":                       (1,   25),
    "Calle Avellanos":                    (1,   20),
    "Calle Fernán González":              (1,   60),
    "Calle San Cosme":                    (1,   40),
    "Calle San Lorenzo":                  (1,   35),
    "Calle Santa Clara":                  (1,   45),
    "Calle Doctor Fleming":               (1,   30),
    "Calle Severo Ochoa":                 (1,   50),
    "Calle Antonio Machado":              (1,   60),
    "Calle Francisco Grandmontagne":      (1,   25),
    "Calle Juan Ramón Jiménez":           (1,   40),
    "Avenida Monasterio de Huelgas":      (1,   20),
    "Paseo de Comendadores":              (1,   15),
    "Calle Alfonso VIII":                 (1,   30),
    "Calle Cervantes":                    (1,   40),
    "Paseo de Fuentecillas":              (1,   50),
    "Calle Calderon de la Barca":         (1,   35),
    "Calle Benito Pérez Galdós":          (1,   30),
    "Calle Arlanzon":                     (1,   60),
    "Paseo de la Sierra de Atapuerca":    (1,   40),
    "Calle Ramon y Cajal":                (1,   50),
    "Calle Tizona":                       (1,   45),
    "Calle Pisuerga":                     (1,   40),
    "Calle San Lucas":                    (1,   30),
    "Calle Huerto del Rey":               (1,   15),
    "Calle Lain Calvo":                   (1,   30),
    "Calle Burgense":                     (1,   25),
    "Calle Anselmo Salvá":                (1,   20),
    "Calle Timoteo Arnaiz":               (1,   25),
    "Calle Menéndez Pidal":               (1,   30),
    "Calle Gonzalo de Berceo":            (1,   40),
    "Calle Juan de Valladolid":           (1,   30),
    "Calle Duque de Frías":               (1,   25),
    "Calle Francisco de Vitoria":         (1,   50),
    "Avenida Islas Canarias":             (1,   60),
    "Calle Enrique Granados":             (1,   30),
    "Calle Dos de Mayo":                  (1,   25),
    "Calle Juan de la Encina":            (1,   20),
    "Avenida del Arlanzón":               (1,   80),
}

# cp → (distrito, secciones_posibles, mesas_posibles)
cp_a_electoral = {
    "09001": (8,  list(range(1,  5)), ["A", "B"]),
    "09002": (3,  list(range(1,  5)), ["A", "B", "C"]),
    "09003": (1,  list(range(1,  4)), ["A", "B"]),
    "09004": (2,  list(range(1,  4)), ["A", "B"]),
    "09005": (5,  list(range(1,  9)), ["A", "B", "C"]),
    "09006": (9,  list(range(1,  7)), ["A", "B", "C"]),
    "09007": (7,  list(range(1,  4)), ["A", "B"]),
}

def asignar_electoral(cp, calle):
    """Devuelve (distrito, seccion, mesa, local) según el código postal."""
    distrito, secciones, mesas = cp_a_electoral.get(cp, (1, [1], ["A"]))
    seccion = random.choice(secciones)
    mesa    = random.choice(mesas)
    local   = random.choice(locales_por_distrito.get(distrito, ["LOCAL ELECTORAL"]))
    return distrito, seccion, mesa, local

def generar_numero_portal(calle):
    """Genera un número de portal real según el rango de la calle."""
    minimo, maximo = rangos_portal.get(calle, (1, 100))
    return random.randint(minimo, maximo)

# Letras DNI
letras = "TRWAGMYFPDXBNJZSQVHLCKE"

# Set para evitar duplicados
dnis_generados = set()

def generar_dni_unico():
    while True:
        numero = random.randint(10000000, 99999999)
        letra = letras[numero % 23]
        dni = str(numero) + letra
        if dni not in dnis_generados:
            dnis_generados.add(dni)
            return dni

inicio_id = 13000000

for i in range(NUM_VOTANTES):

    nombre    = random.choice(nombres)
    apellido1 = random.choice(apellidos1)
    apellido2 = random.choice(apellidos2)

    dni = generar_dni_unico()

    calle  = random.choice(calles)
    numero = generar_numero_portal(calle)
    piso   = random.randint(1, 8)
    puerta = random.choice(["A", "B", "C"])

    direccion     = f"{calle} {numero}, {piso}º{puerta}"
    codigo_postal = calles_cp[calle]
    distrito, seccion, mesa, local = asignar_electoral(codigo_postal, calle)

    cursor.execute("""
    INSERT INTO censo (id, nombre, apellido1, apellido2, dni, direccion, codigo_postal, ciudad, distrito, seccion, mesa, local)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inicio_id + i,
        nombre,
        apellido1,
        apellido2,
        dni,
        direccion,
        codigo_postal,
        "Burgos",
        distrito,
        seccion,
        mesa,
        local
    ))

conn.commit()
conn.close()

print(f"Censo generado correctamente: {NUM_VOTANTES} votantes en {DB_PATH}")
