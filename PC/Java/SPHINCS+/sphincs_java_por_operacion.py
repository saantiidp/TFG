#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Genera boxplots por operación a partir de CSVs de SPHINCS+ (Java/BC).

Soporta dos esquemas:
1) Esquema "corto" (el tuyo, Java):
   Iteracion,Algoritmo,KeyGen_ms,Sign_ms,Verify_ms,Total_ms
2) Esquema "largo" (anterior):
   Iteración,Tipo,Tiempo Generación Claves,Tiempo Firma,Tiempo Verificación,Tiempo Total

Salida:
  - sphincs_java_boxplot_keygen.png
  - sphincs_java_boxplot_sign.png
  - sphincs_java_boxplot_verify.png
  - sphincs_java_boxplot_total.png
  - sphincs_java_boxplot_por_operacion.png  (2x2)

Uso:
  python3 sphincs_java_por_operacion.py [carpeta_csv]
  (si no se pasa carpeta, busca 'SPHINCS_iter_*.csv' en el cwd)
"""

import sys
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# -------------------- Config --------------------
DEFAULT_GLOB = "SPHINCS_iter_*.csv"   # coincide con tus archivos
TITLE_PREFIX = "SPHINCS+ Java (BC) – Boxplot por operación"

# orden preferido para el eje X (si existen)
PREFERRED_ORDER = [
    "sha2-128s","sha2-128f","sha2-192s","sha2-192f","sha2-256s","sha2-256f",
    "shake-128s","shake-128f","shake-192s","shake-192f","shake-256s","shake-256f",
]

# columnas de salida normalizadas
CANON = {
    "algo":  "Algoritmo",
    "it":    "Iteracion",
    "kg":    "KeyGen_ms",
    "sg":    "Sign_ms",
    "vf":    "Verify_ms",
    "tot":   "Total_ms",
}

COLS = {
    CANON["kg"]:  ("KeyGen (ms)",  "sphincs_java_boxplot_keygen.png"),
    CANON["sg"]:  ("Sign (ms)",    "sphincs_java_boxplot_sign.png"),
    CANON["vf"]:  ("Verify (ms)",  "sphincs_java_boxplot_verify.png"),
    CANON["tot"]: ("Total (ms)",   "sphincs_java_boxplot_total.png"),
}
# ------------------------------------------------

def find_csvs(base_dir: str | None):
    pattern = os.path.join(base_dir, DEFAULT_GLOB) if base_dir else DEFAULT_GLOB
    files = sorted(glob.glob(pattern))
    # descarta el resumen global si existe
    files = [f for f in files if "summary" not in os.path.basename(f).lower()]
    return files

def read_one(path: str) -> pd.DataFrame | None:
    """
    Lee un CSV y lo normaliza al esquema CANON*.
    Devuelve None si las cabeceras no son reconocibles.
    """
    for sep in (",", ";"):
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", sep=sep)
        except Exception:
            continue

        cols = set(df.columns)

        # Esquema CORTO (Java)
        if {"Iteracion","Algoritmo","KeyGen_ms","Sign_ms","Verify_ms","Total_ms"}.issubset(cols):
            df = df.rename(columns={
                "Iteracion": CANON["it"],
                "Algoritmo": CANON["algo"],
                "KeyGen_ms": CANON["kg"],
                "Sign_ms":   CANON["sg"],
                "Verify_ms": CANON["vf"],
                "Total_ms":  CANON["tot"],
            })
            return df

        # Esquema LARGO (anterior)
        if {"Iteración","Tipo","Tiempo Generación Claves","Tiempo Firma","Tiempo Verificación","Tiempo Total"}.issubset(cols):
            df = df.rename(columns={
                "Iteración":                  CANON["it"],
                "Tipo":                       CANON["algo"],   # usaremos esto como Algoritmo y lo transformamos abajo
                "Tiempo Generación Claves":   CANON["kg"],
                "Tiempo Firma":               CANON["sg"],
                "Tiempo Verificación":        CANON["vf"],
                "Tiempo Total":               CANON["tot"],
            })
            # Intento de mapear descripciones largas a tokens cortos
            rep = {
                "sha-2_128-bit, standard_robust": "sha2-128s",
                "sha-2_128-bit, robust":          "sha2-128f",
                "sha-2_192-bit, standard_robust": "sha2-192s",
                "sha-2_192-bit, robust":          "sha2-192f",
                "sha-2_256-bit, standard_robust": "sha2-256s",
                "sha-2_256-bit, robust":          "sha2-256f",
                "shake-128, standard_robust":     "shake-128s",
                "shake-128, robust":              "shake-128f",
                "shake-192, standard_robust":     "shake-192s",
                "shake-192, robust":              "shake-192f",
                "shake-256, standard_robust":     "shake-256s",
                "shake-256, robust":              "shake-256f",
            }
            df[CANON["algo"]] = (
                df[CANON["algo"]]
                .astype(str).str.strip().str.lower()
                .replace(rep)
                .str.replace(r"\s+", "", regex=True)
            )
            return df

    print(f"[WARN] Cabeceras inesperadas en {path}. Se omite.")
    return None

def read_all(paths):
    frames = []
    for p in paths:
        d = read_one(p)
        if d is not None:
            frames.append(d)

    if not frames:
        raise SystemExit("No se encontraron CSV válidos.")

    df = pd.concat(frames, ignore_index=True)

    # Normaliza tipos numéricos (por si hay strings)
    for c in (CANON["kg"], CANON["sg"], CANON["vf"], CANON["tot"]):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Si Algoritmo está vacío, intenta inferirlo del nombre del archivo
    mask_empty = df[CANON["algo"]].isna() | (df[CANON["algo"]].astype(str).str.strip() == "")
    if mask_empty.any():
        # No sabemos de qué fichero vienen esas filas tras concat, así que no se puede inferir bien.
        # En la práctica no debería ocurrir con tus CSV de Java.
        df = df[~mask_empty]

    # Limpia NaN
    df = df.dropna(subset=[CANON["kg"], CANON["sg"], CANON["vf"], CANON["tot"]])
    return df

def order_labels(labels):
    present = [t for t in PREFERRED_ORDER if t in labels]
    remaining = [t for t in labels if t not in present]
    return present + remaining

def boxplot_one(ax, df, metric_col, nice_name):
    groups = df.groupby(CANON["algo"])[metric_col].apply(list)
    labels = order_labels(list(groups.index))
    data = [groups[l] for l in labels]
    ax.boxplot(data, labels=labels, showmeans=True)
    ax.set_ylabel(nice_name)
    ax.set_xticklabels(labels, rotation=30, ha="right")

def save_individual(df):
    for col, (nice, outname) in COLS.items():
        fig, ax = plt.subplots(figsize=(10, 5.2))
        boxplot_one(ax, df, col, nice)
        ax.set_title(f"{TITLE_PREFIX} – {nice}")
        fig.tight_layout()
        fig.savefig(outname, dpi=180)
        plt.close(fig)
        print(f"[OK] Guardado {outname}")

def save_combined(df):
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), constrained_layout=True)
    keys = list(COLS.keys())
    for ax, col in zip(axes.ravel(), keys):
        nice, _ = COLS[col]
        boxplot_one(ax, df, col, nice)
        ax.set_title(nice)
    fig.suptitle(f"{TITLE_PREFIX}", fontsize=14)
    fig.savefig("sphincs_java_boxplot_por_operacion.png", dpi=200)
    plt.close(fig)
    print("[OK] Guardado sphincs_java_boxplot_por_operacion.png")

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else None
    csvs = find_csvs(base)
    if not csvs:
        raise SystemExit("No se encontraron CSV (patrón 'SPHINCS_iter_*.csv').")
    print(f"[INFO] CSV detectados ({len(csvs)}):")
    for f in csvs:
        print("  -", f)

    df = read_all(csvs)
    if df.empty:
        raise SystemExit("No hay datos válidos.")

    save_individual(df)
    save_combined(df)

if __name__ == "__main__":
    main()
