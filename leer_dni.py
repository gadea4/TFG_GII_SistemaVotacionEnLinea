
#autor: Gadea Díez Prieto
# Script encargado de detectar el dni en el lector

# Pregunta al sistema operativo que lectores hay conectados y devuelva una lista con ellos 

from smartcard.System import readers 
LECTOR_OBJETIVO="ACS ACR 3901 ICC READER 0"

def detectar_dni(): 
    lista=readers()
    if lista: 
        if str(lector) == LECTOR_OBJETIVO: 
            print ("Lector detectado")
            return
    else: 
        print("No hay lector")

if __name__ == "__main__":
    detectar_dni()