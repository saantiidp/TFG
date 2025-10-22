#!/usr/bin/env python3
# Ejecuta un trabajo “mínimo razonable” de Dilithium puro-Python
# sobre un mensaje de longitud indicada, para que /usr/bin/time mida
# Wall/CPU/RSS del intérprete ejecutando la carga.

import argparse, os, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--level", type=int, required=True)       # 2, 3, 5
    p.add_argument("--msg-bytes", type=int, required=True)   # tamaño mensaje
    args = p.parse_args()

    # Mensaje aleatorio de tamaño pedido
    m = os.urandom(args.msg_bytes)

    # --- Intenta usar tu implementación pura Python ---
    # Hay varios layouts posibles; probamos en cascada.
    # Adapta estos bloques si tu API difiere.
    try:
        # Caso 1: estilo “ml_dsa” (muy común en implementaciones educativas)
        from ml_dsa.ml_dsa import Dilithium
        d = Dilithium(args.level)
        pk, sk = d.keygen()
        sig = d.sign(sk, m)
        assert d.verify(pk, m, sig)
        return 0
    except Exception:
        pass

    try:
        # Caso 2: un módulo “dilithium” con una clase/config por nivel
        import dilithium as dl
        if hasattr(dl, "Dilithium"):
            d = dl.Dilithium(args.level)
            pk, sk = d.keygen()
            sig = d.sign(sk, m)
            assert d.verify(pk, m, sig)
            return 0
        # O bien nombres concretos por nivel (Dilithium2/3/5)
        cls = getattr(dl, f"Dilithium{args.level}", None)
        if cls:
            d = cls()
            pk, sk = d.keygen()
            sig = d.sign(sk, m)
            assert d.verify(pk, m, sig)
            return 0
    except Exception:
        pass

    # Si ninguna ruta funcionó, pide ajustar el runner.
    sys.stderr.write(
        "No pude invocar tu API de Dilithium. "
        "Edita dilithium_workload.py para usar tus funciones reales "
        "(keygen/sign/verify) en la importación correcta.\n"
    )
    sys.exit(2)

if __name__ == "__main__":
    sys.exit(main())
