#autor: Gadea Díez Prieto
# Script encargado de detectar los datos del dni 

import pkcs11

lib = pkcs11.lib(r'C:\Program Files\OpenSC Project\OpenSC\pkcs11\opensc-pkcs11.dll')

for slot in lib.get_slots():
    token = slot.get_token()
    with token.open(user_pin="0000") as session:
        print("Conexión OK")
