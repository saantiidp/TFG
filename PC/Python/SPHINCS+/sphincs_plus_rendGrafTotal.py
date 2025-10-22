#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import time
import importlib
import secrets
from typing import Optional

# Variantes a medir (módulos de pyspx.*)
VARIANTS = [
    ("sha2-128s",  "sha2_128s"),
    ("sha2-192s",  "sha2_192s"),
    ("sha2-256s",  "sha2_256s"),
    ("shake-128s", "shake_128s"),
    ("shake-192s", "shake_192s"),
    ("shake-256s", "shake_256s"),
]

ITERATIONS  = 50         # cambia si quieres
MESSAGE_LEN = 10_000     # bytes del mensaje a firmar
CSV_NAME_FN = lambda token: f"{token}_performancePython.csv"

def _find_seed_bytes(mod) -> int:
    for cand in ("crypto_sign_SEEDBYTES", "SEEDBYTES", "seed_bytes"):
        if hasattr(mod, cand):
            return int(getattr(mod, cand))
    return 48  # fallback razonable

def _generate_keypair(mod) -> tuple[bytes, bytes]:
    seed_len = _find_seed_bytes(mod)
    seed = secrets.token_bytes(seed_len)
    pair = mod.generate_keypair(seed)
    a, b = pair
    pk, sk = (a, b) if isinstance(a, (bytes, bytearray)) else (bytes(a), bytes(b))
    return pk, sk

# ---- llamadas robustas a la API de pyspx ----

def _sign(mod, sk: bytes, msg: bytes) -> bytes:
    """
    PySPX puede exponer sign() como:
      - sign(sk, msg)   (orden A)
      - sign(msg, sk)   (orden B)
    Probamos ambas.
    """
    last_exc = None
    for fn in (
        lambda: mod.sign(sk, msg),  # orden estilo libsodium/python wrapper
        lambda: mod.sign(msg, sk),  # orden “mensaje primero”
    ):
        try:
            return fn()
        except Exception as e:
            last_exc = e
    raise last_exc

def _verify(mod, pk: bytes, msg: bytes, sig: bytes) -> bool:
    """
    PySPX puede exponer verify() como:
      - verify(pk, msg, sig)
      - verify(sig, msg, pk)
      - verify(msg, sig, pk)
    Probamos varios órdenes típicos.
    """
    for fn in (
        lambda: mod.verify(pk, msg, sig),
        lambda: mod.verify(sig, msg, pk),
        lambda: mod.verify(msg, sig, pk),
        lambda: mod.verify(pk, sig, msg),
    ):
        try:
            ok = fn()
            return bool(ok)
        except Exception:
            continue
    return False

# ----------------------------------------------

def run_backend(human_name: str, pyspx_module: str, iters: int, msg_len: int) -> Optional[str]:
    print(f"[INFO] Cargando backend {human_name} ...")
    try:
        mod = importlib.import_module(f"pyspx.{pyspx_module}")
    except Exception as e:
        print(f"[WARN] No se pudo importar {human_name}: {e}")
        return None

    out_csv = CSV_NAME_FN(human_name)
    msg = os.urandom(msg_len)

    rows = []
    for i in range(1, iters + 1):
        # Keygen
        t0 = time.perf_counter()
        pk, sk = _generate_keypair(mod)
        t1 = time.perf_counter()
        keygen_ms = (t1 - t0) * 1000.0

        # Sign
        t0 = time.perf_counter()
        sig = _sign(mod, sk, msg)
        t1 = time.perf_counter()
        sign_ms = (t1 - t0) * 1000.0

        # Verify
        t0 = time.perf_counter()
        ok = _verify(mod, pk, msg, sig)
        t1 = time.perf_counter()
        verify_ms = (t1 - t0) * 1000.0

        if not ok:
            print(f"[ERROR] Verificación fallida en {human_name}, iteración {i}")
            verify_ms = -1.0

        total_ms = keygen_ms + sign_ms + verify_ms if verify_ms >= 0 else -1.0
        rows.append((i, human_name, keygen_ms, sign_ms, verify_ms, total_ms))

        if i % 10 == 0 or i == iters:
            print(f"  {human_name}  iter {i}/{iters}  kg={keygen_ms:.2f}ms  sg={sign_ms:.2f}ms  vf={verify_ms:.2f}ms")

    # Escribir CSV
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Iteracion", "Algoritmo", "KeyGen_ms", "Sign_ms", "Verify_ms", "Total_ms"])
        for r in rows:
            i, alg, kg, sg, vf, tt = r
            w.writerow([i, alg, f"{kg:.4f}", f"{sg:.4f}", f"{vf:.4f}", f"{tt:.4f}"])

    print(f"[OK] CSV generado: {out_csv}")
    return out_csv

def main():
    print("[INFO] Iniciando benchmark Python/pyspx...")
    generated = []
    for human, modname in VARIANTS:
        csv_path = run_backend(human, modname, ITERATIONS, MESSAGE_LEN)
        if csv_path:
            generated.append(csv_path)

    if not generated:
        print("[ERROR] No se generó ningún CSV. ¿Está bien instalada la librería 'pyspx' y su API?")
    else:
        print("[INFO] CSV generados:")
        for p in generated:
            print("  -", p)

if __name__ == "__main__":
    main()
