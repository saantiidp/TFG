#!/usr/bin/env python3
import argparse, time, os, sys
# Asegura imports locales
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import falcon  # usa falcon.py del proyecto

def run_once(n: int, mlen: int) -> None:
    sk = falcon.SecretKey(n)
    pk = falcon.PublicKey(sk)
    msg = bytes(mlen)

    t0 = time.perf_counter()
    sk = falcon.SecretKey(n)
    pk = falcon.PublicKey(sk)
    t_key = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    sig = sk.sign(msg)
    t_sign = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    ok = pk.verify(msg, sig)
    t_verify = (time.perf_counter() - t0) * 1000.0
    if not ok:
        raise RuntimeError("Verificación fallida")

    # imprime algo mínimo (por si quieres ver tiempos micro)
    print(f"Falcon-{n}: keygen={t_key:.3f} ms, sign={t_sign:.3f} ms, verify={t_verify:.3f} ms")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, choices=[256,512,1024], required=True, help="tamaño Falcon")
    ap.add_argument("--iters", type=int, default=1, help="repeticiones")
    ap.add_argument("--mlen", type=int, default=31, help="tamaño mensaje (bytes)")
    args = ap.parse_args()

    for _ in range(args.iters):
        run_once(args.n, args.mlen)

if __name__ == "__main__":
    main()
