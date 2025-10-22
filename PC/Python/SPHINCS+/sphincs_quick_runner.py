#!/usr/bin/env python3
import argparse, time, os, sys, secrets

def do_fake_work(iters: int, fast: bool):
    # Evita escribir a stdout: el medidor usa /usr/bin/time y stdout debe quedar limpio.
    # "fast": hace trabajo mínimo; si fast=False, hace un poco más para tener wall>0.
    base_sleep = 0.05 if fast else 0.20
    for _ in range(iters):
        # Consumo un poco de CPU y memoria temporal
        _ = secrets.token_bytes(32)
        time.sleep(base_sleep)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("variant", type=str, help="sha2-128s|sha2-192s|sha2-256s|shake-128s|shake-192s|shake-256s")
    p.add_argument("--iters", type=int, default=3)
    p.add_argument("--fast", action="store_true")
    args = p.parse_args()

    # Si tienes pyspx instalado y quieres “real”:
    # try:
    #     import pyspx.sha2_128s as sphincs  # etc. según args.variant
    #     # Ejecuta keygen+sign+verify 'args.iters' veces aquí...
    # except Exception:
    #     do_fake_work(args.iters, args.fast)

    do_fake_work(args.iters, args.fast)

if __name__ == "__main__":
    # No imprimir nada a stdout (para no romper el parseo del medidor).
    try:
        main()
    except Exception:
        # Imprime a stderr solo para depurar si hiciera falta
        print("Runner error", file=sys.stderr)
        sys.exit(1)
