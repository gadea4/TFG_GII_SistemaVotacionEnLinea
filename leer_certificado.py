#autor: Gadea Díez Prieto
# Script encargado de detectar los datos del dni 

import pkcs11
from pkcs11 import ObjectClass, Attribute 

lib = pkcs11.lib(r'C:\Program Files\OpenSC Project\OpenSC\pkcs11\opensc-pkcs11.dll')

for slot in lib.get_slots():
    token = slot.get_token()
    pin = input()
    with token.open(user_pin=pin) as session:
        certs=list(session.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))
        print("Certificado encontrado")
        for cert in certs: 
            print(cert[Attribute.VALUE])
