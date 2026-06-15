#autor: Gadea Díez Prieto
# Script encargado de detectar los datos del dni 

import pkcs11
from pkcs11 import ObjectClass, Attribute 
import sys

lib = pkcs11.lib(r'C:\Program Files\OpenSC Project\OpenSC\pkcs11\opensc-pkcs11.dll')
token = None

for slot in lib.get_slots():
    try: 
        token = slot.get_token()
        break
    except: 
        pass 
if token is None: 
    print("No hay DNI insertado en el lector")
    sys.exit(1)

pin = input()

with token.open(user_pin=pin) as session:
        certs=list(session.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))
        print("Certificado encontrado")
        for cert in certs: 
            print(cert[Attribute.VALUE])
