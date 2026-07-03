
# generar_clave_secreta.py
# Genera la clave secreta del servidor usada para calcular el hash de
# control de unicidad de votantes (control_voto_hash.db).
# Autora: Gadea Díez 

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

