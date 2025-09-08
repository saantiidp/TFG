#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kyber C/C++ — Boxplot por operación (6 versiones: 512/768/1024 y sus AVX2)

Lee los CSV:
  resKyber512.csv, resKyber768.csv, resKyber1024.csv
  resKyber512avx2.csv, resKyber768avx2.csv, resKyber1024avx2.csv

Detecta de forma flexible las columnas de:
  - Keygen (ms)
  - Encapsulación (ms)
  - Decapsulación (ms)

Salida:
  kyber_6versiones_boxplot_por_operacion.png
"""

import os, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

FILES = {
    "kyber512": "resKyber512.csv",
    "kyber768": "resKyber768.csv",
    "kyber1024": "resKyber1024.csv",
    "kyber512_avx2": "resKyber512avx2.csv",
    "kyber768_avx2": "resKyber768avx2.csv",
    "kyber1024_avx2": "resKyber1024avx2.csv",
}

PALETTE = {
    "kyber512": "#4c78a8",
    "kyber768": "#f58518",
    "kyber1024": "#54a24b",
    "kyber512_avx2": "#72b7b2",
    "kyber768_avx2": "#ff9da6",
    "kyber1024_avx2": "#9ccc65",
}

def to_float(val):
    """Soporta coma/punto decimal y miles mezclados; tolera NaN/float/str."""
    try:
        if pd.isna(val):
            return np.nan
    except Exception:
        pass
    s = str(val).strip()
    if s == "":
        return np.nan
    # Si hay ambos, el último es decimal.
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    # Quitar miles si quedaran: 1.234.567.89 -> 1234567.89
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return np.nan

def read_csv_robust(path):
    # usa sep=None para autodescubrir separador
    df = pd.read_csv(path, sep=None, engine="python", dtype=str)
    # normaliza nombres
    df.columns = [re.sub(r"\s+", " ", c).strip() for c in df.columns]
    return df

def detect_col(df, patterns):
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in df.columns:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

def extract_ops(df):
    """Devuelve dict {'key','enc','dec'} con Series numéricas en ms si existen."""
    # Patrones habituales
    p_key = [r"key(\s*gen|\s*generation)?(\s*\(ms\))?", r"^keygen", r"\bkg\b"]
    p_enc = [r"encaps(ulation)?(\s*\(ms\))?", r"\benc(\s*\(ms\))?$", r"cipher.?time", r"^enc$", r"^encaps$"]
    p_dec = [r"decaps(ulation)?(\s*\(ms\))?", r"\bdec(\s*\(ms\))?$", r"decipher.?time", r"^decaps?$"]

    key_c = detect_col(df, p_key)
    enc_c = detect_col(df, p_enc)
    dec_c = detect_col(df, p_dec)

    out = {}
    if key_c: out["key"] = df[key_c].map(to_float)
    if enc_c: out["enc"] = df[enc_c].map(to_float)
    if dec_c: out["dec"] = df[dec_c].map(to_float)

    # Si faltan columnas pero existe "Total", intenta reconstruir si hay sumandos
    tot_c = detect_col(df, [r"total(\s*\(ms\))?", r"tiempo\s*total"])
    if tot_c:
        total = df[tot_c].map(to_float)
        if "key" not in out and enc_c and dec_c:
            out["key"] = total - df[enc_c].map(to_float) - df[dec_c].map(to_float)
        if "enc" not in out and key_c and dec_c:
            out["enc"] = total - df[key_c].map(to_float) - df[dec_c].map(to_float)
        if "dec" not in out and key_c and enc_c:
            out["dec"] = total - df[key_c].map(to_float) - df[enc_c].map(to_float)

    return out

def load_all(files_map):
    frames = []
    for label, path in files_map.items():
        if not os.path.exists(path):
            continue
        df = read_csv_robust(path)
        ops = extract_ops(df)
        for op, serie in [("Keygen","key"), ("Encapsulación","enc"), ("Decapsulación","dec")]:
            if serie in ops:
                vals = pd.to_numeric(ops[serie], errors="coerce").dropna().values
                if len(vals):
                    frames.append(pd.DataFrame({"Versión": label, "Operación": op, "Tiempo (ms)": vals}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Versión","Operación","Tiempo (ms)"])

def plot_by_op(data, outfile="kyber_6versiones_boxplot_por_operacion.png", logy=True):
    order_versions = ["kyber512_avx2","kyber768_avx2","kyber1024_avx2","kyber512","kyber768","kyber1024"]
    versions = [v for v in order_versions if (data["Versión"]==v).any()]
    ops_order = [op for op in ["Keygen","Encapsulación","Decapsulación"] if (data["Operación"]==op).any()]

    group_gap, box_w = 1.6, 0.22
    centers = np.arange(len(ops_order)) * group_gap + 1.0
    positions, series, owners = [], [], []

    for gi, op in enumerate(ops_order):
        offs = np.linspace(-box_w*(len(versions)-1), box_w*(len(versions)-1), len(versions))/2
        for vi, v in enumerate(versions):
            vals = data[(data["Versión"]==v) & (data["Operación"]==op)]["Tiempo (ms)"].values
            if len(vals)==0: vals = np.array([np.nan])
            positions.append(centers[gi] + offs[vi]); series.append(vals); owners.append(v)

    valid = [s[~np.isnan(s)] for s in series if len(s)>0 and not np.all(np.isnan(s))]
    all_vals = np.concatenate(valid) if valid else np.array([1.0])
    p1, p99 = np.percentile(all_vals, [1,99]) if all_vals.size>0 else (1e-3, 1.0)
    ymin, ymax = max(p1/1.5, 1e-3), p99*1.5

    plt.figure(figsize=(14,6))
    bp = plt.boxplot(series, positions=positions, widths=box_w*0.95,
                     showfliers=True, patch_artist=True,
                     medianprops=dict(linewidth=2, color="black"),
                     whiskerprops=dict(linewidth=1.3),
                     capprops=dict(linewidth=1.3),
                     boxprops=dict(linewidth=1.3))

    for box, v in zip(bp["boxes"], owners):
        c = PALETTE.get(v, "#777777")
        box.set_facecolor(c); box.set_edgecolor(c); box.set_alpha(0.75)

    plt.xticks(centers, ops_order)
    plt.ylabel("Tiempo (ms)")
    plt.xlabel("Operación")
    plt.title("Kyber — Comparación por operación")
    if logy:
        plt.yscale("log")
    plt.ylim(ymin, ymax)
    plt.grid(True, which="both", axis="y", ls="--", alpha=0.5)

    handles = [Patch(facecolor=PALETTE[v], edgecolor=PALETTE[v], alpha=0.75, label=v) for v in versions]
    plt.legend(handles=handles, title="Versión", loc="upper left", ncol=2)
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    print(f"Gráfico guardado: {outfile}")

def main():
    data = load_all(FILES)
    if data.empty:
        raise SystemExit("No se pudieron cargar datos de los CSV (¿faltan columnas de Keygen/Enc/Dec?).")
    plot_by_op(data)

if __name__ == "__main__":
    main()