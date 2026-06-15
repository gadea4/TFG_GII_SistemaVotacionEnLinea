
#autor: Gadea Díez Prieto
# Script encargado de detectar el dni en el lector

# Pregunta al sistema operativo que lectores hay conectados y devuelva una lista con ellos 

from smartcard.System import readers 
LECTOR_OBJETIVO="ACS ACR3901 ICC Reader 0"

def detectar_dni(): 
    lista=readers()
    if not lista: 
        print("No hay lector")
        return
    for lector in lista :
        if str(lector).strip() == LECTOR_OBJETIVO: 
            print ("Lector detectado")
            return 
        
    print ("Lector no encontrado")
        

if __name__ == "__main__":
    detectar_dni()