
# VERSIÓN: 3
# FECHA: 29/03/2026
# HORA: (actualizar al modificar)
#
# HISTORIAL:
# v3 - Detección robusta del lector  y reintentos
# v2 - Verifica solo la presencia del lector ACS ACR3901 ICC Reader 0
# v1 - Versión inicial


import time
from smartcard.scard import (
    SCardEstablishContext,
    SCardListReaders,
    SCardReleaseContext,
    SCARD_SCOPE_USER,
    SCARD_S_SUCCESS,
)

LECTOR_OBJETIVO = "ACS ACR3901 ICC Reader 0"
REINTENTOS = 8
ESPERA_SEGUNDOS = 1.0


def listar_lectores_pcsc():
    hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)

    if hresult != SCARD_S_SUCCESS:
        return hresult, []

    try:
        hresult, lectores = SCardListReaders(hcontext, [])
        if hresult != SCARD_S_SUCCESS:
            return hresult, []

        lectores = [str(l).strip() for l in lectores]
        return SCARD_S_SUCCESS, lectores
    finally:
        SCardReleaseContext(hcontext)


def main():
    for intento in range(1, REINTENTOS + 1):
        hresult, lectores = listar_lectores_pcsc()

        if hresult == SCARD_S_SUCCESS:
            if LECTOR_OBJETIVO in lectores:
                print(f"LECTOR OK: {LECTOR_OBJETIVO}")
                return

            print(
                "ERROR: Lector no conectado -> "
                f"{LECTOR_OBJETIVO} | Detectados: {', '.join(lectores) if lectores else 'ninguno'}"
            )
        else:
            print(f"ERROR: No se pudo consultar PC/SC (código {hresult})")

        if intento < REINTENTOS:
            time.sleep(ESPERA_SEGUNDOS)

    # Si llega aquí, no se encontró tras todos los reintentos
    return


if __name__ == "__main__":
    main()

    