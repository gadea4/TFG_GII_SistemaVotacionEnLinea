#autor: Gadea Díez Prieto
# Script encargado de detectar los datos del dni 

import pkcs11
from pkcs11 import ObjectClass, Attribute
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import json
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
    print("ERROR: No hay DNI insertado en el lector")
    sys.exit(1)

pin = input()

try:
    with token.open(user_pin=pin) as session:

        certs = list(session.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))

        for cert in certs:
            cert_der = cert[Attribute.VALUE]
            x509_cert = x509.load_der_x509_certificate(cert_der, default_backend())

            subject = x509_cert.subject

            datos = {}

            for attr in subject:
                datos[attr.oid._name] = attr.value

            if "serialNumber" in datos:

                dni = datos.get("serialNumber", "")
                common_name = datos.get("commonName", "")

                apellido1 = ""
                apellido2 = ""
                nombre = ""

                try:
                    base = common_name.split("(")[0].strip()
                    partes = base.split(",")

                    if len(partes) == 2:
                        apellidos = partes[0].strip()
                        nombre = partes[1].strip()

                        apellidos_split = apellidos.split()

                        if len(apellidos_split) >= 2:
                            apellido1 = apellidos_split[0]
                            apellido2 = apellidos_split[1]
                        elif len(apellidos_split) == 1:
                            apellido1 = apellidos_split[0]

                except:
                    pass

                print("CERTIFICADO OK:")
                print(json.dumps({
                    "dni":       dni,
                    "nombre":    nombre,
                    "apellido1": apellido1,
                    "apellido2": apellido2
                }, ensure_ascii=False))

                break

except Exception as e:
    if "CKR_PIN" in str(e) or "pin" in str(e).lower():
        print("PIN incorrecto")
    else: 
        print(f"ERROR: {str(e)}")
    sys.exit(1)


