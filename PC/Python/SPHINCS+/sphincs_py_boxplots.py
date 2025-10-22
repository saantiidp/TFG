#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Carpeta de salida
OUTDIR = "plots_sphincs_py"
os.makedirs(OUTDIR, exist_ok=True)

# Patrones de CSV generados por tu script Python (pyspx)
CSV_PATTERNS = [
    "*sha2-128s*_performancePython.csv",
    "*sha2-192s*_performancePython.csv",
    "*sha2-256s*_performancePython.csv",
    "*shake-128s*_performancePython.csv",
    "*shake-192s*_performancePython.csv",
    "*shake-256s*_performancePython.csv",
]

# Columnas esperadas
COLS = ["Iteracion", "Algoritmo", "KeyGen_ms", "Sign_ms", "Verify_ms", "Total_ms"]

def cargar_csvs():
    """
    Lee todos los CSV que cumplan los patrones y devuelve un DataFrame concatenado.
    Ignora ficheros que no contengan las columnas esperadas.
    """
    frames = []
    encontrados = []
    for pat in CSV_PATTERNS:
        for path in glob.glob(pat):
            try:
                df = pd.read_csv(path)
                # Normaliza encabezados por si difieren en mayúsculas/minúsculas/espacios
                df.columns = [c.strip() for c in df.columns]
                if all(c in df.columns for c in COLS):
                    frames.append(df[COLS].copy())
                    encontrados.append(path)
                else:
                    print(f"[WARN] Cabeceras inesperadas en {path}. Se omite.")
            except Exception as e:
                print(f"[WARN] No pude leer {path}: {e}")
    if not frames:
        print("[ERROR] No se encontraron CSV válidos.")
        return None
    print("[INFO] CSV detectados:")
    for e in encontrados:
        print(f"  - {e}")
    return pd.concat(frames, ignore_index=True)

def boxplot_por_operacion(df, use_log=False):
    """
    Boxplot por operación (KeyGen, Sign, Verify, Total), agrupando por Algoritmo.
    """
    # Orden “bonito” de algoritmos si existen
    orden_alg = [
        "sha2-128s", "sha2-128f",
        "sha2-192s", "sha2-192f",
        "sha2-256s", "sha2-256f",
        "shake-128s", "shake-128f",
        "shake-192s", "shake-192f",
        "shake-256s", "shake-256f",
    ]
    algs = sorted(df["Algoritmo"].unique(), key=lambda x: (orden_alg.index(x) if x in orden_alg else 999, x))
    ops = ["KeyGen_ms", "Sign_ms", "Verify_ms", "Total_ms"]

    # 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 9), constrained_layout=True)
    axes = axes.ravel()

    for ax, op in zip(axes, ops):
        grupos = [df.loc[df["Algoritmo"] == alg, op].dropna().values for alg in algs]
        etiquetas = algs
        # Matplotlib 3.9+: usar tick_labels=
        bp = ax.boxplot(grupos, tick_labels=etiquetas, showfliers=False)

        # Rotación y alineación de las etiquetas del eje X
        ax.tick_params(axis='x', labelrotation=45)     # solo rotación
        for label in ax.get_xticklabels():             # alineación horizontal
            label.set_ha('right')

        ax.set_ylabel("Tiempo (ms)")
        ax.set_title(op.replace("_ms", "").replace("_", " ").title())

        if use_log:
            ax.set_yscale("log")
            ax.set_ylabel("Tiempo (ms, escala log)")

        ax.grid(True, linestyle="--", alpha=0.4)

    titulo = "Python (pyspx) – Versión de referencia"
    if use_log:
        titulo += " [escala log]"
    fig.suptitle(titulo, fontsize=16)

    fname = "sphincs_py_boxplot_por_operacion_log.png" if use_log else "sphincs_py_boxplot_por_operacion.png"
    out = os.path.join(OUTDIR, fname)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[OK] Guardado: {out}")

def boxplot_total(df, use_log=False):
    """
    Boxplot solo de Total_ms agrupado por Algoritmo.
    """
    orden_alg = [
        "sha2-128s", "sha2-128f",
        "sha2-192s", "sha2-192f",
        "sha2-256s", "sha2-256f",
        "shake-128s", "shake-128f",
        "shake-192s", "shake-192f",
        "shake-256s", "shake-256f",
    ]
    algs = sorted(df["Algoritmo"].unique(), key=lambda x: (orden_alg.index(x) if x in orden_alg else 999, x))
    grupos = [df.loc[df["Algoritmo"] == alg, "Total_ms"].dropna().values for alg in algs]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.boxplot(grupos, tick_labels=algs, showfliers=False)

    # Rotación y alineación
    ax.tick_params(axis='x', labelrotation=45)
    for label in ax.get_xticklabels():
        label.set_ha('right')

    ax.set_ylabel("Tiempo total (ms)")
    if use_log:
        ax.set_yscale("log")
        ax.set_ylabel("Tiempo total (ms, escala log)")

    titulo = "Python (pyspx) – Versión de referencia: Total"
    if use_log:
        titulo += " [escala log]"
    ax.set_title(titulo)
    ax.grid(True, linestyle="--", alpha=0.4)

    fname = "sphincs_py_boxplot_total_log.png" if use_log else "sphincs_py_boxplot_total.png"
    out = os.path.join(OUTDIR, fname)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[OK] Guardado: {out}")

def main():
    data = cargar_csvs()
    if data is None or data.empty:
        return
    # Asegura tipos numéricos
    for c in ["KeyGen_ms", "Sign_ms", "Verify_ms", "Total_ms"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")

    # Boxplots por operación
    boxplot_por_operacion(data, use_log=False)
    boxplot_por_operacion(data, use_log=True)

    # Boxplots de total
    boxplot_total(data, use_log=False)
    boxplot_total(data, use_log=True)

if __name__ == "__main__":
    main()
