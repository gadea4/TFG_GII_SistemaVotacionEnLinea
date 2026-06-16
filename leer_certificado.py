#autor: Gadea Díez Prieto
# Script encargado de detectar los datos del dni 

import pkcs11
from pkcs11 import ObjectClass, Attribute 
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import sys

#carga la libreria OpenSC que permite conectar con el lector y el dni
lib = pkcs11.lib(r'C:\Program Files\OpenSC Project\OpenSC\pkcs11\opensc-pkcs11.dll')
token = None

#El bucle recorre todas las "posibilidades" donde puede estar la tarjeta insertada
for slot in lib.get_slots():
    try: 
        #en caso de que haya tarjeta lo guarda en token y en cuanto la encuentra no sigue mirando mas allá
        token = slot.get_token()
        break
    except: 
        pass # Si esta vacia lo ignora
if token is None: #si ha revisado todas y no hay ninguna, concluye que no hay dni
    print("No hay DNI insertado en el lector")
    sys.exit(1) #sale del programa

pin = input() #el usuario introduce el pin y lo guarda en la variable

#abre una sesion con el pin que acabamos de introducir, el with asegura cerrar la sesion
with token.open(user_pin=pin) as session:
        certs=list(session.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))
        print("Certificado encontrado")
        for cert in certs:
            cert_der=cert[Attribute.VALUE] #obtiene los datos del certificado, pero de forma que no se entiende
            x509_cert=x509.load_der_x509_certificate(cert_der, default_backend()) # lo convierte en algo entendible
            subject=x509_cert.subject #obtiene el sujeto, donde estan los datos nombre apellidos dni
            for attr in subject: 
                if attr.oid._name == "commonName":
                 partes = attr.value.split(" , ")
                 nombre=partes[1].strip()
                 apellidos=partes[0].strip()
                 print(nombre, apellidos)
