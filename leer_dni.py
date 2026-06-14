
#autor: Gadea Díez Prieto
# Script encargado de detectar el dni en el lector

# Pregunta al sistema operativo que lectores hay conectados y devuelva una lista con ellos 

from smartcard.System import readers 

def detectar_dni(): 
    lista=readers()
    if lista: 
        print("Lector detectado")
    else: 
        print("No hay lector")

if __name__ == "__main__":
    detectar_dni()