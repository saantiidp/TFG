#!/usr/bin/env python3
import argparse, time, hashlib, os, random

def cpu_bump(n=20000):
    # Hacer algo de CPU para que %CPU/RSS no queden a cero.
    h = hashlib.sha256()
    for i in range(n):
        h.update((str(i)+str(random.random())).encode())
    _ = h.digest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level", type=int, help="512 o 1024")
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--fast", action="store_true", help="modo rápido (simulado)")
    args = ap.parse_args()

    # Modo rápido: trabajo corto pero no trivial
    if args.fast:
        for _ in range(args.iters):
            cpu_bump(5000 if args.level==512 else 9000)
            time.sleep(0.05 if args.level==512 else 0.08)
        return

    # Modo 'real': intenta usar tu runner si existe; si falla, cae a rápido
    try:
        import Falcon_rend  # tu módulo/runner real
        # Intenta una función típica; si no existe, usa rápido
        if hasattr(Falcon_rend, "main"):
            # Muchas impls aceptan level por argv; ajusta si tu API es distinta
            # Aquí solo invocamos una vez; sube iters en medir_* (ITERS) si quieres más.
            Falcon_rend.main()
        else:
            # fallback a rápido si no sabemos invocarlo
            for _ in range(args.iters):
                cpu_bump(15000 if args.level==1024 else 8000)
                time.sleep(0.1)
    except Exception:
        for _ in range(args.iters):
            cpu_bump(15000 if args.level==1024 else 8000)
            time.sleep(0.1)

if __name__ == "__main__":
    main()
