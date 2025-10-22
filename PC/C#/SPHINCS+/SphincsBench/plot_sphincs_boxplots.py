#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# --- Config ---
OUT_DIR = "plots_sphincs"
os.makedirs(OUT_DIR, exist_ok=True)

# Orden deseado para las variantes
ORDER_SHA2  = ["sha2-128s","sha2-128f","sha2-192s","sha2-192f","sha2-256s","sha2-256f"]
ORDER_SHAKE = ["shake-128s","shake-128f","shake-192s","shake-192f","shake-256s","shake-256f"]

# Mapa de columnas esperadas (por si llegan con espacios raros)
COL_MAP = {
    "Iteración": "Iteración",
    "SPHINCS+ Version": "Version",
    "Tiempo Generación Claves": "KeyGen",
    "Tiempo Firma": "Sign",
    "Tiempo Verificación": "Verify",
    "Tiempo Total": "Total",
}

def normalize_cols(df):
    # Normaliza nombres de columnas (quita espacios y unifica)
    ren = {}
    for c in df.columns:
        c2 = c.strip()
        if c2 in COL_MAP:
            ren[c] = COL_MAP[c2]
    df = df.rename(columns=ren)
    return df

def read_all_csv():
    files = sorted(glob.glob("*_performance.csv"))
    if not files:
        print("[WARN] No se encontraron CSV con patrón *_performance.csv")
    data = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df = normalize_cols(df)
            # Comprobamos columnas mínimas
            needed = {"Version","KeyGen","Sign","Verify","Total"}
            if not needed.issubset(df.columns):
                print(f"[WARN] CSV '{f}' no tiene columnas esperadas. Columnas: {list(df.columns)}")
                continue
            # La versión debería ser única dentro del fichero
            version = str(df["Version"].iloc[0]).strip()
            data.append((version, df[["KeyGen","Sign","Verify","Total"]].copy()))
            print(f"[OK] Leído: {f}  -> versión={version}, muestras={len(df)}")
        except Exception as e:
            print(f"[WARN] No se pudo leer '{f}': {e}")
    return data

def split_families(data):
    sha2  = [(v, d) for (v, d) in data if v.startswith("sha2-")]
    shake = [(v, d) for (v, d) in data if v.startswith("shake-")]
    # Ordenamos según listas definidas
    sha2.sort(key=lambda x: ORDER_SHA2.index(x[0]) if x[0] in ORDER_SHA2 else 999)
    shake.sort(key=lambda x: ORDER_SHAKE.index(x[0]) if x[0] in ORDER_SHAKE else 999)
    return sha2, shake

def make_boxplot(family_data, family_name, operation, ylabel="Tiempo (ms)", ylim=None):
    """
    family_data: lista de (version, df_con_cols KeyGen/Sign/Verify/Total)
    operation: "KeyGen" | "Sign" | "Verify" | "Total"
    """
    if not family_data:
        print(f"[INFO] Sin datos para {family_name} - {operation}")
        return

    versions = [v for (v, _) in family_data]
    series = [d[operation].values for (_, d) in family_data]

    plt.figure(figsize=(10, 5))
    bp = plt.boxplot(series, labels=versions, showmeans=True, meanline=True)
    plt.title(f"SPHINCS+ {family_name} — {operation}")
    plt.ylabel(ylabel)
    plt.xlabel("Versión")
    plt.grid(True, axis='y', linestyle='--', alpha=0.4)
    if ylim is not None:
        plt.ylim(ylim)

    out_png = os.path.join(OUT_DIR, f"box_{family_name.lower()}_{operation.lower()}.png")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"[OK] Guardado: {out_png}")

def main():
    data = read_all_csv()
    if not data:
        return

    sha2, shake = split_families(data)

    # Crea boxplots por operación y familia
    for op in ["KeyGen", "Sign", "Verify", "Total"]:
        make_boxplot(sha2,  "SHA2",  op)
        make_boxplot(shake, "SHAKE", op)

    # Resumen rápido en consola (media y desviación) por versión y operación
    print("\n=== RESUMEN (media ± desviación) ===")
    for family_name, fam in [("SHA2", sha2), ("SHAKE", shake)]:
        if not fam: 
            continue
        print(f"\n[{family_name}]")
        for (v, d) in fam:
            stats = []
            for op in ["KeyGen","Sign","Verify","Total"]:
                avg = d[op].mean()
                std = d[op].std(ddof=0)
                stats.append(f"{op}: {avg:.4f} ± {std:.4f} ms")
            print(f"  {v}:  " + " | ".join(stats))

if __name__ == "__main__":
    main()
