#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import pandas as pd
import matplotlib.pyplot as plt

# Patrón de ficheros generados por tu script Python
GLOB = "*_performancePython.csv"

# Columnas esperadas (en español)
COL_ITER   = "Iteración"
COL_ALG    = "SPHINCS+ Version"
COL_KEYGEN = "Tiempo Generación Claves"
COL_SIGN   = "Tiempo Firma"
COL_VERIFY = "Tiempo Verificación"
COL_TOTAL  = "Tiempo Total"

def cargar_csvs():
    rutas = sorted(glob.glob(GLOB))
    if not rutas:
        print("[ERROR] No se encontraron CSV que coincidan con", GLOB)
        return {}

    datos = {}  # alg -> DataFrame
    for ruta in rutas:
        try:
            df = pd.read_csv(ruta)
            # Verifica cabeceras esperadas
            expected = {COL_ITER, COL_ALG, COL_KEYGEN, COL_SIGN, COL_VERIFY, COL_TOTAL}
            if not expected.issubset(df.columns):
                print(f"[WARN] Cabeceras inesperadas en {ruta}. Se omite.")
                continue

            # Nombre del algoritmo: usa la columna del propio CSV
            algs = df[COL_ALG].unique()
            if len(algs) != 1:
                print(f"[WARN] {ruta}: se esperaría un único algoritmo, encontrados {algs}. Se usa el primero.")
            alg = str(algs[0])

            # Asegura datos como float
            for c in [COL_KEYGEN, COL_SIGN, COL_VERIFY, COL_TOTAL]:
                df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.dropna(subset=[COL_KEYGEN, COL_SIGN, COL_VERIFY, COL_TOTAL]).reset_index(drop=True)
            if df.empty:
                print(f"[WARN] {ruta}: sin datos numéricos válidos. Se omite.")
                continue

            datos[alg] = df
            print(f"[OK] Cargado {ruta} -> {alg} ({len(df)} filas).")
        except Exception as e:
            print(f"[WARN] No se pudo leer {ruta}: {e}")

    return datos

def boxplot_por_operacion(datos, operacion, columna, outfile):
    """Genera un boxplot de una sola operación para todas las variantes."""
    if not datos:
        print("[ERROR] Sin datos para graficar.")
        return

    labels = []
    series = []
    for alg, df in datos.items():
        labels.append(alg)
        series.append(df[columna].values)

    plt.figure(figsize=(12, 6))
    plt.boxplot(series, showfliers=False)  # sin outliers para que se compare mejor
    plt.xticks(range(1, len(labels)+1), labels, rotation=30, ha="right")
    plt.ylabel("Tiempo (ms)")
    plt.title(f"SPHINCS+ (Python / pqcrypto) – Boxplot {operacion} – versión de referencia Python")
    plt.tight_layout()
    plt.savefig(outfile, dpi=180)
    plt.close()
    print(f"[OK] Guardado {outfile}")

def boxplot_4paneles(datos, outfile):
    """Un solo PNG con 4 paneles: KeyGen, Sign, Verify, Total."""
    if not datos:
        print("[ERROR] Sin datos para graficar.")
        return

    labels = list(datos.keys())
    keygen = [datos[a][COL_KEYGEN].values for a in labels]
    sign   = [datos[a][COL_SIGN].values   for a in labels]
    verify = [datos[a][COL_VERIFY].values for a in labels]
    total  = [datos[a][COL_TOTAL].values  for a in labels]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    panels = [
        ("KeyGen", keygen, axes[0,0]),
        ("Sign",   sign,   axes[0,1]),
        ("Verify", verify, axes[1,0]),
        ("Total",  total,  axes[1,1]),
    ]
    for title, data, ax in panels:
        ax.boxplot(data, showfliers=False)
        ax.set_title(title)
        ax.set_xticks(range(1, len(labels)+1))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel("Tiempo (ms)")

    fig.suptitle("SPHINCS+ (Python / pqcrypto) – Boxplots por operación – versión de referencia Python", y=0.995)
    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    plt.savefig(outfile, dpi=180)
    plt.close()
    print(f"[OK] Guardado {outfile}")

def main():
    datos = cargar_csvs()
    if not datos:
        print("No se encontraron CSV válidos.")
        return

    os.makedirs("plots_sphincs_py", exist_ok=True)

    # Un PNG por operación
    boxplot_por_operacion(datos, "KeyGen", COL_KEYGEN, "plots_sphincs_py/py_boxplot_keygen.png")
    boxplot_por_operacion(datos, "Sign",   COL_SIGN,   "plots_sphincs_py/py_boxplot_sign.png")
    boxplot_por_operacion(datos, "Verify", COL_VERIFY, "plots_sphincs_py/py_boxplot_verify.png")
    boxplot_por_operacion(datos, "Total",  COL_TOTAL,  "plots_sphincs_py/py_boxplot_total.png")

    # Figura combinada 2x2
    boxplot_4paneles(datos, "plots_sphincs_py/py_boxplot_4paneles.png")

if __name__ == "__main__":
    main()
