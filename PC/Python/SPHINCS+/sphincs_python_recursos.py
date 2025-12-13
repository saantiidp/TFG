#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import csv
import threading
import importlib
from pathlib import Path

import psutil

# --- Configuración ---
ITERS = int(os.environ.get("ITERS", "200"))         # iteraciones por variante
SAMPLE_MS = int(os.environ.get("SAMPLE_MS", "50"))  # periodo de muestreo CPU/RAM (ms)
OUTDIR = Path(".")
OUTDIR.mkdir(exist_ok=True)

# Variantes (puedes añadir las "f": shake_128f, etc.)
VARIANTES = [
    ("SHAKE-128s", "pyspx.shake_128s"),
    ("SHAKE-192s", "pyspx.shake_192s"),
    ("SHAKE-256s", "pyspx.shake_256s"),
    ("SHA2-128s",  "pyspx.sha2_128s"),
    ("SHA2-192s",  "pyspx.sha2_192s"),
    ("SHA2-256s",  "pyspx.sha2_256s"),
]

def medir_todas():
    resumen_rows = []
    for nombre, modulo in VARIANTES:
        try:
            resumen_rows.append(medir_una(nombre, modulo))
        except Exception as e:
            print(f"[WARN] {nombre}: {e}. Se omite esta variante.")
    # CSV resumen
    resumen_csv = OUTDIR / "sphincs_python_resources_summary.csv"
    with open(resumen_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LENGUAJE","VERSION","TIEMPO_TOTAL_EJECUCION(s)","USO_CPU(%)",
                    "MEMORIA_RESIDENTE_USO_MAXIMO(Kbytes)"])
        for r in resumen_rows:
            w.writerow(r)
    print(f"[OK] Resumen: {resumen_csv}")

def medir_una(nombre, modulo):
    print(f"[INFO] Importando {modulo} ({nombre}) ...")
    spx = importlib.import_module(modulo)

    # --- Trabajo CPU-bound ---
    msg = b"A" * 2048

    # Claves iniciales
    seed = os.urandom(spx.crypto_sign_SEEDBYTES)
    pk, sk = spx.generate_keypair(seed)

    def workload():
        nonlocal pk, sk
        for i in range(ITERS):
            # cada 7 iteraciones regeneramos claves para estresar un poco más
            if (i % 7) == 0:
                seed2 = os.urandom(spx.crypto_sign_SEEDBYTES)
                pk, sk = spx.generate_keypair(seed2)
            sig = spx.sign(msg, sk)
            assert spx.verify(msg, sig, pk)

    # --- Muestreador CPU/RAM ---
    proc = psutil.Process()
    stop_evt = threading.Event()
    cpu_samples = []
    rss_peak = 0

    proc.cpu_percent(interval=None)  # “primer disparo” para medir deltas

    def sampler():
        nonlocal rss_peak
        step = max(SAMPLE_MS, 10) / 1000.0
        while not stop_evt.is_set():
            cpu = proc.cpu_percent(interval=step)  # media del intervalo
            cpu_samples.append(cpu)
            try:
                mem = proc.memory_info().rss  # bytes
                if mem > rss_peak:
                    rss_peak = mem
            except psutil.Error:
                pass

    t_samp = threading.Thread(target=sampler, daemon=True)

    # --- Medida de tiempo total ---
    t0 = time.perf_counter()
    t_samp.start()
    workload()
    stop_evt.set()
    t_samp.join()
    t1 = time.perf_counter()

    elapsed = t1 - t0
    cpu_mean = round(sum(cpu_samples)/len(cpu_samples), 2) if cpu_samples else 0.0
    rss_kb = int(rss_peak // 1024)

    # CSV por variante
    per_csv = OUTDIR / f"{nombre.lower().replace('-','_')}_resourcesPython.csv"
    with open(per_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant","elapsed_s","cpu_percent_mean","rss_peak_kbytes","iters","sample_ms"])
        w.writerow([nombre, f"{elapsed:.3f}", f"{cpu_mean:.2f}", rss_kb, ITERS, SAMPLE_MS])
    print(f"[DONE] {nombre}: t={elapsed:.3f}s  CPU≈{cpu_mean:.0f}%  RSSmax={rss_kb} KB")

    # Fila para la tabla estilo “consumo de recursos”
    return ["C (Python)", f"SPHINCS+ {nombre}", f"{elapsed:.2f}", f"{cpu_mean:.0f} %", rss_kb]

if __name__ == "__main__":
    medir_todas()
